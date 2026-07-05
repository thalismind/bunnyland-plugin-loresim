from __future__ import annotations

from bunnyland.core import RoomComponent, WorldActor, spawn_entity
from bunnyland.core.ecs import replace_component

from bunnyland_loresim import (
    KnownSpeciesComponent,
    LoreJournalComponent,
    knowledge_fragments,
    knows_species,
    mark_known,
    mark_mastered,
    masters_species,
    spawn_naturalist,
)


def _naturalist():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Blind")])
    naturalist = spawn_naturalist(actor.world, room_id=room.id)
    return actor, naturalist


def test_mark_mastered_creates_and_implies_known():
    actor, naturalist = _naturalist()
    assert not naturalist.has_component(KnownSpeciesComponent)
    mark_mastered(naturalist, "heron")
    known = naturalist.get_component(KnownSpeciesComponent)
    assert known.mastered == ("heron",)
    assert known.species == ("heron",)
    assert masters_species(actor.world, naturalist, "heron") is True


def test_mark_mastered_promotes_already_known_species():
    actor, naturalist = _naturalist()
    mark_known(naturalist, "heron")
    mark_known(naturalist, "fox")
    mark_mastered(naturalist, "heron")
    known = naturalist.get_component(KnownSpeciesComponent)
    assert known.mastered == ("heron",)
    assert set(known.species) == {"fox", "heron"}


def test_mark_mastered_is_idempotent():
    actor, naturalist = _naturalist()
    mark_mastered(naturalist, "heron")
    mark_mastered(naturalist, "heron")
    assert naturalist.get_component(KnownSpeciesComponent).mastered == ("heron",)


def test_masters_species_false_without_component():
    actor, naturalist = _naturalist()
    assert masters_species(actor.world, naturalist, "heron") is False


def test_masters_species_false_when_only_known():
    actor, naturalist = _naturalist()
    mark_known(naturalist, "heron")
    assert masters_species(actor.world, naturalist, "heron") is False


def test_mark_known_preserves_mastered_subset():
    actor, naturalist = _naturalist()
    mark_mastered(naturalist, "heron")
    mark_known(naturalist, "fox")
    known = naturalist.get_component(KnownSpeciesComponent)
    assert known.mastered == ("heron",)
    assert set(known.species) == {"fox", "heron"}


def test_knowledge_fragments_empty_states():
    actor, naturalist = _naturalist()
    assert knowledge_fragments(actor.world, None) == []
    # Has a component but no species recorded yet.
    replace_component(naturalist, KnownSpeciesComponent())
    assert knowledge_fragments(actor.world, naturalist) == []


def test_knowledge_fragments_known_only():
    actor, naturalist = _naturalist()
    mark_known(naturalist, "heron")
    frags = knowledge_fragments(actor.world, naturalist)
    assert len(frags) == 1
    assert "field knowledge of 1 species" in frags[0]


def test_knowledge_fragments_includes_mastered_line():
    actor, naturalist = _naturalist()
    mark_known(naturalist, "fox")
    mark_mastered(naturalist, "heron")
    frags = knowledge_fragments(actor.world, naturalist)
    assert len(frags) == 2
    assert "mastered 1 species: heron" in frags[1]


def test_knows_species_true_via_component():
    actor, naturalist = _naturalist()
    mark_known(naturalist, "heron")
    assert knows_species(actor.world, naturalist, "heron") is True


def test_knows_species_component_present_species_absent_no_journal():
    actor, naturalist = _naturalist()
    naturalist.remove_component(LoreJournalComponent)
    replace_component(naturalist, KnownSpeciesComponent(species=("fox",)))
    # Known component present but lacks the species, and there is no journal to fall back on.
    assert knows_species(actor.world, naturalist, "heron") is False


def test_knows_species_falls_back_to_journal_when_not_in_component():
    actor, naturalist = _naturalist()
    from bunnyland_loresim.components import SpeciesRecord

    replace_component(naturalist, KnownSpeciesComponent(species=("fox",)))
    replace_component(
        naturalist,
        LoreJournalComponent(
            records=(
                SpeciesRecord(
                    species="heron", habitat="wetland", rarity="common",
                    first_seen_epoch=0, first_seen_room="x",
                ),
            )
        ),
    )
    # Not in the KnownSpecies component, but recorded in the journal -> still known.
    assert knows_species(actor.world, naturalist, "heron") is True
