# Brenton Septuagint

English translation of the Greek Septuagint by Sir Lancelot C. L. Brenton (1851),
including the deuterocanonical books. Public domain.

Two builds live here, both from [eBible.org](https://ebible.org/eng-Brenton/)'s
`eng-Brenton` but from different source formats. They are not interchangeable.

| | `usfm/` | `html-2025-07/` |
|---|---|---|
| Status | **current** | superseded, do not use |
| Source format | USFM | HTML |
| Fetched | 2026-08-23 | July 2025 |
| Books | 53 | 54 (one is a duplicate) |
| Verses | 29,004 | 29,374 |
| Verses ending mid-clause | 0.3% | 20.2% |

## Use `usfm/`

`usfm/` is the good text. It follows the KJV New Testament conventions — plain
text, one verse per line as `chapter:verse text`, a per-chapter file under `NN/`
alongside a whole-book file:

    usfm/genesis/genesis.txt          all 50 chapters
    usfm/genesis/01/genesis_01.txt    chapter 1

Built by `scripts/parse_brenton_usfm.py` from the USFM files kept in
`usfm/src/`. See `usfm/README.md` for parsing decisions and verification.

## Why the HTML build was replaced

Brenton marks translator-supplied words with `\add` in USFM — the same thing the
KJV prints in italics. The 2025 HTML scrape truncated each verse at the first
such span, discarding the rest of the line. Genesis 1:1 reads `In`; Psalm 22:1
loses "The Lord tends me as a shepherd". About a fifth of all verses lost text.

The underlying eBible text was never at fault — only that extraction was.

`html-2025-07/` is kept for diffing against the new build and can be deleted
once nothing references it.
