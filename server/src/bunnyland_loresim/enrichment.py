"""World-generation enrichment: tag generated wildlife and flora as observable species.

Generated entities expose semantic ``tags``/``wants``/``needs`` and an intent
``description``. This hook scans that text for *living* things — creatures and plants — and
attaches a :class:`~bunnyland_loresim.components.SpeciesComponent` so a naturalist has
something to record in generated worlds, without the core generator knowing this plugin
exists. Plain items, tools, and furniture are never tagged.

Habitat and rarity are derived from the same text so the resulting bestiary entries are
meaningful. Nothing here reads or writes any sound/hearing state — observation is a matter
of *sight and patience*, not noise.
"""

from __future__ import annotations

from bunnyland.core import IdentityComponent
from bunnyland.core.ecs import parse_entity_id, replace_component
from bunnyland.core.events import (
    CharacterGeneratedEvent,
    GeneratedEntityEvent,
    ObjectGeneratedEvent,
)
from bunnyland.core.world_actor import WorldActor

from .components import SpeciesComponent

#: Specific living subjects mapped to their habitat, checked before the generic terms.
HABITAT_BY_TERM: dict[str, str] = {
    "heron": "wetland",
    "frog": "wetland",
    "newt": "wetland",
    "dragonfly": "wetland",
    "reed": "wetland",
    "marsh": "wetland",
    "fox": "woodland",
    "deer": "woodland",
    "owl": "woodland",
    "beetle": "woodland",
    "fern": "woodland",
    "toadstool": "woodland",
    "forest": "woodland",
    "hare": "grassland",
    "lark": "grassland",
    "grasshopper": "grassland",
    "poppy": "grassland",
    "meadow": "grassland",
    "crab": "shore",
    "gull": "shore",
    "kelp": "shore",
    "tide": "shore",
    "beach": "shore",
}

#: Generic words that mark a generated entity as a living creature or plant.
LIVING_TERMS: tuple[str, ...] = (
    "creature",
    "animal",
    "beast",
    "critter",
    "wildlife",
    "fauna",
    "bird",
    "fish",
    "insect",
    "amphibian",
    "reptile",
    "mammal",
    "plant",
    "flora",
    "flower",
    "herb",
    "fungus",
    "moss",
    "tree",
    *HABITAT_BY_TERM.keys(),
)

#: Words that raise a subject's rarity above ``common``.
UNCOMMON_TERMS = ("shy", "elusive", "uncommon", "seldom", "wary")
RARE_TERMS = ("rare", "legendary", "fabled", "vanishing", "endangered", "mythic")


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


def _matched_living_term(text: str) -> str | None:
    for term in LIVING_TERMS:
        if term in text:
            return term
    return None


def _habitat_for(text: str) -> str:
    for term, habitat in HABITAT_BY_TERM.items():
        if term in text:
            return habitat
    return "wild"


def _rarity_for(text: str) -> str:
    if any(term in text for term in RARE_TERMS):
        return "rare"
    if any(term in text for term in UNCOMMON_TERMS):
        return "uncommon"
    return "common"


def _species_name(entity, event: GeneratedEntityEvent, matched: str) -> str:
    if entity.has_component(IdentityComponent):
        name = entity.get_component(IdentityComponent).name.strip()
        if name:
            return name.casefold()
    if event.entity_key:
        return event.entity_key.casefold()
    return matched


class LoreWorldgenHook:
    """Attach a :class:`SpeciesComponent` to generated living creatures and plants."""

    def subscribe(self, actor: WorldActor) -> None:
        self._actor = actor
        actor.bus.subscribe(CharacterGeneratedEvent, self._on_entity)
        actor.bus.subscribe(ObjectGeneratedEvent, self._on_entity)

    def _entity(self, entity_id: str):
        parsed = parse_entity_id(entity_id)
        if parsed is None or not self._actor.world.has_entity(parsed):
            return None
        return self._actor.world.get_entity(parsed)

    def _on_entity(self, event: GeneratedEntityEvent) -> None:
        entity = self._entity(event.entity_id)
        if entity is None or entity.has_component(SpeciesComponent):
            return
        text = _text(event)
        matched = _matched_living_term(text)
        if matched is None:
            return
        replace_component(
            entity,
            SpeciesComponent(
                species=_species_name(entity, event, matched),
                habitat=_habitat_for(text),
                rarity=_rarity_for(text),
            ),
        )


__all__ = [
    "HABITAT_BY_TERM",
    "LIVING_TERMS",
    "RARE_TERMS",
    "UNCOMMON_TERMS",
    "LoreWorldgenHook",
]
