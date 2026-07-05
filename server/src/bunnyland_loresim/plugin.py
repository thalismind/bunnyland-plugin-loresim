"""Bunnyland plugin entrypoint for the out-of-tree loresim field-naturalist pack."""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    DependencyContribution,
    EcsContribution,
    Plugin,
    RuntimeContribution,
)

from .components import LoreJournalComponent, SpeciesComponent, SpyglassComponent
from .discovery import journal_fragments
from .enrichment import LoreWorldgenHook
from .events import (
    ExpeditionReturnedEvent,
    ExpeditionStartedEvent,
    FieldGuidePublishedEvent,
    RareMigrationEvent,
    SpeciesDiscoveredEvent,
    SpeciesObservedEvent,
)
from .expeditions import (
    EXPEDITION_ACTION_DEFINITIONS,
    EXPEDITION_ACTION_HANDLERS,
    ExpeditionComponent,
    ExpeditionMember,
    expedition_fragments,
)
from .fieldguide import (
    FIELDGUIDE_ACTION_DEFINITIONS,
    FIELDGUIDE_ACTION_HANDLERS,
    AuthoredBy,
    Collectible,
    FieldGuideComponent,
    fieldguide_fragments,
)
from .install import install_loresim
from .knowledge import KnownSpeciesComponent, knowledge_fragments
from .observe import OBSERVE_ACTION_DEFINITIONS, OBSERVE_ACTION_HANDLERS
from .worldgen import NaturalistWorldgenHook

PLUGIN_ID = "bunnyland.loresim"


def plugin() -> Plugin:
    return Plugin(
        id=PLUGIN_ID,
        name="Bunnyland Loresim",
        version="0.2.0",
        default_enabled=True,
        # cartographysim is an *optional* synergy partner (chart -> expedition), never required:
        # the pack runs fully standalone and disables charted-site expeditions when it is absent.
        dependencies=DependencyContribution(recommends=("bunnyland.cartographysim",)),
        ecs=EcsContribution(
            components=(
                SpeciesComponent,
                LoreJournalComponent,
                KnownSpeciesComponent,
                SpyglassComponent,
                ExpeditionComponent,
                FieldGuideComponent,
                Collectible,
            ),
            edges=(
                ExpeditionMember,
                AuthoredBy,
            ),
        ),
        commands=CommandContribution(
            action_handlers=(
                *OBSERVE_ACTION_HANDLERS,
                *EXPEDITION_ACTION_HANDLERS,
                *FIELDGUIDE_ACTION_HANDLERS,
            ),
            action_definitions=(
                *OBSERVE_ACTION_DEFINITIONS,
                *EXPEDITION_ACTION_DEFINITIONS,
                *FIELDGUIDE_ACTION_DEFINITIONS,
            ),
            typed_events=(
                SpeciesObservedEvent,
                ExpeditionStartedEvent,
                SpeciesDiscoveredEvent,
                ExpeditionReturnedEvent,
                FieldGuidePublishedEvent,
                RareMigrationEvent,
            ),
        ),
        runtime=RuntimeContribution(
            service_factories=(install_loresim,),
        ),
        content=ContentContribution(
            prompt_fragments=(
                knowledge_fragments,
                journal_fragments,
                expedition_fragments,
                fieldguide_fragments,
            ),
            worldgen_hooks=(LoreWorldgenHook, NaturalistWorldgenHook),
        ),
    )


def bunnyland_plugins() -> list[Plugin]:
    return [plugin()]


__all__ = ["PLUGIN_ID", "bunnyland_plugins", "plugin"]
