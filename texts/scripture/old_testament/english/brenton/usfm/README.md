# Brenton Septuagint — USFM build

English translation of the Greek Septuagint by Sir Lancelot C. L. Brenton (1851).
Public domain.

## Source

- **Publisher**: [eBible.org](https://ebible.org/eng-Brenton/), `eng-Brenton`
- **Format**: USFM (`eng-Brenton_usfm.zip`), retained in `src/`
- **Fetched**: 2026-08-23 (eBible source files dated 12 Dec 2025)
- **Built by**: `scripts/parse_brenton_usfm.py`

## Contents

53 books, 29,004 verses, 1,116 chapter files.

Follows the KJV New Testament conventions: plain text, one verse per line as
`chapter:verse text`, a per-chapter file under `NN/`, and a whole-book file.

    genesis/genesis.txt          all 50 chapters
    genesis/01/genesis_01.txt    chapter 1

## Parsing decisions

- `\add` (9,086 spans) marks translator-supplied words — the KJV prints these in
  italics, eBible's VPL brackets them. The NT text here carries no markup, so the
  markers are stripped and the words kept.
- Footnotes (`\f`, 2,600) and cross-references (`\x`, 150) are dropped, matching
  the NT. Re-parse `src/` to recover them.
- Lettered verses (`\v 18a`, 315 of them) are Septuagint material absent from the
  Hebrew. Kept, and emitted in document order rather than sorted. eBible's VPL
  discards these.
- Proverbs 30:1 is empty in the source — Brenton's LXX orders Proverbs
  differently and the verse is a footnote pointing to chapter 24.

## Verification

Cross-checked verse-by-verse against eBible's independently-generated VPL
edition: 28,689 shared verses, none missing, 2 differences — both cases where
VPL is wrong (Ezekiel 11:7 reads "thiscity"; Sirach 1:1 absorbs the Prologue
heading).

Verses ending mid-clause: 0.3%, all genuine sentence-spanning verse breaks.

## Superseded

`../html-2025-07/` is an earlier scrape of eBible's **HTML** edition (July 2025).
Do not use it. Its extractor truncated every verse at the first `\add` span,
losing text in ~20% of verses — Genesis 1:1 reads `In`, Psalm 22:1 loses "The
Lord tends me as a shepherd". It also contains `prayer_of_azariah/`, a
byte-identical duplicate of `daniel/` rather than a real book.
