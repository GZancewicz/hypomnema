# Scripture Texts

This directory contains biblical texts organized by testament, language, and version.

## Directory Structure

```
scripture/
├── old_testament/
│   ├── english/
│   │   └── brenton/
│   │       ├── usfm/         # Brenton's Septuagint — current build
│   │       └── html-2025-07/ # superseded scrape, do not use
│   └── greek/
│       └── apostoliki_diakonia/  # Greek Septuagint from apostoliki-diakonia.gr
└── new_testament/
    ├── english/
    │   └── kjv/              # King James Version
    └── greek/
        └── textus_receptus/  # Greek Textus Receptus
```

## Organization Principles

1. **Testament Division**: Top-level separation between Old Testament and New Testament
2. **Language Grouping**: Each testament is subdivided by language (english, greek, hebrew, etc.)
3. **Version Specificity**: Each language contains specific versions or translations

## Current Contents

### Old Testament
- **English**: Brenton's Septuagint Translation — use `brenton/usfm/`
  (53 books, 29,004 verses; `brenton/html-2025-07/` is superseded)
- **Greek**: Apostoliki Diakonia Septuagint (partially complete - see README in that directory)

### New Testament
- **English**: King James Version (complete)
- **Greek**: Textus Receptus (complete)

## File Format

All scripture texts are stored as UTF-8 encoded plain text files for maximum compatibility and preservation.

## Future Additions

This structure allows for easy addition of:
- Hebrew texts (Masoretic Text, Dead Sea Scrolls, etc.)
- Additional English translations (ESV, NASB, NIV, etc.)
- Other ancient versions (Latin Vulgate, Syriac Peshitta, etc.)
- Additional Greek texts (Nestle-Aland, Byzantine, etc.)