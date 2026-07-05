"""Expeditions: the v2 headline mechanic — set out to survey a habitat and record what you find.

An expedition is *movement with a purpose*. A naturalist embarks from their room; the party
physically travels (core containment/movement) to a **field site** — either a fresh site
opened for the habitat, or, when the optional ``cartographysim`` connector is loaded and the
naturalist carries a charted map, a room they have already charted. After a few ticks the
:class:`ExpeditionConsequence` resolves the trip: a living subject is turned up and recorded
into the field journal (core **memory**), field knowledge deepens, a museum-donatable field
sketch is produced, co-explorers' affective :class:`SocialBond`\\s warm from the shared find,
and the party walks home.

Modelling notes:

- Co-explorers are tracked as a **typed edge** (:class:`ExpeditionMember`, leader → member),
  never a list on a component — each edge is its own index.
- Affective bonds ride the core :class:`SocialBond` typed edge via ``adjust_bond``.
- Everything is deterministic (subject choice via :mod:`hashlib`); no ``random`` or clock.
- Only *sight and patience* is modelled: a turned-up subject may be wary (a
  :class:`StealthComponent`), never anything to do with sound or hearing.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

from bunnyland.core import (
    ContainmentMode,
    Contains,
    IdentityComponent,
    PerceptionComponent,
    RoomComponent,
    StealthComponent,
    container_of,
    spawn_entity,
)
from bunnyland.core.actions import ActionArgument, ActionDefinition
from bunnyland.core.commands import CommandCost, Lane, SubmittedCommand
from bunnyland.core.ecs import contents, parse_entity_id, replace_component
from bunnyland.core.events import DomainEvent, EventVisibility, event_base
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    ok,
    rejected,
    require_character,
)
from bunnyland.mechanics.social import adjust_bond
from pydantic.dataclasses import dataclass
from relics import Component, Edge, Entity, World

from .cartography import charted_biome
from .components import LoreJournalComponent, SpeciesComponent, SpeciesRecord
from .discovery import is_first_in_world
from .events import ExpeditionReturnedEvent, ExpeditionStartedEvent, SpeciesDiscoveredEvent
from .fieldguide import Collectible
from .knowledge import mark_known
from .spatial import room_of

#: Deterministic subject pools per habitat. Real natural-history names, never brands.
HABITAT_SPECIES: dict[str, tuple[str, ...]] = {
    "wetland": ("bittern", "spoonbill", "marsh harrier"),
    "woodland": ("pine marten", "goldcrest", "stag beetle"),
    "grassland": ("corncrake", "harvest mouse", "marbled white"),
    "shore": ("sanderling", "oystercatcher", "sea holly"),
    "wild": ("wanderer moth", "glass lizard", "ghost orchid"),
}

#: How many ticks an expedition runs before it resolves.
EXPEDITION_DURATION = 2

#: The affective warmth a shared discovery adds to co-explorers' bonds.
_BOND_WARMTH = {"affinity": 0.08, "trust": 0.05, "familiarity": 0.05}


@dataclass(frozen=True)
class ExpeditionComponent(Component):
    """A naturalist's in-progress expedition (one per leader while underway)."""

    habitat: str = "wild"
    origin_room_id: str = ""
    site_room_id: str = ""
    progress: int = 0
    duration: int = EXPEDITION_DURATION


@dataclass(frozen=True)
class ExpeditionMember(Edge):
    """leader -> co-explorer taken along on an expedition (a repeatable typed relationship)."""

    role: str = "companion"


def species_for_site(habitat: str, site_room_id: str) -> str:
    """Deterministically pick which species an expedition to ``site_room_id`` turns up."""
    pool = HABITAT_SPECIES.get(habitat, HABITAT_SPECIES["wild"])
    digest = hashlib.sha256(f"discover:{habitat}:{site_room_id}".encode()).hexdigest()
    return pool[int(digest, 16) % len(pool)]


def _is_wary(species: str, site_room_id: str) -> bool:
    """Deterministic: some turned-up subjects are wary and slip into cover (sight, not sound)."""
    digest = hashlib.sha256(f"wary:{species}:{site_room_id}".encode()).hexdigest()
    return int(digest, 16) % 2 == 0


def record_sighting(
    world: World,
    character: Entity,
    *,
    species: str,
    habitat: str,
    rarity: str,
    epoch: int,
    room_id: str,
) -> bool:
    """Write a sighting into the character's journal (core memory); return discovery credit.

    Reused by expeditions so afield sightings land in the *same* journal store as the
    ``observe`` verb. Returns whether this was a first-in-world discovery.
    """
    journal = (
        character.get_component(LoreJournalComponent)
        if character.has_component(LoreJournalComponent)
        else LoreJournalComponent()
    )
    existing = journal.record_for(species)
    if existing is None:
        discovery = is_first_in_world(world, species)
        new_record = SpeciesRecord(
            species=species,
            habitat=habitat,
            rarity=rarity,
            first_seen_epoch=epoch,
            first_seen_room=room_id,
            sightings=1,
        )
        records = (*journal.records, new_record)
        discoveries = (*journal.discoveries, species) if discovery else journal.discoveries
    else:
        discovery = False
        updated = replace(existing, sightings=existing.sightings + 1)
        records = tuple(updated if r.species == species else r for r in journal.records)
        discoveries = journal.discoveries
    replace_component(character, replace(journal, records=records, discoveries=discoveries))
    mark_known(character, species)
    return discovery


def _relocate(world: World, entity: Entity, destination: Entity) -> None:
    """Move ``entity`` into ``destination`` (core containment movement)."""
    current_id = container_of(entity)
    if current_id is not None and world.has_entity(current_id):
        world.get_entity(current_id).remove_relationship(Contains, entity.id)
    destination.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), entity.id)


def _party_members(world: World, leader: Entity, origin: Entity) -> list[Entity]:
    """Fellow naturalists (journal-carriers) standing with the leader, sorted by id."""
    members: list[Entity] = []
    for entity_id in contents(origin):
        if entity_id == leader.id or not world.has_entity(entity_id):
            continue
        entity = world.get_entity(entity_id)
        if entity.has_component(LoreJournalComponent):
            members.append(entity)
    return sorted(members, key=lambda member: str(member.id))


class EmbarkHandler:
    """Set out on an expedition to a habitat (optionally a charted site)."""

    command_type = "embark"

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id, character, rejection = require_character(ctx, command.character_id)
        if rejection is not None:
            return rejection
        if character.has_component(PerceptionComponent) and not character.get_component(
            PerceptionComponent
        ).active:
            return rejected("you cannot survey anything right now")
        origin = room_of(ctx.world, character_id)
        if origin is None:
            return rejected("you must set out from a room")
        if character.has_component(ExpeditionComponent):
            return rejected("you are already on an expedition")

        destination, habitat, charted, rejection = self._destination(ctx, character, command)
        if rejection is not None:
            return rejection

        members = _party_members(ctx.world, character, origin)
        for member in members:
            character.add_relationship(ExpeditionMember(), member.id)
        _relocate(ctx.world, character, destination)
        for member in members:
            _relocate(ctx.world, member, destination)
        replace_component(
            character,
            ExpeditionComponent(
                habitat=habitat,
                origin_room_id=str(origin.id),
                site_room_id=str(destination.id),
                progress=0,
                duration=EXPEDITION_DURATION,
            ),
        )
        return ok(
            ExpeditionStartedEvent(
                **ctx.event_base(
                    visibility=EventVisibility.ROOM,
                    actor_id=str(character_id),
                    room_id=str(origin.id),
                    target_ids=(str(destination.id),),
                    habitat=habitat,
                    site_room_id=str(destination.id),
                    members=len(members),
                    charted=charted,
                )
            )
        )

    def _destination(self, ctx: HandlerContext, character: Entity, command: SubmittedCommand):
        """Resolve where the expedition goes: a charted site, or a freshly opened one."""
        raw_site = command.payload.get("site_id")
        if raw_site is not None and str(raw_site).strip():
            parsed = parse_entity_id(raw_site)
            if parsed is None:
                return None, "", False, rejected("invalid site id")
            biome = charted_biome(ctx.world, character, str(parsed))
            if biome is None:
                return None, "", False, rejected("that site is not on your field map")
            if not ctx.world.has_entity(parsed):
                return None, "", False, rejected("that site no longer exists")
            return ctx.entity(parsed), biome, True, None
        habitat = str(command.payload.get("habitat") or "wild").strip() or "wild"
        site = spawn_entity(
            ctx.world,
            [RoomComponent(title=f"{habitat} field site")],
        )
        return site, habitat, False, None


class ExpeditionConsequence:
    """Advance every underway expedition; resolve it into a discovery when its time is up."""

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        leaders = sorted(
            world.query().with_all([ExpeditionComponent]).execute_entities(),
            key=lambda entity: str(entity.id),
        )
        events: list[DomainEvent] = []
        for leader in leaders:
            events.extend(self._advance(world, epoch, leader))
        return events

    def _advance(self, world: World, epoch: int, leader: Entity) -> list[DomainEvent]:
        expedition = leader.get_component(ExpeditionComponent)
        progress = expedition.progress + 1
        if progress < expedition.duration:
            replace_component(leader, replace(expedition, progress=progress))
            return []
        return self._resolve(world, epoch, leader, expedition)

    def _resolve(
        self, world: World, epoch: int, leader: Entity, expedition: ExpeditionComponent
    ) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        site = world.get_entity(parse_entity_id(expedition.site_room_id))
        species = species_for_site(expedition.habitat, expedition.site_room_id)
        subject = self._spawn_subject(world, species, expedition, site)
        discovery = record_sighting(
            world,
            leader,
            species=species,
            habitat=expedition.habitat,
            rarity="uncommon",
            epoch=epoch,
            room_id=expedition.site_room_id,
        )
        self._spawn_sketch(world, species, expedition, leader)
        events.append(
            SpeciesDiscoveredEvent(
                **event_base(
                    epoch,
                    default_visibility=EventVisibility.PRIVATE,
                    actor_id=str(leader.id),
                    room_id=expedition.site_room_id,
                    target_ids=(str(subject.id),),
                    subject_id=str(subject.id),
                    species=species,
                    habitat=expedition.habitat,
                    first_in_world=discovery,
                )
            )
        )
        events.extend(self._return_home(world, epoch, leader, expedition, species))
        return events

    def _spawn_subject(
        self, world: World, species: str, expedition: ExpeditionComponent, site: Entity
    ) -> Entity:
        components: list[Component] = [
            IdentityComponent(name=species, kind="creature", tags=("loresim",)),
            SpeciesComponent(species=species, habitat=expedition.habitat, rarity="uncommon"),
        ]
        if _is_wary(species, expedition.site_room_id):
            components.append(StealthComponent(visibility_level=1.0, hiding=False))
        subject = spawn_entity(world, components)
        site.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), subject.id)
        return subject

    def _spawn_sketch(
        self, world: World, species: str, expedition: ExpeditionComponent, leader: Entity
    ) -> Entity:
        """A field sketch of the subject — a museum-donatable :class:`Collectible`."""
        sketch = spawn_entity(
            world,
            [
                IdentityComponent(name=f"field sketch of {species}", kind="document"),
                Collectible(
                    kind="specimen",
                    title=f"field sketch of {species}",
                    category="natural-history",
                    quality="uncommon",
                ),
            ],
        )
        leader.add_relationship(Contains(mode=ContainmentMode.INVENTORY), sketch.id)
        return sketch

    def _return_home(
        self,
        world: World,
        epoch: int,
        leader: Entity,
        expedition: ExpeditionComponent,
        species: str,
    ) -> list[DomainEvent]:
        origin_id = parse_entity_id(expedition.origin_room_id)
        origin = world.get_entity(origin_id) if world.has_entity(origin_id) else None
        member_ids = [target for _edge, target in leader.get_relationships(ExpeditionMember)]
        if origin is not None:
            _relocate(world, leader, origin)
        for member_id in member_ids:
            if origin is not None and world.has_entity(member_id):
                _relocate(world, world.get_entity(member_id), origin)
            # A shared discovery warms co-explorers' affective bonds, both ways.
            if world.has_entity(member_id):
                adjust_bond(world, leader.id, member_id, _BOND_WARMTH)
                adjust_bond(world, member_id, leader.id, _BOND_WARMTH)
            leader.remove_relationship(ExpeditionMember, member_id)
        leader.remove_component(ExpeditionComponent)
        return [
            ExpeditionReturnedEvent(
                **event_base(
                    epoch,
                    default_visibility=EventVisibility.ROOM,
                    actor_id=str(leader.id),
                    room_id=expedition.origin_room_id or None,
                    habitat=expedition.habitat,
                    site_room_id=expedition.site_room_id,
                    discovered=(species,),
                )
            )
        ]


def expedition_fragments(world: World, character: Entity) -> list[str]:
    """Surface an in-progress expedition in the naturalist's prompt."""
    if character is None or not character.has_component(ExpeditionComponent):
        return []
    expedition = character.get_component(ExpeditionComponent)
    return [
        f"You are on an expedition to the {expedition.habitat} "
        f"({expedition.progress}/{expedition.duration})."
    ]


EMBARK_DEF = ActionDefinition(
    command_type="embark",
    title="Embark",
    description="Set out on an expedition to survey a habitat and record what you find.",
    lane=Lane.WORLD,
    cost=CommandCost(action=1),
    arguments={
        "habitat": ActionArgument(
            title="Habitat",
            description="The habitat to survey (wetland, woodland, grassland, shore, or wild).",
            kind="text",
            required=False,
        ),
        "site_id": ActionArgument(
            title="Charted site",
            description="Optional: a room already charted on your field map to expedition to.",
            kind="entity",
            required=False,
        ),
    },
)

EXPEDITION_ACTION_DEFINITIONS = (EMBARK_DEF,)
EXPEDITION_ACTION_HANDLERS = (EmbarkHandler,)


__all__ = [
    "EMBARK_DEF",
    "EXPEDITION_ACTION_DEFINITIONS",
    "EXPEDITION_ACTION_HANDLERS",
    "EXPEDITION_DURATION",
    "HABITAT_SPECIES",
    "EmbarkHandler",
    "ExpeditionComponent",
    "ExpeditionConsequence",
    "ExpeditionMember",
    "expedition_fragments",
    "record_sighting",
    "species_for_site",
]
