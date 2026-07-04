from __future__ import annotations

from bunnyland.core import RoomComponent, WorldActor, spawn_entity
from bunnyland.core.ecs import replace_component

from bunnyland_loresim import (
    KnownSpeciesComponent,
    LoreJournalComponent,
    knows_species,
    mark_known,
    spawn_naturalist,
)
from bunnyland_loresim.components import SpeciesRecord


def _naturalist():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Blind")])
    naturalist = spawn_naturalist(actor.world, room_id=room.id)
    return actor, naturalist


def test_mark_known_creates_registry():
    actor, naturalist = _naturalist()
    mark_known(naturalist, "heron")
    assert naturalist.get_component(KnownSpeciesComponent).species == ("heron",)


def test_mark_known_is_idempotent_and_sorted():
    actor, naturalist = _naturalist()
    mark_known(naturalist, "heron")
    mark_known(naturalist, "fox")
    mark_known(naturalist, "heron")
    assert naturalist.get_component(KnownSpeciesComponent).species == ("fox", "heron")


def test_knows_species_reads_open_registry():
    actor, naturalist = _naturalist()
    assert knows_species(actor.world, naturalist, "heron") is False
    mark_known(naturalist, "heron")
    assert knows_species(actor.world, naturalist, "heron") is True


def test_knows_species_falls_back_to_journal():
    actor, naturalist = _naturalist()
    # A character populated only through the journal (no KnownSpeciesComponent) still resolves.
    record = SpeciesRecord(
        species="crane",
        habitat="wetland",
        rarity="rare",
        first_seen_epoch=0,
        first_seen_room="room_1",
    )
    replace_component(naturalist, LoreJournalComponent(records=(record,)))
    assert not naturalist.has_component(KnownSpeciesComponent)
    assert knows_species(actor.world, naturalist, "crane") is True
    assert knows_species(actor.world, naturalist, "heron") is False
