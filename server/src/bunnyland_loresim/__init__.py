"""Out-of-tree Bunnyland plugin: a pacifist field-naturalist bestiary of knowledge.

You *observe and record* living creatures and plants — you never capture, tame, or harm them,
and nothing changes hands. Recording sharpens the naturalist: every recorded species is marked
"known" on an open surface other packs can consult, repeated sightings unlock deterministic
lore notes, and first-in-world sightings earn discovery credit. The only tension is sight and
patience: a wary subject flushes into cover if you crowd it without a spyglass, then slowly
settles back into view. No sound or hearing state is used anywhere.

v2 adds the **expedition** headline (set out to survey a habitat and record what you find),
**research & publishing** (turn a journal into a museum-donatable field guide that *masters*
its species), a deeper :class:`KnownSpeciesComponent` payoff (known vs. mastered), an optional
``cartographysim`` connector (chart -> expedition), and a rare-migration storyteller incident.
"""

from .cartography import (
    MapComponent,
    cartography_available,
    charted_biome,
    charted_sites,
)
from .components import (
    LoreJournalComponent,
    SpeciesComponent,
    SpeciesRecord,
    SpyglassComponent,
)
from .discovery import completion_by_habitat, is_first_in_world, journal_fragments
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
    EMBARK_DEF,
    EXPEDITION_ACTION_DEFINITIONS,
    EXPEDITION_ACTION_HANDLERS,
    EXPEDITION_DURATION,
    HABITAT_SPECIES,
    EmbarkHandler,
    ExpeditionComponent,
    ExpeditionConsequence,
    ExpeditionMember,
    expedition_fragments,
    record_sighting,
    species_for_site,
)
from .fieldguide import (
    FIELDGUIDE_ACTION_DEFINITIONS,
    FIELDGUIDE_ACTION_HANDLERS,
    PUBLISH_DEF,
    PUBLISH_MIN_SPECIES,
    STUDY_SIGHTINGS,
    AuthoredBy,
    Collectible,
    FieldGuideComponent,
    PublishFieldGuideHandler,
    author_editions,
    authored_guides,
    fieldguide_fragments,
)
from .install import install_loresim
from .knowledge import (
    KnownSpeciesComponent,
    knowledge_fragments,
    knows_species,
    mark_known,
    mark_mastered,
    masters_species,
)
from .lore import activity_for, lore_notes, temperament_for
from .migration import MIGRATION_INTERVAL, MigrationConsequence
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
from .worldgen import NATURALIST_TERMS, NaturalistWorldgenHook

__all__ = [
    "EMBARK_DEF",
    "EXPEDITION_ACTION_DEFINITIONS",
    "EXPEDITION_ACTION_HANDLERS",
    "EXPEDITION_DURATION",
    "FIELDGUIDE_ACTION_DEFINITIONS",
    "FIELDGUIDE_ACTION_HANDLERS",
    "HABITAT_SPECIES",
    "MIGRATION_INTERVAL",
    "NATURALIST_TERMS",
    "OBSERVE_ACTION_DEFINITIONS",
    "OBSERVE_ACTION_HANDLERS",
    "OBSERVE_DEF",
    "PLUGIN_ID",
    "PUBLISH_DEF",
    "PUBLISH_MIN_SPECIES",
    "STUDY_SIGHTINGS",
    "AuthoredBy",
    "Collectible",
    "EmbarkHandler",
    "ExpeditionComponent",
    "ExpeditionConsequence",
    "ExpeditionMember",
    "ExpeditionReturnedEvent",
    "ExpeditionStartedEvent",
    "FieldGuideComponent",
    "FieldGuidePublishedEvent",
    "KnownSpeciesComponent",
    "LoreJournalComponent",
    "LoreWorldgenHook",
    "MapComponent",
    "MigrationConsequence",
    "NaturalistWorldgenHook",
    "ObserveHandler",
    "PublishFieldGuideHandler",
    "RareMigrationEvent",
    "SettleConsequence",
    "SpeciesComponent",
    "SpeciesDiscoveredEvent",
    "SpeciesObservedEvent",
    "SpeciesRecord",
    "SpyglassComponent",
    "activity_for",
    "author_editions",
    "authored_guides",
    "bunnyland_plugins",
    "cartography_available",
    "charted_biome",
    "charted_sites",
    "completion_by_habitat",
    "expedition_fragments",
    "fieldguide_fragments",
    "held_component",
    "install_loresim",
    "is_first_in_world",
    "journal_fragments",
    "knowledge_fragments",
    "knows_species",
    "lore_notes",
    "mark_known",
    "mark_mastered",
    "masters_species",
    "plugin",
    "record_sighting",
    "room_of",
    "spawn_naturalist",
    "spawn_spyglass",
    "spawn_subject",
    "species_for_site",
    "temperament_for",
]
