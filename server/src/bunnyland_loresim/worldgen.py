"""World-generation enrichment (v2): seed generated field naturalists for expeditions.

v1's :class:`~bunnyland_loresim.enrichment.LoreGenerationEnricher` seeds *subjects* (tagging
generated wildlife and flora as recordable species). This v2 hook seeds the other half — the
*naturalists* who record them — so a generated world is expedition-ready without the core
generator knowing this pack exists.

When the generator produces a character that reads as a field naturalist (a ranger, botanist,
zoologist, warden…), this hook gives them the field **journal** (the same memory store the
``observe`` verb and expeditions write to) and seeds a little starting field knowledge for
their local habitat on the open :class:`~bunnyland_loresim.knowledge.KnownSpeciesComponent`
surface. Habitat and seeded species are derived deterministically from the generation text —
no ``random`` or clock, and nothing about sound or hearing.
"""

from __future__ import annotations

from bunnyland.core.generation import GenerationDelta, GenerationRequest

from .components import LoreJournalComponent
from .expeditions import HABITAT_SPECIES
from .knowledge import KnownSpeciesComponent

#: Words that mark a generated character as a field naturalist worth equipping.
NATURALIST_TERMS: tuple[str, ...] = (
    "naturalist",
    "ranger",
    "botanist",
    "zoologist",
    "ecologist",
    "warden",
    "field scientist",
    "lorekeeper",
)


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


def _is_naturalist(text: str) -> bool:
    return any(term in text for term in NATURALIST_TERMS)


def _habitat_for(text: str) -> str:
    for habitat in HABITAT_SPECIES:
        if habitat in text:
            return habitat
    return "wild"


class NaturalistGenerationEnricher:
    """Equip generated field naturalists with a journal and starting field knowledge."""

    capabilities: tuple[str, ...] = ()

    def enrich(self, request: GenerationRequest) -> GenerationDelta:
        text = _text(request)
        if request.entity_kind != "character" or not _is_naturalist(text):
            return GenerationDelta()
        habitat = _habitat_for(text)
        return GenerationDelta(
            components=(
                LoreJournalComponent(),
                KnownSpeciesComponent(species=(HABITAT_SPECIES[habitat][0],)),
            )
        )


__all__ = ["NATURALIST_TERMS", "NaturalistGenerationEnricher"]
