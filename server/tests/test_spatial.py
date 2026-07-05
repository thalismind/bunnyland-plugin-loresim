from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    RoomComponent,
    WorldActor,
    spawn_entity,
)

from bunnyland_loresim import SpyglassComponent, spawn_naturalist, spawn_spyglass
from bunnyland_loresim.spatial import held_component, room_of


def test_room_of_missing_entity_returns_none():
    actor = WorldActor()
    assert room_of(actor.world, "entity_999999") is None


def test_room_of_uncontained_entity_returns_none():
    actor = WorldActor()
    loose = spawn_entity(actor.world, [RoomComponent(title="floating")])
    # An entity with no container walks up and finds no room parent.
    naturalist = spawn_naturalist(actor.world)
    assert room_of(actor.world, naturalist.id) is None
    assert room_of(actor.world, loose.id) is None


def test_room_of_resolves_through_nested_container():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Hide")])
    crate = spawn_entity(actor.world, [])
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), crate.id)
    subject = spawn_entity(actor.world, [])
    crate.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), subject.id)
    resolved = room_of(actor.world, subject.id)
    assert resolved is not None
    assert str(resolved.id) == str(room.id)


def test_held_component_finds_and_misses():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Hide")])
    naturalist = spawn_naturalist(actor.world, room_id=room.id)
    assert held_component(actor.world, naturalist, SpyglassComponent) is None
    spyglass = spawn_spyglass(actor.world)
    naturalist.add_relationship(Contains(mode=ContainmentMode.INVENTORY), spyglass.id)
    found = held_component(actor.world, naturalist, SpyglassComponent)
    assert found is not None and str(found.id) == str(spyglass.id)
