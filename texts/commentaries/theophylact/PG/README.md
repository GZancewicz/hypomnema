# Theophylact of Ohrid — Patrologia Graeca 123–124

Greek source, processing pipeline, and derived artifacts for **Theophylact of
Ohrid's Gospel commentaries** (Ἑρμηνεία on Matthew, Mark, Luke, John). This folder
takes the raw OCR of Migne's *Patrologia Graeca* vols. 123–124 to a cleaned,
chapter-sectioned, lemma-indexed corpus ready for translation.

---

## 1. Provenance — where the files came from

### Source PDFs (page scans) — `PG_123.pdf`, `PG_124.pdf`
- Migne, *Patrologiae Cursus Completus, Series Graeca* vols. **123–124** (1864 printing), public domain.
- Downloaded from the **Internet Archive**:
  - vol. 123: `bim_early-english-books-1641-1700_patrologiae-cursus-completus-_1864_123`
  - vol. 124: `bim_early-english-books-1641-1700_patrologiae-cursus-completus-_1864_124`
- ~400 MB each, image scans with a poor built-in text layer.
- **git-ignored** (too large) — see `.gitignore`. Re-download from the identifiers above if needed.
- Contents: vol. 123 = commentary on Matthew, Mark, Luke, John; vol. 124 = tail of John + Acts/Pauline epistles (epistles out of scope here).

### Greek OCR text — `PG_123.txt`, `PG_124.txt` (~262k + 268k words)
- **NOT our own OCR.** Pulled from the **CGPG project** (Calfa–GREgORI Patrologia Graeca), which already OCR'd these exact volumes at high quality (**CER ≈ 1.05%, WER ≈ 4.69%**).
- Repo: `github.com/calfa-co/Patrologia-Graeca` — files `PG123/PG123_text.txt`, `PG124/PG124_text.txt` (raw GitHub URLs). License **CC-BY 4.0**.
- Paper: *The Patrologia Graeca Corpus…* (arXiv **2603.09470**).
- **Greek only** — the project drops Migne's parallel Latin column.
- Original CGPG reference markers `$0=vol $8=pdfpage $9=line` are present in these raw files; they are **stripped** during sectioning (page info preserved in `MANIFEST.json`).

### Textus Receptus Greek (external helper, not stored here)
- `texts/scripture/new_testament/greek/textus_receptus/<gospel>/<gospel>.txt`
- Used as the **matching anchor** for lemma isolation / verse coverage (see §4). Present for all four Gospels.

---

## 2. Structure discovered
- Theophylact's commentary is **continuous verse-by-verse exegesis**, not homilies/sermons.
- Migne divides each Gospel into **kephalaia (numbered chapters) that correspond 1:1 to modern KJV chapter numbers** (Matthew 28, Mark 16, Luke 24, John 21 = 89 chapters). Verified by matching each chapter's *titlos* (its `Περὶ …` content summary) to the expected chapter.
- Within a chapter: a chain of **lemma → exposition** — Theophylact quotes a Gospel snippet (`«…»`) then comments on it.

---

## 3. Directory layout

```
PG/
├── README.md                     ← this file
├── PG_123.pdf, PG_124.pdf        ← source scans (git-ignored)
├── PG_123.txt, PG_124.txt        ← raw CGPG OCR, full volumes (Greek)
├── translation-methodology.md    ← pointer to the translate-theophylact skill
└── sectioned/                    ← the processed corpus
    ├── MANIFEST.json             ← per-chapter: line, page, boundary confidence
    ├── CLEANUP.md                ← OCR cleanup status/checklist
    ├── lemmata_index.json        ← per-chapter lemma + verse-coverage index
    ├── ΚΑΤΑ_ΜΑΤΘΑΙΟΝ/
    │   ├── ΤΑ_ΚΕΦΑΛΑΙΑ.txt              ← titloi list (front matter)
    │   └── ΕΡΜΗΝΕΙΑ/
    │       ├── ΠΡΟΟΙΜΙΟΝ.txt            ← prologue
    │       └── ΚΕΦΑΛΑΙΟΝ_01_Αʹ/         ← each chapter is a FOLDER
    │           ├── ΚΕΦΑΛΑΙΟΝ_01_Αʹ.txt  ← full chapter text (kept, source of truth)
    │           ├── 00_ΑΡΧΗ.txt          ← chapter header + titlos (pre-first-lemma)
    │           ├── ΛΗΜΜΑ_01_1.1/        ← one SUBFOLDER per lemma
    │           │   └── ΛΗΜΜΑ_01_1.1.txt ← the Greek lemma + its exposition (.en.md added here later)
    │           └── ΛΗΜΜΑ_02_1.1/ …      (ΛΗΜΜΑ_NN_<chapter>.<verse>)
    ├── ΚΑΤΑ_ΜΑΡΚΟΝ/  (ΒΙΟΣ + ΤΑ_ΚΕΦΑΛΑΙΑ + ΕΡΜΗΝΕΙΑ/ 16 chapter folders)
    ├── ΚΑΤΑ_ΛΟΥΚΑΝ/  (ΤΑ_ΚΕΦΑΛΑΙΑ + ΕΡΜΗΝΕΙΑ/ 24 chapter folders)
    └── ΚΑΤΑ_ΙΩΑΝΝΗΝ/ (ΒΙΟΣ + ΕΡΜΗΝΕΙΑ/ 21 chapter folders; ch1–7 from PG_123, ch8–21 from PG_124)
```
- **Each kephalaion is a folder**; inside it the full chapter `.txt` is kept, plus `00_ΑΡΧΗ.txt` and one **`ΛΗΜΜΑ_NN_ch.verse/` subfolder per lemma** holding the Greek. Total: **5,028 lemma folders**.
- A **lemma** = a scripture snippet Theophylact quotes (`«…»`) then expounds — *not* 1:1 with verses (he splits some verses into several lemmata, e.g. 5:1 → two). The verse in the folder name is the verse it draws from; verse tags are monotonic per chapter.
- Filenames keep **Greek numerals** (`ΚΕΦΑΛΑΙΟΝ_05_Εʹ`, `ΛΗΜΜΑ`= *lemma*), with zero-padded indices for sort order.
- **John spans both volumes:** chapters 1–7 come from `PG_123.txt`, chapters 8–21 from `PG_124.txt` (stopping before the Pauline epistles).
- **Reconstruction:** `00_ΑΡΧΗ.txt` + the lemma files in sequence == the kept chapter `.txt`, byte-for-byte (asserted on every split; 0 failures across all 89).

---

## 4. What we did (pipeline)

1. **Fetched** the PDFs (Internet Archive) and the Greek OCR text (CGPG GitHub). §1.
2. **Sectioned** `PG_123/124.txt` into the 89 kephalaia + front matter. Chapter boundaries found by detecting `ΚΕΦΑΛ`/Latin `CAPUT` headers; **~20% of headers were OCR-destroyed** and recovered by matching each chapter's *titlos* and opening-verse lemma. Every boundary titlos-verified. 5 chapters (Mt 21, Mt 28, Mk 1, Lk 3, Jn 17) had headers reconstructed → flagged `"confidence":"medium"` in `MANIFEST.json`.
3. **Cleaned up OCR structure** (all scripted, verified against backups, zero content loss):
   - normalized all 89 chapter headers to `ΚΕΦΑΛ. <numeral>.`
   - removed 51 inline-noise lines (Latin `CAPUT` running-heads, orphan numerals, bled-in Greek page-titles)
   - fixed front-matter header typos
   - conservative body pass: 65 high-frequency **non-word** corrections (`Ιερὶ`→`Περὶ`, `Ἰλσοῦ`→`Ἰησοῦ`, `Χριστου`→`Χριστοῦ`) — Greek-token count unchanged.
   - Broad auto-correction was **deliberately not done**: the OCR is ~99% accurate and edit-distance analysis showed most near-neighbors are valid inflections/minimal pairs (`οἶνον`/`οἶκον`, `κακὸν`/`καλὸν`), so a blind pass would inject errors. Long tail left for a lexicon/human pass — see `sectioned/CLEANUP.md`.
4. **Isolated lemmata + computed verse coverage** by matching each chapter against the **Textus Receptus**: **97.8% of TR verses located** (`sectioned/lemmata_index.json`, a per-chapter verse-coverage summary).
5. **Split each chapter into per-lemma folders** (`split_lemmata_to_files.py`): boundaries at Theophylact's `«` marks (his own divisions), gap-filled where a verse's `«` was OCR-dropped; each lemma tagged with its verse via a forward-window cursor (monotonic, never jumps backward). **5,028 lemma folders**, byte-perfect reconstruction, 0 untagged. This is the working structure for translation.
6. **Wrote the translation methodology** as a reusable skill (see below) and **began translating** lemma-by-lemma (sibling `.en.md` per lemma folder).
7. **Built per-lemma verse coverage** by matching each lemma's Greek `«…»` quote against the **Patriarchal (Byzantine)** NT — see `theophylact-lemma-verses` skill + `match_verses.py`. Emitted the app `coverage.json` (Section = "Lemma N") for Matthew.
8. **Set up the Stade (Chrysostom Press) benchmark** for translation QC — `compare-theophylact-stade` skill; benchmark text is git-ignored (in-copyright).
9. **Wrote a `metadata.json` into every one of the 5,028 lemma folders** — the durable, machine-readable verse coverage for each lemma. Fully local, no LLM. See §4a.

---

## 4a. Per-lemma `metadata.json` — how coverage was derived

Every lemma folder now holds a `metadata.json` sibling to its `.txt`, recording which
Gospel verse(s) that lemma expounds. Written by
`.claude/skills/theophylact-lemma-verses/write_metadata.py`, which drives
`match_verses.py` and writes each folder's file as the lemma is processed.

### Method — deterministic, local, no model calls
The whole derivation is pure-stdlib Python. **The Greek is the sole arbiter** — the
`.en.md` English is never read (its verse refs are known-unreliable), and the folder-name
suffix is treated only as a hint to check against, never as a source.

Each lemma resolves through this cascade, recorded in `match_method`:

1. **`tfidf`** — the lemma's opening `«…»` quote is normalized (accents/breathings
   stripped, final sigma folded, non-Greek dropped) and scored by TF-IDF cosine against
   **only its own chapter's** verses in the Patriarchal text. Accepted at cosine ≥ 0.34;
   `high` at ≥ 0.55, else `medium`.
2. **`fuzzy`** — OCR-tolerant fallback when the token match fails. Common PG scan
   confusions are folded on both sides (δ/θ, γ/τ, π/τ, κ/χ, β/κ) and the quote is scored
   by character-level containment (`difflib`, counting only contiguous blocks ≥ 3 chars,
   so scatter noise can't inflate a match). Accepted only at ≥ 0.72 **and** with a ≥ 0.08
   margin over the runner-up. This is what resolves quotes the token matcher cannot see at
   all — e.g. ΛΗΜΜΑ_01 of Matthew 1, whose OCR reads «ΧίΚλρς τενέαεως» for
   «Βίβλος γενέσεως».
3. **`inherited`** — no in-chapter match survived. The lemma is a **cross-reference**
   (Theophylact quoting Isaiah, a Psalm, or another Gospel mid-exposition) or a
   **continuation** (opening with his own words, or a sentence broken across our section
   boundary). It inherits the preceding lemma's verse by sequence and is marked
   `confidence: "low"`, `continuation: true`. A foreign verse is **never** assigned as
   coverage — that goes in `cross_references`.
4. **`override`** — human-adjudicated, recorded in
   `.claude/skills/theophylact-lemma-verses/overrides_<gospel>.json` and applied *before*
   inheritance so a correction propagates to the continuations that follow it. Overrides
   accept a plain `[start, end]` or, for a lemma physically filed under the wrong chapter,
   `{"chapter": N, "start": S, "end": E}`. Three such cross-chapter cases exist: Matthew
   ch12 Lemma 1 → **Mt 11:29–30** (the "yoke" saying), John ch8 Lemma 1 → **Jn 7:52**
   (Theophylact omits the pericope adulterae), John ch19 Lemma 1 → **Jn 18:40** (Barabbas).

Ranges are the exception, not the rule: coverage is single-verse by default. Automatic
tail-ranging was removed because on this OCR it produced spurious wide spans (a quote's
tail colliding with a distant verse that shares a stock phrase like «βασιλεία τῶν
οὐρανῶν»); genuine multi-verse spans are supplied by override.

### Initial breakdown by confidence (first full run, all four Gospels)

| Gospel | Lemmata | high | medium | low | tfidf | fuzzy | inherited | override |
|---|---|---|---|---|---|---|---|---|
| Matthew | 1,124 | 992 (88.3%) | 88 | 44 (3.9%) | 1,056 | 8 | 44 | 16 |
| Mark | 526 | 503 (95.6%) | 12 | 11 (2.1%) | 513 | 2 | 11 | 0 |
| Luke | 1,046 | 871 (83.3%) | 79 | 96 (9.2%) | 939 | 11 | 96 | 0 |
| John | 2,332 | 1,289 (55.3%) | 638 | 405 (17.4%) | 1,788 | 137 | 405 | 2 |
| **Total** | **5,028** | **3,655 (72.7%)** | **817 (16.2%)** | **556 (11.1%)** | **4,296 (85.4%)** | **158** | **556** | **18** |

Reading these numbers:
- **0 lemmata are without coverage** across all four Gospels.
- **`low` does not mean wrong.** It means the verse was not independently derivable from
  that lemma's own quote, so it came from sequence. For most low rows inheritance is the
  *correct* answer (a Psalm or Pauline proof-text quoted mid-exposition), and the label
  just records that the evidence was indirect.
- **John is the outlier** — 55% high vs. 83–96% elsewhere, and 73% of all low rows. Two
  causes compound: its OCR is the worst in the corpus (hence 137 of the 158 fuzzy
  rescues), and its lemmatization is by far the most phrase-level (2,332 lemmata over 21
  chapters vs. Matthew's 1,124 over 28), so many lemmata are 1–3 word fragments too short
  to match uniquely.
- **The rows actually worth adjudicating** are not all 556 low rows but the subset where a
  *strong* in-chapter candidate disagrees with the inherited verse. A scan for that
  condition (fuzzy top candidate ≥ 0.70 whose verse is not among the inherited leaders)
  returns **29 rows, all in John** — Matthew, Mark, and Luke contribute none. They cluster
  on short formulas repeated within one chapter («Δέδωκάς μοι» at 17:6/9/22/24, «Οὐκ εἰμί»
  in Peter's denials at 18:17/25/26, «Σὺ οἶδας» at 21:15/16/17), where the margin rule
  correctly refuses to guess and only reading the surrounding exposition can decide.
  **Left un-adjudicated as of this writing.**
- **1,980 folder-name suffixes (39.4%) are wrong** — `folder_suffix_agrees: false` — i.e.
  the verse in the folder name falls outside the derived coverage. John alone accounts for
  1,307. The `metadata.json` carries the corrected verse; renaming the folders is a
  separate, still-pending step.

### Schema
```json
{
  "lemma": "ΛΗΜΜΑ_01_1.1", "gospel": "matthew", "chapter": 1, "index": 1,
  "scripture_reference": {
    "book": "matthew",
    "start": {"chapter": 1, "verse": 1}, "end": {"chapter": 1, "verse": 1},
    "verses": [{"chapter": 1, "verse": 1}],
    "display": "Matthew 1:1"
  },
  "lemma_quote": "Βίβλος γενέσεως.",
  "lemma_quote_en": "The book of the generation.",
  "cross_references": [],
  "coverage_source": "greek_pat",
  "confidence": "high",
  "match_method": "override",
  "match_score": 1.0,
  "adjudicated": true,
  "continuation": false,
  "folder_suffix": "1.1", "folder_suffix_agrees": true,
  "notes": "OCR reads «ΧίΚλρς τενέαεως»; adjudicated as «Βίβλος γενέσεως»…"
}
```
`coverage_source` is always `greek_pat` — there is no English-derived value, by design.
`lemma_quote_en` is display-only and never used to decide a verse.

### Re-running
```bash
S=.claude/skills/theophylact-lemma-verses
python3 $S/match_verses.py  --gospel john --all --overrides $S/overrides_john.json --review
python3 $S/write_metadata.py --gospel john --all --overrides $S/overrides_john.json
```
`--review` lists every inherited row with its top fuzzy candidates — the adjudication
worklist. `write_metadata.py` is idempotent and **preserves hand-curated fields**
(`lemma_quote_en`, `cross_references`, `notes`) across re-runs, so manual annotation
survives; `--force` discards them. Adjudications belong in `overrides_<gospel>.json`, never
in the metadata by hand, so they propagate and survive regeneration.

---

## 5. Helper scripts (in project `scripts/`)
All idempotent and re-runnable; paths resolve to `sectioned/` automatically.

| Script | Purpose |
|--------|---------|
| `_pg_common.py` | shared detectors/util (imported by the others) |
| `scan_pg_noise.py` | report remaining header/noise counts (single source of truth) |
| `strip_pg_noise.py [--apply]` | remove inline Latin/orphan/running-head noise (dry-run by default) |
| `fix_pg_headers.py [--apply]` | normalize chapter headers from filenames |
| `fix_pg_body_conservative.py [--apply]` | apply the curated non-word body corrections |
| `segment_lemmata.py` | match chapters vs. Textus Receptus → `lemmata_index.json` (verse-coverage summary) |
| `split_lemmata_to_files.py [names] [--apply]` | split chapters into per-lemma folders (`«` + gap-fill; forward-window verse tags). Byte-perfect (asserts reconstruction). |

Verse-coverage tooling lives with its skill, not in `scripts/` (`.claude/skills/theophylact-lemma-verses/`):

| Script | Purpose |
|--------|---------|
| `match_verses.py` | derive each lemma's verse: Greek `«…»` → Patriarchal, TF-IDF + OCR-fuzzy fallback + sequence inheritance. `--flags` / `--review` / `--json` / `--coverage-json`. No LLM. |
| `write_metadata.py` | write the per-lemma `metadata.json` from those matches (`--gospel X --all`); idempotent, preserves hand-curated fields. |
| `overrides_<gospel>.json` | adjudicated verse corrections, applied before inheritance. |

**Note:** the chapters are now **per-lemma folders**, not flat `.txt`. The scripts that scan/edit whole chapters (`scan_/strip_/fix_`, `segment_lemmata`) predate this and read flat `ΚΕΦΑΛΑΙΟΝ_*.txt`; their cleanup work is already done. To re-run them you'd first reconstruct flat chapters from each folder's kept `.txt`.

## 6. Key reference files
- **`sectioned/MANIFEST.json`** — per-chapter source file, start line, page, boundary confidence.
- **`sectioned/CLEANUP.md`** — OCR cleanup status; what's done and the remaining (manual) long tail.
- **`sectioned/lemmata_index.json`** — the **original** per-chapter verse-coverage summary from `segment_lemmata.py` (matched vs. **Textus Receptus**). Superseded for coverage by `match_verses.py` (below), which uses the Patriarchal text; kept for reference.
- **`…/ΛΗΜΜΑ_NN_ch.v/metadata.json`** — **the authoritative per-lemma verse coverage** (all 5,028 lemmata, all four Gospels). Schema and derivation in §4a.
- **`../matthew/coverage.json`** — the app-facing verse↔lemma coverage (Section = "Lemma N"), generated by `match_verses.py`. Consumed by the Scripture-References/Index table.
- **Skills & tooling** (`.claude/skills/`, now git-tracked):
  - `translate-theophylact/` — binding translation methodology (formal-equivalence, italic supplied words, translate-his-Greek-not-the-English-Bible, footnote ambiguity, two-pass verify).
  - `theophylact-lemma-verses/` — verse-coverage derivation. `match_verses.py` (deterministic Greek→**Patriarchal**, no LLM) + `write_metadata.py` + `overrides_<gospel>.json` → per-lemma `metadata.json` and `coverage.json`. See §4a.
  - `compare-theophylact-stade/` — QC vs. the Stade benchmark, joined on `coverage.json` verses.

## 7. Status
- ✅ Corpus fetched, sectioned, structurally cleaned, **split into 5,028 per-lemma folders** (integrity-verified).
- ◐ **Translation in progress** (sibling `.en.md` per lemma): **Matthew 1124/1124 · Mark 452/526 · Luke 248/1046 · John 278/2332**.
- ✅ **Verse coverage — all four Gospels done.** Per-lemma `metadata.json` in all **5,028** lemma folders; 0 without coverage; 72.7% high / 16.2% medium / 11.1% low confidence (§4a). Derived entirely locally (no model calls).
- ◐ Body-text OCR: conservative pass done; long tail remains (non-blocking).
- ✅ **Served in the app — Greek, all four Gospels.** `extractTheophylactGreek()` in
  `hypomnema-server/main.go` reads each lemma's `.txt` **straight from `PG/sectioned/`**,
  bypassing the `content/` pipeline (only Matthew lemma 1 was ever built there). Lemma
  ids map to folders by `theophylactLemmaPaths()`: chapters sorted, then lemmata by their
  numeric `ΛΗΜΜΑ_NN_` prefix, so index `i` = id `i+1` — the same order as `coverage.json`,
  verified against the `source` field in `matthew/content/001/metadata.json`. All 1,124
  Matthew rows in the index table (`/api/index`) link through to it.
  - Endpoint: `/api/homily/theophylact/<gospel>/<lemma-id>`.
  - **Lemma counts as served:** Matthew 1124 · Mark 526 · Luke 1046 · John **2332**
    (John has one fewer folder than `metadata.json` files — the folder count governs).
  - **Guillemets are not symmetric across the split:** 796 lemmata open `«` and never
    close; 250 close `»` having never opened. Both heads are scripture and are rendered
    as the bold blockquote; leftover strays (a `»` OCR'd as `«`) become curly quotes.
  - Known bad source: `ΚΑΤΑ_ΛΟΥΚΑΝ/…/ΛΗΜΜΑ_37_21.38` contains only `«` → empty panel.

## 8. Next steps
- **Finish translation** of Mark, Luke, John (lemma-by-lemma via `translate-theophylact`; fan out with the `theophylact-scribe` agent).
- **Adjudicate the 29 contested John rows** (§4a) — short formulas repeated within a chapter, where the inherited verse disagrees with a strong in-chapter candidate. Needs the surrounding exposition read; record verdicts in `overrides_john.json`.
- **Emit `coverage.json` for Mark, Luke, John** from the per-lemma metadata (`match_verses.py --coverage-json`); Matthew's already exists.
- **Rename the 1,980 stale folder verse-suffixes** to match derived coverage (all catalogued via `folder_suffix_agrees: false`).
- **Rebuild the Stade benchmark comparison** off `coverage.json` (per-verse, `compare-theophylact-stade`); currently scoped to a Matthew ch1 pilot.
- **Serve the English where it exists.** The reader currently shows the PG Greek for
  every lemma. The 2,102 translated `.en.md` files are not wired up — the natural next
  step is a Greek/English toggle in the commentary panel that falls back to Greek.
- **Re-enable the reader markers.** `loadCommentary("theophylact", …)` is still commented
  out in `main.go`, so no Theophylact markers appear in the reader margin; only the
  Commentaries index links through.
- **Note on `.en.md` verse refs:** unreliable — do **not** use them to derive coverage; the Greek→Patriarchal match is authoritative.
