"""The ``observe`` verb: record a living subject into the naturalist's field journal.

This is a *pacifist* verb — it never captures, moves, or claims the subject; it only writes
*knowledge* into the observer's :class:`~bunnyland_loresim.components.LoreJournalComponent`.
The tension is sight and patience, not sound:

1. The observer must be able to perceive (:class:`PerceptionComponent` active).
2. The subject must be reachable (same room) and *visible* — a subject hidden in cover
   (:class:`StealthComponent`) cannot be recorded.
3. The subject must be a recordable species (:class:`SpeciesComponent`).
4. A **wary** subject (any subject carrying a :class:`StealthComponent`) is spooked by a
   close approach and flushes into cover — *unless* the naturalist carries a
   :class:`SpyglassComponent`, which lets them record it safely from a distance.

Validation order follows the project convention: invalid id -> missing entity ->
not reachable / not visible -> wrong kind -> (spook) -> record.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core import (
    PerceptionComponent,
    StealthComponent,
)
from bunnyland.core.actions import ActionArgument, ActionDefinition, ActionEffort, effort_cost
from bunnyland.core.commands import Lane, SubmittedCommand
from bunnyland.core.ecs import reachable_ids
from bunnyland.core.events import EventVisibility
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    planned,
    rejected,
    require_character,
    require_entity,
)
from bunnyland.core.mutations import MutationPlan, SetComponent

from .components import (
    LoreJournalComponent,
    SpeciesComponent,
    SpeciesRecord,
    SpyglassComponent,
)
from .discovery import is_first_in_world
from .events import SpeciesObservedEvent
from .knowledge import KnownSpeciesComponent
from .spatial import held_component, room_of


def _is_hidden(subject) -> bool:
    """A subject is out of sight when it is hiding below its own visibility threshold."""
    if not subject.has_component(StealthComponent):
        return False
    stealth = subject.get_component(StealthComponent)
    return stealth.hiding and stealth.visibility_level <= stealth.hidden_threshold


class ObserveHandler:
    """Record a visible living subject into the observer's field journal."""

    command_type = "observe"

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id, character, rejection = require_character(ctx, command.character_id)
        if rejection is not None:
            return rejection

        subject_id, subject, rejection = require_entity(
            ctx,
            command.payload.get("subject_id"),
            invalid_reason="invalid subject id",
            missing_reason="subject does not exist",
        )
        if rejection is not None:
            return rejection

        if (
            character.has_component(PerceptionComponent)
            and not character.get_component(PerceptionComponent).active
        ):
            return rejected("you cannot see anything right now")
        if subject_id not in reachable_ids(ctx.world, character):
            return rejected("you cannot see that from here")
        if _is_hidden(subject):
            return rejected("that is hidden from view")
        if not subject.has_component(SpeciesComponent):
            return rejected("that is not a living thing you can record")

        species_component = subject.get_component(SpeciesComponent)
        # A wary subject bolts if you get close enough to record it without a spyglass.
        wary = subject.has_component(StealthComponent)
        has_spyglass = held_component(ctx.world, character, SpyglassComponent) is not None
        if wary and not has_spyglass:
            stealth = subject.get_component(StealthComponent)
            return planned(
                MutationPlan(
                    (
                        SetComponent(
                            subject.id,
                            replace(stealth, hiding=True, visibility_level=0.0),
                        ),
                    )
                )
            )

        room = room_of(ctx.world, character_id)
        room_id = str(room.id) if room is not None else ""
        event, updated_journal = self._record(
            ctx, character, species_component, subject_id, room_id
        )
        knowledge = (
            character.get_component(KnownSpeciesComponent)
            if character.has_component(KnownSpeciesComponent)
            else KnownSpeciesComponent()
        )
        updated_knowledge = replace(
            knowledge,
            species=tuple(sorted({*knowledge.species, species_component.species})),
        )
        return planned(
            MutationPlan(
                (
                    SetComponent(character.id, updated_journal),
                    SetComponent(character.id, updated_knowledge),
                )
            ),
            event,
        )

    def _record(
        self,
        ctx: HandlerContext,
        character,
        species_component: SpeciesComponent,
        subject_id,
        room_id: str,
    ) -> tuple[SpeciesObservedEvent, LoreJournalComponent]:
        species = species_component.species
        journal = (
            character.get_component(LoreJournalComponent)
            if character.has_component(LoreJournalComponent)
            else LoreJournalComponent()
        )
        existing = journal.record_for(species)
        discovery = False

        if existing is None:
            discovery = is_first_in_world(ctx.world, species)
            new_record = SpeciesRecord(
                species=species,
                habitat=species_component.habitat,
                rarity=species_component.rarity,
                first_seen_epoch=ctx.epoch,
                first_seen_room=room_id,
                sightings=1,
            )
            records = (*journal.records, new_record)
            discoveries = (*journal.discoveries, species) if discovery else journal.discoveries
            sightings = 1
        else:
            updated = replace(existing, sightings=existing.sightings + 1)
            records = tuple(updated if r.species == species else r for r in journal.records)
            discoveries = journal.discoveries
            sightings = updated.sightings

        updated_journal = replace(journal, records=records, discoveries=discoveries)
        return SpeciesObservedEvent(
            **ctx.event_base(
                visibility=EventVisibility.PRIVATE,
                actor_id=str(character.id),
                room_id=room_id or None,
                target_ids=(str(subject_id),),
                subject_id=str(subject_id),
                species=species,
                sightings=sightings,
                new_record=existing is None,
                discovery=discovery,
            )
        ), updated_journal


OBSERVE_DEF = ActionDefinition(
    command_type="observe",
    title="Observe",
    description="Record a living creature or plant you can see into your field journal.",
    lane=Lane.WORLD,
    cost=effort_cost(action=ActionEffort.ROUTINE),
    arguments={
        "subject_id": ActionArgument(
            title="Subject",
            description="The living creature or plant to observe and record.",
            kind="entity",
            required=True,
        ),
    },
)

OBSERVE_ACTION_DEFINITIONS = (OBSERVE_DEF,)
OBSERVE_ACTION_HANDLERS = (ObserveHandler,)


__all__ = [
    "OBSERVE_ACTION_DEFINITIONS",
    "OBSERVE_ACTION_HANDLERS",
    "OBSERVE_DEF",
    "ObserveHandler",
]
