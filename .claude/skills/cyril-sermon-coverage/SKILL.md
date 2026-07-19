---
name: cyril-sermon-coverage
description: Determine the true verse range (start AND end) each Cyril-of-Alexandria sermon on Luke covers by reading every sermon, fix mislabeled roman numerals, and regenerate coverage.json, metadata.json, and verse_mapping.json. Use for Payne Smith HTML-sourced commentaries where 1:1 placeholder lemmata, "same subject continued" sermons, and single-verse lemma ranges make coverage unreliable.
---

# Cyril Sermon Coverage

Cyril's Sermons on Luke (Payne Smith translation, HTML source) differ from the
CCEL ThML Chrysostom pipeline (`ccel-homily-coverage`) in three ways that make
that skill inapplicable:

1. **Starts are unreliable too.** The extractor left `1:1-1:1` placeholders on
   sermons whose lemma it could not parse, so `start` must be determined by
   reading, not trusted. (In Chrysostom the lemma/start is authoritative.)
2. **Citations are inline prose, not scripRef tags.** Lemmata appear as
   paragraph-leading citations ("12:22-31.", "(6:24)", "Luke ii. 1") inside
   `content/<NNN>/content.json` paragraphs.
3. **Continuation sermons.** Sermons titled "THE SAME SUBJECT CONTINUED" carry
   no lemma; they continue (and may legitimately **overlap**) the preceding
   sermon's passage. Numbering also has real holes (sermons lost from the
   Syriac MS: 9, 13-19, 24, 28, 97, 98, 113, 114) — gaps around them are
   correct, not defects.

Runtime note: the Go server rebuilds the verse-marker map from
`coverage.json` starts whenever `verse_mapping.json` is chapter-keyed (see
`loadCommentary` in `hypomnema-server/main.go`), so **coverage.json is the
single runtime source of truth** for both margin markers and shading.
Metadata and verse_mapping are updated for consistency with the project rule
that metadata.json is authoritative.

## When to use
- Whenever Cyril-on-Luke verse coverage, markers, or shading must be accurate.
- After any regeneration of Cyril metadata/coverage from the HTML source.
- Adaptable to other HTML-sourced commentaries with inline lemmata.

## Inputs (commentary dir: `texts/commentaries/cyril/luke`)
- `coverage.json` — entries with `id` (authoritative), possibly wrong
  roman/title labels and placeholder ranges.
- `content/<NNN>/content.json` — sermon paragraphs (HTML fragments).
- `content/<NNN>/metadata.json` — per-sermon metadata (`scripture_reference`).
- KJV Luke text under `texts/scripture/.../kjv/luke/` for verse-bound checks.

## Procedure

### 1. Extract candidates (deterministic)
```
python scripts/extract_candidates.py <commentary_dir> <manifest.json> <text_dir>
```
For each sermon this yields `candidate_start` (first paragraph-leading
citation near the top), `candidate_end` (furthest citation within the window
up to the next extant sermon's lemma), a `continued` flag, previous/next
extant sermon context, all detected citations, and plain text at
`<text_dir>/<NNN>.txt`. It also flags `1:1` placeholders and label mismatches
(roman recomputed from id).

Candidates are hints, not answers: Cyril often expounds past his last quoted
verse, and continuation sermons have no citations at all.

### 2. Confirm by reading — every sermon, no exceptions
Fan out subagents in id order, ~10-15 sermons per batch. Give each agent its
batch's manifest entries and text files, **plus the manifest entry of the
sermon immediately before the batch** (context for a leading "continued"
sermon). Each agent reads every sermon text fully and returns the true range.

Reading rules:
- **start** = the first verse the sermon actually expounds.
  - An explicit opening lemma ("12:22-31.") fixes the start of the range.
  - A "same subject continued" sermon starts where its exposition actually
    picks up — usually inside the previous sermon's passage (overlap is
    correct); state the verse the text first engages.
  - No lemma and not continued: infer from content between the neighbors'
    ranges (parables/episodes are identifiable; e.g. an exposition of the
    Great Supper is Luke 14:15-24).
- **end** = the highest Luke verse the **running exposition** reaches,
  including verses discussed in prose just past the final quotation.
  Mid-sermon paragraph-leading citations ("2:4.") mark sequential progress.
- **Ignore** illustrative cross-references, verses quoted in the closing
  hortatory section that are not part of the sequential exposition, and any
  non-Luke citation.
- Ranges may cross chapter boundaries (e.g. Sermon CXL covers 21:37-22:6).
- `start <= end` always; end normally stays below the next extant sermon's
  start except for continuation chains and multi-sermon expositions of one
  passage (e.g. consecutive sermons on the Lord's Prayer) — those overlaps
  are genuine.
- If the exposition stops well before the next extant sermon's lemma, keep
  the earlier end; lost sermons make many gaps real.
- Fragments (e.g. Sermon XXIX, a Syriac fragment on 6:24) get exactly the
  verses the surviving text treats.

Return strict JSON per sermon:
`{"id": int, "start": {"chapter": int, "verse": int}, "end": {"chapter": int,
"verse": int}, "evidence": "short quote/verse ref", "confidence":
"high|medium|low"}`.

Re-read any sermon where the agent's range conflicts with an explicit opening
lemma in the manifest, or where confidence is low.

### 3. Apply
Concatenate all agent results into `results.json`, then:
```
python scripts/apply_coverage.py <commentary_dir> <results.json>
```
This rewrites `start`, `end`, `roman`, and `title` in coverage.json
(roman/title recomputed from id — fixes the copied-from-neighbor labels),
updates each `content/<NNN>/metadata.json` `scripture_reference` + `subtitle`,
regenerates chapter-keyed `verse_mapping.json`, and prints a validation
report (KJV verse bounds, overlaps, gaps).

### 4. Verify
Review the report: every overlap should be a continuation chain or a
multi-sermon single-passage exposition; every 1:1 placeholder must be gone
(`grep -c '"verse": 1' coverage.json` sanity, or re-run step 1 and confirm
`placeholder_1_1` is false everywhere). Ask the user to restart the server,
then curl a Luke chapter page and confirm markers/shading (e.g. Luke 1 must
show no Cyril markers; Luke 3 must include Sermon X at 3:15).

### 5. Adversarial KJV cross-check (correction pass)
For a corrections audit of already-applied ranges, re-run step 1 (confirms no
placeholders/label drift), then fan out verifiers instead of readers: each
agent gets its batch's current ranges and tries to REFUTE them by re-reading
the sermon and comparing the quoted scripture at the claimed start and end
against the KJV text (`texts/scripture/.../kjv/luke/<NN>/luke_<NN>.txt`,
lines "chapter:verse text"). This catches versification mismatches between
Payne Smith's citations and real verse numbers (e.g. clauses of the Lord's
Prayer that Matthew splits across verses but Luke keeps in 11:2-4). Agents
return `verdict: correct|incorrect` per sermon with the verified range; apply
only refuted entries. A range counts as wrong only on concrete KJV evidence.
This pass was run 2026-07-06 against all 139 sermons: 139/139 confirmed.

## Notes
- Sermon `id` is the only trusted identity; folder `content/<NNN>` matches id.
- `content.json` `subtitle` fields like "Luke 104" are the sermon number, not
  a reference — never parse them. Metadata subtitles are rewritten by apply.
- Sermons 154-156 exist only as fragments and are absent from the collection;
  139 extant sermons is the expected count.
