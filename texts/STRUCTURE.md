# Commentary Structure Documentation

## Required Folder Structure

All commentaries must follow this standardized structure:

```
/texts/commentaries/[author]/[book]/
├── content/           # Main content directory
│   ├── 001/          # Each homily/sermon numbered with 3 digits
│   │   ├── metadata.json           # Metadata with scripture references
│   │   ├── content.json            # Actual text content
│   │   └── scripture_references.json # Footnote-to-scripture mapping
│   ├── 002/
│   └── ...
├── source/           # Original source files (XML, HTML, etc.)
├── scripts/          # Processing scripts specific to this commentary
├── coverage.json     # Maps scripture passages to homilies/sermons
└── verse_mapping.json # Maps individual verses to homilies/sermons
```

## Required JSON File Formats

### metadata.json
```json
{
  "id": 1,
  "roman": "I",
  "title": "Homily I",
  "subtitle": "Matthew 1:1",
  "author": "chrysostom",
  "author_full": "John Chrysostom",
  "work": "Homilies on Matthew",
  "scripture_reference": {
    "book": "matthew",
    "start": {"chapter": 1, "verse": 1},
    "end": {"chapter": 1, "verse": 1},
    "display": "Matthew 1:1"
  },
  "themes": [],
  "date_delivered": null,
  "word_count": 6287,
  "excerpt": "Brief excerpt...",
  "source_file": "source_filename.xml",
  "extraction_method": "div2",
  "has_footnotes": true,
  "footnotes": {
    "1": "Footnote text...",
    "2": "Another footnote..."
  },
  "verified": true
}
```

### content.json
```json
{
  "title": "Homily I",
  "subtitle": "Matthew 1:1",
  "paragraphs": [
    {
      "number": 1,
      "text": "Paragraph text..."
    },
    {
      "number": 2,
      "text": "Next paragraph..."
    }
  ]
}
```

### scripture_references.json
```json
{
  "1": ["John 14:26", "Matthew 5:17"],
  "2": [],
  "3": ["Luke 2:14"]
}
```

### coverage.json
```json
{
  "1": {
    "start": {"chapter": 1, "verse": 1},
    "end": {"chapter": 1, "verse": 1}
  },
  "2": {
    "start": {"chapter": 1, "verse": 2},
    "end": {"chapter": 1, "verse": 17}
  }
}
```

### verse_mapping.json
```json
{
  "1": {
    "1": [1],
    "2": [2],
    "3": [2],
    ...
  },
  "2": {
    "1": [3, 4],
    ...
  }
}
```

## Adding New Commentaries

1. Create the folder structure following the pattern above
2. Place source files in the `source/` directory
3. Create extraction scripts in `scripts/` to:
   - Extract content to `content.json` files
   - Generate `metadata.json` with scripture references
   - Create `scripture_references.json` mapping footnotes to verses
   - Generate `coverage.json` and `verse_mapping.json`
4. All homily/sermon folders must use 3-digit numbering (001, 002, etc.)
5. No special-case handling in the server code - all commentaries use the same structure

## Important Notes

- **Never** use book-specific prefixes in JSON filenames (e.g., not `matthew_verse_mapping.json`)
- **Always** use standardized names: `verse_mapping.json`, `coverage.json`
- **Content numbering** starts from 001 and uses 3 digits
- **Footnotes** must start from "1" in each homily/sermon
- **Server expectations**: The Go server expects all files at these exact paths with these exact structures

## Server Content Extraction

The server uses a unified function for all commentaries:
```go
extractHomilyFromContent(author, book string, homilyNum int)
```

This function expects:
- Path: `../texts/commentaries/[author]/[book]/content/[3-digit-number]/content.json`
- No special handling for different authors or books
- All content in the same JSON structure