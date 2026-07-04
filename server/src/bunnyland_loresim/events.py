"""Domain events emitted by the observe verb."""

from __future__ import annotations

from bunnyland.core.events import DomainEvent


class SpeciesObservedEvent(DomainEvent):
    """A naturalist recorded (or re-observed) a living subject into their field journal."""

    subject_id: str
    species: str
    sightings: int
    new_record: bool
    discovery: bool = False


__all__ = ["SpeciesObservedEvent"]
