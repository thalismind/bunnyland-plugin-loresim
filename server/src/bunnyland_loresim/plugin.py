"""Bunnyland plugin entrypoint for the out-of-tree loresim field-naturalist pack."""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    EcsContribution,
    Plugin,
    RuntimeContribution,
)

from .components import LoreJournalComponent, SpeciesComponent, SpyglassComponent
from .discovery import journal_fragments
from .enrichment import LoreWorldgenHook
from .events import SpeciesObservedEvent
from .install import install_loresim
from .knowledge import KnownSpeciesComponent, knowledge_fragments
from .observe import OBSERVE_ACTION_DEFINITIONS, OBSERVE_ACTION_HANDLERS

PLUGIN_ID = "bunnyland.loresim"


def plugin() -> Plugin:
    return Plugin(
        id=PLUGIN_ID,
        name="Bunnyland Loresim",
        version="0.1.0",
        default_enabled=True,
        ecs=EcsContribution(
            components=(
                SpeciesComponent,
                LoreJournalComponent,
                KnownSpeciesComponent,
                SpyglassComponent,
            ),
        ),
        commands=CommandContribution(
            action_handlers=OBSERVE_ACTION_HANDLERS,
            action_definitions=OBSERVE_ACTION_DEFINITIONS,
            typed_events=(SpeciesObservedEvent,),
        ),
        runtime=RuntimeContribution(
            service_factories=(install_loresim,),
        ),
        content=ContentContribution(
            prompt_fragments=(knowledge_fragments, journal_fragments),
            worldgen_hooks=(LoreWorldgenHook,),
        ),
    )


def bunnyland_plugins() -> list[Plugin]:
    return [plugin()]


__all__ = ["PLUGIN_ID", "bunnyland_plugins", "plugin"]
