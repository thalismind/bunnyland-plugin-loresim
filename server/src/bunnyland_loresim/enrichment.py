"""World-generation enrichment: tag generated wildlife and flora as observable species.

Generated entities expose semantic ``tags``/``wants``/``needs`` and an intent
``description``. This hook scans that text for *living* things — creatures and plants — and
attaches a :class:`~bunnyland_loresim.components.SpeciesComponent` so a naturalist has
something to record in generated worlds, without the core generator knowing this plugin
exists. Plain items, tools, and furniture are never tagged.

Habitat and rarity are derived from the same text so the resulting bestiary entries are
meaningful. Nothing here reads or writes any sound/hearing state — observation is a matter
of *sight and patience*, not noise.
"""

from __future__ import annotations

from bunnyland.core import IdentityComponent
from bunnyland.core.generation import GenerationDelta, GenerationRequest

from .components import SpeciesComponent

#: Specific living subjects mapped to their habitat, checked before the generic terms.
HABITAT_BY_TERM: dict[str, str] = {
    "heron": "wetland",
    "frog": "wetland",
    "newt": "wetland",
    "dragonfly": "wetland",
    "reed": "wetland",
    "marsh": "wetland",
    "fox": "woodland",
    "deer": "woodland",
    "owl": "woodland",
    "beetle": "woodland",
    "fern": "woodland",
    "toadstool": "woodland",
    "forest": "woodland",
    "hare": "grassland",
    "lark": "grassland",
    "grasshopper": "grassland",
    "poppy": "grassland",
    "meadow": "grassland",
    "crab": "shore",
    "gull": "shore",
    "kelp": "shore",
    "tide": "shore",
    "beach": "shore",
}

#: Generic words that mark a generated entity as a living creature or plant.
LIVING_TERMS: tuple[str, ...] = (
    "creature",
    "animal",
    "beast",
    "critter",
    "wildlife",
    "fauna",
    "bird",
    "fish",
    "insect",
    "amphibian",
    "reptile",
    "mammal",
    "plant",
    "flora",
    "flower",
    "herb",
    "fungus",
    "moss",
    "tree",
    *HABITAT_BY_TERM.keys(),
)

#: Words that raise a subject's rarity above ``common``.
UNCOMMON_TERMS = ("shy", "elusive", "uncommon", "seldom", "wary")
RARE_TERMS = ("rare", "legendary", "fabled", "vanishing", "endangered", "mythic")


def _text(request: GenerationRequest) -> str:
    return " ".join(
        (
            request.source_key,
            request.entity_kind,
            request.description,
            *request.tags,
            *request.capabilities,
        )
    ).casefold()


def _matched_living_term(text: str) -> str | None:
    for term in LIVING_TERMS:
        if term in text:
            return term
    return None


def _habitat_for(text: str) -> str:
    for term, habitat in HABITAT_BY_TERM.items():
        if term in text:
            return habitat
    return "wild"


def _rarity_for(text: str) -> str:
    if any(term in text for term in RARE_TERMS):
        return "rare"
    if any(term in text for term in UNCOMMON_TERMS):
        return "uncommon"
    return "common"


def _species_name(request: GenerationRequest, matched: str) -> str:
    identity = next(
        (
            component
            for component in request.context.get("base_components", ())
            if isinstance(component, IdentityComponent)
        ),
        None,
    )
    if identity is not None and identity.name.strip():
        return identity.name.strip().casefold()
    if request.source_key:
        return request.source_key.casefold()
    return matched


class LoreGenerationEnricher:
    """Attach a :class:`SpeciesComponent` to generated living creatures and plants."""

    capabilities: tuple[str, ...] = ()

    def enrich(self, request: GenerationRequest) -> GenerationDelta:
        if request.entity_kind == "room":
            return GenerationDelta()
        text = _text(request)
        matched = _matched_living_term(text)
        if matched is None:
            return GenerationDelta()
        return GenerationDelta(
            components=(
                SpeciesComponent(
                    species=_species_name(request, matched),
                    habitat=_habitat_for(text),
                    rarity=_rarity_for(text),
                ),
            )
        )


__all__ = [
    "HABITAT_BY_TERM",
    "LIVING_TERMS",
    "RARE_TERMS",
    "UNCOMMON_TERMS",
    "LoreGenerationEnricher",
]
