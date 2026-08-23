# Brenton Septuagint — HTML scrape (July 2025) — SUPERSEDED

**Do not use this text.** It is retained only for diffing against the current
build in `../usfm/`, and can be deleted once nothing references it.

## What is wrong with it

Brenton marks translator-supplied words the way the KJV uses italics — `\add`
spans in USFM, square brackets in eBible's plain-text editions. The extractor
that produced this tree truncated every verse at the first such span and
discarded the remainder of the line.

    Genesis 1:1    In                    → In the beginning God made the heaven and the earth.
    Genesis 2:4    This                  → This is the book of the generation of heaven and earth…
    Psalm 22:1     A Psalm of David.     → A Psalm of David. The Lord tends me as a shepherd, and I shall want nothing.
    1 Chron 1:1    Adam                  → Adam, Seth, Enos,
    Exodus 12:37   …departed to          → …to the full number of six hundred thousand footmen, even men, besides the baggage.

5,936 of 29,374 verses (20.2%) end mid-clause with no punctuation. The loss is
unrecoverable from these files — the missing text was never written to disk.

`prayer_of_azariah/` is not a real book. It is a byte-identical copy of
`daniel/`, another artifact of the same fetch, which is why this tree shows 54
books where the source has 53.

## Provenance

- **Source**: [eBible.org](https://ebible.org/eng-Brenton/) `eng-Brenton`, HTML edition
- **Fetched**: July 2025
- **Fetch script**: not preserved. `texts/README.md` refers to download scripts
  in `scripts/`, but none for Brenton survives, so this build cannot be
  reproduced or its extractor inspected.

The eBible source text is sound; only this extraction was defective. The
replacement in `../usfm/` parses eBible's USFM edition instead.

## Format

One file per book, `<book>/<book>.txt`, one verse per line as
`chapter:verse text`. No chapter subdirectories — unlike `../usfm/`, which
mirrors the KJV New Testament layout.
