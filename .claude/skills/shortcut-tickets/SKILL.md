---
name: shortcut-tickets
description: Create, label, and transition Shortcut tickets for the hypomnema project on the orthodox-net workspace. Use whenever work needs to be filed as a ticket, an epic needs creating, a story needs moving through the workflow, or the maintainer asks what is on the board.
---

# Shortcut tickets (hypomnema)

Shortcut is the board for this project. Read it before proposing work; update it in the
change that completes an item. No parallel todo lists — link to the doc with the detail
instead of restating it.

MCP server `shortcut`, workspace `orthodox-net`.

## Hard-won IDs

Do not re-discover these. They were verified against the API.

**Workflow 500000005 ("Standard") states:**

| State | ID |
|---|---|
| Backlog | 500000006 |
| To Do | 500000007 |
| Blocked | 500000018 |
| In Progress | 500000008 |
| In Review | 500000009 |
| Done | 500000010 |

**Epic workflow 500000001 states:** to do 500000002, in progress 500000003, done 500000004.

**Project labels** — one per project, applied to every story:

| Label | ID |
|---|---|
| hypomnema | 472 |
| onet-v3 | 440 |
| rsna-knee | 426 |

Other labels: agent 429, human 428, needs qa 8, ready for design 7, release 1.0 9.

**Hypomnema epics:** 383 Theophylact, 384 Data quality, 385 Someday,
464 Performance — Lighthouse mobile.

**Maintainer user ID:** `674e42f8-c2d2-42c9-871a-8435b58c8d58` (Gregory Zancewicz).

## Creating a story

```
stories-create
  name: <imperative, specific — the problem or the change, not "fix bug">
  type: feature | bug | chore
  epic: <id>
  workflow_state_id: 500000006      # Backlog is the default landing state
  description: <see below>
```

Then apply the project label — `stories-create` takes no label argument:

```
stories-update  storyPublicId: <id>  labels: [{name: "hypomnema"}]
```

**`labels` replaces the whole array.** It does not append. Before labeling a story that
may already have labels, read it first and pass the existing labels back alongside the
new one, or you will silently strip them.

## Story type

- `bug` — something is wired up but does not work. Prefer this over `feature` when the
  code already exists and is broken; it changes how the ticket reads.
- `chore` — measurement, config, dependency, verification passes.
- `feature` — genuinely new behaviour.

## Description conventions

Match the existing hypomnema tickets. Markdown, and:

- **Lead with evidence, not narrative.** Paste the actual numbers, trace excerpts, or
  file:line that prove the problem. A ticket that asserts without showing gets
  re-litigated later.
- **Cite real code** as `path/to/file.ext:123` with the relevant snippet inline.
- **Give a "Done when" section** with checkable conditions, not aspirations.
- **Carry project constraints forward** into the ticket that will violate them. The
  CLAUDE.md gotchas — `formatCoverageRange()` fallback book, `?v={{.AssetVersion}}`
  cache busting, "adding a commentary needs no code" — belong in the done-criteria of
  whichever ticket could break them.
- **Flag what cannot be verified where.** E.g. Google Analytics lives only in `main`, so
  GA tickets cannot be checked on staging. Say so in the ticket rather than leaving a trap.
- **State open questions as questions.** If a decision is the maintainer's, write it as a
  call to make, do not silently pick one.
- Reference sibling tickets as `sc-466` so they autolink.

## Estimating — required on every story

Every new story gets a token estimate in its description AND an `estimate` (points)
field. This is not optional; a story without both is incomplete.

### Calibration

**1 story point = 2,000,000 total accounted tokens.**

Points scale is `0 / 1 / 2 / 4 / 8` — a doubling scale, not continuous. Compute
`likely_total / 2M`, then **round UP to the next allowed rung**:

| raw | points |
|---|---|
| ≤ 1.0 | 1 |
| 1.01 – 2.0 | 2 |
| 2.01 – 4.0 | 4 |
| 4.01 – 8.0 | 8 |
| > 8.0 | **cap at 8 and say in the ticket that it is oversized — it should probably be split** |

Round up to the *rung*, not to the next integer: 2.5 raw → 4, not 3. Reserve 0 for
work that genuinely costs nothing; a real ticket never estimates 0.

Calibrated 2026-08-23 against epic 464 (7 stories). Revisit after ~15 tickets have
actuals — thin basis until then.

### Producing the token figure

1. Decompose into agent sessions (1–8 typical). Name each by what it produces.
2. Classify each session and take its measured band — first match wins:

| Session class | D1 (best) | D5 (likely) | D9 (worst) |
|---|--:|--:|--:|
| Q&A / ops / doc-write (no edits) | 1.1k | 6k | 32k |
| Single-file edit (1–2 sites) | 3k | 10.6k | 29k |
| Multi-file change (3+ sites) | 6k | 19k | 52k |
| Feature — new files + test cycles | 20k | 52k | 126k |
| Exploration / audit (read-heavy) | 7k | 14k | 33k |
| Web research | 6k | 16k | 40k |

   Debugging with **unknown cause** is quoted as the full range (single-file D1 3k →
   feature D9 126k) and never narrowed — the symptom does not reveal the depth.
   **Diagnosing the cause before writing the ticket collapses that 40× spread to ~10×.**
   Do that whenever possible; it is the single highest-leverage estimating move.

3. Sum best/likely/worst across sessions.
4. Multiply output by **180** to get total accounted tokens (this account's measured
   ratio: 176.0 cache read + 4.07 cache write + ~0.01 uncached, from 16,474 real API
   calls over 14 days).

### The block to append to every description

```
---

## Token estimate

| | best | likely | worst |
|---|--:|--:|--:|
| Output tokens | Xk | Xk | Xk |
| **Total accounted** | **X.XM** | **X.XM** | **X.XM** |

Sessions: N. Driver of the spread: <the single biggest one>.

**Method.** Output tokens from the measured D1/D5/D9 bands in the
attention-hours-estimation skill (391 real episodes), adjusted per session. Total
accounted applies this account's measured ratio of 180 input tokens per output token.

**Caveat.** Anthropic does not publish how session/weekly limit percentages are
computed, and the mix is ~97% cache reads which are almost certainly discounted rather
than counted at parity. Treat "total accounted" as raw token volume, NOT as a direct
percentage of the limit — it is an upper bound on what the meter sees.
```

## Recording actuals — required on completion

When a story's work is finished, **before** moving it to In Review, post a comment with
what it actually cost. This is what turns the estimate from a guess into a calibrated
one; skipping it means the 2M/point figure never improves.

```
## Actual

| | estimated (likely) | actual |
|---|--:|--:|
| Output tokens | Xk | Xk |
| Total accounted | X.XM | X.XM |
| Points | N | N |

Sessions: estimated N, actual N.
Landed <at / above / below> the likely figure. <One line on why, if it missed.>
```

Measure actuals from the session transcripts rather than guessing:

```bash
python3 - <<'EOF'
import json,glob,os,time,collections
t=collections.Counter()
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    if os.path.getmtime(f) < time.time()-86400: continue
    for line in open(f,errors="ignore"):
        if '"usage"' not in line: continue
        try: u=(json.loads(line).get("message") or {}).get("usage") or {}
        except: continue
        if not u.get("output_tokens"): continue
        for k in ("input_tokens","output_tokens","cache_read_input_tokens","cache_creation_input_tokens"):
            t[k]+=u.get(k) or 0
print(f"output {t['output_tokens']:,}   total {sum(t.values()):,}")
EOF
```

That window is the whole day, not one story — narrow it by mtime, or note in the
comment that the figure covers the session rather than the ticket alone. **An honest
approximate actual beats a precise-looking fabrication**; say which it is.

If actual lands outside best–worst, say so plainly in the comment. Those are the cases
that recalibrate the bands.

## Transitioning

Move the story as the work actually progresses:

```
stories-update  storyPublicId: <id>  workflow_state_id: 500000008   # In Progress
stories-update  storyPublicId: <id>  workflow_state_id: 500000009   # In Review
```

Do not jump a story to Done. The maintainer commits and pushes; Done follows their
verification, not the agent's.

Per CLAUDE.md: don't call something fixed until you've curled the page and seen it work.
Verify before moving to In Review.

## Epics

```
epics-create  name: <name>  owner: 674e42f8-c2d2-42c9-871a-8435b58c8d58
```

Leave `teamId` unset — the hypomnema and ONET epics carry no team. Give the epic a
description holding the shared context (baseline measurements, diagnosis, scope) so the
stories underneath can stay short and point at it.

## What this MCP server cannot do

**Spaces / saved views have no API.** `stories/space/<id>` URLs are server-side saved
views; they cannot be created, read, or filtered via MCP. If the maintainer wants a new
board view, they must make it in the UI: **+ Spaces** in the tab row → filter
`Label any of <project>` → name and save. Warn them not to save onto an existing space's
tab or it overwrites that view.

Stable URLs that do work without a space:
- Label view — `https://app.shortcut.com/orthodox-net/label/472`
- Epic view — `https://app.shortcut.com/orthodox-net/epic/464`
- Search — `https://app.shortcut.com/orthodox-net/search#label:hypomnema`

## Never run these

- **git** — the maintainer commits and pushes.
- **`go build -o app`** — `air` owns that binary and serves it. Building over it kills
  the running server, and only the maintainer restarts it. To check a change compiles,
  build to a throwaway path (`go build -o /tmp/xx .`) or just let `air` reload and curl
  the page.
- **starting or stopping the server** — the maintainer does both.

## Git

Never run git commands — the maintainer does. Hand them the exact
`git add` / `git commit` / `git push` block, with the story id (`sc-471`) in the commit
message trailer line.
