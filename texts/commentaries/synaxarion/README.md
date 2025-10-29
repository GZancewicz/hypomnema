# Synaxarion Commentary Directory

This directory contains entries from the Synaxarion (lives of the saints) that reference Gospel passages.

## Special Treatment

Unlike other commentaries in this project, Synaxarion entries have special handling:

### Directory Structure
- Files are stored **directly** in the `synaxarion/` directory (no subdirectories by book)
- `coverage.json` - Contains all synaxarion entries across all books
- `verse_mapping.json` - Maps verses to synaxarion entry IDs

### Data Structure

#### coverage.json
Each entry includes special fields:
- `date` - The liturgical date (e.g., "October 16")
- `saint` - The saint's name and title (e.g., "Holy Martyr Longinus the Centurion")
- `start.book` - The Gospel book (e.g., "matthew")

#### verse_mapping.json
Uses standard verse mapping format:
```json
{
    "27:54": [
        {
            "id": 1,
            "roman": "October 16",
            "type": "primary"
        }
    ]
}
```

### Display Format

**In Commentaries Table:**
- **Father column**: Left blank (empty)
- **Work column**: "Synaxarion"
- **Section column**: `{saint} ({date})` format (plain text, no link)
  - Example: "Holy Martyr Longinus the Centurion (October 16)"

**As Blue Markers:**
- Tooltip: "Synaxarion: {saint} ({date}) ({verse})"
- No click action (informational only)

### Loading in main.go

The server loads synaxarion using:
```go
loadCommentary("synaxarion", "matthew",
    "../texts/commentaries/synaxarion/verse_mapping.json",
    "../texts/commentaries/synaxarion/coverage.json")
```

Note: Only one `loadCommentary` call is needed because all entries are in a single coverage.json file, regardless of which Gospel book they reference.

### Adding New Entries

1. Add entry to `coverage.json` with required fields:
   - `id`, `date`, `saint`, `start`, `end`
2. Add mapping to `verse_mapping.json`:
   - Use "chapter:verse" format as key
   - Use the date as the "roman" field
3. No code changes needed - server reads structure automatically
