# Hypomnema Project Instructions

## Project Overview
Hypomnema is a biblical text reader featuring the KJV New Testament with integrated patristic commentary from John Chrysostom (Matthew and John) and Cyril of Alexandria (Luke). The application includes Eusebian canon cross-references and responsive design.

## Key Commands
```bash
# Start the Go server with live reload
cd hypomnema-server
~/go/bin/air

# Build the application
go build -o app

# Run directly without air
go run main.go

# Python scripts for data processing
python scripts/generate_unified_metadata.py   # Generate all commentary metadata
python scripts/verify_kjv_completeness.py     # Verify KJV completeness
python scripts/verify_commentaries_complete.py # Verify commentary metadata
```

## Project Structure
```
/hypomnema-server/      - Go web server (main application)
  main.go              - Server code with all endpoints and logic
  /templates/          - HTML templates (index.html, homily.html)
  /static/             - CSS files (styles.css), favicon
  
/texts/                - All text content
  /scripture/          - Biblical texts
    /new_testament/    - NT books
      /english/kjv/    - KJV text by book/chapter
      /greek/tr/       - Textus Receptus
  /commentaries/       - Patristic commentaries
    /chrysostom/       - John Chrysostom's works
      /matthew/        - Homilies on Matthew
        /homilies/     - Individual homily folders
          /homily_001/ - Each contains metadata.json with footnotes
      /john/           - Homilies on John
        /homilies/     - Individual homily folders
    /cyril/            - Cyril of Alexandria's works
      /luke/           - Sermons on Luke
        /sermons/      - Individual sermon folders
          /sermon_001/ - Each contains metadata.json
  /reference/          - Supporting data
    /eusebian_canons/  - Canon tables and mappings
    /kjv_paragraphs/   - Paragraph divisions

/scripts/              - Python utilities for text processing
  generate_unified_metadata.py - Generate metadata structure for all commentaries
```

## Commentary Metadata Structure

Each commentary has its own folder with standardized `metadata.json` containing:
- Scripture references (correct verse ranges)
- All footnotes for that homily/sermon
- Word count, excerpt, themes
- Author and work information

**The application uses metadata.json for verse references** - no longer extracts from XML/HTML.

### metadata.json format:
```json
{
  "id": 90,
  "roman": "XC",
  "title": "Homily XC",
  "subtitle": "Matthew XC. 27:27",
  "author": "chrysostom",
  "author_full": "John Chrysostom",
  "work": "Homilies on Matthew",
  "scripture_reference": {
    "book": "matthew",
    "start": {"chapter": 27, "verse": 27},
    "end": {"chapter": 28, "verse": 20},
    "display": "Matthew 27:27-28:20"
  },
  "footnotes": {"1": "text...", "2": "text..."},
  "has_footnotes": true,
  "verified": true
}
```

## Development Guidelines
- Server runs on http://localhost:8080
- Uses HTMX for dynamic content loading
- **No comments in code** unless explicitly requested
- **CSS version bumping**: Update `?v=XX` in index.html when changing styles.css
- **Footnote handling**: Use XXXFOOTNOTEREFXXX placeholder to preserve class names
- **Path handling**: Server expects texts at `../texts/` relative to hypomnema-server
- **Responsive breakpoint**: 700px for mobile view
- Never run git commands - user manages git through IDE
- **Metadata is authoritative** - always use metadata.json files for verse references, footnotes, and homily info
- **NEVER calculate or regenerate data that already exists in JSON files** - always use existing JSON data files

## Important Notes
- Footnotes are extracted to JSON to avoid XML parsing on each request
- Homily references use Roman numerals in display but Arabic in URLs
- Cross-Gospel references work via Eusebian canon system
- Server reads PORT from environment (defaults to 8080)
- All static files are served from `/static/` path
- Text files are organized by language/version/book/chapter
- Each chapter is in format: `bookname_##.txt` (e.g., `matthew_01.txt`)

## Coding Rules and Conventions
- Under no circumstance should a commentary's footnote begin with anything other than 1

## Common Tasks

### Adding new commentaries
1. Create folder structure: `/texts/commentaries/[author]/[book]/[homilies|sermons]/`
2. Generate metadata using `generate_unified_metadata.py` as template
3. Each homily/sermon needs a folder with `metadata.json`
4. No code changes needed - app reads metadata structure

### Adding new biblical texts
1. Place files in `/texts/scripture/new_testament/english/kjv/[book]/[chapter]/`
2. Format: `[book]_[chapter].txt` with verses as `[chapter]:[verse] text`

### Updating commentary data
**Regenerate metadata structure:**
1. Edit source files (XML/HTML) if needed
2. Run `python scripts/generate_unified_metadata.py`
3. This creates/updates all metadata.json files with:
   - Correct verse references
   - All footnotes included
   - Word counts and excerpts
4. Restart the server

**Available scripts:**
- `generate_unified_metadata.py` - Generate/update all metadata.json files
- `verify_kjv_completeness.py` - Verify KJV text completeness
- `verify_commentaries_complete.py` - Verify commentary metadata
- `generate_canon_lookup_from_sql.py` - Generate Eusebian canon lookup
- `generate_verse_to_canon_mapping.py` - Generate verse-to-canon mapping

### Debugging commentary references
- Check verse mapping files: `[book]_verse_to_homilies.json` (note plural 's')
- Verify `homily_coverage.json` for passage ranges (all commentary directories)
- Use browser DevTools to inspect `.homily-ref` elements
- Cyril's sermons use negative numbers internally to distinguish from Chrysostom

### Testing responsive design
- Toggle viewport below/above 700px
- Check sidebar behavior (hamburger menu)
- Verify homily panel 50/50 split
- Test footnote hover tooltips

### Deployment checklist for Render
1. Ensure all text files are committed to staging branch
2. Verify go.mod is in hypomnema-server/
3. Check static/styles.css is committed
4. Root Directory: `hypomnema-server`
5. Build Command: `go build -o app`
6. Start Command: `./app`

## Current Features
- KJV New Testament with chapter navigation
- John Chrysostom's 90 homilies on Matthew and 88 homilies on John
- Cyril of Alexandria's 153 sermons on Luke (manuscript contains only fragments for 154-156)
- Minimal blue markers in right margin for commentary references
- Custom hover tooltips showing homily/sermon numbers
- Split-screen commentary viewing (50/50 layout)
- Footnotes with hover tooltips (Chrysostom only)
- Cross-Gospel homily references via Eusebian canons (Matthew and John homilies appear in Mark/Luke)
- Responsive design with mobile hamburger menu
- Eusebian canon numbers with parallel passage tooltips
- Unified commentary system using common data structures

## Server Startup Reminders
- User should always start/restart server
- User should always execute git commands
- Let user start and stop server

## Workflow Guidelines
- When fixing an issue do not report issue as resolved until you can curl to the page being worked on and confirm it
- When troubleshooting, when a hypothesis arises test hypothesis to ensure that it is in fact true.  Don't just start coding based on unvalidated assumptions.
- When troubleshooting, consider all possible root causes.  Don't just hypothesize one and assume it is actually the root cause or the sole root cause
- Before reporting that an issue is fixed, the fix(es) should be tested to the extent possible