import asyncio

from bunnyland.core import WorldActor
from bunnyland.plugins import apply_plugins
from bunnyland.worldgen import CharacterSpec, ObjectSpec, RoomSpec, WorldProposal, instantiate

from bunnyland_loresim import SpeciesComponent
from bunnyland_loresim.plugin import bunnyland_plugins as _plugins


def _world(*, characters=(), objects=()):
    actor = WorldActor()
    apply_plugins(_plugins(), actor)
    result = asyncio.run(
        instantiate(
            actor,
            WorldProposal(
                seed="seed",
                rooms=[RoomSpec(key="room", title="Room")],
                characters=list(characters),
                objects=list(objects),
            ),
        )
    )
    return actor, result


def test_creature_gets_species_component():
    actor, result = _world(
        characters=(
            CharacterSpec(
                key="heron",
                name="heron",
                room_key="room",
                species="bird",
                traits=("wildlife",),
            ),
        )
    )
    component = actor.world.get_entity(result.characters["heron"]).get_component(SpeciesComponent)
    assert component.species == "heron"
    assert component.habitat == "wetland"


def test_plant_object_gets_species_from_description():
    actor, result = _world(
        objects=(
            ObjectSpec(
                key="fern",
                room_key="room",
                name="fern",
                description="a shy woodland fern",
            ),
        )
    )
    component = actor.world.get_entity(result.objects["fern"]).get_component(SpeciesComponent)
    assert component.habitat == "woodland"
    assert component.rarity == "uncommon"


def test_rarity_from_text():
    actor, result = _world(
        characters=(
            CharacterSpec(
                key="owl",
                name="owl",
                room_key="room",
                species="bird",
                description="a rare vanishing forest owl",
            ),
        )
    )
    assert (
        actor.world.get_entity(result.characters["owl"]).get_component(SpeciesComponent).rarity
        == "rare"
    )


def test_non_living_entities_are_not_tagged():
    actor, result = _world(
        characters=(
            CharacterSpec(
                key="smith",
                name="smith",
                room_key="room",
                species="person",
                traits=("villager",),
            ),
        ),
        objects=(ObjectSpec(key="crate", room_key="room", name="wooden crate"),),
    )
    assert not actor.world.get_entity(result.characters["smith"]).has_component(SpeciesComponent)
    assert not actor.world.get_entity(result.objects["crate"]).has_component(SpeciesComponent)
