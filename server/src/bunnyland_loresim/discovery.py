"""Completion and discovery: first-in-world credit, habitat tallies, and the nudge fragment.

Two payoffs sit on top of the journal:

- **Discovery** — the first naturalist in the entire world to record a species earns a
  discovery credit (tracked in their journal's ``discoveries``). :func:`is_first_in_world`
  scans every journal so the credit is unambiguous and self-contained.
- **Completion** — the journal is tallied by habitat, and a prompt fragment both reports the
  running total and *nudges* the naturalist toward an unrecorded subject standing in the room
  ("a heron here is unrecorded"), which is the whole loop: see it, record it, know it.
"""

from __future__ import annotations

from bunnyland.core import IdentityComponent
from bunnyland.core.ecs import reachable_ids
from relics import Entity, World

from .components import LoreJournalComponent, SpeciesComponent


def is_first_in_world(world: World, species: str) -> bool:
    """Return whether *no* journal in the world has recorded ``species`` yet."""
    for entity in world.query().with_all([LoreJournalComponent]).execute_entities():
        if species in entity.get_component(LoreJournalComponent).recorded_species():
            return False
    return True


def completion_by_habitat(journal: LoreJournalComponent) -> dict[str, int]:
    """Return how many distinct species the journal holds per habitat, sorted by habitat."""
    tally: dict[str, int] = {}
    for record in journal.records:
        tally[record.habitat] = tally.get(record.habitat, 0) + 1
    return dict(sorted(tally.items()))


def _subject_name(entity: Entity, species: str) -> str:
    if entity.has_component(IdentityComponent):
        name = entity.get_component(IdentityComponent).name.strip()
        if name:
            return name
    return species


def _unrecorded_here(world: World, character: Entity, journal: LoreJournalComponent) -> list[str]:
    """Names of species-bearing subjects the character can see here but has not recorded."""
    known = set(journal.recorded_species())
    seen: set[str] = set()
    names: list[str] = []
    for entity_id in reachable_ids(world, character):
        if entity_id == character.id:
            continue
        entity = world.get_entity(entity_id)
        if not entity.has_component(SpeciesComponent):
            continue
        species = entity.get_component(SpeciesComponent).species
        if species in known or species in seen:
            continue
        seen.add(species)
        names.append(_subject_name(entity, species))
    return sorted(names)


def journal_fragments(world: World, character: Entity) -> list[str]:
    """Report journal size, per-habitat completion, and any unrecorded subject in the room."""
    if character is None or not character.has_component(LoreJournalComponent):
        return []
    journal = character.get_component(LoreJournalComponent)
    lines: list[str] = []
    count = len(journal.records)
    lines.append(f"Your field journal holds {count} species.")
    if journal.discoveries:
        lines.append(f"You hold {len(journal.discoveries)} first-in-world discoveries.")
    for habitat, tally in completion_by_habitat(journal).items():
        lines.append(f"Journal ({habitat}): {tally} recorded.")
    for name in _unrecorded_here(world, character, journal):
        lines.append(f"A {name} here is unrecorded.")
    return lines


__all__ = [
    "completion_by_habitat",
    "is_first_in_world",
    "journal_fragments",
]
