"""Runtime wiring: register loresim's per-tick consequences on a world actor."""

from __future__ import annotations

from bunnyland.core.world_actor import WorldActor

from .expeditions import ExpeditionConsequence
from .migration import MigrationConsequence
from .settle import SettleConsequence


def install_loresim(actor: WorldActor) -> None:
    """Register loresim's consequences (a ``service_factories`` entry).

    - :class:`SettleConsequence` — spooked subjects settle back into view (v1).
    - :class:`ExpeditionConsequence` — advance and resolve expeditions (v2).
    - :class:`MigrationConsequence` — the paced rare-migration storyteller incident (v2).
    """
    actor.register_consequence(SettleConsequence())
    actor.register_consequence(ExpeditionConsequence())
    actor.register_consequence(MigrationConsequence())


__all__ = ["install_loresim"]
