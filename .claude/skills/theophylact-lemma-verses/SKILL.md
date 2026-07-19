---
name: theophylact-lemma-verses
description: Given a single Theophylact lemma (a folder or .txt under theophylact/PG/sectioned), determine which Gospel verse or verse-range it belongs to, by matching its quoted Greek scripture against the Greek Patriarchal (Byzantine) New Testament. Greek-to-Greek only — never relies on the English translation. Use when the maintainer asks "what verse(s) does this lemma cover?" or as the per-lemma primitive for building a verse↔lemma coverage map.
---

# Find the verse(s) a Theophylact lemma belongs to

Take one lemma from `texts/commentaries/theophylact/PG/sectioned/…` and return the
Gospel verse — or verse **range** — it expounds. This is the atomic step the full
Theophylact coverage map is built from.

## The one rule that governs everything
**The Greek is the arbiter, and the Greek alone.** A lemma "belongs to" the verse(s)
whose Byzantine-text scripture its **opening scripture quotation reproduces**. You resolve
this by matching Theophylact's quoted Greek against the Greek **Patriarchal** text — never
by reading the English.

**Use the Patriarchal (Byzantine), NOT the Textus Receptus.** Theophylact is an 11th-c.
Byzantine writer; his quotations track the Byzantine/Majority text, so match against the
**Patriarchal** New Testament (Antoniades 1904). Versification is identical to the TR, so
verse *numbers* are the same, but the Patriarchal wording is the closer match to what he
actually quotes (and resolves borderline word-variants the TR would miss). The TR is a
fallback only.

**This task is NOT blocked on the English translation.** Everything needed is Greek:
- the lemma's own quoted scripture (the `« … »` span at the head of its `.txt`), and
- the Greek Patriarchal text at
  `texts/scripture/new_testament/greek/patriarchal/<book>/<book>.txt` (one verse per line,
  `ch:verse …`; note chapter breaks may be appended inline as `… Chapter N`).

The `.en.md` header verse is itself *derived* from this same Greek match, so the English
adds no independent information. Do **not** open `.en.md` to decide the verse, and do
**not** report this skill as blocked. (If a lemma has *no* Greek scripture quote at all —
a pure-exposition continuation — see step 4; that case is still resolved from Greek +
sequence, not English.)

**Never trust the folder-name suffix as truth.** `ΛΗΜΜΑ_100_1.15` *claims* John 1:15, but
those suffixes are an unreliable earlier guess (e.g. John 1 lemmata 01–09 are all tagged
`1.3`). Re-derive the verse; treat the suffix only as a hint to sanity-check against.

## Inputs
A lemma identified by any of:
- a lemma **folder** (e.g. `…/ΚΕΦΑΛΑΙΟΝ_01_Αʹ/ΛΗΜΜΑ_100_1.15`), or
- its `.txt` file, or
- the lemma's Greek text pasted directly (then the maintainer must also say gospel+chapter).

From the path you already know:
- **gospel** — `ΚΑΤΑ_ΜΑΤΘΑΙΟΝ`→matthew · `ΚΑΤΑ_ΜΑΡΚΟΝ`→mark · `ΚΑΤΑ_ΛΟΥΚΑΝ`→luke · `ΚΑΤΑ_ΙΩΑΝΝΗΝ`→john
- **chapter** — from `ΚΕΦΑΛΑΙΟΝ_NN_…` (`NN` is the Arabic chapter).

## Tool — `match_verses.py` (bundled with this skill)
A deterministic matcher lives next to this file: `match_verses.py`. **No LLM** — pure stdlib
TF-IDF cosine over normalized Greek, matching each lemma's `«…»` quote against **only its own
chapter's** verses (chapter from the `ΚΕΦΑΛΑΙΟΝ_NN` folder). On a no in-chapter match it
inherits the previous lemma's verse by sequence (cross-ref/continuation). Flags:
```
S=.claude/skills/theophylact-lemma-verses
python3 $S/match_verses.py --gospel matthew --chapter 1                        # one chapter, table
python3 $S/match_verses.py --gospel matthew --all --overrides $S/overrides_matthew.json --flags        # whole gospel, rows to review
python3 $S/match_verses.py --gospel matthew --all --overrides $S/overrides_matthew.json --coverage-json # -> coverage.json
```
- **Single verse per lemma by default.** Auto tail-ranging was removed — on this OCR text it
  produced spurious wide ranges (a quote's tail collides with a distant verse sharing a stock
  phrase, e.g. «βασιλεία τῶν οὐρανῶν»). Genuine multi-verse spans are supplied via overrides.
- **`--overrides <file>`** applies `{folder_name:[start,end]}` **before** sequence-inheritance
  (so a correction propagates to continuations that inherit from it). This is where every
  adjudication is recorded — e.g. `overrides_matthew.json`.
- **`--flags`** prints only rows needing eyes. Triage: `weak/none in-chapter` = the real
  adjudication set (short genuine quote that under-scored → set its in-chapter verse; OR a true
  cross-ref/continuation → inheritance is already right). `suffix-off` = the matcher is right
  and the folder tag is wrong (informational, trust the match). Use the model only on the
  flagged rows — never per lemma.

**Recipe to finish a gospel:** run `--all --flags`; adjudicate every `weak/none` against the
Patriarchal chapter; add the corrections to `overrides_<gospel>.json`; re-run `--flags` until
the weak set is clean; then `--coverage-json` → `texts/commentaries/theophylact/<gospel>/coverage.json`.
Sanity-check: 0 null verses, all chapters present, per-chapter max verse ≈ chapter length.

## Procedure
`match_verses.py` automates steps 1–2 for a whole chapter; do them by hand only when
adjudicating a flagged lemma or working one lemma in isolation.

1. **Read the lemma `.txt`.** Isolate the leading scripture quotation — the first
   `« … »` guillemet span. That opening quote is the locator. (Ignore later `« »` spans;
   they may be Theophylact re-quoting mid-exposition.)

2. **Find the verse.** Load the Patriarchal chapter file for the gospel+chapter. Pick
   3–6 distinctive consecutive words from the opening quote (prefer rare nouns/verbs over
   particles) and grep them across the Patriarchal verse lines. Match on **normalized** Greek:
   - lowercase; strip accents/breathings/iota-subscript; normalize final sigma;
   - forgive OCR noise — the PG text is OCR'd (`νέννῃσιν` for `γέννησιν`, dropped/merged
     letters, `θ/δ`, `κ/χ`, `π/τ` swaps). Match on the skeleton of consonants+order, not
     an exact string. A partial hit on the rare words is enough.
   The Patriarchal line whose text the opening quote reproduces is the **verse**. Coverage is
   **single-verse by default** (see the Tool note on why auto-ranging was removed).

3. **Ranges are the exception, added by adjudication only.** If a quote genuinely runs across
   a verse boundary, record it as a `[start,end]` in `overrides_<gospel>.json` — do not rely on
   the matcher to find ranges. Most lemmata are a single verse or a phrase within one.

4. **Continuation lemmata (no fresh quote).** Some lemma folders open with Theophylact's
   *own* words or with him quoting himself (e.g. `ΛΗΜΜΑ_05` → `«Ὁρᾷς οὖν πῶς…»`, which is
   not scripture). If the opening `« »` does **not** match any Patriarchal verse:
   - Walk backward through the **preceding** sibling lemmata (by their numeric `ΛΗΜΜΑ_NN`
     order in the same chapter folder) until you reach the nearest lemma that *does* carry
     a matchable scripture quote; that verse is the **current lemma**, and this
     continuation **inherits** it.
   - Report it as `→ <verse> (continuation of ΛΗΜΜΑ_NN)`, still Greek-derived.

5. **Sanity-check & confidence.** Compare your derived verse to the folder-name suffix and
   to the entry in `PG/sectioned/lemmata_index.json` (keyed by chapter `.txt`, listing a
   `verse`/`score`/`preview` per lemma). Agreement → high confidence. Disagreement → trust
   *your* Greek match, and **flag the mismatch** so the map/rename can be corrected.

## Output
Report concisely in chat:
1. **Verdict line** — `ΛΗΜΜΑ_100 → John 1:15` (or a range `→ Matt 5:4–5`, or
   `→ John 1:3 (continuation of ΛΗΜΜΑ_03)`).
2. **Evidence** — the opening Greek quote you matched and the Patriarchal verse text it
   reproduced; for a range, the tail quote + its Patriarchal verse too. One line each.
3. **Confidence** — high / medium (OCR-fuzzy or short quote) / low (continuation-inherited
   or no clean anchor), and **any mismatch** vs. the folder suffix or `lemmata_index.json`.

Keep it tight — the deliverable is a defensible verse locator per lemma, with the Greek
that proves it.

## Which Greek text you match against
- **Primary anchor: the Patriarchal (Byzantine, Antoniades 1904)** — `texts/scripture/
  new_testament/greek/patriarchal/<book>/<book>.txt`, one verse per line (`2:22 ἀκούσας δὲ …`).
  This is the right comparand for a Byzantine author: his quotations track the Byzantine/
  Majority text, so his wording matches it more closely than the TR.
- **Textus Receptus** (`…/greek/textus_receptus/…`) is a **fallback only** — same
  versification (identical chapter/verse boundaries, so verse *numbers* agree), useful only
  if a Patriarchal match is ambiguous. Do not default to it.
- Note: the earlier `lemmata_index.json` / `segment_lemmata.py` were built against the TR;
  the go-forward coverage build uses the Patriarchal text.

## Persisting the result — per-lemma `metadata.json`
The follow-on step writes the derived coverage into **`metadata.json` inside each lemma
folder** (sibling to the `.txt`/`.en.md`), so coverage is durable and machine-readable.
Schema (matches the project's other commentaries' `scripture_reference` convention):

```json
{
  "lemma": "ΛΗΜΜΑ_47_2.21", "gospel": "matthew", "chapter": 2, "index": 47,
  "scripture_reference": {
    "book": "matthew",
    "start": {"chapter": 2, "verse": 22}, "end": {"chapter": 2, "verse": 22},
    "verses": [{"chapter": 2, "verse": 22}],
    "display": "Matthew 2:22"
  },
  "lemma_quote": "Χρηματισθεὶς δὲ κατ᾽ ὄναρ, ἀνεχώρησεν εἰς τὰ μέρη τῆς Γαλιλαίας",
  "lemma_quote_en": "But having been warned in a dream, he withdrew into the parts of Galilee",
  "cross_references": [],
  "coverage_source": "greek_pat", "confidence": "high",
  "folder_suffix": "2.21", "folder_suffix_agrees": false,
  "notes": "…"
}
```

Rules for populating it:
- **Coverage = the verse(s) the lemma EXPOUNDS**, expressed as a range (`start`/`end`) and
  an explicit `verses[]` list (supports non-contiguous sets). A lemma often spans verses
  (`ΛΗΜΜΑ_46` → 2:21–22); many opening lemmata are one long verse split phrase-by-phrase
  (all of Matt 2:1 across five lemmata).
- **Coverage is derived ONE way: the lemma's Greek `«…»` quote matched against the
  Patriarchal chapter** (the atomic procedure above). **Do NOT read the verse from the
  `.en.md`.** The `.en.md` blockquote refs are **known-unreliable** — reproducing them is the
  very reason this coverage work is being redone from scratch. Never treat the English as a
  source of, or shortcut to, the verse. `coverage_source` is always `greek_pat` (Patriarchal
  match) — no `en.md` value exists. The folder suffix is a hint to sanity-check, never a source.
- **Coverage vs. cross-reference — do NOT conflate.** Coverage comes only from the verse in
  the lemma's own `«…»` quote **as matched in its own chapter**. If the `«…»` quote matches a
  verse in a *different* chapter (Theophylact quoting Matt 28:20 while expounding 1:25) or
  matches nothing in-chapter, it is a **cross-reference / continuation** → put that foreign
  verse in `cross_references`, and set coverage by sequence (inherit the preceding lemma's
  verse), never the foreign verse.
- **`folder_suffix_agrees`** = the folder-name verse falls **within** the derived coverage.
  `true` = tag is correct or merely incomplete (a range start, e.g. `ΛΗΜΜΑ_46`); `false` =
  tag points **outside** coverage → a genuinely WRONG suffix to flag for the rename step
  (e.g. `ΛΗΜΜΑ_47` tagged 2.21 but expounds 2:22). This is the field the scale-up run
  triages on.
- **`confidence`**: `high` (clean, unambiguous Patriarchal match), `medium` (OCR-fuzzy or
  short quote), `low` (continuation-inherited, or no clean anchor). Route every `low`/`false`
  case through the atomic procedure above (model adjudication) before trusting it.
- **`lemma_quote` / `lemma_quote_en`**: the Greek `«…»` opening quote and, optionally, a plain
  English gloss for legibility. This is **display only — never used to decide the verse.**

## Build the app `coverage.json` (the Scripture-References/Index table)
The Hypomnema index table (`indexPageHandler`, route `/api/index`, in
`hypomnema-server/main.go`) renders each commentary from
`texts/commentaries/<author>/<book>/coverage.json`. For each entry it shows the **Section
column = the entry's `title`**, and it **merges consecutive entries with the same
Scripture+Father+Work into one row**, joining their titles with `<br>` (main.go ~3100-3136).
So to show Theophylact as `Lemma 1`, `Lemma 2`, … (multiple lemmata stacked on one verse,
exactly like Chrysostom's `Homily I / Homily II` on Mt 1:1), write **one entry per lemma**:

```json
{ "commentary": "Theophylact of Ohrid — Explanation … Matthew",
  "total_homilies": 1124,
  "homilies": [
    { "id": 1, "roman": "", "title": "Lemma 1",
      "start": {"book": "matthew", "chapter": 1, "verse": 1},
      "end":   {"book": "matthew", "chapter": 1, "verse": 1} }
  ] }
```
- `title` = `"Lemma <N>"` where **N is the lemma's `ΛΗΜΜΑ_NN` index** (our own sequential
  number — the source does NOT number lemmata; only chapters carry Greek numerals).
- `start`/`end` = the lemma's derived verse coverage, obtained the **one sanctioned way for
  all four gospels (Matthew included): the atomic chapter-scoped Greek→Patriarchal match** of
  the lemma's `«…»` quote. **Do NOT read verses from the `.en.md`** — those refs are unreliable
  and are exactly what this rebuild exists to replace. A quote that does not match anywhere in
  the lemma's own chapter is a cross-reference/continuation → resolve by sequence, do NOT
  assign the foreign verse.
- **Generate coverage.json from the per-lemma `metadata.json`** where those exist (invert
  `scripture_reference` → `start`/`end`), so confidence/cross-ref data is not thrown away;
  emit a mismatch report (every `folder_suffix_agrees:false`) for the maintainer before trust.
- The app currently renders Theophylact's Section as **plain text** (it is in the no-link
  branch, main.go ~3082); making `Lemma N` clickable is a separate, later main.go change.

## Scope
- Theophylact only; works for all four Gospels (Patriarchal present for each; TR as fallback).
- This skill's **atomic procedure is read-only** (finds one verse). The documented
  `metadata.json` populate above is the sanctioned follow-on that *writes* coverage; it
  calls this procedure per lemma for the untranslated/flagged cases. Renaming folder
  suffixes to match is a further, separate step.
- Related: [compare-theophylact-stade](../compare-theophylact-stade/SKILL.md) (QC of the
  English) and [translate-theophylact](../translate-theophylact/SKILL.md) (rendering).
