# Hypomnema REST API — Implementation Plan

## Goal

Expose two public JSON endpoints from the existing `hypomnema-server` web app:

1. **Coverage lookup** — given a Bible reference (`book`, `chapter`, `verse`, where
   `book` accepts a full name **or** a recognized abbreviation), return every
   patristic commentary that covers that verse.
2. **Commentary retrieval** — given a commentary ID, return the actual commentary
   content the app renders (the same text served today at `/api/homily/...`).

These live inside the current Go server (no new binary). They reuse the data that
is already loaded into memory at startup, so this is mostly wiring, not new logic.

This plan is the HTTP-API counterpart to `MCP_SERVER_PLAN.md`. The two share one
data model; see [Relationship to the MCP plan](#relationship-to-the-mcp-plan).

## What already exists (verified 2026-07-09)

The server does almost everything these endpoints need. Key facts from `main.go`:

- **In-memory commentary index.** `init()` loads all commentaries into two globals:
  - `commentaries map[string]*Commentary`, keyed `"<author>-<book>"` (e.g.
    `chrysostom-matthew`, `cyril-luke`, `nikolai-prologue`, `synaxarion-matthew`).
    Each `*Commentary` holds `VerseToHomily` (`"ch:vs"` → `[]Homily`) and
    `Coverage map[int]HomilyRange` (id → verse span). These are the Tier‑1 /
    verse-mapped works.
  - `unavailableWorks []UnavailableWork` — the Tier‑2 works (Gregory, Bede,
    Maximos, Theophylact) that ship coverage ranges but no readable text. Each has
    `Author`, `Work`, and `Ranges []HomilyRange`.
- **Range containment helpers** already exist:
  `coverageContains(HomilyRange, chapter, verse)` and
  `coveringHomilyIDs(coverage, chapter, verse)` (`main.go:1091`, `:1104`).
- **Content rendering** already exists: `extractHomilyFromContent(author, book, num)`
  (`main.go:1670`) reads `content/NNN/content.json` and returns the HTML the app
  injects; `homilyAPIHandler` (`main.go:1896`) is the current
  `/api/homily/<author>/<book>/<num>` handler that wraps it.
- **`HomilyRange`** carries `ID, Roman, Title, Date, Saint, Start{Book,Chapter,Verse},
  End{Book,Chapter,Verse}` — everything an API response needs.

### Gaps to fill

1. **No book-name normalizer.** Only ad-hoc Gospel abbreviation maps exist inline
   (`main.go:366, 1356, 2464`). We need one canonical `normalizeBook()` covering
   full names + common abbreviations.
2. **`coverageContains` ignores the `book` field.** For single-Gospel works that is
   fine, but multi-Gospel works (Gregory, Bede) store entries across all four
   Gospels in one coverage map. A raw `coveringHomilyIDs` call would match
   `12:46` in *any* Gospel. The API request names a book, so the coverage endpoint
   **must** filter on `HomilyRange.Start.Book` when that field is present.
3. **Tier‑2 works are in a separate slice** (`unavailableWorks`), not in
   `commentaries`. The coverage scan must walk both.
4. **No JSON API surface.** Existing `/api/*` routes return HTML fragments for
   HTMX. New endpoints go under a versioned `/api/v1/` prefix to avoid collision
   and signal "machine-readable, stable contract."

## Endpoint 1 — Coverage lookup

```
GET /api/v1/coverage?book={name|abbr}&chapter={int}&verse={int}
GET /api/v1/coverage?ref={free-form reference}      # convenience, e.g. ?ref=John+3:16
```

- `book` accepts full names (`Matthew`, `1 Corinthians`), directory slugs
  (`matthew`, `1corinthians`), and abbreviations (`Mt`, `Matt`, `Jn`, `1 Cor`,
  `1Co`). Case-insensitive, whitespace-tolerant.
- `ref` is an optional single-string alternative parsed into book/chapter/verse
  (e.g. `John 3:16`, `jn 3.16`, `1 cor 13:4`). If both forms are supplied, explicit
  params win.
- Unknown book → `400` with a message listing valid names. A book in the NT but
  with no commentary coverage → `200` with an empty `results` array (not an error).

### Response

```json
{
  "query": { "book": "john", "book_display": "John", "chapter": 3, "verse": 16 },
  "count": 2,
  "results": [
    {
      "commentary_id": "chrysostom/john/28",
      "author": "chrysostom",
      "author_full": "John Chrysostom",
      "work": "Homilies on John",
      "work_slug": "john",
      "id": 28,
      "roman": "XXVIII",
      "title": "Homily XXVIII",
      "covers": "John 3:12-21",
      "match_type": "primary",
      "text_available": true
    },
    {
      "commentary_id": "gregory_the_great/forty-gospel-homilies/...",
      "author": "gregory_the_great",
      "author_full": "Gregory the Great",
      "work": "Forty Gospel Homilies",
      "id": 12,
      "roman": "XII",
      "title": "Homily XII",
      "covers": "John 3:...",
      "match_type": "range",
      "text_available": false
    }
  ]
}
```

Per-result fields:

- **`commentary_id`** — the canonical ID consumed by Endpoint 2. Format
  `"<author>/<work_slug>/<id>"`, which mirrors the app's own
  `/api/homily/<author>/<book>/<num>` route. For works whose on-disk directory
  name has spaces (Gregory, Bede, Maximos), `work_slug` is a stable slugified
  form (`forty-gospel-homilies`) resolved back to the real path server-side.
- **`match_type`** — `"primary"` for an exact `verse_mapping.json` hit,
  `"range"` for a coverage-range containment hit. Deduplicated by
  `(author, work, id)`; prefer `primary` when both fire.
- **`covers`** — human-readable span from the `HomilyRange` (`"John 3:12-21"`).
- **`text_available`** — `true` for Tier‑1 (Chrysostom, Cyril), `false` for
  Tier‑2 and for Nikolai (licensing — text on disk but not distributable).
- **`date` / `saint`** — included only for calendar-dated works (Nikolai
  Prologue, Synaxarion) from `HomilyRange.Date` / `.Saint`.

### Lookup algorithm

1. `normalizeBook(book)` → slug, or `400`.
2. For each entry in `commentaries` and each Tier‑2 work in `unavailableWorks`:
   - If the work is single-book, skip unless its book matches the query book.
   - For multi-Gospel works, iterate `Ranges`/`Coverage` and keep entries whose
     `Start.Book == queryBook` (guard added per Gap #2) that also satisfy
     `coverageContains(range, chapter, verse)`.
   - When a `VerseToHomily["ch:vs"]` entry exists, tag those IDs `primary`;
     tag remaining range hits `range`.
3. Build result objects; set `text_available` per tier (hard-code Nikolai =
   false); attach `date`/`saint` where present.
4. Sort deterministically (by author, then work, then id) and dedupe.

Almost all of this is a thin loop over existing globals plus the book-filter
guard — no new file I/O on the hot path.

## Endpoint 2 — Commentary retrieval

```
GET /api/v1/commentary/{author}/{work}/{id}
GET /api/v1/commentary/{author}/{work}/{id}?format=html
GET /api/v1/commentary/{author}/{work}/{id}?paragraph_start={n}&paragraph_end={n}
```

`{author}/{work}/{id}` is exactly the `commentary_id` returned by Endpoint 1
(e.g. `/api/v1/commentary/chrysostom/matthew/26`).

### Response (default `format=json`)

```json
{
  "commentary_id": "chrysostom/matthew/26",
  "author": "chrysostom",
  "author_full": "John Chrysostom",
  "work": "Homilies on Matthew",
  "id": 26,
  "roman": "XXVI",
  "title": "Homily XXVI",
  "subtitle": "Matthew 8:5",
  "covers": "Matthew 8:5-13",
  "paragraphs": ["<paragraph html>", "..."],
  "total_paragraphs": 42,
  "footnotes": { "1": "text…", "2": "text…" },
  "text_available": true
}
```

- **`paragraphs`** come straight from `content/NNN/content.json` — the same source
  `extractHomilyFromContent` reads, so the text is identical to what the app shows.
  Footnote markers use the app's `XXXFOOTNOTEREFXXX`/`[n]` convention; the
  `footnotes` map (from `metadata.json`) is the appendix.
- **`?format=html`** returns the exact HTML fragment `homilyAPIHandler` produces
  today (`<div class="chapter-text">…</div>`), for callers that want to drop the
  app's rendering straight into a page. Recommended: refactor the HTML-building
  tail of `homilyAPIHandler` into a shared helper both handlers call, so the two
  never drift.
- **`?paragraph_start`/`paragraph_end`** — optional 1-based slice for paging long
  homilies (a Chrysostom homily is ~5,500 words). Out-of-range indices clamp.
- **Tier‑2 / Nikolai** → `404` with
  `{"error": "text_not_available", "message": "Full text for <work> is not included in this dataset; only the citation is available.", "citation": {…}}`,
  echoing the coverage-result citation so the caller still gets author/work/roman/covers.
- Unknown author/work/id → `404`.

## Book-name normalization

Add `books.go` (or a block in `main.go`) with one `normalizeBook(string) (slug, ok)`:

- Canonical slugs match the existing directory names and the `books` slice in
  `main.go:157` (`matthew`…`revelation`).
- Include, per book: full name, no-space slug, and common abbreviation schemes
  (SBL/OSIS/Paratext + colloquial): `Mt/Matt/Matth`, `Mk/Mark`, `Lk/Luke`,
  `Jn/John`, `1 Cor/1Co/1 Corinthians`, `Rev/Apoc`, etc. Numbered books tolerate
  `1 John`, `1John`, `1Jn`, `I John`.
- Lowercase, strip spaces/periods, then map.
- Unknown → `ok=false`; handler returns `400` with the valid-name list.

Note the dataset scope: **scripture** covers the whole NT, but **commentary
coverage** is Gospel-centric (plus Maximos on the Lord's Prayer). A valid non-Gospel
book (e.g. Romans) normalizes fine and simply returns zero coverage results.

## Cross-cutting concerns

- **Routing:** register under `/api/v1/` in `main()` alongside the existing
  `http.HandleFunc` calls (`main.go:628`). Two handlers: `coverageAPIHandler`,
  `commentaryAPIHandler`.
- **Content type & CORS:** `application/json; charset=utf-8`; add permissive
  `Access-Control-Allow-Origin: *` (public-domain data, read-only) plus `GET,
  OPTIONS` handling so browser clients can call it.
- **Errors:** consistent JSON envelope `{"error": "<code>", "message": "..."}`
  with correct status codes (`400` bad book/params, `404` not found / text
  unavailable).
- **Method guard:** `GET`/`OPTIONS` only; others → `405`.
- **No new startup cost:** both endpoints read the already-loaded globals;
  Endpoint 2's only I/O is the lazy `content.json` read it already does per homily.
- **CLAUDE.md rules honored:** metadata/coverage JSON is authoritative; nothing is
  recomputed; footnote numbering (starts at 1) is passed through untouched; the
  user starts/restarts the server and runs all git.

## Implementation phases

### Phase 1 — Book normalizer + coverage endpoint
1. Add `normalizeBook()` with full unit coverage of names/abbreviations.
2. Add the multi-Gospel **book filter** to the coverage scan (Gap #2) — either a
   `coverageContainsBook(range, book, ch, vs)` wrapper or a `book` param threaded
   into a new scan helper. Do **not** change `coverageContains`'s existing callers.
3. Implement `coverageAPIHandler`: parse params/`ref`, scan `commentaries` +
   `unavailableWorks`, dedupe, emit JSON. Register `/api/v1/coverage`.

### Phase 2 — Commentary endpoint
4. Refactor the HTML-assembly tail of `homilyAPIHandler` into a shared helper.
5. Implement `commentaryAPIHandler`: resolve `commentary_id` → path, load
   `content.json` + `metadata.json`, honor `format` and paragraph paging, handle
   Tier‑2/Nikolai citation-only `404`. Register `/api/v1/commentary/`.
6. Resolve `work_slug` ↔ real directory (spaces) via a small slug map built at load.

### Phase 3 — Verification (curl-driven, per CLAUDE.md workflow rules)
7. `curl` each case and confirm against the live app:
   - `John 3:16`, `Matthew 8:5` (Chrysostom, `primary`), `Luke 2:1` (Cyril).
   - A verse only Tier‑2 covers (Bede/Gregory) → `text_available:false`.
   - Multi-Gospel book filter: a `12:46`-style verse that must **not** leak across
     Gospels.
   - Abbreviations: `Jn`, `Mt`, `1 Cor`; bogus book → `400`.
   - Endpoint 2: fetch an ID from Endpoint 1's `commentary_id`; verify JSON
     paragraphs match the app's `/api/homily/...` HTML; verify `?format=html`
     byte-matches the app fragment; verify paging clamps; Tier‑2 → `404` citation.
8. Confirm existing app routes and HTMX behavior are unaffected.

## Relationship to the MCP plan

`MCP_SERVER_PLAN.md` proposes a **separate binary** exposing the same lookups as
MCP *tools*. This REST API and that MCP server answer the same two questions over
the same data. Options, in order of preference:

1. **Ship the REST API first** (this plan) — smaller, in-process, immediately
   usable by the app itself and any HTTP client. Then have the MCP server call
   these HTTP endpoints, so there is one implementation of the lookup logic.
2. Or extract the coverage-scan + normalizer into a small shared package both the
   web server and the MCP binary import. Revisit only if the two start drifting;
   the MCP plan already accepts a re-implementation for now.

Either way, keep response field names aligned across REST and MCP
(`commentary_id`, `covers`, `match_type`, `text_available`, `date`, `saint`) so a
consumer learns one vocabulary.

## Non-goals
- No changes to templates/CSS or existing HTMX endpoints.
- No text extraction or metadata regeneration — existing JSON used as-is.
- No auth in v1 (public-domain, read-only) — same exposure as the website. Add a
  per-IP rate limit if abuse appears; a static bearer token is the fallback.
- Nikolai text is never served (licensing); only its citation/date is returned.

## Decided (2026-07-09)
- **Endpoint 2 default body = JSON paragraphs**; `?format=html` returns the app
  fragment as an opt-in.
- **REST first; the MCP server calls these HTTP endpoints.** One implementation of
  the lookup logic — the MCP plan's re-implementation is superseded by this.

## Open decisions
1. **`work_slug` scheme** for space-containing works — confirm
   `forty-gospel-homilies` style vs. keeping the raw directory name URL-encoded.
2. **Whether to fold non-covering NT books** into `400` vs. empty‑`200` (plan
   assumes empty `200` — a valid book with no Fathers is a real, non-error answer).
