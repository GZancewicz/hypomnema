# Synaxarion graphify plan

Plan for building a knowledge graph over `synaxarion/calendar/`. Written 2026-08-08.

## Corpus

Measured, not estimated:

| Metric | Value |
|---|---|
| Day folders | 366 (all populated) |
| `commemorations.json` files | 366 |
| Commemorations (saint lives) | 2,513 — 2,504 with text, 9 empty |
| Total JSON | 6.2 MB |
| Per-file size | mean 17 KB, median 15 KB, p90 30 KB, max 58 KB |
| Per-life text | mean 2.1 KB, median 1.2 KB, max 42 KB |
| Icons (`.jpg`) | 897, spread across 337 day folders |
| Total files under `calendar/` | 1,263 |

Record shape — every commemoration has `url`, `title`, `commemorated_on`, `text`,
`source_note`, `image_url`; 900 also have `image_file`.

Both `graphify-out/` directories currently hold only `cache/stat-index.json`. There is
no `graph.json`, so this is a cold build, not an `--update`.

## Cost

~6.2 MB of English prose is **~1.7M input tokens**. Semantic extraction chunks at 20–25
files per subagent, so 366 files → **17 general-purpose agents**, each reading ~370 KB
(~100k tokens) plus the extraction spec, each emitting a sizeable node/edge JSON.

| Scenario | Tokens | Notes |
|---|---|---|
| JSON only, default mode | ~2.0–2.5M (~1.7M in, ~300–500k out) | The recommended run |
| JSON only, `--mode deep` | ~3–4M | Roughly doubles output; more INFERRED edges |
| Including the 897 icons | +5–10M | Each image gets its own vision chunk. Avoid. |
| One month pilot | ~150k | 31 files |

For context: 2–2.5M is a few hours of ordinary agent work on a large codebase. It is a
one-time build cost — queries against the resulting `graph.json` are cheap forever after.

## Two things that will bite

**1. The 500-file gate.** Step 2 of the skill warns and *stops to ask* when
`total_files > 500`. `calendar/` has 1,263 files, so a bare invocation will halt and ask
you to narrow before any extraction happens. Expect the prompt; it is not an error.

**2. The icons are the real expense.** The spec gives every image its own chunk. 897
vision agents over saint icons would cost several times the entire text pass and produce
almost no useful edges — icons of saints yield "this is an icon of a bearded man holding
a scroll," which adds nothing the `title` field does not already carry. Exclude them.

## Recommended sequence

### Phase 1 — one-month pilot (~150k tokens)

```
/graphify synaxarion/calendar/09-September --no-viz
```

September is a good probe: 30 days, 90 icons, and it contains the Zacharias/Elizabeth
material already cross-referenced into the reader, so there is a known-good edge to look
for.

Then read `graphify-out/GRAPH_REPORT.md` and judge against the decision criteria below
before spending the full amount.

### Phase 2 — full build, JSON only

Only if the pilot earns it:

```
/graphify synaxarion/calendar --no-viz
```

Answer the narrowing prompt by directing it at the JSON, and keep the icons out. If the
skill will not filter by extension from the invocation, stage a clean input tree first:

```bash
mkdir -p /tmp/synaxarion-text
cd synaxarion/calendar
for f in */*/commemorations.json; do
  d=$(dirname "$f")
  mkdir -p "/tmp/synaxarion-text/$d"
  cp "$f" "/tmp/synaxarion-text/$d/"
done
```

…then run graphify against `/tmp/synaxarion-text`. 366 files still trips the >500 gate?
No — 366 is under it, so staging also sidesteps the prompt entirely. This is the cleanest
path.

### Phase 3 — optional enrichment

- `--wiki` for an agent-crawlable article per community.
- `--neo4j` if the graph turns out to be worth querying in Cypher.
- Skip `--mode deep` unless Phase 1 showed the default mode was too sparse.

## Decision criteria after the pilot

The honest risk: **2,513 saint lives are largely independent documents.** Hagiography
cross-references scripture and the occasional shared emperor or persecution, but one
saint's Life rarely cites another's. Graphify's payoff comes from community detection over
genuinely linked material, so this corpus may yield mostly low-confidence `INFERRED`
thematic edges — "both were martyrs under Diocletian" — which is real but is also
something a grep could surface.

Proceed to the full build only if the September graph shows:

- A meaningful count of `EXTRACTED` edges, not overwhelmingly `INFERRED`.
- Communities that correspond to something you would actually want to navigate —
  persecution eras, monastic lineages, geographic sees, scripture-linked figures — rather
  than one giant "saints" blob.
- Cross-day connections you did not already know, since same-day grouping is already
  encoded by the folder structure and needs no graph.

If the pilot mostly produces thematic INFERRED edges, the better investment is targeted
structured extraction — emperor, date, place, martyrdom type, scripture citations — as
fields on the existing JSON, which the app can already read and which costs a fraction of
a full graph build.

## Interaction with existing project structure

- Metadata is authoritative per project ground rules. The graph is a derived artifact
  and must never become the source of truth for calendar data.
- `graphify-out/` and `synaxarion/graphify-out/` are currently untracked. Keep them
  untracked; the graph is rebuildable and does not belong in the deploy branch.
- The existing Synaxarion→verse citation mechanism (`add-synaxarion-reference` skill)
  stays the authoritative link between lives and scripture. If the graph surfaces good
  candidate verse links, feed them through that skill rather than writing them directly.
