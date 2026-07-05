"""World-generation enrichment (v2): seed generated field naturalists for expeditions.

v1's :class:`~bunnyland_loresim.enrichment.LoreWorldgenHook` seeds *subjects* (tagging
generated wildlife and flora as recordable species). This v2 hook seeds the other half — the
*naturalists* who record them — so a generated world is expedition-ready without the core
generator knowing this pack exists.

When the generator produces a character that reads as a field naturalist (a ranger, botanist,
zoologist, warden…), this hook gives them the field **journal** (the same memory store the
``observe`` verb and expeditions write to) and seeds a little starting field knowledge for
their local habitat on the open :class:`~bunnyland_loresim.knowledge.KnownSpeciesComponent`
surface. Habitat and seeded species are derived deterministically from the generation text —
no ``random`` or clock, and nothing about sound or hearing.
"""

from __future__ import annotations

from bunnyland.core.ecs import parse_entity_id, replace_component
from bunnyland.core.events import CharacterGeneratedEvent, GeneratedEntityEvent
from bunnyland.core.world_actor import WorldActor

from .components import LoreJournalComponent
from .expeditions import HABITAT_SPECIES
from .knowledge import mark_known

#: Words that mark a generated character as a field naturalist worth equipping.
NATURALIST_TERMS: tuple[str, ...] = (
    "naturalist",
    "ranger",
    "botanist",
    "zoologist",
    "ecologist",
    "warden",
    "field scientist",
    "lorekeeper",
)


def _text(event: GeneratedEntityEvent) -> str:
    generation = event.generation
    return " ".join(
        (
            event.entity_key,
            event.entity_kind,
            generation.description,
            *generation.tags,
            *generation.wants,
            *generation.needs,
        )
    ).casefold()


def _is_naturalist(text: str) -> bool:
    return any(term in text for term in NATURALIST_TERMS)


def _habitat_for(text: str) -> str:
    for habitat in HABITAT_SPECIES:
        if habitat in text:
            return habitat
    return "wild"


class NaturalistWorldgenHook:
    """Equip generated field naturalists with a journal and starting field knowledge."""

    def subscribe(self, actor: WorldActor) -> None:
        self._actor = actor
        actor.bus.subscribe(CharacterGeneratedEvent, self._on_character)

    def _entity(self, entity_id: str):
        parsed = parse_entity_id(entity_id)
        if parsed is None or not self._actor.world.has_entity(parsed):
            return None
        return self._actor.world.get_entity(parsed)

    def _on_character(self, event: CharacterGeneratedEvent) -> None:
        entity = self._entity(event.entity_id)
        if entity is None or entity.has_component(LoreJournalComponent):
            return
        text = _text(event)
        if not _is_naturalist(text):
            return
        replace_component(entity, LoreJournalComponent())
        habitat = _habitat_for(text)
        # Seed a single starting species of the local habitat so the naturalist begins with
        # a little field knowledge on the open KnownSpecies surface.
        mark_known(entity, HABITAT_SPECIES[habitat][0])


__all__ = ["NATURALIST_TERMS", "NaturalistWorldgenHook"]
