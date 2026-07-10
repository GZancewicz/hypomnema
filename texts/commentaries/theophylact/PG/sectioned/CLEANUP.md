# Theophylact PG 123–124 — OCR Cleanup Status

Cleanup tracker for the sectioned Greek text under `sectioned/`. Source: CGPG OCR of Migne PG 123–124. Chapter boundaries verified against each chapter's *titlos*.

**Current state (verified by `scripts/scan_pg_noise.py`):**

```
header-issues=0  latin-caput=0  orphan-numerals=0  runhead-noise=0
```

---

## ✅ 1. Chapter headers — DONE

All 89 kephalaion files now begin with exactly `ΚΕΦΑΛ. <numeral>.` (matching the filename). 45 garbled/wrong-numeral headers corrected in place; 5 header-lost chapters (Mt 21, Mt 28, Mk 1, Lk 3, Jn 17) had a correct header **prepended** above their surviving titlos/lemma. Applied via `scripts/fix_pg_headers.py --apply`.

## ✅ 2. Inline noise removed — DONE

Removed via `scripts/strip_pg_noise.py --apply` (content verified against backup — 0 commentary text lost):

- **42** Latin `CAPUT` running-heads (`ΟΑΡΟΤ ΧΧ` etc.) — deleted (3 of them became proper headers in §1).
- **5** orphan Latin numerals (`Χvi.`, `ΧΙiΙ.`, `vii` …) — deleted.
- **4** Greek page-top running-heads bled into chapter bodies (`ΛΡΧΙΕΠΙΣΚΟΠΟΥ ΒΟΥΛΓΑΡΙΑΣ`, `Θεοφυλάκτου` …) — deleted.

## ✅ 4. Front-matter header typos — DONE

- `ΚΑΤΑ_ΛΟΥΚΑΝ/…/ΠΡΟΟΙΜΙΟΝ.txt` — `ΠΡΟΟΙΙΟΝ` → `ΠΡΟΟΙΜΙΟΝ`
- `ΚΑΤΑ_ΜΑΤΘΑΙΟΝ/ΤΑ_ΚΕΦΑΛΑΙΑ.txt` — `ΕΥΑΓΓΕΛΙΟΨ` → `ΕΥΑΓΓΕΛΙΟΝ`
- `ΚΑΤΑ_ΛΟΥΚΑΝ/ΤΑ_ΚΕΦΑΛΑΙΑ.txt` — `ΕΡΜΗΝΕΙΑ ΕΓΣ ΤΟ ΚΑTΑ` → `ΕΡΜΗΝΕΙΑ ΕΙΣ ΤΟ ΚΑΤΑ`; deleted stray `ΒΦ ΡΑΕΦΑΤΙΟ` (Latin *PRAEFATIO*)
- `ΚΑΤΑ_ΜΑΡΚΟΝ/ΤΑ_ΚΕΦΑΛΑΙΑ.txt` — `ΤΑ ΚΕΦΑΛΑΙΑΤΟΥ ΚΑΤΑ ΜΑΡΚΟΝΕΥΑΙΓΕΑΙΟΥ` → `ΤΑ ΚΕΦΑΛΑΙΑ ΤΟΥ ΚΑΤΑ ΜΑΡΚΟΝ ΕΥΑΓΓΕΛΙΟΥ`

## ◐ 3. Medium-confidence boundaries — VERIFIED (construction-time)

The 5 header-lost chapters (Mt 21, Mt 28, Mk 1, Lk 3, Jn 17) were each pinned by matching **both** the titlos and the opening-verse lemma against the expected Gospel chapter, and now carry a prepended header. Considered sound. Re-open only if a spot-read shows bleed from the previous chapter's tail.

## ◐ 5. Global body-text OCR — CONSERVATIVE PASS DONE; long tail remains

**Done:** 65 high-frequency *non-word* corruptions fixed via `scripts/fix_pg_body_conservative.py --apply` (whole-token, context-aware casing): `Ιερὶ/ερὶ/Ζερὶ/…`→`Περὶ/περὶ`, `Ἰλσοῦ/Ἰησους`→`Ἰησοῦ(ς)`, `Χριστου`→`Χριστοῦ`. Verified: Greek-token count unchanged, only spellings altered.

**Deliberately NOT auto-fixed (unsafe):** the long tail of scattered errors. Edit-distance analysis showed most near-neighbors are *valid* inflections or minimal pairs (`οἶνον`/`οἶκον` = wine/house, `κακὸν`/`καλὸν` = evil/good), so blind correction would inject errors into an already ~99%-accurate text. Remaining fixes need a Greek morphological analyzer/spellchecker or human review — not a find/replace.

Original pending note: pervasive character-level scan errors remain in the commentary body (does not block using the corpus). Recurring patterns for a scripted frequency-list pass:

- `Περὶ` → `Ζερὶ` / `ἱερὶ` / `Ιερὶ` / `ερὶ`  (e.g. Jn 17 titlos still reads `ἵερὶ τῆς προσευχῆς`)
- `Ἰησοῦ(ς)` → `Ἰλσοῦ(ς)` / `Ἐησοῦ`
- stray mid-word capitals (`Κ`, `Ζ`); broken guillemet lemmata `«…»`; Latin `i`/`v` glyphs inside Greek words

**Approach:** frequency list of non-lexicon tokens → fix top recurring by rule → leave the long tail.

---

## Scripts (in `scripts/`)

- `scan_pg_noise.py` — reports remaining counts (run anytime; single source of truth).
- `strip_pg_noise.py [--apply]` — removes §2 noise (dry-run without `--apply`).
- `fix_pg_headers.py [--apply]` — normalizes §1 headers from filenames (dry-run without `--apply`).
- `_pg_common.py` — shared detectors.

All three are idempotent and re-runnable. A pre-edit backup was taken during the first run.
