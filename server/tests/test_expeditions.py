from __future__ import annotations

from bunnyland.core import (
    Contains,
    PerceptionComponent,
    RoomComponent,
    StealthComponent,
    WorldActor,
    container_of,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.ecs import contents, parse_entity_id, replace_component
from bunnyland.core.handlers import HandlerContext
from bunnyland.mechanics.social import bond_between

from bunnyland_loresim import (
    Collectible,
    ExpeditionComponent,
    ExpeditionConsequence,
    ExpeditionMember,
    KnownSpeciesComponent,
    LoreJournalComponent,
    SpeciesComponent,
    expedition_fragments,
    record_sighting,
    spawn_naturalist,
    species_for_site,
)
from bunnyland_loresim.components import SpeciesRecord
from bunnyland_loresim.expeditions import (
    EMBARK_DEF,
    HABITAT_SPECIES,
    EmbarkHandler,
    _is_wary,
)


def _scene(members=0, perceive=True):
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Base Camp")])
    leader = spawn_naturalist(actor.world, name="Rue", room_id=room.id)
    if not perceive:
        replace_component(leader, PerceptionComponent(active=False))
    companions = []
    for i in range(members):
        companions.append(spawn_naturalist(actor.world, name=f"C{i}", room_id=room.id))
    return actor, room, leader, companions


def _embark(actor, character_id, payload):
    ctx = HandlerContext(world=actor.world, epoch=5)
    cmd = build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="embark",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload=payload,
    )
    return EmbarkHandler().execute(ctx, cmd)


def test_embark_opens_fresh_site_and_sets_expedition():
    actor, room, leader, _ = _scene()
    result = _embark(actor, leader.id, {"habitat": "wetland"})

    assert result.ok
    event = result.events[0]
    assert event.habitat == "wetland"
    assert event.charted is False
    assert event.members == 0
    assert leader.has_component(ExpeditionComponent)
    expedition = leader.get_component(ExpeditionComponent)
    assert expedition.origin_room_id == str(room.id)
    # The leader physically travelled out of base camp into the field site.
    assert str(container_of(leader)) == expedition.site_room_id
    assert expedition.site_room_id != str(room.id)


def test_embark_default_habitat_is_wild():
    actor, _room, leader, _ = _scene()
    result = _embark(actor, leader.id, {})
    assert result.ok
    assert leader.get_component(ExpeditionComponent).habitat == "wild"


def test_embark_takes_party_members_as_typed_edges():
    actor, _room, leader, companions = _scene(members=2)
    result = _embark(actor, leader.id, {"habitat": "woodland"})
    assert result.ok
    assert result.events[0].members == 2
    member_ids = {target for _edge, target in leader.get_relationships(ExpeditionMember)}
    assert member_ids == {c.id for c in companions}
    # Everyone relocated to the field site together.
    site_id = leader.get_component(ExpeditionComponent).site_room_id
    for companion in companions:
        assert str(container_of(companion)) == site_id


# ---- rejection paths ----------------------------------------------------------------


def test_embark_rejects_invalid_character():
    actor, _room, _leader, _ = _scene()
    result = _embark(actor, "???", {"habitat": "wetland"})
    assert not result.ok
    assert result.reason == "invalid character id"


def test_embark_rejects_when_cannot_perceive():
    actor, _room, leader, _ = _scene(perceive=False)
    result = _embark(actor, leader.id, {"habitat": "wetland"})
    assert not result.ok
    assert result.reason == "you cannot survey anything right now"


def test_embark_rejects_when_not_in_a_room():
    actor, room, leader, _ = _scene()
    room.remove_relationship(Contains, leader.id)
    result = _embark(actor, leader.id, {"habitat": "wetland"})
    assert not result.ok
    assert result.reason == "you must set out from a room"


def test_embark_rejects_when_already_on_expedition():
    actor, _room, leader, _ = _scene()
    _embark(actor, leader.id, {"habitat": "wetland"})
    result = _embark(actor, leader.id, {"habitat": "shore"})
    assert not result.ok
    assert result.reason == "you are already on an expedition"


def test_embark_rejects_invalid_site_id():
    actor, _room, leader, _ = _scene()
    result = _embark(actor, leader.id, {"site_id": "???"})
    assert not result.ok
    assert result.reason == "invalid site id"


def test_embark_rejects_uncharted_site_when_cartography_absent():
    actor, _room, leader, _ = _scene()
    other = spawn_entity(actor.world, [RoomComponent(title="Uncharted")])
    result = _embark(actor, leader.id, {"site_id": str(other.id)})
    assert not result.ok
    assert result.reason == "that site is not on your field map"


# ---- consequence resolution ---------------------------------------------------------


def test_expedition_consequence_advances_then_resolves():
    actor, room, leader, companions = _scene(members=1)
    _embark(actor, leader.id, {"habitat": "wetland"})
    consequence = ExpeditionConsequence()

    # First tick: progress advances, not yet resolved.
    events = consequence.process(actor.world, 10)
    assert events == []
    assert leader.get_component(ExpeditionComponent).progress == 1

    # Second tick: resolves with a discovery + return home.
    events = consequence.process(actor.world, 20)
    kinds = {type(e).__name__ for e in events}
    assert "SpeciesDiscoveredEvent" in kinds
    assert "ExpeditionReturnedEvent" in kinds

    # Expedition cleared, party home, bonds warmed, journal + knowledge updated, sketch held.
    assert not leader.has_component(ExpeditionComponent)
    assert str(container_of(leader)) == str(room.id)
    for companion in companions:
        assert str(container_of(companion)) == str(room.id)
        assert bond_between(actor.world, leader.id, companion.id) is not None
        assert bond_between(actor.world, companion.id, leader.id) is not None
    assert list(leader.get_relationships(ExpeditionMember)) == []

    journal = leader.get_component(LoreJournalComponent)
    assert len(journal.records) == 1
    species = journal.records[0].species
    assert species in leader.get_component(KnownSpeciesComponent).species

    sketches = [
        actor.world.get_entity(i)
        for i in contents(leader)
        if actor.world.get_entity(i).has_component(Collectible)
    ]
    assert len(sketches) == 1
    assert sketches[0].get_component(Collectible).kind == "specimen"


def test_expedition_resolve_home_missing_still_clears():
    actor, room, leader, _ = _scene()
    _embark(actor, leader.id, {"habitat": "wetland"})
    # Destroy the origin room before resolution: the party can't walk home but state clears.
    actor.world.remove(room.id)
    consequence = ExpeditionConsequence()
    consequence.process(actor.world, 10)
    consequence.process(actor.world, 20)
    assert not leader.has_component(ExpeditionComponent)


def test_expedition_wary_subject_gets_stealth():
    # Pick a habitat/site whose subject is wary so the StealthComponent branch runs.
    actor, _room, leader, _ = _scene()
    _embark(actor, leader.id, {"habitat": "wetland"})
    site_id = leader.get_component(ExpeditionComponent).site_room_id
    species = species_for_site("wetland", site_id)
    consequence = ExpeditionConsequence()
    consequence.process(actor.world, 10)
    consequence.process(actor.world, 20)
    site = actor.world.get_entity(parse_entity_id(site_id))
    subjects = [
        actor.world.get_entity(i)
        for i in contents(site)
        if actor.world.get_entity(i).has_component(SpeciesComponent)
    ]
    assert subjects
    wary = _is_wary(species, site_id)
    assert any(s.has_component(StealthComponent) for s in subjects) == wary


# ---- helpers ------------------------------------------------------------------------


def test_species_for_site_is_deterministic_and_in_pool():
    a = species_for_site("woodland", "room_42")
    b = species_for_site("woodland", "room_42")
    assert a == b
    assert a in HABITAT_SPECIES["woodland"]
    # Unknown habitat falls back to the "wild" pool.
    assert species_for_site("nowhere", "room_1") in HABITAT_SPECIES["wild"]


def test_record_sighting_increments_existing_record():
    actor, _room, leader, _ = _scene()
    first = record_sighting(
        actor.world, leader, species="bittern", habitat="wetland",
        rarity="uncommon", epoch=1, room_id="r1",
    )
    assert first is True  # first in world
    second = record_sighting(
        actor.world, leader, species="bittern", habitat="wetland",
        rarity="uncommon", epoch=2, room_id="r1",
    )
    assert second is False
    record = leader.get_component(LoreJournalComponent).record_for("bittern")
    assert record.sightings == 2


def test_record_sighting_creates_journal_when_absent():
    actor, _room, leader, _ = _scene()
    leader.remove_component(LoreJournalComponent)
    record_sighting(
        actor.world, leader, species="bittern", habitat="wetland",
        rarity="uncommon", epoch=1, room_id="r1",
    )
    assert leader.has_component(LoreJournalComponent)


def test_record_sighting_not_first_when_another_has_it():
    actor, _room, leader, _ = _scene()
    other = spawn_naturalist(actor.world, name="Other")
    replace_component(
        other,
        LoreJournalComponent(
            records=(
                SpeciesRecord(
                    species="bittern", habitat="wetland", rarity="uncommon",
                    first_seen_epoch=0, first_seen_room="x", sightings=1,
                ),
            )
        ),
    )
    first = record_sighting(
        actor.world, leader, species="bittern", habitat="wetland",
        rarity="uncommon", epoch=1, room_id="r1",
    )
    assert first is False


def test_expedition_fragment_reports_progress():
    actor, _room, leader, _ = _scene()
    assert expedition_fragments(actor.world, leader) == []
    _embark(actor, leader.id, {"habitat": "grassland"})
    frags = expedition_fragments(actor.world, leader)
    assert frags and "expedition to the grassland" in frags[0]
    assert expedition_fragments(actor.world, None) == []


def test_embark_definition_shape():
    assert EMBARK_DEF.command_type == "embark"
    assert EMBARK_DEF.lane == Lane.WORLD
    assert set(EMBARK_DEF.arguments) == {"habitat", "site_id"}
