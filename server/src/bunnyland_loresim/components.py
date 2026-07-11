"""Core Loresim components: observable species, the field journal, and the spyglass.

Loresim is a *pacifist cataloguing* pack. Nothing here captures, tames, or removes a
creature — a :class:`SpeciesComponent` merely marks a living thing as observable, and a
:class:`LoreJournalComponent` is a character's private bestiary of *knowledge* recorded from
what they have watched. No item ever changes hands; only knowledge accrues.

Components are immutable frozen pydantic dataclasses; the observe verb swaps whole values
with ``replace_component(entity, replace(component, ...))``.
"""

from __future__ import annotations

from pydantic.dataclasses import dataclass
from relics import Component

# --------------------------------------------------------------------------------------
# Observable subjects
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SpeciesComponent(Component):
    """Marks a *living* creature or plant as an observable, recordable species.

    Placed on generated wildlife/flora by
    :class:`~bunnyland_loresim.enrichment.LoreGenerationEnricher`,
    or on hand-built subjects via the spawn helpers. It is descriptive metadata only — it does
    not make the subject capturable or ownable.
    """

    species: str = "creature"
    habitat: str = "wild"
    rarity: str = "common"


# --------------------------------------------------------------------------------------
# The field journal (per-character memory of knowledge)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SpeciesRecord:
    """One species' entry in a naturalist's field journal.

    ``first_seen_epoch``/``first_seen_room`` pin the first sighting; ``sightings`` counts how
    many times the species has been observed, which unlocks progressively deeper lore notes.
    """

    species: str
    habitat: str
    rarity: str
    first_seen_epoch: int
    first_seen_room: str
    sightings: int = 1


@dataclass(frozen=True)
class LoreJournalComponent(Component):
    """A character's field journal: the bestiary of knowledge they have recorded.

    This *is* the per-character memory Loresim reuses — a private, growing catalogue of
    living things the naturalist has watched. ``discoveries`` lists the species this observer
    was the first in the whole world to record.
    """

    records: tuple[SpeciesRecord, ...] = ()
    discoveries: tuple[str, ...] = ()

    def record_for(self, species: str) -> SpeciesRecord | None:
        """Return the journal entry for ``species``, or ``None`` if it is unrecorded."""
        for record in self.records:
            if record.species == species:
                return record
        return None

    def recorded_species(self) -> tuple[str, ...]:
        """Return the species names this journal holds, in record order."""
        return tuple(record.species for record in self.records)


# --------------------------------------------------------------------------------------
# The spyglass (patience aid)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SpyglassComponent(Component):
    """A held optic that lets a naturalist record wary or distant subjects without spooking them.

    Without one, approaching close enough to record a wary subject flushes it into cover.
    """

    magnification: float = 1.0


__all__ = [
    "LoreJournalComponent",
    "SpeciesComponent",
    "SpeciesRecord",
    "SpyglassComponent",
]
