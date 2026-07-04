# Bunnyland Loresim

Out-of-tree [Bunnyland](https://github.com/thalismind/bunnyland-server) plugin that adds a
pacifist **field-naturalist** loop: you watch **living** creatures and plants and record them
into a personal **bestiary of knowledge**. You never capture, tame, or harm a subject, and
nothing ever changes hands — the payoff is *knowledge*, and that knowledge sharpens the
naturalist and can be consulted by other packs.

The only tension is **sight and patience**, never sound:

- A subject must be **visible** — in line of sight, not hidden in cover.
- A **wary** subject flushes into cover if you crowd it without a **spyglass**.
- A spooked subject slowly **settles** back into view if you wait.

Loresim is deliberately distinct from its neighbours:

- **petsim** tames and *keeps* creatures — Loresim only ever *observes* them.
- **anglersim** *extracts* and logs catches — Loresim logs *living* sightings; the subject
  stays right where it is.
- **museumsim** *donates* physical objects — Loresim records *knowledge*; no item moves.

## What it contributes

- **Observable species** — `SpeciesComponent(species, habitat, rarity)` on living creatures
  and plants, attached by `LoreWorldgenHook` from generation tags/description.
- **The `observe` verb** — records a visible subject into the observer's
  `LoreJournalComponent` (the bestiary), capturing first-seen time and place. Requires line of
  sight; a wary subject spooks and flees unless you carry a `SpyglassComponent`.
- **Deterministic lore notes** — repeated observations unlock habitat/temperament/activity
  notes assembled with `hashlib` over the recorded species (no `random`, no clock).
- **Lore payoff** — every recorded species is marked "known" on an open
  `KnownSpeciesComponent`, and `knows_species(world, character, species)` lets *any* other
  pack read it without depending on Loresim. Surfaced in `knowledge_fragments`.
- **Completion & discovery** — the first naturalist in the world to record a species earns a
  discovery credit; the journal is tallied by habitat; `journal_fragments` reports the total
  and nudges toward an unrecorded subject in the room ("a heron here is unrecorded").
- **Patience** — `SettleConsequence` lets spooked subjects settle back into view over ticks.

This repo intentionally keeps all field-naturalist work outside the main `bunnyland-server`
repo. It never imports or touches the sound/hearing systems.

## Layout

- `server/` - Python Bunnyland plugin package with the species/journal components, the
  `observe` verb, deterministic lore notes, the known-species payoff surface, discovery and
  completion tracking, prompt fragments, a worldgen enrichment hook, the settle consequence,
  spawn factories, and tests.

## Server Plugin

The plugin exposes `bunnyland_loresim.bunnyland_plugins()`. `default_enabled=True`, so once
the module is imported no `--plugin` flag is required. Load it with:

```bash
bunnyland serve --module bunnyland_loresim
```
