"""Per-tick patience: a spooked subject slowly settles back into view.

When a wary subject is flushed into cover by a careless approach (see
:mod:`bunnyland_loresim.observe`), it is not gone for good — it just needs the naturalist to
*wait*. Each tick this consequence nudges every hiding :class:`StealthComponent` subject's
``visibility_level`` back up; once it rises above the subject's ``hidden_threshold`` the
subject stops hiding and can be observed again. This is the patience half of the pack's
sight-and-patience tension, and it is deterministic (a fixed step per tick, no randomness or
wall-clock time). It reads and writes only stealth/visibility state — never any sound state.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core import StealthComponent
from bunnyland.core.ecs import replace_component
from bunnyland.core.events import DomainEvent
from relics import World

#: How much a hiding subject's visibility recovers per tick.
SETTLE_STEP = 0.25


class SettleConsequence:
    """Let spooked subjects settle back into view over time."""

    def __init__(self, *, settle_step: float = SETTLE_STEP):
        self.settle_step = settle_step

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        for subject in list(world.query().with_all([StealthComponent]).execute_entities()):
            stealth = subject.get_component(StealthComponent)
            if not stealth.hiding:
                continue
            new_level = min(1.0, stealth.visibility_level + self.settle_step)
            hiding = new_level <= stealth.hidden_threshold
            if new_level == stealth.visibility_level and hiding == stealth.hiding:
                continue
            replace_component(
                subject, replace(stealth, visibility_level=new_level, hiding=hiding)
            )
        return []


__all__ = ["SETTLE_STEP", "SettleConsequence"]
