# RAG / "Ask Claude" Feature — Plan

Goal: let end-users of the Hypomnema web app ask questions and get answers
(the same conversational Q&A experience available in the IDE), grounded in the
biblical text and patristic commentary the app already serves.

Status: **planning only — no code written yet.**

---

## Decisions made

| Decision | Choice | Rationale |
|---|---|---|
| **Scope** | Context-scoped chat — questions about *whatever the user is currently reading* (the open chapter + its attached commentary) | Simplest, cheapest, no retrieval infrastructure. Great for "explain this verse" / "what does Chrysostom mean here." |
| **Guardrails** | Build open first; add rate limiting / cost caps later | Fastest path to a working feature. See "Deferred" below — these must land before a public launch. |
| **Provider / SDK** | Anthropic Claude API via the official Go SDK (`github.com/anthropics/anthropic-sdk-go`) | Matches the existing Go server; keeps the key server-side. |
| **Model** | Default `claude-opus-4-8`; `claude-sonnet-5` as the cost option | Opus for theological precision; Sonnet if public volume makes cost the priority. Trivial to switch. |

Because the scope is "whatever they're reading," **no vector database, no
embeddings, and no search tool are needed.** The app already knows the current
chapter and the attached commentary; we inject that text into the prompt as
context. This is prompt-context-stuffing, not retrieval RAG.

---

## Architecture / data flow

```
Browser (chat panel)
   │  POST /api/chat  { question, book, chapter, homilyId? , history[] }
   ▼
Go server  (new chatHandler in main.go)
   │  1. Load the same data the page already uses:
   │       - KJV chapter text  (existing chapter-loading code)
   │       - attached commentary / open homily (existing homily code + metadata.json)
   │  2. Assemble a system prompt + context block
   │  3. Call Claude API (streaming) via anthropic-sdk-go
   ▼
Anthropic Claude API  (claude-opus-4-8)
   │  streamed tokens
   ▼
Go server  →  Server-Sent Events (or chunked response)  →  Browser renders live
```

Key point: the context is assembled server-side by **reusing the existing
chapter/homily loading functions** — no new parsing, no duplication of the
text corpus.

---

## Backend (Go)

- **New route:** `http.HandleFunc("/api/chat", chatHandler)` in `main.go`
  (registered alongside the other `/api/*` routes near line 637).
- **New dependency:** `go get github.com/anthropics/anthropic-sdk-go`.
  - ⚠️ **Caveat:** `go.mod` currently declares `go 1.19`. The Anthropic Go SDK
    targets a newer Go toolchain — expect to bump the `go` directive (and the
    Render build image if pinned). Verify the SDK's minimum before committing.
- **Client:** `anthropic.NewClient()` reads `ANTHROPIC_API_KEY` from the
  environment — the key never reaches the browser.
- **Streaming:** use `client.Messages.NewStreaming(...)` and forward deltas to
  the browser as Server-Sent Events so answers appear token-by-token (also
  avoids request-timeout issues on longer answers).
- **Request shape (proposed):**
  ```json
  { "question": "...", "book": "john", "chapter": 18,
    "homilyId": 82, "history": [ {"role":"user","content":"..."}, ... ] }
  ```
  `history` lets the conversation be multi-turn (the API is stateless — the
  client resends prior turns).

### Context assembly (the core of the feature)

The system prompt should:
1. Establish the persona — a careful assistant for a patristics + KJV reader.
2. Include the **current KJV chapter text**.
3. Include the **attached commentary** (the open homily/sermon text, pulled the
   same way `homilyAPIHandler` / metadata.json already provide it).
4. Instruct Claude to **answer only from the provided text**, cite the source
   (e.g. "Chrysostom, Homily LXXXII on John 18"), and say plainly when the
   provided material doesn't address the question — no invented Father-quotes.

This grounding discipline matters more here than in a generic chatbot: a
hallucinated patristic citation would be a real credibility problem.

---

## Frontend

- A chat panel in the reader UI (new markup in `templates/index.html`, styles
  in `static/styles.css` — remember the `?v=XX` cache-bump rule).
- The client already knows the current book/chapter and any open homily; it
  sends those with each question so the server can rebuild context.
- Render the streamed SSE response live. Consistent with the app's existing
  HTMX-driven dynamic loading (a small JS `fetch` + `ReadableStream` reader is
  the cleanest fit for SSE).
- Responsive: the chat panel needs a mobile layout under the 700px breakpoint.

---

## Configuration / deployment

- `ANTHROPIC_API_KEY` set as an environment variable (locally + in Render).
- Model id and (optionally) `max_tokens` could be env-configurable for easy
  tuning without a redeploy.
- No change to how texts are stored or served.

---

## Deferred (explicitly out of scope for the first cut)

These were consciously deferred but should be revisited **before a public,
unauthenticated launch**, since `/api/chat` is a metered, abusable, billable
endpoint:

- **Rate limiting** (per-IP) and a **max-tokens-per-request cap**.
- Optional: gate the feature behind a key/login while iterating.
- Basic usage logging / cost monitoring.

### Future scope expansion (not now)

If "answer about the whole corpus" is ever wanted, two upgrade paths — neither
needed for the current context-scoped design:

- **Agentic RAG (recommended upgrade):** give Claude a `search_texts` tool
  backed by the existing `/api/search` + the sectioned text files and the
  `verse_to_homilies.json` / `homily_coverage.json` mappings. Claude searches,
  reads, and answers with citations across all commentators (Chrysostom, Cyril,
  Gregory, Bede, Theophylact). Reuses existing infrastructure; no vector DB. The
  Go SDK's `toolrunner` drives the loop.
- **Full vector RAG:** chunk + embed the whole corpus (Anthropic doesn't sell
  embeddings — use Voyage AI or similar), store vectors, retrieve top-k per
  question. Most powerful for thematic/cross-corpus questions, but adds an
  embeddings pipeline and a vector store to build and keep in sync.

---

## Open questions to resolve before building

1. **Model:** `claude-opus-4-8` (quality) vs `claude-sonnet-5` (cost) as the
   default for a potentially high-volume public endpoint.
2. **Go toolchain bump** required by the Anthropic Go SDK — confirm the minimum
   and whether Render's build config needs updating.
3. Exact UI placement of the chat panel relative to the existing 50/50
   commentary split.
