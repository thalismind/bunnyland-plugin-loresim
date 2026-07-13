from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    IdentityComponent,
    PerceptionComponent,
    RoomComponent,
    StealthComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.ecs import replace_component
from bunnyland.core.handlers import HandlerContext
from conftest import execute_handler

from bunnyland_loresim import (
    KnownSpeciesComponent,
    LoreJournalComponent,
    ObserveHandler,
    knows_species,
    spawn_naturalist,
    spawn_spyglass,
    spawn_subject,
)


def _scene(*, wary=False, hiding=False, with_journal=True, perceive=True):
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Marsh Hide")])
    naturalist = spawn_naturalist(actor.world, name="Rue", room_id=room.id)
    if not with_journal:
        naturalist.remove_component(LoreJournalComponent)
    if not perceive:
        replace_component(naturalist, PerceptionComponent(active=False))
    subject = spawn_subject(
        actor.world, species="heron", habitat="wetland", room_id=room.id, wary=wary, hiding=hiding
    )
    return actor, room, naturalist, subject


def _cmd(character_id, payload):
    return build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="observe",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload=payload,
    )


def _observe(actor, character_id, subject_id):
    ctx = HandlerContext(world=actor.world, epoch=7)
    return execute_handler(
        ObserveHandler(), ctx, _cmd(character_id, {"subject_id": str(subject_id)})
    )


def test_observe_records_first_sighting():
    actor, room, naturalist, subject = _scene()
    result = _observe(actor, naturalist.id, subject.id)

    assert result.ok
    event = result.events[0]
    assert event.species == "heron"
    assert event.new_record is True
    assert event.sightings == 1
    journal = naturalist.get_component(LoreJournalComponent)
    record = journal.record_for("heron")
    assert record is not None
    assert record.first_seen_epoch == 7
    assert record.first_seen_room == str(room.id)


def test_observe_marks_species_known_payoff():
    actor, _room, naturalist, subject = _scene()
    _observe(actor, naturalist.id, subject.id)

    assert naturalist.has_component(KnownSpeciesComponent)
    assert "heron" in naturalist.get_component(KnownSpeciesComponent).species
    assert knows_species(actor.world, naturalist, "heron") is True


def test_repeat_observation_updates_notes_not_rejected():
    actor, _room, naturalist, subject = _scene()
    _observe(actor, naturalist.id, subject.id)
    result = _observe(actor, naturalist.id, subject.id)

    assert result.ok
    event = result.events[0]
    assert event.new_record is False
    assert event.sightings == 2
    journal = naturalist.get_component(LoreJournalComponent)
    assert len(journal.records) == 1
    assert journal.record_for("heron").sightings == 2


def test_observe_creates_journal_when_absent():
    actor, _room, naturalist, subject = _scene(with_journal=False)
    assert not naturalist.has_component(LoreJournalComponent)

    result = _observe(actor, naturalist.id, subject.id)

    assert result.ok
    assert naturalist.has_component(LoreJournalComponent)
    assert naturalist.get_component(LoreJournalComponent).record_for("heron") is not None


def test_observe_with_spyglass_does_not_spook_wary_subject():
    actor, room, naturalist, subject = _scene(wary=True)
    spyglass = spawn_spyglass(actor.world)
    naturalist.add_relationship(Contains(mode=ContainmentMode.INVENTORY), spyglass.id)

    result = _observe(actor, naturalist.id, subject.id)

    assert result.ok
    assert naturalist.get_component(LoreJournalComponent).record_for("heron") is not None


# ---- rejection paths, in validation order -------------------------------------------


def test_reject_invalid_character_id():
    actor, _room, _naturalist, subject = _scene()
    result = _observe(actor, "???", subject.id)
    assert not result.ok
    assert result.reason == "invalid character id"


def test_reject_missing_character():
    actor, _room, _naturalist, subject = _scene()
    result = _observe(actor, "entity_9999", subject.id)
    assert not result.ok
    assert result.reason == "character does not exist"


def test_reject_invalid_subject_id():
    actor, _room, naturalist, _subject = _scene()
    ctx = HandlerContext(world=actor.world, epoch=0)
    result = execute_handler(ObserveHandler(), ctx, _cmd(naturalist.id, {"subject_id": "???"}))
    assert not result.ok
    assert result.reason == "invalid subject id"


def test_reject_missing_subject():
    actor, _room, naturalist, _subject = _scene()
    result = _observe(actor, naturalist.id, "entity_9999")
    assert not result.ok
    assert result.reason == "subject does not exist"


def test_reject_when_observer_cannot_perceive():
    actor, _room, naturalist, subject = _scene(perceive=False)
    result = _observe(actor, naturalist.id, subject.id)
    assert not result.ok
    assert result.reason == "you cannot see anything right now"


def test_reject_subject_in_another_room_not_visible():
    actor, _room, naturalist, _subject = _scene()
    far_room = spawn_entity(actor.world, [RoomComponent(title="Far Fen")])
    elsewhere = spawn_subject(actor.world, species="crane", room_id=far_room.id)
    result = _observe(actor, naturalist.id, elsewhere.id)
    assert not result.ok
    assert result.reason == "you cannot see that from here"


def test_reject_hidden_subject_not_visible():
    actor, _room, naturalist, subject = _scene(hiding=True)
    result = _observe(actor, naturalist.id, subject.id)
    assert not result.ok
    assert result.reason == "that is hidden from view"


def test_reject_non_species_target_wrong_kind():
    actor, room, naturalist, _subject = _scene()
    rock = spawn_entity(actor.world, [IdentityComponent(name="rock", kind="item")])
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), rock.id)
    result = _observe(actor, naturalist.id, rock.id)
    assert not result.ok
    assert result.reason == "that is not a living thing you can record"


def test_wary_subject_spooks_and_flees_without_spyglass():
    actor, _room, naturalist, subject = _scene(wary=True)

    result = _observe(actor, naturalist.id, subject.id)

    assert result.ok
    assert result.events == ()
    stealth = subject.get_component(StealthComponent)
    assert stealth.hiding is True
    assert stealth.visibility_level == 0.0
    assert not naturalist.get_component(LoreJournalComponent).records
