"""Deterministic lore notes unlocked by repeated observation.

Each species has a temperament and an activity pattern that a naturalist infers only after
watching it more than once. Those notes are assembled purely from the recorded species'
stable data (species/habitat/rarity) via :mod:`hashlib` — never from ``random`` or the clock
— so the same species always yields the same lore, and tests can assert it exactly.

Unlock ladder (by ``sightings``):

- 1 sighting  -> habitat note.
- 2 sightings -> temperament note.
- 3+ sightings -> activity note (the full field entry).
"""

from __future__ import annotations

import hashlib

from .components import SpeciesRecord

#: Temperament vocabulary, indexed by a stable hash of the species name.
TEMPERAMENTS: tuple[str, ...] = (
    "skittish",
    "watchful",
    "bold",
    "placid",
    "territorial",
    "gregarious",
)

#: Activity-pattern vocabulary, indexed by a stable hash of the species name.
ACTIVITIES: tuple[str, ...] = (
    "most active at dawn",
    "most active at dusk",
    "active through the midday sun",
    "abroad only after dark",
    "stirs with the changing tide",
)


def _index(species: str, salt: str, modulus: int) -> int:
    """Stable, deterministic index in ``range(modulus)`` from a species name and salt."""
    digest = hashlib.sha256(f"{salt}:{species}".encode()).hexdigest()
    return int(digest, 16) % modulus


def temperament_for(species: str) -> str:
    """Return the deterministic temperament label for a species name."""
    return TEMPERAMENTS[_index(species, "temperament", len(TEMPERAMENTS))]


def activity_for(species: str) -> str:
    """Return the deterministic activity-pattern label for a species name."""
    return ACTIVITIES[_index(species, "activity", len(ACTIVITIES))]


def lore_notes(record: SpeciesRecord) -> tuple[str, ...]:
    """Return the lore notes unlocked for ``record`` given how often it has been observed."""
    notes: list[str] = [f"Habitat: {record.habitat} ({record.rarity})."]
    if record.sightings >= 2:
        notes.append(f"Temperament: {temperament_for(record.species)}.")
    if record.sightings >= 3:
        notes.append(f"Activity: {activity_for(record.species)}.")
    return tuple(notes)


__all__ = [
    "ACTIVITIES",
    "TEMPERAMENTS",
    "activity_for",
    "lore_notes",
    "temperament_for",
]
