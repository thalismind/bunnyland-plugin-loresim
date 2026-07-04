from __future__ import annotations

import asyncio

from bunnyland.core import (
    CharacterComponent,
    IdentityComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.components import GenerationIntentComponent
from bunnyland.core.events import CharacterGeneratedEvent, ObjectGeneratedEvent, event_base
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_loresim import SpeciesComponent


def _actor():
    actor = WorldActor()
    apply_plugins(load_modules(["bunnyland_loresim"]), actor)
    return actor


def _publish(actor, event):
    asyncio.run(actor.bus.publish(event))


def _character(actor, *, name="npc", tags=(), description=""):
    entity = spawn_entity(
        actor.world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    event = CharacterGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id=str(entity.id),
        entity_key=name,
        entity_kind="character",
        generation=GenerationIntentComponent(tags=tuple(tags), description=description),
        character_key=name,
        room_id="room_1",
    )
    _publish(actor, event)
    return entity


def _object(actor, *, name="thing", tags=(), description=""):
    entity = spawn_entity(actor.world, [IdentityComponent(name=name, kind="item")])
    event = ObjectGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id=str(entity.id),
        entity_key=name,
        entity_kind="object",
        generation=GenerationIntentComponent(tags=tuple(tags), description=description),
        object_key=name,
    )
    _publish(actor, event)
    return entity


def test_creature_gets_species_component():
    actor = _actor()
    heron = _character(actor, name="heron", tags=("bird", "wildlife"))
    assert heron.has_component(SpeciesComponent)
    component = heron.get_component(SpeciesComponent)
    assert component.species == "heron"
    assert component.habitat == "wetland"


def test_plant_object_gets_species_from_description():
    actor = _actor()
    fern = _object(actor, name="fern", description="a shy woodland fern")
    component = fern.get_component(SpeciesComponent)
    assert component.habitat == "woodland"
    assert component.rarity == "uncommon"


def test_rarity_from_text():
    actor = _actor()
    owl = _character(actor, name="owl", description="a rare vanishing forest owl")
    assert owl.get_component(SpeciesComponent).rarity == "rare"


def test_non_living_object_is_not_tagged():
    actor = _actor()
    crate = _object(actor, name="crate", tags=("wooden", "storage"))
    assert not crate.has_component(SpeciesComponent)


def test_plain_character_without_living_terms_is_not_tagged():
    actor = _actor()
    smith = _character(actor, name="smith", tags=("villager",), description="a burly blacksmith")
    assert not smith.has_component(SpeciesComponent)
