---
name: ccel-homily-coverage
description: Determine the true verse range each Chrysostom homily covers by READING each homily against the actual biblical text, then reset its coverage range. Use for CCEL commentaries (Chrysostom on Matthew, John, etc.) when verse-coverage / shading must reflect what each homily actually expounds, not a lemma-to-next-lemma assumption.
---

# CCEL Homily Coverage

Chrysostom's homilies are titled on an opening **lemma** (e.g. "Matthew 1:17"),
but the source never states where each homily's exposition **ends**. Assuming a
homily covers everything up to the next homily's lemma is wrong — sometimes the
exposition stops earlier (a real gap), sometimes it runs right to the next lemma.

**The ending verse cannot be found by a script.** It requires reading each
homily and comparing its exposition against the actual biblical text to see which
verses it genuinely treats. Do NOT use scripRef counting, "furthest citation," or
any other heuristic to decide the end — those undershoot on passages expounded in
prose and overshoot on cross-references. An LLM must read every homily, one by
one, against the Bible.

## When to use
- After a commentary's `coverage.json` exists with correct `id`, `roman`, and
  `start` (lemma), to set each homily's true `end`.
- Whenever shading / verse coverage must be accurate.

## Inputs (per commentary directory, e.g. `texts/commentaries/chrysostom/matthew`)
- `coverage.json` — entries with correct `id`, `roman`, `start` (the lemma; never changed here).
- `content/<NNN>/content.json` — the homily body text.
- The repo's KJV text under `texts/scripture/**/kjv/<book>/` (located automatically).

## Procedure

### 1. Build bundles (plumbing only — makes no judgement)
```
python scripts/build_bundles.py <commentary_dir> <work_dir>
```
Writes `<work_dir>/bundles/<NNN>.txt` (each = the full commentary text + the KJV
verses of the passage) and `<work_dir>/manifest.json`.

### 2. Read every homily against the Bible (LLM, one by one)
Fan out subagents; split `manifest.json` into small batches (≈6–9 each). Give each
agent its batch and have it, for every homily:
1. Read the bundle file (commentary text + KJV verses).
2. Walk the homily's running, sequential exposition from the lemma forward.
3. By comparing what the commentary discusses against the KJV verses, determine
   the **last verse the homily actually expounds** as part of this passage.

Judgement rules the agents must apply:
- `start` is authoritative; determine only the `end`.
- The end is the highest verse whose content the homily genuinely treats in its
  running exposition of THIS passage.
- EXCLUDE cross-references cited to illustrate a point, verses quoted only in the
  closing moral/hortatory section, and anything from another book.
- For genealogies / list passages, do NOT extend to verses the homily never
  actually discusses — a real gap before the next homily is correct.
- `start <= end`, normally `<= next_start - 1`.

Each agent writes strict JSON: `[{"id": int, "end": {"chapter": int, "verse":
int}, "evidence": "the biblical verse last treated + the commentary phrase
showing it", "confidence": "high|medium|low"}]`.

**Recommended: run two independent passes and reconcile.** Where the two passes
agree (usually the large majority), trust it; manually review only the homilies
where they disagree — those are the genuinely hard interpretive cases (long
discourses, genealogies, parables). This is how the Matthew set was validated.

### 3. Apply
Concatenate all agent results into `results.json`, then:
```
python scripts/apply_coverage.py <commentary_dir> <results.json>
```
Rewrites each homily's `end` in `coverage.json` and the `coverage` block in each
`content/<NNN>/metadata.json`, recomputes display strings, and reports overlaps
and the genuine verse gaps (chapter-boundary false positives are filtered out
using the KJV verse counts). `start` and `verse_mapping.json` are untouched.

### 4. Verify
Restart the server and confirm shaded verses match the real coverage — gaps
appear only where a homily's exposition truly stops before the next lemma.
Spot-check the medium/low-confidence homilies and any two-pass disagreements.

## Notes
- Shading/tooltips read `coverage.json` `end` directly (`formatCoverageRef` /
  `coverageContains` in the Go server) — no code change needed.
- Multiple homilies may share a `start` (e.g. Matthew 1:1); overlapping ends
  among same-start homilies are allowed.
- Out-of-order/"backtrack" homilies (a lemma earlier than the previous homily's)
  can legitimately overlap their neighbours; apply_coverage.py reports these as
  overlaps for review rather than failing.
- Reusable as-is for Chrysostom on John and any other CCEL commentary with the
  same `content/` + `coverage.json` layout; `build_bundles.py` also honours a
  `"unit"` field in coverage.json (e.g. "Sermon") for the label.
