from __future__ import annotations

from bunnyland.core import RoomComponent, StealthComponent, WorldActor, spawn_entity

from bunnyland_loresim import SettleConsequence, spawn_subject


def _world():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Thicket")])
    return actor, room


def test_hidden_subject_recovers_visibility_each_tick():
    actor, room = _world()
    subject = spawn_subject(actor.world, species="hare", room_id=room.id, hiding=True)
    # A tiny step keeps it below its hidden_threshold (0.1) after one tick: still recovering.
    consequence = SettleConsequence(settle_step=0.05)

    consequence.process(actor.world, epoch=1)
    stealth = subject.get_component(StealthComponent)
    assert stealth.visibility_level == 0.05
    assert stealth.hiding is True  # visibility is rising but has not cleared the threshold yet


def test_subject_settles_back_into_view_after_enough_patience():
    actor, room = _world()
    subject = spawn_subject(actor.world, species="hare", room_id=room.id, hiding=True)
    consequence = SettleConsequence(settle_step=0.5)

    for tick in range(3):
        consequence.process(actor.world, epoch=tick)

    # Once it clears its hidden_threshold it stops hiding and is observable again; the
    # consequence then leaves the (now visible) subject alone.
    stealth = subject.get_component(StealthComponent)
    assert stealth.hiding is False
    assert stealth.visibility_level == 0.5


def test_visible_subject_is_untouched():
    actor, room = _world()
    subject = spawn_subject(actor.world, species="hare", room_id=room.id, wary=True)
    before = subject.get_component(StealthComponent)

    SettleConsequence().process(actor.world, epoch=0)

    assert subject.get_component(StealthComponent) == before
