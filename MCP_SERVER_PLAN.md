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
| Nikolai Velimirović, Prologue | ✅ | — | ✅ `homilies/` + `homilies.json` (verify shape in Phase 1) |
| Gregory the Great, Forty Gospel Homilies | ✅ | — | ❌ coverage only |
| Venerable Bede, Homilies on the Gospels | ✅ | — | ❌ coverage only |
| Maximos the Confessor, On the Lord's Prayer | ✅ | — | ❌ coverage only |
| Theophylact, Explanation of the Gospels | ✅ | — | ❌ coverage only (`homilies/` dir empty) |
| Synaxarion | ✅ (with `date`, `saint` fields) | — | ❌ coverage only |

Implication: the server operates in two tiers.

- **Tier 1 (full text):** Chrysostom Matthew/John, Cyril Luke, Nikolai — return
  excerpts and full text.
- **Tier 2 (reference only):** Gregory, Bede, Maximos, Theophylact, Synaxarion —
  return the citation (author, work, homily number/title, verse range) so the
  client knows the commentary exists, with `text_available: false`.

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
- **Transport:** stdio (this is all Claude Desktop / Claude Code need). The SDK
  makes streamable-HTTP a drop-in swap later if a hosted version is wanted.
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
  "text_available": true
}
```

Lookup order: exact hit in `verse_mapping.json` where present (`match_type:
"primary"`), then coverage-range containment for everything else (`match_type:
"range"`), deduplicated by (author, work, id). Tier-2 works appear with
`text_available: false` and no excerpt.

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

### Deferred (Phase 4 candidates)

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
   Inspect Nikolai's `homilies.json` and either wire it into Tier 1 or park it in
   Tier 2 for now.
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

### Phase 4 — Optional extensions

10. `get_verse_text` (KJV) and `get_parallel_passages` (Eusebian canons).
11. Streamable-HTTP transport + Render deployment if a hosted public server is
    wanted (new Render service, Root Directory `hypomnema-mcp`, same build/start
    pattern as the website).
12. Source Tier-2 texts (Bede, Gregory, Theophylact, Maximos) into the standard
    `content/NNN/` format — a data project, not a server change; the server picks
    them up automatically once `content/` exists.

## Testing checklist

- [ ] Store loads every commentary directory without error; counts match
      `total_homilies` in each coverage.json.
- [ ] Verse with `verse_mapping` entry returns `primary` matches.
- [ ] Verse inside a coverage range but absent from `verse_mapping` returns
      `range` matches (no duplicates when both hit).
- [ ] Multi-Gospel works (Gregory, Bede) match only when the requested book
      matches the entry's `book` field.
- [ ] Tier-2 `get_commentary_text` returns the not-available error, not a crash.
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

## Open questions

1. Should Tier-2 (reference-only) results be included in `get_commentary_for_verse`
   by default, or behind an `include_reference_only` flag? Plan default: included,
   clearly flagged — knowing Bede preached on a verse is useful even without text.
2. Footnote rendering: inline `[n]` markers with a footnotes appendix, or strip
   them? Plan default: inline `[n]` + footnotes map in the response.
3. Nikolai Prologue: commentary or calendar devotional? Decide in Phase 1 whether
   it belongs in verse-lookup results at all.
