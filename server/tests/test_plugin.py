from __future__ import annotations

from bunnyland.core.world_actor import WorldActor
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_loresim import (
    KnownSpeciesComponent,
    LoreJournalComponent,
    LoreWorldgenHook,
    SpeciesComponent,
    SpyglassComponent,
    journal_fragments,
    knowledge_fragments,
)
from bunnyland_loresim.plugin import PLUGIN_ID


def test_plugin_loads_with_dotted_id():
    plugins = load_modules(["bunnyland_loresim"])
    assert [p.id for p in plugins] == ["bunnyland.loresim"]
    assert PLUGIN_ID == "bunnyland.loresim"


def test_plugin_declares_its_contributions():
    plugin = load_modules(["bunnyland_loresim"])[0]
    for component in (
        SpeciesComponent,
        LoreJournalComponent,
        KnownSpeciesComponent,
        SpyglassComponent,
    ):
        assert component in plugin.ecs.components
    assert LoreWorldgenHook in plugin.content.worldgen_hooks
    assert knowledge_fragments in plugin.content.prompt_fragments
    assert journal_fragments in plugin.content.prompt_fragments


def test_plugin_version():
    plugin = load_modules(["bunnyland_loresim"])[0]
    assert plugin.version == "0.2.0"


def test_plugin_applies_and_registers_observe_verb():
    actor = WorldActor()
    applied = apply_plugins(load_modules(["bunnyland_loresim"]), actor)
    assert applied[0].id == "bunnyland.loresim"
    command_types = {definition.command_type for definition in actor.action_definitions()}
    assert "observe" in command_types
