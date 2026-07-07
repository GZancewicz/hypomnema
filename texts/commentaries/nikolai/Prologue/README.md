# Prologue of Ohrid — Daily Homilies

Homily sections extracted from *The Prologue from Ochrid* by St. Nikolai Velimirovich, one per calendar day (366 including February 29).

- **Source**: https://www.ochrid.org/ via its open-source content repository https://github.com/jaredef/ochrid (`content/<month>/<day>.mdx`, `## HOMILY` section of each day)
- **Extracted**: July 5, 2026

## Layout

- `homilies/<mm>-<month>/<month>_<dd>.md` — one homily per day: heading, bolded homily title, italicized scripture epigraph, body, and any translator footnotes after a `---` separator
- `homilies.json` — full index, sorted by date, with fields: `month`, `day`, `date` (MM-DD), `title`, `epigraph` (plain text), `word_count`, `footnotes`, `file`, `source`, `text` (full homily body)
- `coverage.json` — scripture coverage in the standard commentary format, read by the Commentaries index page: one entry per day whose homily epigraph cites a New Testament verse (232 of 366), ordered by church year (September 1 = id 1), with `start`/`end` verse ranges validated against the KJV text; only Gospel entries (110) are rendered on the page
- `util/generate_coverage.py` — regenerates `coverage.json` from `homilies.json`; includes corrections for two source citation errors (March 8: Philippians 2:7 → 2:8 KJV versification; March 14: Matthew 26:24 → 26:64)
