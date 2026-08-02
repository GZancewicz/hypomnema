# Hypomnema

KJV New Testament reader with patristic commentary (Chrysostom, Cyril, Gregory, Bede,
Theophylact) and Eusebian canon cross-references. Go + HTMX, port 8080.

## Task tracking
Shortcut is the board (MCP server `shortcut`, workspace `orthodox-net`). Epics 383
Theophylact, 384 Data quality, 385 Someday. Read it before proposing work; update it in
the change that completes an item. No parallel todo lists — link to the doc with the
detail instead of restating it.

## Communication style
Lead with the answer. Skip preamble, recaps, and summaries of what you just did — the
tool calls are visible. Don't offer next steps unless asked. Yes/no questions get Yes or
No first. Length should fit the question: usually a line or two, more when a short answer
would be wrong.

## Ground rules
- Never run git commands, and never start/stop the server — the user does both.
- No comments in code unless asked.
- Metadata is authoritative. Use existing JSON; never recalculate what a file already
  holds.
- A commentary's footnotes always start at 1.
- Don't call something fixed until you've curled the page and seen it work.
- Test a hypothesis before coding against it, and consider that there may be more than
  one root cause.

## Commands
```bash
cd hypomnema-server && ~/go/bin/air   # live reload
go build -o app                       # build
python scripts/generate_unified_metadata.py    # regenerate all metadata.json
python scripts/verify_kjv_completeness.py
python scripts/verify_commentaries_complete.py
```

## Layout
`hypomnema-server/` is the Go app (main.go holds all endpoints); it expects texts at
`../texts/`. Under `texts/`: `scripture/` (KJV + Greek TR), `commentaries/<author>/<book>/`
(each homily/sermon folder has a `metadata.json` with verse range and footnotes),
`reference/` (Eusebian canons, KJV paragraphs). Chapter files are `matthew_01.txt`, verses
`chapter:verse text`.

Adding a commentary needs no code — create the folder structure and metadata; the app
reads it. Homily numbers are Roman in display, Arabic in URLs. Cyril's sermons use
negative IDs internally to distinguish from Chrysostom.

## Gotchas
- **Cache busting is automatic** — templates use `?v={{.AssetVersion}}` off the
  `styles.css` mtime. Never hardcode a version. Give any new `/static/*.js` the same
  treatment.
- **Footnotes**: XXXFOOTNOTEREFXXX placeholder preserves class names through parsing.
- **`data-refs` is HTML-escaped** — grep curl output for `&#34;range&#34;`, not `"range"`.
- **Verse mapping files are `[book]_verse_to_homilies.json`** — note the plural.
- **Responsive breakpoint is 700px**; commentary panel is a 50/50 split.

### Commentary panel verse range
Server builds `VerseRef.Range` via `formatCoverageRange()` (or `lookupCoverageRange()`
when only a homily ID is known); client applies it through `setHomilyRange()`. Most
`coverage.json` files omit `book` inside `start`/`end`, so `formatCoverageRange()` takes a
fallback book — pass the right one or the range renders empty. Any new commentary link
site must pass the range too: the reader, `/api/index`, `/api/scripture-references`, and
`/api/homilies/`. Synaxarion Lives attach to single verses and intentionally have none.

### Theophylact — served from PG Greek, not `content/`
`extractTheophylactGreek()` reads from `PG/sectioned/` (only lemma 1 was ever built into
`content/`). `theophylactLemmaPaths()` maps id → folder: chapters sorted, then lemmata by
numeric `ΛΗΜΜΑ_NN_` prefix, so index `i` = id `i+1`. Cached at first use.
- Counts by folder (not metadata): Matthew 1124, Mark 526, Luke 1046, John 2332.
- Guillemets are asymmetric — 796 lemmata open `«` unclosed, 250 close `»` unopened. Both
  heads are scripture; leftover strays are OCR noise → curly quotes.
- **Don't reuse `.greek-text`** — it's `display: none` (reader interlinear). Use
  `.greek-commentary`.
- `loadCommentary("theophylact", …)` is currently commented out in main.go, so Theophylact
  shows only in the Commentaries index, not the reader margin (sc-390).

## Deploy (Render)
Root directory `hypomnema-server`, build `go build -o app`, start `./app`. Commit texts
and `static/styles.css` to the staging branch. Google Analytics lives only in main.
