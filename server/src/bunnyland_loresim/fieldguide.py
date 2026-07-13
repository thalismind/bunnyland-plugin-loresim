"""Research & publishing: turn a field journal into a published field guide.

Recording species fills a private journal; *publishing* turns that research into a **field
guide** — a real, museum-donatable work that deepens the author's knowledge. This is the v2
research payoff on top of v1's cataloguing:

- A guide can only be published once the author has *studied* a habitat: several species,
  each seen more than once (repeat sightings are what unlock lore, so they gate publishing).
- Publishing promotes every covered species to **mastered** on the open
  :class:`~bunnyland_loresim.knowledge.KnownSpeciesComponent` surface — the deeper payoff
  other packs consult.
- The guide entity carries a :class:`Collectible`, the open **museum** donation surface, so a
  museum pack can accept field guides (and expedition field sketches) without importing lore.
- Authorship is a **typed edge** (:class:`AuthoredBy`, guide → naturalist), never a list.

Guide notes are assembled deterministically from the journal via :mod:`hashlib` (reusing the
lore vocabulary), never from ``random`` or the clock.
"""

from __future__ import annotations

from bunnyland.core import ContainmentMode, Contains, IdentityComponent
from bunnyland.core.actions import ActionArgument, ActionDefinition, ActionEffort, effort_cost
from bunnyland.core.commands import Lane, SubmittedCommand
from bunnyland.core.events import EventVisibility
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    planned,
    rejected,
    require_character,
)
from bunnyland.core.mutations import AddEdge, AddEntity, EntityReference, MutationPlan, SetComponent
from pydantic.dataclasses import dataclass
from relics import Component, Edge, Entity, World

from .components import LoreJournalComponent, SpeciesRecord
from .events import FieldGuidePublishedEvent
from .knowledge import KnownSpeciesComponent
from .lore import lore_notes

#: How many *well-studied* species (seen >= STUDY_SIGHTINGS) a habitat needs to publish.
PUBLISH_MIN_SPECIES = 2

#: Sightings that make a species "well-studied" and eligible to appear in a guide.
STUDY_SIGHTINGS = 2


@dataclass(frozen=True)
class Collectible(Component):
    """Open museum-donation surface: a specimen, sketch, or field guide anything can donate.

    Kept self-contained so a museum pack can accept it structurally without importing lore.
    ``kind`` is ``specimen`` / ``field-guide``; ``category`` groups a museum wing.
    """

    kind: str = "specimen"
    title: str = ""
    origin: str = "loresim"
    category: str = "natural-history"
    quality: str = "common"


@dataclass(frozen=True)
class FieldGuideComponent(Component):
    """A published field guide: which habitat and species it covers, and its edition."""

    habitat: str = "wild"
    species: tuple[str, ...] = ()
    edition: int = 1
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthoredBy(Edge):
    """guide -> naturalist authorship (a repeatable typed relationship; guides may be revised)."""

    role: str = "author"


def _well_studied(journal: LoreJournalComponent, habitat: str) -> tuple[SpeciesRecord, ...]:
    """Records for ``habitat`` seen enough times to be worth publishing, sorted by species."""
    records = [
        record
        for record in journal.records
        if record.habitat == habitat and record.sightings >= STUDY_SIGHTINGS
    ]
    return tuple(sorted(records, key=lambda record: record.species))


def _guide_notes(records: tuple[SpeciesRecord, ...]) -> tuple[str, ...]:
    """Deterministic per-species guide lines built from the recorded lore."""
    lines: list[str] = []
    for record in records:
        notes = " ".join(lore_notes(record))
        lines.append(f"{record.species} — {notes}")
    return tuple(lines)


def author_editions(world: World, author_id, habitat: str) -> int:
    """How many guides ``author_id`` has already published for ``habitat``."""
    count = 0
    for entity in world.query().with_all([FieldGuideComponent]).execute_entities():
        guide = entity.get_component(FieldGuideComponent)
        if guide.habitat != habitat:
            continue
        if entity.has_relationship(AuthoredBy, author_id):
            count += 1
    return count


def authored_guides(world: World, author: Entity) -> list[Entity]:
    """Field-guide entities authored by ``author``, sorted by id."""
    guides = [
        entity
        for entity in world.query().with_all([FieldGuideComponent]).execute_entities()
        if entity.has_relationship(AuthoredBy, author.id)
    ]
    return sorted(guides, key=lambda guide: str(guide.id))


class PublishFieldGuideHandler:
    """Publish a field guide for a habitat the naturalist has studied enough to write up."""

    command_type = "publish-field-guide"

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id, character, rejection = require_character(ctx, command.character_id)
        if rejection is not None:
            return rejection
        habitat = str(command.payload.get("habitat") or "").strip()
        if not habitat:
            return rejected("name the habitat to write up")
        if not character.has_component(LoreJournalComponent):
            return rejected("you have nothing recorded to publish")
        journal = character.get_component(LoreJournalComponent)
        records = _well_studied(journal, habitat)
        if len(records) < PUBLISH_MIN_SPECIES:
            return rejected("you must study more species of that habitat before publishing")

        species = tuple(record.species for record in records)
        edition = author_editions(ctx.world, character_id, habitat) + 1
        guide = EntityReference()
        quality = "rich" if len(species) >= 4 else "standard"
        knowledge = (
            character.get_component(KnownSpeciesComponent)
            if character.has_component(KnownSpeciesComponent)
            else KnownSpeciesComponent()
        )
        known = tuple(sorted({*knowledge.species, *species}))
        mastered = tuple(sorted({*knowledge.mastered, *species}))
        return planned(
            MutationPlan(
                (
                    AddEntity(
                        (
                            IdentityComponent(
                                name=f"field guide to the {habitat}", kind="document"
                            ),
                            FieldGuideComponent(
                                habitat=habitat,
                                species=species,
                                edition=edition,
                                notes=_guide_notes(records),
                            ),
                            Collectible(
                                kind="field-guide",
                                title=f"field guide to the {habitat} (ed. {edition})",
                                category="field-guides",
                                quality=quality,
                            ),
                        ),
                        reference=guide,
                    ),
                    AddEdge(guide, character.id, AuthoredBy()),
                    AddEdge(
                        character.id,
                        guide,
                        Contains(mode=ContainmentMode.INVENTORY),
                    ),
                    SetComponent(
                        character.id,
                        KnownSpeciesComponent(species=known, mastered=mastered),
                    ),
                )
            ),
            lambda: FieldGuidePublishedEvent(
                **ctx.event_base(
                    visibility=EventVisibility.PRIVATE,
                    actor_id=str(character_id),
                    target_ids=(str(guide.require()),),
                    guide_id=str(guide.require()),
                    habitat=habitat,
                    species=species,
                    edition=edition,
                )
            ),
        )


def fieldguide_fragments(world: World, character: Entity) -> list[str]:
    """Surface the naturalist's published field guides in their prompt."""
    if character is None:
        return []
    guides = authored_guides(world, character)
    if not guides:
        return []
    lines: list[str] = []
    for guide in guides:
        component = guide.get_component(FieldGuideComponent)
        lines.append(
            f"You published a field guide to the {component.habitat} "
            f"(ed. {component.edition}) covering {len(component.species)} species."
        )
    return sorted(lines)


PUBLISH_DEF = ActionDefinition(
    command_type="publish-field-guide",
    title="Publish field guide",
    description="Write up a habitat you have studied into a museum-donatable field guide.",
    lane=Lane.WORLD,
    cost=effort_cost(action=ActionEffort.EXTENDED),
    arguments={
        "habitat": ActionArgument(
            title="Habitat",
            description="The habitat to write up (you must have studied several of its species).",
            kind="text",
            required=True,
        ),
    },
)

FIELDGUIDE_ACTION_DEFINITIONS = (PUBLISH_DEF,)
FIELDGUIDE_ACTION_HANDLERS = (PublishFieldGuideHandler,)


__all__ = [
    "FIELDGUIDE_ACTION_DEFINITIONS",
    "FIELDGUIDE_ACTION_HANDLERS",
    "PUBLISH_DEF",
    "PUBLISH_MIN_SPECIES",
    "STUDY_SIGHTINGS",
    "AuthoredBy",
    "Collectible",
    "FieldGuideComponent",
    "PublishFieldGuideHandler",
    "author_editions",
    "authored_guides",
    "fieldguide_fragments",
]
