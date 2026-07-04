"""Runtime wiring: register the per-tick settle consequence on a world actor."""

from __future__ import annotations

from bunnyland.core.world_actor import WorldActor

from .settle import SettleConsequence


def install_loresim(actor: WorldActor) -> None:
    """Register the settle consequence (a ``service_factories`` entry)."""
    actor.register_consequence(SettleConsequence())


__all__ = ["install_loresim"]
