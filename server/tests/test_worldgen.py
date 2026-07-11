import asyncio

from bunnyland.core import WorldActor
from bunnyland.plugins import apply_plugins
from bunnyland.worldgen import CharacterSpec, RoomSpec, WorldProposal, instantiate

from bunnyland_loresim import KnownSpeciesComponent, LoreJournalComponent
from bunnyland_loresim.plugin import bunnyland_plugins as _plugins


def _character(*, name="Naturalist", tags=(), description=""):
    actor = WorldActor()
    apply_plugins(_plugins(), actor)
    result = asyncio.run(
        instantiate(
            actor,
            WorldProposal(
                seed="seed",
                rooms=[RoomSpec(key="room", title="Room")],
                characters=[
                    CharacterSpec(
                        key=name.casefold(),
                        name=name,
                        room_key="room",
                        species="person",
                        traits=tuple(tags),
                        description=description,
                    )
                ],
            ),
        )
    )
    return actor.world.get_entity(result.characters[name.casefold()])


def test_naturalist_gets_journal_and_starting_knowledge():
    ranger = _character(tags=("ranger",), description="a woodland ranger")
    assert ranger.has_component(LoreJournalComponent)
    assert ranger.get_component(KnownSpeciesComponent).species == ("pine marten",)


def test_naturalist_without_habitat_defaults_to_wild():
    scholar = _character(tags=("lorekeeper",), description="a keeper of lore")
    assert scholar.get_component(KnownSpeciesComponent).species == ("wanderer moth",)


def test_non_naturalist_is_left_alone():
    smith = _character(name="Smith", tags=("villager",), description="a burly blacksmith")
    assert not smith.has_component(KnownSpeciesComponent)
