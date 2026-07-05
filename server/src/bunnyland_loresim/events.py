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


class ExpeditionStartedEvent(DomainEvent):
    """A naturalist set out on an expedition to survey a habitat."""

    habitat: str
    site_room_id: str
    members: int
    charted: bool = False


class SpeciesDiscoveredEvent(DomainEvent):
    """An expedition turned up a living subject and recorded it into the journal."""

    subject_id: str
    species: str
    habitat: str
    first_in_world: bool


class ExpeditionReturnedEvent(DomainEvent):
    """An expedition party returned home with what it recorded afield."""

    habitat: str
    site_room_id: str
    discovered: tuple[str, ...] = ()


class FieldGuidePublishedEvent(DomainEvent):
    """A naturalist published a field guide from their journal (a museum-donatable work)."""

    guide_id: str
    habitat: str
    species: tuple[str, ...]
    edition: int


class RareMigrationEvent(DomainEvent):
    """The storyteller's rare-migration incident: a new species appears in the world."""

    subject_id: str
    species: str
    habitat: str


__all__ = [
    "ExpeditionReturnedEvent",
    "ExpeditionStartedEvent",
    "FieldGuidePublishedEvent",
    "RareMigrationEvent",
    "SpeciesDiscoveredEvent",
    "SpeciesObservedEvent",
]
