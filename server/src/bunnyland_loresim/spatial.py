"""Spatial helpers: find the room an entity is ultimately in, and a held spyglass.

A naturalist and the subject they record are usually side by side in a room, but a subject
may be nested (e.g. perched inside an open container the core generator produced). These
helpers answer the two questions the observe verb and the fragments actually ask:

- ``room_of(entity)`` — which room is this entity ultimately in, walking up ``Contains``?
- ``held_component(character, type)`` — does the character carry an item with this component?
"""

from __future__ import annotations

from bunnyland.core import RoomComponent, container_of
from bunnyland.core.ecs import contents
from relics import Component, Entity, World

#: Guard against pathological containment cycles while walking up to a room.
_MAX_CONTAINMENT_DEPTH = 8


def room_of(world: World, entity_id) -> Entity | None:
    """Return the room ``entity_id`` is ultimately in, resolving through any container.

    Walks ``Contains`` parents upward until an entity with :class:`RoomComponent` is found,
    so it works for a subject resting in a room *and* one nested inside a container.
    """
    if not world.has_entity(entity_id):
        return None
    current = world.get_entity(entity_id)
    for _ in range(_MAX_CONTAINMENT_DEPTH):
        parent_id = container_of(current)
        if parent_id is None or not world.has_entity(parent_id):
            return None
        parent = world.get_entity(parent_id)
        if parent.has_component(RoomComponent):
            return parent
        current = parent
    return None


def held_component(
    world: World, character: Entity, component_type: type[Component]
) -> Entity | None:
    """Return an item in ``character``'s inventory carrying ``component_type``, or ``None``."""
    for item_id in contents(character):
        if not world.has_entity(item_id):
            continue
        item = world.get_entity(item_id)
        if item.has_component(component_type):
            return item
    return None


__all__ = ["held_component", "room_of"]
