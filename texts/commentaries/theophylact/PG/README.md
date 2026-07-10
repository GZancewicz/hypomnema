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
    │   ├── ΤΑ_ΚΕΦΑΛΑΙΑ.txt        ← titloi list (front matter)
    │   └── ΕΡΜΗΝΕΙΑ/
    │       ├── ΠΡΟΟΙΜΙΟΝ.txt      ← prologue
    │       └── ΚΕΦΑΛΑΙΟΝ_01_Αʹ.txt … ΚΕΦΑΛΑΙΟΝ_28_ΚΗʹ.txt
    ├── ΚΑΤΑ_ΜΑΡΚΟΝ/  (ΒΙΟΣ + ΤΑ_ΚΕΦΑΛΑΙΑ + ΕΡΜΗΝΕΙΑ/ 16 kephalaia)
    ├── ΚΑΤΑ_ΛΟΥΚΑΝ/  (ΤΑ_ΚΕΦΑΛΑΙΑ + ΕΡΜΗΝΕΙΑ/ 24 kephalaia)
    └── ΚΑΤΑ_ΙΩΑΝΝΗΝ/ (ΒΙΟΣ + ΕΡΜΗΝΕΙΑ/ 21 kephalaia; ch1–7 from PG_123, ch8–21 from PG_124)
```
- Filenames keep **Greek numerals** (`ΚΕΦΑΛΑΙΟΝ_05_Εʹ`), with a zero-padded index for sort order.
- **John spans both volumes:** chapters 1–7 come from `PG_123.txt`, chapters 8–21 from `PG_124.txt` (stopping before the Pauline epistles).

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
4. **Isolated lemmata + computed verse coverage** by matching each chapter against the **Textus Receptus** (not the unreliable `«»` marks): **3,694 lemmata, 97.8% of TR verses located** (`sectioned/lemmata_index.json`). See §5 of the translate skill.
5. **Wrote the translation methodology** as a reusable skill (see below). Translation itself has **not started** — pilot pending on Matthew Εʹ.

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
| `segment_lemmata.py` | match chapters vs. Textus Receptus → regenerate `lemmata_index.json` |

Rerun `segment_lemmata.py` after any edit to the Greek to refresh the lemma/verse index.

## 6. Key reference files
- **`sectioned/MANIFEST.json`** — per-chapter source file, start line, page, boundary confidence.
- **`sectioned/CLEANUP.md`** — OCR cleanup status; what's done and the remaining (manual) long tail.
- **`sectioned/lemmata_index.json`** — per chapter: `verses_covered`, `range`, and `lemmata` (`{verse, char, score, preview}`).
- **`.claude/skills/translate-theophylact/SKILL.md`** — the binding translation methodology (formal-equivalence, italic supplied words, translate-his-Greek-not-the-English-Bible, footnote ambiguity, sibling `.en.md` output, two-pass verification). `translation-methodology.md` here is a pointer to it.

## 7. Status & next step
- ✅ Corpus fetched, sectioned (89 chapters), structurally cleaned, lemma/verse indexed.
- ◐ Body-text OCR: conservative pass done; long tail remains (non-blocking).
- ☐ **Translation: not started.** Next action = the **Matthew Εʹ (Beatitudes) pilot** under the `translate-theophylact` skill, then scale.
