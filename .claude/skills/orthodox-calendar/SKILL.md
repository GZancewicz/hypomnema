---
name: orthodox-calendar
description: Fetch the saints commemorated on a given Orthodox calendar day from the Holy Trinity Orthodox Church website, with full life text and icon images. Two tools — build_synaxarion_day.py builds a whole synaxarion/calendar/<MM-Month>/<MM-DD>/ folder (commemorations.json + icons) from any OLD-STYLE date by crawling the Lives-of-Saints pages directly; fetch_commemorations.py queries calendar.php for TODAY's commemorations. Use when populating or updating the synaxarion calendar day folders.
---

# Orthodox Calendar (Holy Trinity) fetcher

Retrieves the daily commemorations from holytrinityorthodox.com's calendar
service and extracts the per-saint "Lives of Saints" (los) links that its
on-page modals load. Given a date, you get the list of saint pages for that day.

## The "API"

**Endpoint**
```
http://www.holytrinityorthodox.com/calendar/calendar.php
```

**Date + content parameters** (content flags take `1` to enable):

| Param | Meaning                              |
|-------|--------------------------------------|
| `mm`  | month (1–12)                         |
| `dd`  | day                                  |
| `yy`  | year                                 |
| `dt`  | emit date header                     |
| `ll`  | emit Lives of Saints (saint links)   |
| `hh`  | emit header                          |
| `tt`  | emit troparia                        |
| `ss`  | emit daily scripture readings        |

For just the commemorated-saints links, only `mm`, `dd`, `yy`, `dt=1`, `ll=1`
are needed.

**Saint-life ("modal") URL pattern** — what each commemoration links to:
```
http://www.holytrinityorthodox.com/calendar/los/<MonthName>/<DD>-<NN>.htm
```
`<MonthName>` is the English month (`June`), `<DD>` the day, `<NN>` a sequential
index per saint that day (`29-01`, `29-02`, …). The index is NOT commemoration
rank — e.g. June 29 returns Peter & Paul (`29-01`), Nicander (`29-02`), and the
Kasperovsk Icon (`29-03`).

**No proxy required.** The `ppp.php` proxy in the official for-webmasters docs
only exists to satisfy the browser same-origin policy for in-page JavaScript;
plain server-side GETs (curl / urllib) work directly.

**The life page IS the popup.** Clicking a commemoration on the site opens a
modal that simply loads the `<DD>-<NN>.htm` life page — there is no separate
popup endpoint. Each life page is **windows-1251** encoded (decode as `cp1251`,
not utf-8, or em-dashes/quotes become `�`) and has this shape:
- `<title>` — the full commemoration title.
- `<p class="body10">Commemorated on <dates></p>` — the feast date(s).
- one or more `<p class="body10">` — the life text; only `<br>` marks a real
  paragraph break (source line-wrapping newlines are just wrapping).
- a trailing `<p class="body10">© … translator …</p>` — the source note.
- `<img src="<DD>-<NN>.jpg">` — the saint's icon, at the SAME path as the
  `.htm` with a `.jpg` extension (e.g. `.../June/29-01.jpg`). Every life page
  has exactly one.

## Tools

### `build_synaxarion_day.py` — build a day folder from an OLD-STYLE date (primary)

Given any old-style (Julian) date, this builds the full
`synaxarion/calendar/<MM-Month>/<MM-DD>/` folder: `commemorations.json` plus the
downloaded icon `.jpg`s. It does NOT go through `calendar.php` (which only ever
returns *today*) — it crawls the Lives-of-Saints pages directly, enumerating
`<DD>-01.htm`, `<DD>-02.htm`, … until the indices 404. So it works for **any**
date, not just today.

```bash
# Old-style date as MM-DD, 'Month DD', or 'MM DD' — all equivalent
python .claude/skills/orthodox-calendar/build_synaxarion_day.py 06-29
python .claude/skills/orthodox-calendar/build_synaxarion_day.py June 29
python .claude/skills/orthodox-calendar/build_synaxarion_day.py 6 29

python .claude/skills/orthodox-calendar/build_synaxarion_day.py 06-29 --stdout     # print JSON, write nothing
python .claude/skills/orthodox-calendar/build_synaxarion_day.py 06-29 --no-images  # skip icon download
python .claude/skills/orthodox-calendar/build_synaxarion_day.py 06-29 --out DIR    # write into another calendar dir

# Build a WHOLE old-style month in one command (loops its days, polite pauses):
python .claude/skills/orthodox-calendar/build_synaxarion_day.py --month 6
python .claude/skills/orthodox-calendar/build_synaxarion_day.py --month June

# Build the ENTIRE old-style year (all 12 months) in one command:
python .claude/skills/orthodox-calendar/build_synaxarion_day.py --year

# Resume: skip any day whose commemorations.json already exists (no re-fetch).
python .claude/skills/orthodox-calendar/build_synaxarion_day.py --year --skip-existing
```

Days past a month's real length auto-skip; February runs 29 (Julian leap).

Writes `<MM-DD>/commemorations.json`:
```json
{
  "old_style_date": "June 29",
  "old_style_mmdd": "06-29",
  "source": "http://www.holytrinityorthodox.com/calendar/los/June/",
  "count": 3,
  "commemorations": [
    {
      "url": ".../calendar/los/June/29-01.htm",
      "title": "The Holy, Glorious and All-praised Leaders of the Apostles, Peter and Paul",
      "commemorated_on": "June 29",
      "text": "Sermon of Blessed Augustine…\n\nOn this present day…",
      "source_note": "© 1996-2001 by translator Fr. S. Janos.",
      "image_url": ".../calendar/los/June/29-01.jpg",
      "image_file": "29-01.jpg"
    }
  ]
}
```
Icons are saved next to it as `<DD>-<NN>.jpg`. Day/index numbers are always
zero-padded 2 digits (`05-01.htm`, not `5-1.htm`).

### `fetch_commemorations.py` — query calendar.php for TODAY

Returns the same per-commemoration fields, but sourced from `calendar.php`, which
**ignores the passed date and returns today's saints** — useful for "what's
commemorated today" (it also gives the civil↔old-style date mapping), not for
back-filling. Prefer `build_synaxarion_day.py` for populating specific days.

```bash
# By ISO date
python .claude/skills/orthodox-calendar/fetch_commemorations.py 2024-06-29

# By separate ints (MM DD YYYY)
python .claude/skills/orthodox-calendar/fetch_commemorations.py 6 29 2024

# Also fetch each life page's title, commemorated-on date, body text,
# source note, and icon image_url
python .claude/skills/orthodox-calendar/fetch_commemorations.py 2024-06-29 --lives

# Dump the raw calendar.php HTML (for debugging the parse)
python .claude/skills/orthodox-calendar/fetch_commemorations.py 2024-06-29 --raw
```

Output shape:
```json
{
  "date": "2026-07-12",
  "civil_mmdd": "07-12",
  "mmdd": "06-29",
  "source": "http://www.holytrinityorthodox.com/calendar/calendar.php?mm=7&dd=12&yy=2026&dt=1&ll=1",
  "count": 3,
  "commemorations": [
    {"label": "Peter", "url": ".../calendar/los/June/29-01.htm"}
  ]
}
```
With `--lives`, each commemoration also gains the parsed life-page fields:
`title`, `commemorated_on`, `text` (paragraphs joined by blank lines),
`source_note`, and `image_url` (or `error`). To also download the icons, have
your driver GET each `image_url` into the day folder (the icon filename is the
same `<DD>-<NN>.jpg`). See `scripts`/driver examples for the batch pattern.

**Index by the OLD-calendar date.** Commemorations are keyed to the Julian
(old-style) date, and every los link is filed under its old-style month/day
(`/los/June/29-01.htm` → June 29). The output's `mmdd` is that derived
old-style date (`06-29`); `civil_mmdd` is the Gregorian date you passed in
(`07-12`). Populate `synaxarion/calendar/<MM-Month>/<MM-DD>/` using `mmdd`, not
`civil_mmdd` — today's saints (civil July 12, 2026) belong in `06-June/06-29/`.

## Notes & gotchas

- **`label` is short.** The anchor text on the calendar page is a brief tag
  ("Peter", "Nicander"), not the full commemoration title. Use `--lives` to pull
  the full title from the life page's `<title>`.
- **Dedup by URL.** Peter and Paul share one link (`29-01`), so a single link may
  represent multiple saints; the script dedups on URL.
- **`mmdd`** (old-style) maps to this project's
  `synaxarion/calendar/<MM-Month>/<MM-DD>/` day folders (nested under month
  folders `01-January` … `12-December`, sibling of `texts/`).
- **The endpoint ignores the passed `dd`/`mm`/`yy` and returns TODAY's
  commemorations.** Verified: `?mm=7&dd=1`, `&dd=12`, `&dd=31` all returned the
  same "Sunday July 12, 2026 / June 29, 2026" content. So this fetcher is only
  reliable for the current day — you cannot back/forward-fill arbitrary dates
  through `calendar.php` this way. Bulk-populating all 366 days would need a
  different source (e.g. crawling the `/los/<Month>/` life pages directly, which
  are addressable by old-style date). Do NOT trust a batch run over many dates:
  it will silently write today's saints into every folder.
- **Movable feasts** (Paschal-cycle content) are not what `ll` returns.
- Be polite when fetching: sequential requests with a small delay, not a
  massive parallel burst.
