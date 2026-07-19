---
name: add-synaxarion-reference
description: Attach a Synaxarion "Life of X" citation to one or more specific New Testament verses, linking each verse's marker to a saint's Life from a synaxarion/calendar day. Use when the user gives a verse (or list of verses), a saint's name, and a calendar date — e.g. "Add a Zacharias citation to Luke 1:5, Luke 1:12 and Mt 23:35, link to 9/5."
---

# Add Synaxarion Reference

Given **verse(s)**, a **saint's name**, and a **calendar date**, register a Synaxarion
citation so each of those verses shows a blue marker in the reader. Clicking the marker
opens that saint's Life (the `text` from the day's `commemorations.json`) in the side
panel, with the Priest Stephen Janos attribution at the bottom.

All the mechanical work is done by the deterministic helper `add_citation.py` — no
codebase search or exploration is needed per run.

## The one command

```bash
python3 .claude/skills/add-synaxarion-reference/add_citation.py \
  --verse "matthew 18:2" --date 12-20 --saint "Ignatius of Antioch"
```

Multiple verses in a single call:

```bash
python3 .claude/skills/add-synaxarion-reference/add_citation.py \
  --date 9/5 --saint "Zacharias" \
  --title "Life of the Holy Prophet Zacharias" \
  --verses "mt 23:35, lk 1:5, lk 1:12, lk 1:13, lk 1:18, lk 1:21, lk 1:40, lk 1:59, lk 1:67, lk 3:2, lk 11:51"
```

## Per-run steps

1. From the user's message, pull out: the **verse(s)**, the **saint name**, and the
   **date**. (No file reading needed for this.)
2. Run `add_citation.py` once with `--dry-run` to preview, then again to write.
3. Relay the printed JSON summary and remind the user to **restart the server** (they
   manage it) so the new markers load.

That's the whole loop — one script call, minimal tokens.

## Helper reference: `add_citation.py`

| Flag | Meaning |
|------|---------|
| `--verse` | one verse, e.g. `"matthew 18:2"` (accepts `mt`/`mk`/`lk`/`jn`, `:` or `.`) |
| `--verses` | comma/semicolon list, e.g. `"lk 1:5, lk 1:12, mt 23:35"` |
| `--date` | calendar day: `12-20`, `12/20`, or `"December 20"` (required) |
| `--saint` | saint name, matched against that day's commemorations and used to build the title (required) |
| `--title` | override the marker title (default `"Life of <saint>"`) |
| `--index` | commemoration index within the day (default: auto-match `--saint`) |
| `--dry-run` | print the summary, write nothing |

### Behavior

- Writes/updates one entry in `texts/commentaries/synaxarion/coverage.json`. Re-running
  with the same **date + index + title** merges the new verses into the existing entry
  (deduping) instead of creating a duplicate.
- Resolves the commemoration index by matching `--saint` (case-insensitive substring) in
  the day's `commemorations.json`. If it matches **zero or several** commemorations, the
  script stops and prints the numbered list — pass `--index N` to pick.
  - Watch spelling: e.g. Sept 5 is titled "Zachari**ah**"; searching "Zachari**as**"
    won't match, so pass `--index` (or the exact spelling).
- The `saint` and `date` fields are auto-filled from the calendar day; the marker title
  comes from `--title`/`--saint`.

## Requirements

- The calendar day folder must exist under
  `synaxarion/calendar/<MM-Month>/<MM-DD>/commemorations.json`. If it doesn't, the script
  says so — populate it first with the `orthodox-calendar` skill, then re-run.
- No server or code changes are needed to add citations; `main.go` reads
  `coverage.json` at startup (see the synaxarion
  [README](../../../texts/commentaries/synaxarion/README.md) for the data model).
