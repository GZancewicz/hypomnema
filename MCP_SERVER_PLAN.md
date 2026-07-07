# Hypomnema MCP Server — Implementation Plan

## Goal

Add an MCP (Model Context Protocol) server to this repository that lets AI clients
(Claude Desktop, Claude Code, and any other MCP client) look up patristic commentary
for a requested Bible verse and retrieve the commentary text.

The existing website (`hypomnema-server/`) is untouched. The MCP server is a second,
independent Go binary that reads the same `texts/` data.

## Why this is a small project

The data layer already answers the exact question an MCP client asks:

1. `texts/commentaries/<author>/<work>/coverage.json` — for **every** commentary,
   a `homilies` array of `{id, roman, title, start: {chapter, verse}, end: {chapter, verse}}`
   ranges (book-level works omit `book` in start/end; multi-Gospel works include it).
   This is the universal verse → work index.
2. `texts/commentaries/<author>/<work>/verse_mapping.json` — for the three largest
   commentaries, a precomputed `"chapter:verse"` → `[{id, roman, type}]` map.
3. `texts/commentaries/<author>/<work>/content/NNN/metadata.json` — author, work,
   title, authoritative `coverage` range, excerpt, word count, footnotes.
4. `texts/commentaries/<author>/<work>/content/NNN/content.json` — full text as
   `{title, subtitle, paragraphs}`.

So "what did the Fathers say about John 3:16" is a range scan over coverage.json
plus two file reads. No new data processing is required.

## Data inventory (verified 2026-07-07)

| Commentary | Coverage index | Verse mapping | Local full text |
|---|---|---|---|
| Chrysostom, Homilies on Matthew (90) | ✅ | ✅ | ✅ `content/NNN/` |
| Chrysostom, Homilies on John (88) | ✅ | ✅ | ✅ `content/NNN/` |
| Cyril of Alexandria, Sermons on Luke (~153) | ✅ | ✅ | ✅ `content/NNN/` |
| Nikolai Velimirović, Prologue | ✅ | — | ⚠️ text on disk, but **no distribution rights** — served as reference-only |
| Gregory the Great, Forty Gospel Homilies | ✅ | — | ❌ coverage only |
| Venerable Bede, Homilies on the Gospels | ✅ | — | ❌ coverage only |
| Maximos the Confessor, On the Lord's Prayer | ✅ | — | ❌ coverage only |
| Theophylact, Explanation of the Gospels | ✅ | — | ❌ coverage only (`homilies/` dir empty) |
| Synaxarion | ✅ (with `date`, `saint` fields) | — | ❌ coverage only |

Implication: the server operates in two tiers.

- **Tier 1 (full text):** Chrysostom Matthew/John, Cyril Luke — return excerpts
  and full text.
- **Tier 2 (reference only):** Gregory, Bede, Maximos, Theophylact, Synaxarion,
  and Nikolai — return the citation (author, work, homily number/title, verse
  range) with `text_available: false`. Nikolai is Tier 2 by **licensing**, not
  data availability: the Prologue text exists on disk but we lack rights to
  distribute it, so the server must never serve its content. For calendar-dated
  works (Nikolai Prologue, Synaxarion) the citation includes the `date` on which
  the entry falls (e.g. "September 1") so a user can look it up in a licensed
  copy.

Design rules carried over from CLAUDE.md:

- **Metadata is authoritative.** Use the `coverage` block in `metadata.json` (and
  `coverage.json` ranges), not `scripture_reference` — homily 001 of Chrysostom
  Matthew has null chapter/verse in `scripture_reference` but a valid `coverage`.
- **Never recompute what the JSON already provides.** Prefer `verse_mapping.json`
  where it exists; fall back to a coverage-range containment check elsewhere.
- Footnote numbering starts at 1 per homily; footnotes live in `metadata.json`.

## Architecture

```
hypomnema/
├── hypomnema-server/        existing website (unchanged)
├── hypomnema-mcp/           NEW: MCP server binary
│   ├── go.mod               own module — no coupling to the web server
│   ├── main.go              transport setup + tool registration
│   ├── store.go             data loading (coverage, verse mappings, metadata)
│   ├── tools.go             tool handlers
│   └── books.go             book-name normalization
└── texts/                   shared data (read-only from both binaries)
```

- **Language:** Go, matching the existing codebase.
- **MCP SDK:** `github.com/modelcontextprotocol/go-sdk` (official). Fallback if it
  proves awkward: `github.com/mark3labs/mcp-go` (widely used community SDK).
  Decide during Phase 1 spike; the tool-handler code is nearly identical either way.
- **Transport:** both, selected by flag/env. **Streamable HTTP** is the primary
  transport because the server deploys to Render (see Deployment section);
  **stdio** is kept for local development and for users who clone the repo and
  run the binary directly. The tool handlers are transport-agnostic — only
  `main.go` differs.
- **Data path:** default `../texts` relative to the binary (same convention as the
  web server), overridable with `HYPOMNEMA_TEXTS_DIR` env var so the binary can be
  installed anywhere.
- **Loading strategy:** load all coverage.json + verse_mapping.json + metadata.json
  into memory at startup (small — a few MB). Read `content/NNN/content.json` lazily
  per request; homily bodies are the only large files.
- **Code reuse:** the loading logic in `hypomnema-server/main.go` (~lines 200–480)
  is the reference implementation, but it is entangled with HTTP handlers in a
  3,000-line file. Re-implement the ~150 lines of loaders in `store.go` rather than
  refactoring the web server. Revisit extraction into a shared package only if the
  two copies start drifting.

## Tool API

Three tools. Responses are structured JSON.

### 1. `get_commentary_for_verse`

The primary lookup. Deliberately returns references + excerpts, not full texts —
a single Chrysostom homily is ~5,500 words (~8k tokens), and dumping several into
context uninvited would be hostile to the client.

```json
{
  "name": "get_commentary_for_verse",
  "input": {
    "book": "string — Bible book, e.g. 'John' (normalized, see below)",
    "chapter": "integer",
    "verse": "integer",
    "author": "string, optional — filter to one author slug"
  }
}
```

Output per match:

```json
{
  "author": "chrysostom",
  "author_full": "John Chrysostom",
  "work": "Homilies on Matthew",
  "id": 26,
  "roman": "XXVI",
  "title": "Homily XXVI",
  "covers": "Matthew 8:5-13",
  "match_type": "primary | range",
  "word_count": 5573,
  "excerpt": "first ~300 chars…",
  "text_available": true,
  "date": "September 1 (calendar-dated works only, omitted otherwise)"
}
```

Lookup order: exact hit in `verse_mapping.json` where present (`match_type:
"primary"`), then coverage-range containment for everything else (`match_type:
"range"`), deduplicated by (author, work, id). Tier-2 works appear with
`text_available: false` and no excerpt; calendar-dated works (Nikolai Prologue,
Synaxarion) carry the `date` field, and Synaxarion entries also carry `saint`.

### 2. `get_commentary_text`

The drill-in call after the client picks a result.

```json
{
  "name": "get_commentary_text",
  "input": {
    "author": "string — e.g. 'chrysostom'",
    "work": "string — e.g. 'matthew' (work slug as returned by tool 1)",
    "id": "integer — homily/sermon number",
    "paragraph_start": "integer, optional (1-based)",
    "paragraph_end": "integer, optional"
  }
}
```

Output: title, subtitle, covers, paragraphs (sliced if a range was given),
`total_paragraphs`, and the footnotes map from metadata. For Tier-2 works return a
clear error: `"Full text for <work> is not included in this dataset; only the
citation is available."` If a full homily exceeds a size guard (~30k chars),
return the first N paragraphs plus a note telling the client to page with
`paragraph_start`/`paragraph_end`.

### 3. `list_commentaries`

No input. Returns one entry per (author, work): author slug, full name, work
title, count of homilies/sermons, books covered, and `text_available`. Lets a
client discover coverage before querying.

### Deferred (Phase 5 candidates)

- `get_verse_text(book, chapter, verse)` — KJV text from
  `texts/scripture/new_testament/english/kjv/`. Trivial and useful.
- `get_parallel_passages(book, chapter, verse)` — Eusebian canon lookup from
  `texts/reference/eusebian_canons/`. A differentiator; enables "what do the
  Fathers say about this passage *or its synoptic parallels*."

## Book-name normalization

Inputs like `John`, `john`, `Jn`, `JHN`, `1 John` must resolve deterministically.
`books.go` holds a map of canonical slugs (matching the directory names:
`matthew`, `mark`, `luke`, `john`, …) plus common abbreviations. Unknown book →
error listing the valid names. Commentary coverage keys use these same slugs, so
normalization happens once at the tool boundary.

## Implementation phases

### Phase 1 — Skeleton + data store (the spike)

1. `hypomnema-mcp/go.mod`, pull in the official Go SDK; confirm a hello-world
   stdio server registers with `claude mcp add`.
2. `store.go`: walk `texts/commentaries/`, load every `coverage.json` (handle both
   range shapes: with and without per-entry `book`; tolerate extra fields like the
   Synaxarion's `date`/`saint` and Chrysostom Matthew's `missing_numbers`). Load
   the three `verse_mapping.json` files. Index metadata for Tier-1 works.
   Hard-code Nikolai as Tier 2 (licensing) — the loader must not register its
   `homilies/` content even though the files exist.
3. Unit-test the store against the real `texts/` tree: known verse → expected
   homily IDs (e.g. Matthew 1:1 → Chrysostom homilies I–III per `verse_mapping`).

### Phase 2 — Tools

4. Implement the three tools with strict JSON schemas.
5. Book normalization + friendly errors (unknown book, verse out of range, Tier-2
   text requests).
6. Size guard + paragraph paging on `get_commentary_text`.

### Phase 3 — Client integration + verification

7. Register locally: `claude mcp add hypomnema -- /path/to/hypomnema-mcp` (or the
   Claude Desktop JSON config; document both in a `hypomnema-mcp/README.md`).
8. End-to-end check from a real client: ask about John 3:16, Matthew 5:3, Luke
   2:1 (Cyril), a verse only covered by a Tier-2 work (Bede/Gregory), and a bogus
   book name. Confirm the model chains tool 1 → tool 2 naturally.
9. Spot-check text fidelity: footnote markers in paragraphs vs the footnotes map
   (the `XXXFOOTNOTEREFXXX` placeholder convention from the web server — decide
   whether to strip markers or render `[n]`).

### Phase 4 — Render deployment

10. Add the streamable-HTTP transport path in `main.go` (serve on `PORT`, MCP
    endpoint at `/mcp`, plus a `/healthz` endpoint for Render health checks).
11. Create the Render service and deploy per the Deployment section below.
12. Verify from a remote client: `claude mcp add --transport http hypomnema
    https://<service>.onrender.com/mcp`, then repeat the Phase 3 end-to-end
    checks against the hosted server.

### Phase 5 — Optional extensions

13. `get_verse_text` (KJV) and `get_parallel_passages` (Eusebian canons).
14. Source Tier-2 texts (Bede, Gregory, Theophylact, Maximos) into the standard
    `content/NNN/` format — a data project, not a server change; the server picks
    them up automatically once `content/` exists. Nikolai stays reference-only
    unless distribution rights are obtained.

## Deployment (Render)

The MCP server deploys to Render as a **second web service** on this repo,
side by side with the existing website. It follows the same conventions as the
`hypomnema-server` service documented in CLAUDE.md.

### Service configuration

| Setting | Value |
|---|---|
| Service type | Web Service |
| Root Directory | `hypomnema-mcp` |
| Build Command | `go build -o app` |
| Start Command | `./app` |
| Health Check Path | `/healthz` |
| Branch | `main` (staging branch for pre-production testing, same flow as the website) |

Notes:

- **Port:** Render injects `PORT`; the server reads it and defaults to 8080
  locally (same convention as the website). When `PORT` is set the binary starts
  in streamable-HTTP mode automatically; with no `PORT` and a TTY it defaults to
  stdio, so one binary serves both use cases.
- **Data path:** Render clones the full repo even with Root Directory set to
  `hypomnema-mcp`, so `../texts` resolves exactly as it does for the website
  today. `HYPOMNEMA_TEXTS_DIR` remains available as an override.
- **Statelessness:** run the streamable-HTTP transport in stateless mode (no
  server-side session affinity). All data is read-only and in-memory, so
  restarts, redeploys, and Render's free-tier spin-down are harmless — cold
  start is just re-reading the JSON indexes (fast).
- **Transport endpoint:** `/mcp` via streamable HTTP. No SSE-only legacy
  endpoint — current MCP clients (Claude Code, Claude Desktop via connectors,
  the API's MCP connector) all speak streamable HTTP.
- **TLS:** "streamable HTTP" is the MCP transport's name, not the URL scheme.
  Clients always connect over **HTTPS** (`https://<service>.onrender.com/mcp`);
  Render terminates TLS at its edge and forwards to the binary, which listens
  on plain HTTP on `PORT` — standard for services behind a TLS-terminating
  proxy, and the same setup as the existing website.

### Authentication

The texts are public domain, so v1 ships **unauthenticated** — same exposure as
the website itself. Guardrails to include anyway:

- Modest rate limiting (per-IP token bucket in middleware) so a misbehaving
  client can't hammer the service.
- Response size caps already exist at the tool layer (paragraph paging).

If abuse or cost becomes an issue, add a static bearer token check
(`Authorization: Bearer <token>`, token in a Render environment variable) —
MCP clients pass custom headers, so this needs no protocol work. Full OAuth is
out of scope unless the server is ever listed in a public MCP directory that
requires it.

### Client configuration (hosted)

```bash
# Claude Code
claude mcp add --transport http hypomnema https://<service>.onrender.com/mcp
```

Claude Desktop: add as a remote connector (Settings → Connectors → Add custom
connector) pointing at the same URL. Document both in `hypomnema-mcp/README.md`
alongside the local-stdio instructions.

### Deployment checklist

1. All `texts/` JSON committed to the deploy branch (coverage, mappings,
   metadata, content).
2. `hypomnema-mcp/go.mod` and `go.sum` committed.
3. `/healthz` returns 200 and the MCP initialize handshake succeeds against the
   Render URL (`curl -X POST https://<service>.onrender.com/mcp` with an
   `initialize` payload).
4. Verse-lookup smoke test from a real client against production.
5. Confirm the Nikolai licensing guard holds in production (no text served).

## Testing checklist

- [ ] Store loads every commentary directory without error; counts match
      `total_homilies` in each coverage.json.
- [ ] Verse with `verse_mapping` entry returns `primary` matches.
- [ ] Verse inside a coverage range but absent from `verse_mapping` returns
      `range` matches (no duplicates when both hit).
- [ ] Multi-Gospel works (Gregory, Bede) match only when the requested book
      matches the entry's `book` field.
- [ ] Tier-2 `get_commentary_text` returns the not-available error, not a crash.
- [ ] Nikolai text is never returned by any tool, even though `homilies/` exists
      on disk (licensing guard); its verse-lookup results carry the Prologue date.
- [ ] Homily with null `scripture_reference` (Chrysostom Matthew I) still reports
      correct `covers` from its `coverage` block.
- [ ] Paragraph paging: out-of-range indices clamp; slice boundaries correct.
- [ ] Book normalization: `Jn`, `john`, `JOHN`, `Saint John` → `john`; `Genesis` →
      helpful error (NT-only dataset).

## Non-goals

- No changes to `hypomnema-server/` or its templates/CSS.
- No text extraction or metadata regeneration — existing JSON is used as-is.
- No auth (stdio server runs with the user's local permissions; revisit if/when
  an HTTP deployment happens).

## Resolved decisions (2026-07-07)

1. **Tier-2 results are included by default** in `get_commentary_for_verse`,
   flagged with `text_available: false`. No opt-in parameter — knowing Bede
   preached on a verse is useful even without text.
2. **Footnotes render as inline `[n]` markers** in paragraph text, with the
   footnotes map included as an appendix in the `get_commentary_text` response.
3. **Nikolai Prologue is reference-only for licensing reasons.** The text exists
   on disk but distribution rights are not held, so no tool may serve its
   content. Verse-lookup results include the Prologue **date** on which the
   commentary falls (e.g. "September 1") so users can consult a licensed copy.
