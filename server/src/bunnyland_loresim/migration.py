"""Storyteller incident: a rare migration brings a new species into the world.

Loresim registers one **storyteller incident** so its world pressure is *paced* alongside
every other pack's (roadmap §2). On a steady cadence a rare migrant appears — a new species
turns up in a room where a naturalist can find it — giving the pack a recurring, cross-pack
beat rather than only player-driven observation.

The cadence is deterministic (fires on epoch multiples of :data:`MIGRATION_INTERVAL`) and the
migrant is chosen with :mod:`hashlib`, so there is no ``random`` or wall-clock reliance. The
migrant may be wary (a :class:`StealthComponent`) — this is *sight and patience* only; nothing
here touches sound or hearing.
"""

from __future__ import annotations

import hashlib

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    StealthComponent,
    container_of,
    spawn_entity,
)
from bunnyland.core.events import DomainEvent, EventVisibility, event_base
from relics import World

from .components import SpeciesComponent
from .events import RareMigrationEvent
from .expeditions import HABITAT_SPECIES

#: How often (in epoch units) a rare migration incident fires.
MIGRATION_INTERVAL = 24 * 60 * 60


def _pick(options: tuple[str, ...], salt: str) -> str:
    digest = hashlib.sha256(salt.encode()).hexdigest()
    return options[int(digest, 16) % len(options)]


def _occupied_room(world: World):
    """The lowest-id room that currently holds a character, or ``None``."""
    rooms = []
    for character in world.query().with_all([CharacterComponent]).execute_entities():
        room_id = container_of(character)
        if room_id is None or not world.has_entity(room_id):
            continue
        room = world.get_entity(room_id)
        if room.has_component(RoomComponent):
            rooms.append(room)
    return min(rooms, key=lambda room: str(room.id)) if rooms else None


class MigrationConsequence:
    """Bring a rare migrant species into an occupied room on a deterministic cadence."""

    def __init__(self, *, interval: int = MIGRATION_INTERVAL) -> None:
        self.interval = interval

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        if epoch <= 0 or epoch % self.interval != 0:
            return []
        room = _occupied_room(world)
        if room is None:
            return []
        habitat = _pick(tuple(HABITAT_SPECIES), f"habitat:{epoch}")
        species = _pick(HABITAT_SPECIES[habitat], f"migrant:{epoch}:{habitat}")
        subject = spawn_entity(
            world,
            [
                IdentityComponent(name=species, kind="creature", tags=("loresim", "migrant")),
                SpeciesComponent(species=species, habitat=habitat, rarity="rare"),
                StealthComponent(visibility_level=1.0, hiding=False),
            ],
        )
        room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), subject.id)
        return [
            RareMigrationEvent(
                **event_base(
                    epoch,
                    default_visibility=EventVisibility.ROOM,
                    actor_id=str(subject.id),
                    room_id=str(room.id),
                    target_ids=(str(subject.id),),
                    subject_id=str(subject.id),
                    species=species,
                    habitat=habitat,
                )
            )
        ]


__all__ = ["MIGRATION_INTERVAL", "MigrationConsequence"]
