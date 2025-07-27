# Scripture Texts Documentation

This directory contains biblical texts in various languages and translations. All texts are formatted with `chapter:verse` followed by the text content.

## Directory Structure

```
texts/
└── scripture/
    ├── english/
    │   ├── kjv/        # King James Version (New Testament)
    │   └── brenton/    # Brenton Septuagint (Old Testament + Deuterocanon)
    └── greek/
        └── textus_receptus/  # Greek New Testament
```

## English Translations

### King James Version (KJV)
- **Location**: `scripture/english/kjv/`
- **Content**: 27 New Testament books
- **Source**: [bible-api.com](https://bible-api.com)
- **Format**: Plain text, `chapter:verse text`
- **License**: Public Domain
- **Total Verses**: ~7,957

### Brenton Septuagint Translation
- **Location**: `scripture/english/brenton/`
- **Content**: 54 books (39 Old Testament + 15 Deuterocanonical)
- **Source**: [eBible.org](https://ebible.org/eng-Brenton/)
- **Downloaded**: July 2025 HTML version
- **Format**: Plain text, `chapter:verse text`
- **License**: Public Domain
- **Total Verses**: ~23,000+
- **Includes Deuterocanonical books**:
  - Tobit, Judith, Wisdom of Solomon, Sirach (Ecclesiasticus)
  - Baruch, Letter of Jeremiah
  - Additions to Daniel (Prayer of Azariah, Susanna, Bel and the Dragon)
  - 1-4 Maccabees
  - Prayer of Manasseh
  - 1 Esdras

## Greek Texts

### Septuagint (Greek Old Testament)
- **Location**: `scripture/greek/septuagint/`
- **Content**: Greek Old Testament books with chapter/verse structure
- **Source**: [Apostoliki Diakonia](https://apostoliki-diakonia.gr/)
- **Format**: Individual verse files in chapter folders (e.g., `genesis/1/1.txt`)
- **License**: Greek Orthodox Church
- **Encoding**: Unicode UTF-8 (converted from ISO-8859-7)
- **Books Successfully Fetched** (38 books):
  - **Torah**: Genesis (50 ch), Exodus (40 ch), Leviticus (27 ch), Numbers (36 ch), Deuteronomy (34 ch)
  - **Historical**: Joshua (24 ch), Judges (21 ch), Ruth (4 ch), Nehemiah (13 ch)
  - **Deuterocanonical**: Tobit (14 ch), Judith (16 ch), Esther (10 ch)
  - **Wisdom**: Psalms (150 ch), Job (42 ch), Proverbs (29 ch), Ecclesiastes (12 ch), Song of Songs (8 ch), Wisdom (19 ch), Sirach (51 ch)
  - **Major Prophets**: Isaiah (66 ch), Jeremiah (52 ch), Lamentations (5 ch), Ezekiel (48 ch), Daniel (14 ch)
  - **Minor Prophets**: Hosea (14 ch), Joel (4 ch), Amos (9 ch), Obadiah (1 ch), Jonah (4 ch), Micah (7 ch), Nahum (3 ch), Habakkuk (3 ch), Zephaniah (3 ch), Haggai (2 ch), Zechariah (14 ch), Malachi (4 ch)
  - **Additional**: Baruch (5 ch), Letter of Jeremiah (1 ch)
- **Note**: Some books (Samuel, Kings, Chronicles, Ezra, Maccabees) may require different URL patterns

### Textus Receptus (Greek New Testament)
- **Location**: `scripture/greek/textus_receptus/`
- **Content**: 27 New Testament books in Unicode Greek
- **Source**: [King James Textus Receptus (KJTR)](https://github.com/Center-for-New-Testament-Restoration/KJTR)
- **Editor**: Alan Bunning, Center for New Testament Restoration (2014)
- **Format**: Plain text, `chapter:verse Greek_text`
- **License**: CC BY 4.0 (Attribution Required)
- **Total Verses**: 7,957
- **Note**: This is the Greek text underlying the King James Version

### Attribution for Greek Textus Receptus
When using the Greek Textus Receptus text, please include the following attribution:
> Text: Alan Bunning, Center for New Testament Restoration (2014)
> Source: https://github.com/Center-for-New-Testament-Restoration/KJTR

## Data Format

All texts follow a consistent format:
```
chapter:verse text_content
```

Example from John 1:1:
- **English (KJV)**: `1:1 In the beginning was the Word, and the Word was with God, and the Word was God.`
- **Greek (TR)**: `1:1 Ἐν ἀρχῇ ἦν ὁ Λόγος, καὶ ὁ Λόγος ἦν πρὸς τὸν Θεόν, καὶ Θεὸς ἦν ὁ Λόγος.`

## Fetch Scripts

The scripts used to download these texts are located in `/scripts/`:
- `fetch-kjv-simple.py` - Downloads KJV New Testament
- `parse-brenton-html.py` - Parses Brenton Septuagint from eBible HTML
- `fetch-greek-unicode-tr.py` - Downloads Unicode Greek Textus Receptus

## Usage Notes

1. All texts are UTF-8 encoded
2. Greek texts use proper Unicode characters (not transliteration)
3. Each book is in its own directory with a `.txt` file named after the book
4. Some single-chapter books in KJV may have incomplete verses due to API limitations

## Updates and Maintenance

- KJV texts fetched via bible-api.com API
- Brenton texts parsed from eBible.org HTML downloads
- Greek TR downloaded from GitHub (KJTR repository)
- Last updated: July 2025