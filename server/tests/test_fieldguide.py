from __future__ import annotations

from bunnyland.core import RoomComponent, WorldActor, spawn_entity
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.ecs import replace_component
from bunnyland.core.handlers import HandlerContext

from bunnyland_loresim import (
    AuthoredBy,
    Collectible,
    FieldGuideComponent,
    KnownSpeciesComponent,
    LoreJournalComponent,
    PublishFieldGuideHandler,
    author_editions,
    authored_guides,
    fieldguide_fragments,
    masters_species,
    spawn_naturalist,
)
from bunnyland_loresim.components import SpeciesRecord
from bunnyland_loresim.fieldguide import PUBLISH_DEF


def _journal(records):
    return LoreJournalComponent(records=tuple(records))


def _rec(species, habitat="wetland", sightings=2):
    return SpeciesRecord(
        species=species, habitat=habitat, rarity="uncommon",
        first_seen_epoch=1, first_seen_room="r1", sightings=sightings,
    )


def _scene(records=None):
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Study")])
    author = spawn_naturalist(actor.world, name="Rue", room_id=room.id)
    if records is not None:
        replace_component(author, _journal(records))
    return actor, author


def _publish(actor, author_id, habitat):
    ctx = HandlerContext(world=actor.world, epoch=9)
    cmd = build_submitted_command(
        character_id=str(author_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="publish-field-guide",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"habitat": habitat},
    )
    return PublishFieldGuideHandler().execute(ctx, cmd)


def test_publish_happy_path_masters_species_and_makes_collectible():
    actor, author = _scene([_rec("bittern"), _rec("spoonbill")])
    result = _publish(actor, author.id, "wetland")

    assert result.ok
    event = result.events[0]
    assert event.habitat == "wetland"
    assert event.edition == 1
    assert set(event.species) == {"bittern", "spoonbill"}

    guides = authored_guides(actor.world, author)
    assert len(guides) == 1
    guide = guides[0]
    assert guide.has_relationship(AuthoredBy, author.id)
    component = guide.get_component(FieldGuideComponent)
    assert component.habitat == "wetland"
    assert len(component.notes) == 2
    collectible = guide.get_component(Collectible)
    assert collectible.kind == "field-guide"
    assert collectible.category == "field-guides"

    # Both species promoted to mastered on the open surface.
    known = author.get_component(KnownSpeciesComponent)
    assert set(known.mastered) == {"bittern", "spoonbill"}
    assert set(known.species) >= {"bittern", "spoonbill"}
    assert masters_species(actor.world, author, "bittern")


def test_publish_rich_quality_when_four_species():
    records = [_rec(s) for s in ("a", "b", "c", "d")]
    actor, author = _scene(records)
    result = _publish(actor, author.id, "wetland")
    assert result.ok
    guide = authored_guides(actor.world, author)[0]
    assert guide.get_component(Collectible).quality == "rich"


def test_publish_second_edition_increments():
    actor, author = _scene([_rec("bittern"), _rec("spoonbill")])
    _publish(actor, author.id, "wetland")
    result = _publish(actor, author.id, "wetland")
    assert result.ok
    assert result.events[0].edition == 2
    assert author_editions(actor.world, author.id, "wetland") == 2
    # A different habitat starts back at edition 1.
    replace_component(
        author,
        _journal([_rec("bittern"), _rec("spoonbill"), _rec("corncrake", habitat="grassland"),
                  _rec("harvest mouse", habitat="grassland")]),
    )
    other = _publish(actor, author.id, "grassland")
    assert other.events[0].edition == 1


# ---- rejection paths ----------------------------------------------------------------


def test_publish_rejects_missing_habitat():
    actor, author = _scene([_rec("bittern"), _rec("spoonbill")])
    result = _publish(actor, author.id, "")
    assert not result.ok
    assert result.reason == "name the habitat to write up"


def test_publish_rejects_no_journal():
    actor, author = _scene()
    author.remove_component(LoreJournalComponent)
    result = _publish(actor, author.id, "wetland")
    assert not result.ok
    assert result.reason == "you have nothing recorded to publish"


def test_publish_rejects_too_few_studied_species():
    # Only one well-studied species (the other seen once) -> under the minimum.
    actor, author = _scene([_rec("bittern", sightings=2), _rec("spoonbill", sightings=1)])
    result = _publish(actor, author.id, "wetland")
    assert not result.ok
    assert result.reason == "you must study more species of that habitat before publishing"


def test_publish_rejects_invalid_character():
    actor, _author = _scene([_rec("bittern"), _rec("spoonbill")])
    result = _publish(actor, "???", "wetland")
    assert not result.ok
    assert result.reason == "invalid character id"


# ---- fragments & helpers ------------------------------------------------------------


def test_fieldguide_fragment_lists_published_guides():
    actor, author = _scene([_rec("bittern"), _rec("spoonbill")])
    assert fieldguide_fragments(actor.world, author) == []
    _publish(actor, author.id, "wetland")
    frags = fieldguide_fragments(actor.world, author)
    assert frags and "field guide to the wetland" in frags[0]
    assert fieldguide_fragments(actor.world, None) == []


def test_author_editions_ignores_other_authors_and_habitats():
    actor, author = _scene([_rec("bittern"), _rec("spoonbill")])
    _publish(actor, author.id, "wetland")
    stranger = spawn_naturalist(actor.world, name="Stranger")
    assert author_editions(actor.world, stranger.id, "wetland") == 0
    assert author_editions(actor.world, author.id, "shore") == 0


def test_publish_definition_shape():
    assert PUBLISH_DEF.command_type == "publish-field-guide"
    assert PUBLISH_DEF.lane == Lane.WORLD
    assert PUBLISH_DEF.arguments["habitat"].required is True
