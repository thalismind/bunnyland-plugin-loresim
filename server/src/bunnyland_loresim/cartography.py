"""Optional connector: consume ``cartographysim`` field maps to steer expeditions.

Loresim expeditions run perfectly well **standalone** — you set out for a habitat and a
field site is opened for you. But when the ``cartographysim`` pack is *also* loaded, a
naturalist carrying a charted field map can expedition to a room they have already charted,
letting the two packs interlock (chart → explore) without loresim depending on cartography.

This is a **safe, optional consumption** (roadmap §1). The import is guarded: if
``cartographysim`` is not installed, :data:`MapComponent` is ``None`` and every helper here
reports "no charted sites", so the expedition mechanic simply falls back to opening a fresh
field site. Nothing in loresim's own surface depends on this module resolving.
"""

from __future__ import annotations

import logging

from bunnyland.core.ecs import contents
from relics import Entity, World

_LOG = logging.getLogger(__name__)

try:  # pragma: no cover - import outcome depends on whether the sibling pack is installed
    from bunnyland_cartographysim import MapComponent
except ImportError:  # pragma: no cover - dormant standalone path
    MapComponent = None
    _LOG.warning(
        "cartographysim not installed: loresim expeditions to charted sites are disabled; "
        "expeditions will open fresh field sites instead."
    )


def cartography_available() -> bool:
    """Whether the optional ``cartographysim`` map surface is loaded in this process."""
    return MapComponent is not None


def charted_sites(world: World, character: Entity) -> tuple[tuple[str, str], ...]:
    """Return ``(room_id, biome)`` for each room on a held field map.

    Returns ``()`` when cartography is not loaded or the character carries no field map, so
    callers never have to know whether the connector is active.
    """
    if MapComponent is None:
        return ()
    for item_id in contents(character):
        if not world.has_entity(item_id):
            continue
        item = world.get_entity(item_id)
        if item.has_component(MapComponent):
            field_map = item.get_component(MapComponent)
            return tuple((room.room_id, room.biome) for room in field_map.rooms)
    return ()


def charted_biome(world: World, character: Entity, room_id: str) -> str | None:
    """Return the charted biome for ``room_id`` on a held map, or ``None`` if not charted."""
    for charted_id, biome in charted_sites(world, character):
        if charted_id == room_id:
            return biome
    return None


__all__ = ["MapComponent", "cartography_available", "charted_biome", "charted_sites"]
