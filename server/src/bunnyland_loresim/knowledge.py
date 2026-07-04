"""Lore payoff: a self-contained "known species" surface other packs can consult.

Recording a species is not just a journal entry — it *sharpens* the naturalist. Every
recorded species is marked "known" on an open :class:`KnownSpeciesComponent`, and the
free-function :func:`knows_species` reads it. Neither depends on any other plugin package,
so a cooking, foraging, or dialogue pack can ask "does this character know the heron?" and
branch on the answer without importing Loresim's internals.
"""

from __future__ import annotations

from bunnyland.core.ecs import replace_component
from pydantic.dataclasses import dataclass
from relics import Component, Entity, World

from .components import LoreJournalComponent


@dataclass(frozen=True)
class KnownSpeciesComponent(Component):
    """The open registry of species a character has field knowledge of (sorted, de-duped)."""

    species: tuple[str, ...] = ()


def mark_known(character: Entity, species: str) -> None:
    """Record that ``character`` now knows ``species`` (idempotent, kept sorted)."""
    current: tuple[str, ...] = ()
    if character.has_component(KnownSpeciesComponent):
        current = character.get_component(KnownSpeciesComponent).species
    if species in current:
        return
    updated = tuple(sorted({*current, species}))
    replace_component(character, KnownSpeciesComponent(species=updated))


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


def knowledge_fragments(world: World, character: Entity) -> list[str]:
    """Surface the naturalist's field knowledge (the lore payoff) in their prompt."""
    if character is None or not character.has_component(KnownSpeciesComponent):
        return []
    known = character.get_component(KnownSpeciesComponent).species
    if not known:
        return []
    listing = ", ".join(known)
    return [f"You have field knowledge of {len(known)} species: {listing}."]


__all__ = [
    "KnownSpeciesComponent",
    "knowledge_fragments",
    "knows_species",
    "mark_known",
]
