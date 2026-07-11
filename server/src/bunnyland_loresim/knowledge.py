"""Lore payoff: a self-contained "known species" surface other packs can consult.

Recording a species is not just a journal entry — it *sharpens* the naturalist. Every
recorded species is marked "known" on an open :class:`KnownSpeciesComponent`, and the
free-function :func:`knows_species` reads it. Neither depends on any other plugin package,
so a cooking, foraging, or dialogue pack can ask "does this character know the heron?" and
branch on the answer without importing Loresim's internals.

v2 **deepens** this surface. Field knowledge now has two tiers: a species you have merely
*seen and recorded* is **known**, but a species you have **published a field guide on** is
**mastered** — expert knowledge. Both tiers ride the same open component (``species`` for
known, ``mastered`` for the expert subset), so a pet-taming or hunting pack can ask not just
"does this character know the heron?" but "have they *mastered* it?" and ease handling
accordingly. ``mastered`` is always a subset of ``species``.
"""

from __future__ import annotations

from bunnyland.core.ecs import replace_component
from pydantic.dataclasses import dataclass
from relics import Component, Entity, World

from .components import LoreJournalComponent


@dataclass(frozen=True)
class KnownSpeciesComponent(Component):
    """The open registry of species a character has field knowledge of (sorted, de-duped).

    ``species`` is everything the naturalist has *recorded* (known); ``mastered`` is the
    expert subset they have *published a field guide on*. ``mastered`` is always contained in
    ``species``.
    """

    species: tuple[str, ...] = ()
    mastered: tuple[str, ...] = ()


def mark_known(character: Entity, species: str) -> None:
    """Record that ``character`` now knows ``species`` (idempotent, kept sorted)."""
    current: tuple[str, ...] = ()
    mastered: tuple[str, ...] = ()
    if character.has_component(KnownSpeciesComponent):
        component = character.get_component(KnownSpeciesComponent)
        current, mastered = component.species, component.mastered
    if species in current:
        return
    updated = tuple(sorted({*current, species}))
    replace_component(character, KnownSpeciesComponent(species=updated, mastered=mastered))


def mark_mastered(character: Entity, species: str) -> None:
    """Promote ``species`` to *mastered* (expert) knowledge, ensuring it is also known.

    Called when a naturalist publishes a field guide: mastery is the deeper payoff other
    packs consult. Idempotent and kept sorted; mastering implies knowing.
    """
    known: tuple[str, ...] = ()
    mastered: tuple[str, ...] = ()
    if character.has_component(KnownSpeciesComponent):
        component = character.get_component(KnownSpeciesComponent)
        known, mastered = component.species, component.mastered
    if species in mastered:
        return
    replace_component(
        character,
        KnownSpeciesComponent(
            species=tuple(sorted({*known, species})),
            mastered=tuple(sorted({*mastered, species})),
        ),
    )


def knows_species(world: World, character: Entity, species: str) -> bool:
    """Return whether ``character`` has field knowledge of ``species``.

    Reads the open :class:`KnownSpeciesComponent` first, then falls back to the journal so the
    answer is correct even for characters populated only through the journal.
    """
    if character.has_component(KnownSpeciesComponent):
        if species in character.get_component(KnownSpeciesComponent).species:
            return True
    if character.has_component(LoreJournalComponent):
        return species in character.get_component(LoreJournalComponent).recorded_species()
    return False


def masters_species(world: World, character: Entity, species: str) -> bool:
    """Return whether ``character`` has *expert* (published) knowledge of ``species``."""
    if not character.has_component(KnownSpeciesComponent):
        return False
    return species in character.get_component(KnownSpeciesComponent).mastered


def knowledge_fragments(world: World, character: Entity) -> list[str]:
    """Surface the naturalist's field knowledge (the lore payoff) in their prompt."""
    if character is None or not character.has_component(KnownSpeciesComponent):
        return []
    component = character.get_component(KnownSpeciesComponent)
    known = component.species
    if not known:
        return []
    lines = [f"You have field knowledge of {len(known)} species: {', '.join(known)}."]
    if component.mastered:
        lines.append(
            f"You have mastered {len(component.mastered)} species: {', '.join(component.mastered)}."
        )
    return lines


__all__ = [
    "KnownSpeciesComponent",
    "knowledge_fragments",
    "knows_species",
    "mark_known",
    "mark_mastered",
    "masters_species",
]
