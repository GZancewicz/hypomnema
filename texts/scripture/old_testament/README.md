# Old Testament Texts

This directory contains Old Testament (Hebrew Bible/Septuagint) texts in various languages and versions.

## Current Contents

### English
- **brenton/**: Brenton's English translation of the Septuagint (1851), including
  the deuterocanonical books. Based on the Greek Septuagint rather than the
  Hebrew Masoretic Text.
  - Use **`brenton/usfm/`** — 53 books, 29,004 verses, built from eBible.org's
    USFM edition and laid out like the KJV New Testament (`genesis/genesis.txt`
    plus `genesis/01/genesis_01.txt`).
  - `brenton/html-2025-07/` is an earlier HTML scrape that truncated ~20% of
    verses. Superseded — do not use. See `brenton/README.md`.

### Greek
- **apostoliki_diakonia/**: Greek Septuagint text from apostoliki-diakonia.gr
  - 68% complete (34 of 50 books fully fetched)
  - See the README in that directory for detailed status

## Book Organization

Each version maintains its own book naming and organization scheme:

- **Brenton**: Uses traditional English book names (genesis, exodus, etc.)
- **Apostoliki Diakonia**: Uses transliterated Greek names (Genesis, Exodos, etc.)

## Septuagint vs Masoretic Differences

The texts here primarily follow the Septuagint tradition, which includes:
- Additional books (Tobit, Judith, 1-4 Maccabees, etc.)
- Different book order
- Textual variations from the Hebrew Masoretic Text
- Different chapter/verse divisions in some books

## Known Gaps

- The Greek AD text is missing 12 books outright (Kingdoms, Chronicles, Esdras,
  Maccabees) and 4 more are missing individual chapters. Every one of those
  books *is* present in English in `brenton/usfm/`.
- Brenton's footnotes and cross-references are not carried into the text files,
  matching the New Testament convention. The USFM sources in
  `brenton/usfm/src/` retain them if an apparatus is ever wanted.

## Future Additions

Potential additions to this directory:
- Hebrew Masoretic Text
- Hebrew Dead Sea Scrolls variants
- Additional English translations
- Latin Vulgate Old Testament
- Other ancient versions