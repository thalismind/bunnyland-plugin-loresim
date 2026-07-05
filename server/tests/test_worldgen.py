from __future__ import annotations

import asyncio

from bunnyland.core import (
    CharacterComponent,
    IdentityComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.components import GenerationIntentComponent
from bunnyland.core.ecs import replace_component
from bunnyland.core.events import CharacterGeneratedEvent, event_base
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_loresim import KnownSpeciesComponent, LoreJournalComponent
from bunnyland_loresim.components import SpeciesRecord
from bunnyland_loresim.worldgen import NaturalistWorldgenHook


def _actor():
    actor = WorldActor()
    apply_plugins(load_modules(["bunnyland_loresim"]), actor)
    return actor


def _generate(actor, entity, *, name="npc", tags=(), description=""):
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
    asyncio.run(actor.bus.publish(event))


def _character(actor, name="npc"):
    return spawn_entity(
        actor.world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )


def test_naturalist_gets_journal_and_starting_knowledge():
    actor = _actor()
    ranger = _character(actor, "Fern")
    _generate(actor, ranger, name="Fern", tags=("ranger",), description="a woodland ranger")
    assert ranger.has_component(LoreJournalComponent)
    known = ranger.get_component(KnownSpeciesComponent)
    # Woodland habitat seeds the first woodland species (pine marten).
    assert known.species == ("pine marten",)


def test_naturalist_without_habitat_defaults_to_wild():
    actor = _actor()
    scholar = _character(actor, "Sage")
    _generate(actor, scholar, name="Sage", tags=("lorekeeper",), description="a keeper of lore")
    assert scholar.get_component(KnownSpeciesComponent).species == ("wanderer moth",)


def test_non_naturalist_is_left_alone():
    actor = _actor()
    smith = _character(actor, "Smith")
    _generate(actor, smith, name="Smith", tags=("villager",), description="a burly blacksmith")
    assert not smith.has_component(KnownSpeciesComponent)


def test_existing_journal_is_not_reseeded():
    actor = _actor()
    ranger = _character(actor, "Fern")
    replace_component(
        ranger,
        LoreJournalComponent(
            records=(
                SpeciesRecord(
                    species="bittern", habitat="wetland", rarity="rare",
                    first_seen_epoch=0, first_seen_room="x",
                ),
            )
        ),
    )
    _generate(actor, ranger, name="Fern", tags=("ranger",), description="a woodland ranger")
    # Untouched: no starting knowledge was seeded over the pre-existing journal.
    assert not ranger.has_component(KnownSpeciesComponent)
    assert ranger.get_component(LoreJournalComponent).recorded_species() == ("bittern",)


def test_hook_ignores_missing_entity():
    actor = _actor()
    hook = NaturalistWorldgenHook()
    hook.subscribe(actor)
    event = CharacterGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id="entity_999999",
        entity_key="ghost",
        entity_kind="character",
        generation=GenerationIntentComponent(tags=("ranger",), description="a ranger"),
        character_key="ghost",
        room_id="room_1",
    )
    # No entity for that id: the hook returns quietly without raising.
    asyncio.run(actor.bus.publish(event))
