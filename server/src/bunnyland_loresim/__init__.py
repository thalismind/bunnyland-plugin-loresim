"""Out-of-tree Bunnyland plugin: a pacifist field-naturalist bestiary of knowledge.

You *observe and record* living creatures and plants — you never capture, tame, or harm them,
and nothing changes hands. Recording sharpens the naturalist: every recorded species is marked
"known" on an open surface other packs can consult, repeated sightings unlock deterministic
lore notes, and first-in-world sightings earn discovery credit. The only tension is sight and
patience: a wary subject flushes into cover if you crowd it without a spyglass, then slowly
settles back into view. No sound or hearing state is used anywhere.
"""

from .components import (
    LoreJournalComponent,
    SpeciesComponent,
    SpeciesRecord,
    SpyglassComponent,
)
from .discovery import completion_by_habitat, is_first_in_world, journal_fragments
from .enrichment import LoreWorldgenHook
from .events import SpeciesObservedEvent
from .install import install_loresim
from .knowledge import (
    KnownSpeciesComponent,
    knowledge_fragments,
    knows_species,
    mark_known,
)
from .lore import activity_for, lore_notes, temperament_for
from .observe import (
    OBSERVE_ACTION_DEFINITIONS,
    OBSERVE_ACTION_HANDLERS,
    OBSERVE_DEF,
    ObserveHandler,
)
from .plugin import PLUGIN_ID, bunnyland_plugins, plugin
from .prefabs import spawn_naturalist, spawn_spyglass, spawn_subject
from .settle import SettleConsequence
from .spatial import held_component, room_of

__all__ = [
    "OBSERVE_ACTION_DEFINITIONS",
    "OBSERVE_ACTION_HANDLERS",
    "OBSERVE_DEF",
    "PLUGIN_ID",
    "KnownSpeciesComponent",
    "LoreJournalComponent",
    "LoreWorldgenHook",
    "ObserveHandler",
    "SettleConsequence",
    "SpeciesComponent",
    "SpeciesObservedEvent",
    "SpeciesRecord",
    "SpyglassComponent",
    "activity_for",
    "bunnyland_plugins",
    "completion_by_habitat",
    "held_component",
    "install_loresim",
    "is_first_in_world",
    "journal_fragments",
    "knowledge_fragments",
    "knows_species",
    "lore_notes",
    "mark_known",
    "plugin",
    "room_of",
    "spawn_naturalist",
    "spawn_spyglass",
    "spawn_subject",
    "temperament_for",
]
