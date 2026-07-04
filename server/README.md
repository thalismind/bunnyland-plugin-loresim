# bunnyland-loresim (server plugin)

The out-of-tree Bunnyland plugin package `bunnyland_loresim` — a pacifist field-naturalist
pack that records **living** creatures and plants into a bestiary of knowledge.

## Development

Tests run against a sibling `bunnyland-server` checkout without installing anything —
`tests/conftest.py` puts both this package's `src/` and `../bunnyland-server/src` on
`sys.path`. From this `server/` directory:

```bash
# uses the sibling bunnyland-server's virtualenv/deps
uv run --project ../../bunnyland-server -m pytest
# or, if bunnyland + relics are already importable:
python -m pytest
```

Lint:

```bash
uv run --project ../../bunnyland-server ruff check src tests
```

## Loading into the server

```bash
bunnyland serve --module bunnyland_loresim
```

`default_enabled=True`, so no `--plugin` flag is required once the module is imported.

## What it contributes

- **Components** — `SpeciesComponent` (observable creatures/plants), `LoreJournalComponent`
  (the per-character bestiary of knowledge), `KnownSpeciesComponent` (the open lore-payoff
  registry), and `SpyglassComponent` (the patience aid).
- **The `observe` verb** — records a *visible* living subject into the observer's journal,
  capturing first-seen time/place. Validation order: invalid id -> missing entity ->
  not reachable / not visible -> wrong kind -> (wary subject spooks) -> record. A held
  `SpyglassComponent` lets you record wary subjects safely; without it they flee into cover.
  Re-observing a recorded species increments its sightings and deepens its lore notes.
- **Deterministic lore notes** — `lore_notes(record)` unlocks habitat/temperament/activity
  notes assembled with `hashlib` over the recorded species; `temperament_for`/`activity_for`
  are stable per species with no randomness or clock use.
- **Lore payoff** — recording marks the species "known" via `mark_known`; `knows_species`
  reads the open `KnownSpeciesComponent` (falling back to the journal), so other packs can
  branch on a naturalist's knowledge without importing Loresim internals.
- **Completion & discovery** — `is_first_in_world` grants a discovery credit to the first
  recorder of a species; `completion_by_habitat` tallies the journal; `journal_fragments`
  reports the total, discoveries, per-habitat completion, and any unrecorded subject in view.
- **A worldgen hook** — `LoreWorldgenHook` tags generated wildlife/flora with a
  `SpeciesComponent` (deriving habitat and rarity from the generation text).
- **A settle consequence** — `SettleConsequence` recovers a spooked subject's visibility each
  tick so patience lets it be observed again.
- **Spawn factories** — `spawn_subject`, `spawn_naturalist`, `spawn_spyglass`.

Nothing in this package imports or touches the sound/hearing systems (`NoiseComponent`,
`HearingComponent`, `StimulusComponent`); the "don't spook it" tension is purely visibility
and patience based (`PerceptionComponent` + `StealthComponent`).
