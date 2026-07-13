from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    RoomComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.handlers import HandlerContext
from conftest import execute_handler
from pydantic.dataclasses import dataclass
from relics import Component

from bunnyland_loresim import cartography, spawn_naturalist
from bunnyland_loresim.cartography import (
    cartography_available,
    charted_biome,
    charted_sites,
)
from bunnyland_loresim.expeditions import EmbarkHandler, ExpeditionComponent


@dataclass(frozen=True)
class _FakeMapRoom:
    room_id: str = ""
    biome: str = ""


@dataclass(frozen=True)
class _FakeMapComponent(Component):
    rooms: tuple[_FakeMapRoom, ...] = ()


# ---- dormant standalone path (cartographysim not installed) --------------------------


def test_cartography_unavailable_by_default():
    assert cartography_available() is False


def test_charted_sites_empty_without_cartography():
    actor = WorldActor()
    naturalist = spawn_naturalist(actor.world)
    assert charted_sites(actor.world, naturalist) == ()
    assert charted_biome(actor.world, naturalist, "anything") is None


# ---- active connector path (cartographysim present) ----------------------------------


def _with_map(monkeypatch, rooms):
    monkeypatch.setattr(cartography, "MapComponent", _FakeMapComponent)
    actor = WorldActor()
    base = spawn_entity(actor.world, [RoomComponent(title="Base")])
    naturalist = spawn_naturalist(actor.world, name="Rue", room_id=base.id)
    field_map = spawn_entity(actor.world, [_FakeMapComponent(rooms=tuple(rooms))])
    naturalist.add_relationship(Contains(mode=ContainmentMode.INVENTORY), field_map.id)
    return actor, base, naturalist


def test_cartography_available_when_patched(monkeypatch):
    monkeypatch.setattr(cartography, "MapComponent", _FakeMapComponent)
    assert cartography_available() is True


def test_charted_sites_reads_held_map(monkeypatch):
    actor, _base, naturalist = _with_map(
        monkeypatch,
        [_FakeMapRoom(room_id="room_7", biome="woodland")],
    )
    assert charted_sites(actor.world, naturalist) == (("room_7", "woodland"),)
    assert charted_biome(actor.world, naturalist, "room_7") == "woodland"
    assert charted_biome(actor.world, naturalist, "room_9") is None


def test_charted_sites_empty_when_no_map_held(monkeypatch):
    monkeypatch.setattr(cartography, "MapComponent", _FakeMapComponent)
    actor = WorldActor()
    naturalist = spawn_naturalist(actor.world)
    # A non-map item in the inventory is skipped.
    junk = spawn_entity(actor.world, [RoomComponent(title="not a map")])
    naturalist.add_relationship(Contains(mode=ContainmentMode.INVENTORY), junk.id)
    assert charted_sites(actor.world, naturalist) == ()


def _embark(actor, character_id, payload):
    ctx = HandlerContext(world=actor.world, epoch=5)
    cmd = build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="embark",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload=payload,
    )
    return execute_handler(EmbarkHandler(), ctx, cmd)


def test_embark_to_charted_site_when_cartography_present(monkeypatch):
    monkeypatch.setattr(cartography, "MapComponent", _FakeMapComponent)
    actor = WorldActor()
    base = spawn_entity(actor.world, [RoomComponent(title="Base")])
    naturalist = spawn_naturalist(actor.world, name="Rue", room_id=base.id)
    charted = spawn_entity(actor.world, [RoomComponent(title="Charted Glade")])
    field_map = spawn_entity(
        actor.world,
        [_FakeMapComponent(rooms=(_FakeMapRoom(room_id=str(charted.id), biome="woodland"),))],
    )
    naturalist.add_relationship(Contains(mode=ContainmentMode.INVENTORY), field_map.id)

    result = _embark(actor, naturalist.id, {"site_id": str(charted.id)})
    assert result.ok
    assert result.events[0].charted is True
    expedition = naturalist.get_component(ExpeditionComponent)
    assert expedition.site_room_id == str(charted.id)
    assert expedition.habitat == "woodland"


def test_embark_charted_site_removed_before_travel(monkeypatch):
    monkeypatch.setattr(cartography, "MapComponent", _FakeMapComponent)
    actor = WorldActor()
    base = spawn_entity(actor.world, [RoomComponent(title="Base")])
    naturalist = spawn_naturalist(actor.world, name="Rue", room_id=base.id)
    charted = spawn_entity(actor.world, [RoomComponent(title="Charted Glade")])
    field_map = spawn_entity(
        actor.world,
        [_FakeMapComponent(rooms=(_FakeMapRoom(room_id=str(charted.id), biome="woodland"),))],
    )
    naturalist.add_relationship(Contains(mode=ContainmentMode.INVENTORY), field_map.id)
    actor.world.remove(charted.id)

    result = _embark(actor, naturalist.id, {"site_id": str(charted.id)})
    assert not result.ok
    assert result.reason == "that site no longer exists"
