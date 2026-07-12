# Synaxarion Commentary Directory

Entries from the Synaxarion (Lives of the Saints) attached to Gospel/NT verses that
mention a commemorated saint. A "Life" appears as a blue marker on **every** verse in its
`verses` list, across any book. Clicking the marker opens the saint's Life (the `text`
from that day's calendar entry) in the side panel.

## coverage.json

Single file, all books. Shape:

```json
{
  "commentary": "Synaxarion",
  "lives": [
    {
      "id": 6,
      "title": "Life of Peter",
      "saint": "The Holy, Glorious and All-praised Leaders of the Apostles, Peter and Paul",
      "date": "June 29",
      "mmdd": "06-29",
      "commemoration_index": 0,
      "verses": [
        {"book": "matthew", "chapter": 4, "verse": 18},
        {"book": "luke", "chapter": 5, "verse": 8}
      ]
    }
  ]
}
```

Fields:
- `id` – unique integer within this file
- `title` – pseudo-commentary label shown in the marker popover (e.g. "Life of Peter")
- `saint` – full commemoration title (auto-filled from `commemorations.json`)
- `date` – display date (auto-filled from the calendar day's `old_style_date`)
- `mmdd` – calendar day, `MM-DD`; links to `synaxarion/calendar/<MM-Month>/<mmdd>/`
- `commemoration_index` – which entry in that day's `commemorations` array to show
- `verses` – every verse the marker appears on (`book` is a lowercase slug)

## Loading in main.go

`loadSynaxarion("../texts/commentaries/synaxarion/coverage.json")` reads all `lives` into
the global `synaxarionLives`. In `formatChapterHTML`, each verse checks every Life's
`verses` list (book-scoped), so a single file drives markers in all books. The marker's
click loads `/api/life/{mmdd}/{commemoration_index}` (`lifeAPIHandler`), which renders the
commemoration's title + text.

## Adding entries

Use the `add-synaxarion-reference` skill (`.claude/skills/add-synaxarion-reference/`): it
runs the NT search for a term, picks the Life from a calendar day, and appends/updates a
`lives` entry. No code changes needed. Restart the server to load new entries.
