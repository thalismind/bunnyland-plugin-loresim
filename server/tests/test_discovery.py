from __future__ import annotations

from bunnyland.core import RoomComponent, WorldActor, spawn_entity
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.handlers import HandlerContext
from conftest import execute_handler

from bunnyland_loresim import (
    LoreJournalComponent,
    ObserveHandler,
    completion_by_habitat,
    is_first_in_world,
    spawn_naturalist,
    spawn_subject,
)
from bunnyland_loresim.components import SpeciesRecord


def _observe(actor, character_id, subject_id, epoch=0):
    command = build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="observe",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"subject_id": str(subject_id)},
    )
    return execute_handler(
        ObserveHandler(), HandlerContext(world=actor.world, epoch=epoch), command
    )


def _world_with_room():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Fen")])
    return actor, room


def test_first_in_world_is_true_until_recorded():
    actor, room = _world_with_room()
    naturalist = spawn_naturalist(actor.world, room_id=room.id)
    subject = spawn_subject(actor.world, species="heron", room_id=room.id)

    assert is_first_in_world(actor.world, "heron") is True
    result = _observe(actor, naturalist.id, subject.id)
    assert result.events[0].discovery is True
    assert "heron" in naturalist.get_component(LoreJournalComponent).discoveries
    assert is_first_in_world(actor.world, "heron") is False


def test_second_recorder_gets_no_discovery_credit():
    actor, room = _world_with_room()
    first = spawn_naturalist(actor.world, name="first", room_id=room.id)
    second = spawn_naturalist(actor.world, name="second", room_id=room.id)
    subject = spawn_subject(actor.world, species="heron", room_id=room.id)

    _observe(actor, first.id, subject.id)
    result = _observe(actor, second.id, subject.id)

    assert result.events[0].discovery is False
    assert second.get_component(LoreJournalComponent).discoveries == ()


def test_completion_by_habitat_tallies_distinct_species():
    journal = LoreJournalComponent(
        records=(
            SpeciesRecord("heron", "wetland", "common", 0, "room_1"),
            SpeciesRecord("frog", "wetland", "common", 0, "room_1"),
            SpeciesRecord("fox", "woodland", "common", 0, "room_1"),
        )
    )
    assert completion_by_habitat(journal) == {"wetland": 2, "woodland": 1}
