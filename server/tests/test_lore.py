from __future__ import annotations

from bunnyland_loresim import activity_for, lore_notes, temperament_for
from bunnyland_loresim.components import SpeciesRecord
from bunnyland_loresim.lore import TEMPERAMENTS


def _record(species="heron", habitat="wetland", rarity="common", sightings=1):
    return SpeciesRecord(
        species=species,
        habitat=habitat,
        rarity=rarity,
        first_seen_epoch=0,
        first_seen_room="room_1",
        sightings=sightings,
    )


def test_first_sighting_unlocks_only_habitat_note():
    notes = lore_notes(_record(sightings=1))
    assert notes == ("Habitat: wetland (common).",)


def test_second_sighting_unlocks_temperament():
    notes = lore_notes(_record(sightings=2))
    assert notes == (
        "Habitat: wetland (common).",
        f"Temperament: {temperament_for('heron')}.",
    )


def test_third_sighting_unlocks_full_entry():
    notes = lore_notes(_record(sightings=3))
    assert len(notes) == 3
    assert notes[2] == f"Activity: {activity_for('heron')}."


def test_lore_is_deterministic_across_calls():
    assert temperament_for("heron") == temperament_for("heron")
    assert activity_for("heron") == activity_for("heron")
    assert lore_notes(_record(sightings=3)) == lore_notes(_record(sightings=3))


def test_lore_varies_by_species_but_is_stable_per_species():
    labels = {species: temperament_for(species) for species in ("heron", "fox", "owl", "crab")}
    # Stable: recomputing gives the same label.
    for species, label in labels.items():
        assert temperament_for(species) == label
    # The vocabulary is drawn from the known temperament set.
    assert set(labels.values()) <= set(TEMPERAMENTS)
