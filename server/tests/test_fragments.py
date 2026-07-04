from __future__ import annotations

from bunnyland.core import RoomComponent, WorldActor, spawn_entity
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.handlers import HandlerContext

from bunnyland_loresim import (
    journal_fragments,
    knowledge_fragments,
    mark_known,
    spawn_naturalist,
    spawn_subject,
)
from bunnyland_loresim.observe import ObserveHandler


def _scene():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Reedbank")])
    naturalist = spawn_naturalist(actor.world, room_id=room.id)
    return actor, room, naturalist


def _observe(actor, character_id, subject_id):
    command = build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="observe",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"subject_id": str(subject_id)},
    )
    return ObserveHandler().execute(HandlerContext(world=actor.world, epoch=0), command)


def test_knowledge_fragment_lists_known_species():
    actor, _room, naturalist = _scene()
    mark_known(naturalist, "heron")
    mark_known(naturalist, "fox")

    lines = knowledge_fragments(actor.world, naturalist)
    assert lines == ["You have field knowledge of 2 species: fox, heron."]


def test_knowledge_fragment_empty_without_knowledge():
    actor, _room, naturalist = _scene()
    assert knowledge_fragments(actor.world, naturalist) == []


def test_journal_fragment_reports_count_and_unrecorded_subject():
    actor, room, naturalist = _scene()
    spawn_subject(actor.world, species="heron", name="heron", room_id=room.id)

    lines = journal_fragments(actor.world, naturalist)
    assert "Your field journal holds 0 species." in lines
    assert "A heron here is unrecorded." in lines


def test_journal_fragment_drops_nudge_once_recorded():
    actor, room, naturalist = _scene()
    subject = spawn_subject(actor.world, species="heron", name="heron", room_id=room.id)
    _observe(actor, naturalist.id, subject.id)

    lines = journal_fragments(actor.world, naturalist)
    assert "Your field journal holds 1 species." in lines
    assert "Journal (wetland): 1 recorded." in lines
    assert not any("unrecorded" in line for line in lines)


def test_journal_fragment_reports_discoveries():
    actor, room, naturalist = _scene()
    subject = spawn_subject(actor.world, species="heron", name="heron", room_id=room.id)
    _observe(actor, naturalist.id, subject.id)

    lines = journal_fragments(actor.world, naturalist)
    assert "You hold 1 first-in-world discoveries." in lines
