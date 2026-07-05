from __future__ import annotations

from bunnyland.core.world_actor import WorldActor
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_loresim import (
    Collectible,
    ExpeditionComponent,
    ExpeditionMember,
    FieldGuideComponent,
    KnownSpeciesComponent,
    LoreJournalComponent,
    LoreWorldgenHook,
    NaturalistWorldgenHook,
    SpeciesComponent,
    SpyglassComponent,
    expedition_fragments,
    fieldguide_fragments,
    journal_fragments,
    knowledge_fragments,
)
from bunnyland_loresim.fieldguide import AuthoredBy
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


def test_plugin_is_v2():
    plugin = load_modules(["bunnyland_loresim"])[0]
    assert plugin.version == "0.2.0"
    for component in (ExpeditionComponent, FieldGuideComponent, Collectible):
        assert component in plugin.ecs.components
    for edge in (ExpeditionMember, AuthoredBy):
        assert edge in plugin.ecs.edges
    assert NaturalistWorldgenHook in plugin.content.worldgen_hooks
    assert expedition_fragments in plugin.content.prompt_fragments
    assert fieldguide_fragments in plugin.content.prompt_fragments
    # Optional synergy with the cartography pack is a recommendation, never a hard requirement.
    assert plugin.dependencies.recommends == ("bunnyland.cartographysim",)
    assert plugin.dependencies.requires == ()


def test_plugin_registers_v2_events():
    from bunnyland_loresim.events import (
        ExpeditionReturnedEvent,
        ExpeditionStartedEvent,
        FieldGuidePublishedEvent,
        RareMigrationEvent,
        SpeciesDiscoveredEvent,
    )

    plugin = load_modules(["bunnyland_loresim"])[0]
    for event in (
        ExpeditionStartedEvent,
        SpeciesDiscoveredEvent,
        ExpeditionReturnedEvent,
        FieldGuidePublishedEvent,
        RareMigrationEvent,
    ):
        assert event in plugin.commands.typed_events


def test_plugin_applies_and_registers_verbs():
    actor = WorldActor()
    applied = apply_plugins(load_modules(["bunnyland_loresim"]), actor)
    assert applied[0].id == "bunnyland.loresim"
    command_types = {definition.command_type for definition in actor.action_definitions()}
    assert {"observe", "embark", "publish-field-guide"} <= command_types


def test_plugin_registers_consequences_via_install():
    import asyncio

    actor = WorldActor()
    apply_plugins(load_modules(["bunnyland_loresim"]), actor)
    # The three consequences (settle, expedition, migration) should advance without error.
    asyncio.run(actor.tick(1.0))
