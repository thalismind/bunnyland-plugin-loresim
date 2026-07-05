from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    RoomComponent,
    StealthComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.ecs import contents

from bunnyland_loresim import (
    MIGRATION_INTERVAL,
    MigrationConsequence,
    SpeciesComponent,
    spawn_naturalist,
)


def _scene(place_character=True):
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Fen")])
    if place_character:
        spawn_naturalist(actor.world, name="Rue", room_id=room.id)
    return actor, room


def _migrants(world, room):
    return [
        world.get_entity(i)
        for i in contents(room)
        if world.get_entity(i).has_component(SpeciesComponent)
    ]


def test_migration_fires_on_interval():
    actor, room = _scene()
    events = MigrationConsequence().process(actor.world, MIGRATION_INTERVAL)
    assert len(events) == 1
    event = events[0]
    assert event.species
    migrants = _migrants(actor.world, room)
    assert len(migrants) == 1
    subject = migrants[0]
    assert subject.get_component(SpeciesComponent).rarity == "rare"
    # A migrant arrives wary (sight-and-patience only, never sound).
    assert subject.has_component(StealthComponent)


def test_migration_silent_off_interval():
    actor, _room = _scene()
    assert MigrationConsequence().process(actor.world, MIGRATION_INTERVAL + 1) == []


def test_migration_silent_at_epoch_zero():
    actor, _room = _scene()
    assert MigrationConsequence().process(actor.world, 0) == []


def test_migration_needs_an_occupied_room():
    actor, _room = _scene(place_character=False)
    assert MigrationConsequence().process(actor.world, MIGRATION_INTERVAL) == []


def test_migration_targets_lowest_id_occupied_room():
    actor, first = _scene()
    second = spawn_entity(actor.world, [RoomComponent(title="Second Fen")])
    spawn_naturalist(actor.world, name="Wren", room_id=second.id)
    events = MigrationConsequence().process(actor.world, MIGRATION_INTERVAL)
    assert len(events) == 1
    # The lowest-id occupied room gets the migrant.
    assert events[0].room_id == str(first.id)


def test_migration_skips_room_without_room_component():
    # A character standing in a plain container (no RoomComponent) is not a valid site.
    actor = WorldActor()
    holder = spawn_entity(actor.world, [])
    naturalist = spawn_naturalist(actor.world)
    holder.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), naturalist.id)
    assert MigrationConsequence().process(actor.world, MIGRATION_INTERVAL) == []


def test_migration_skips_unplaced_characters():
    actor, placed_room = _scene()
    # A second naturalist with no container at all must be skipped, not crash.
    spawn_naturalist(actor.world, name="Drifter")
    events = MigrationConsequence().process(actor.world, MIGRATION_INTERVAL)
    assert len(events) == 1
    assert events[0].room_id == str(placed_room.id)


def test_migration_custom_interval():
    actor, _room = _scene()
    events = MigrationConsequence(interval=10).process(actor.world, 20)
    assert len(events) == 1
