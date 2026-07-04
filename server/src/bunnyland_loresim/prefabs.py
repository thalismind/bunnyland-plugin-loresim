"""Spawn factories for Loresim subjects and gear.

The loader does not consume ``ContentContribution.prefabs``, so subjects and gear are created
with these ``spawn_entity`` helpers (from tests, admin tooling, or a worldgen hook). A subject
is an ordinary living entity carrying a :class:`SpeciesComponent` (optionally wary, via a
:class:`StealthComponent`); it is never made ownable or portable. Pass ``room_id`` to place an
entity into a room, or leave it out to spawn it uncontained.
"""

from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    HoldableComponent,
    IdentityComponent,
    PerceptionComponent,
    PortableComponent,
    StealthComponent,
    spawn_entity,
)
from relics import Entity, World

from .components import LoreJournalComponent, SpeciesComponent, SpyglassComponent


def _link_into_room(world: World, entity: Entity, room_id) -> None:
    if room_id is None or not world.has_entity(room_id):
        return
    world.get_entity(room_id).add_relationship(
        Contains(mode=ContainmentMode.ROOM_CONTENT), entity.id
    )


def spawn_subject(
    world: World,
    *,
    species: str = "heron",
    habitat: str = "wetland",
    rarity: str = "common",
    name: str | None = None,
    wary: bool = False,
    hiding: bool = False,
    room_id=None,
) -> Entity:
    """Spawn an observable living subject, optionally wary and/or already hidden."""
    components = [
        IdentityComponent(name=name or species, kind="creature", tags=("loresim",)),
        SpeciesComponent(species=species, habitat=habitat, rarity=rarity),
    ]
    if wary or hiding:
        components.append(
            StealthComponent(
                visibility_level=0.0 if hiding else 1.0,
                hiding=hiding,
            )
        )
    subject = spawn_entity(world, components)
    _link_into_room(world, subject, room_id)
    return subject


def spawn_naturalist(world: World, *, name: str = "naturalist", room_id=None) -> Entity:
    """Spawn a character with an empty field journal, ready to observe."""
    character = spawn_entity(
        world,
        [
            IdentityComponent(name=name, kind="character"),
            CharacterComponent(),
            PerceptionComponent(),
            LoreJournalComponent(),
        ],
    )
    _link_into_room(world, character, room_id)
    return character


def spawn_spyglass(world: World, *, room_id=None, magnification: float = 1.0) -> Entity:
    """Spawn a holdable spyglass item, optionally placed in ``room_id``."""
    item = spawn_entity(
        world,
        [
            IdentityComponent(name="spyglass", kind="item", tags=("loresim",)),
            PortableComponent(),
            HoldableComponent(slot="hand"),
            SpyglassComponent(magnification=magnification),
        ],
    )
    _link_into_room(world, item, room_id)
    return item


__all__ = ["spawn_naturalist", "spawn_spyglass", "spawn_subject"]
