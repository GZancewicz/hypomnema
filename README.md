# Hypomnema

**Hypomnema** (ὑπόμνημα) is a Greek word meaning "reminder," "note," "commentary," or "memorandum." In ancient times, a *hypomnema* was a notebook or commentary where readers would record their thoughts, interpretations, and cross-references while studying texts. This application embodies that tradition by providing integrated commentary and cross-references alongside the biblical text.

The hypomnema app is a biblical text reader featuring the King James Version (KJV) New Testament with integrated patristic commentary from Church Fathers including John Chrysostom, Cyril of Alexandria, Gregory the Great, Venerable Bede, and Maximos the Confessor.

## Features

- **Commentary Index Home Page** with collapsible sections for each Gospel book
  - Complete table view of all available commentaries
  - Direct links to open specific homilies/sermons
  - Shows scripture coverage for each commentary
- **Complete KJV New Testament** with chapter-by-chapter navigation
- **Patristic Commentary Integration**:
  - John Chrysostom's 90 homilies on Matthew
  - John Chrysostom's 88 homilies on John
  - Cyril of Alexandria's 153 sermons on Luke
  - Gregory the Great's 40 homilies across all four Gospels
  - Venerable Bede's 50 homilies across all four Gospels
  - Nikolai Velimirovich's daily meditations from the Prologue of Ohrid featuring homilies on Scripture (In progress)
  - Maximos the Confessor's treatise On the Lord's Prayer
  - Synaxarion entries linking saints' lives to New Testament passages (Sept 1 – Oct 31, in progress)
  - Theophylact of Ohrid's commentary (In progress)
  - Minimal blue markers in the right margin
  - Split-screen commentary viewing (50/50 layout), with the passage covered shown under the title
  - Hover tooltips showing commentary references
  - Smart cross-referencing to parallel Gospel passages
  - Footnotes with hover tooltips
- **Eusebian Canon System**
  - Canon numbers displayed in text with clickable links
  - Modal showing parallel Gospel passages with full verse text
  - Integrated on both Commentaries and Scripture References pages
- **Scripture References Page** showing Eusebian canon cross-references and patristic commentary coverage
- **JSON REST API** (`/api/v1`) for programmatic commentary lookup and retrieval, with interactive Swagger docs at `/api/v1/docs`
- **Responsive Design** with mobile-friendly hamburger menu
- **Clean Typography** with paragraph-based formatting
- Live reload during development with Air
- **Google Analytics** integration (production only)

## Technology & Design Choices

Hypomnema is built as a **Go server that renders HTML, with [HTMX](https://htmx.org)
on the front end** — deliberately not a JavaScript single-page application. The
Go backend renders both full pages and small HTML fragments; HTMX requests those
fragments (e.g. `/api/chapter/...`, `/api/homily/...`) and swaps them into the
page via attributes like `hx-get` and `hx-target`, with no client-side framework
or build step.

**Why Go:**
- Compiles to a single self-contained binary with no runtime dependencies — trivial to deploy (one `app` on Render, no Node runtime, no package install at boot).
- Fast startup and low memory; the standard library's HTTP server handles everything, so there are few third-party dependencies to track or patch.
- Naturally suited to what this app does: read text/JSON data files from disk and serve HTML and JSON. The same binary now also serves the `/api/v1` JSON API.

**Why HTMX (instead of React/Vue/etc.):**
- This is a **read-mostly text reader** — content-heavy, interaction-light. Server-rendered HTML is the natural fit; a heavy SPA would add complexity without a matching payoff.
- Dynamic behavior (loading chapters, opening the split-screen commentary panel, live search) is achieved by swapping server-rendered fragments, so the **server stays the single source of truth for rendering** — no duplicated view logic between a backend and a JS frontend.
- No build pipeline, bundler, or `node_modules` — HTMX is a single `<script>` tag. This keeps the toolchain small and the project easy to run, reason about, and hand off.

The net effect is a small, fast, low-dependency stack: one Go binary renders the
pages, HTMX makes them feel dynamic, and the same server exposes a JSON API — all
without a separate frontend project.

## Commentary Metadata Structure

Each commentary (homily/sermon) is stored in a structured folder system with standardized `metadata.json` files. The application reads these metadata files dynamically, allowing new commentaries to be added without code changes.

### Directory Structure
```
texts/commentaries/
├── chrysostom/
│   ├── matthew/
│   │   ├── content/
│   │   │   ├── homily_001/
│   │   │   │   └── metadata.json
│   │   │   └── homily_090/
│   │   │       └── metadata.json
│   │   └── source/          # Source XML files
│   └── john/
│       ├── content/
│       │   └── homily_001/
│       │       └── metadata.json
│       └── source/          # Source XML files
├── cyril/
│   └── luke/
│       └── sermons/
│           ├── sermon_001/
│           │   └── metadata.json
│           └── sermon_153/
│               └── metadata.json
├── gregory_the_great/       # 40 Gospel Homilies
├── bede/                    # 50 Homilies on the Gospels
├── nikolai/                 # Prologue of Ohrid
├── maximos_the_confessor/   # On the Lord's Prayer
├── synaxarion/              # Saints' lives linked to Gospel passages
└── theophylact/             # Commentary (in progress)
```

### Metadata Format
```json
{
  "id": 90,
  "roman": "XC",
  "title": "Homily XC",
  "subtitle": "Matthew XC. 27:27",
  "author": "chrysostom",
  "author_full": "John Chrysostom",
  "work": "Homilies on Matthew",
  "scripture_reference": {
    "book": "matthew",
    "start": {"chapter": 27, "verse": 27},
    "end": {"chapter": 28, "verse": 20},
    "display": "Matthew 27:27-28:20"
  },
  "footnotes": {"1": "text...", "2": "text..."},
  "has_footnotes": true,
  "verified": true,
  "word_count": 5033,
  "excerpt": "First 200 words..."
}
```

## Getting Started

### Prerequisites

- Go (v1.19 or higher)
- Air (for live reload during development)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hypomnema.git
cd hypomnema
```

2. Install Air for live reload:
```bash
go install github.com/air-verse/air@latest
```

3. Start the development server:
```bash
cd hypomnema-server
~/go/bin/air
```

4. Open [http://localhost:8080](http://localhost:8080) in your browser

### Running without Air

To run the server directly without live reload:
```bash
cd hypomnema-server
go run main.go
```

## Project Structure

```
hypomnema/
├── hypomnema-server/         # Go web server
│   ├── main.go              # Main server code with all routing
│   ├── apiv1/               # JSON REST API package (mounted at /api/v1)
│   ├── templates/           # HTML templates (index.html, homily.html)
│   ├── static/              # CSS (styles.css) and favicon
│   └── tmp/                 # Air build artifacts (git ignored)
├── texts/                   # Biblical texts and reference data
│   ├── scripture/           
│   │   └── new_testament/
│   │       ├── english/
│   │       │   └── kjv/     # KJV text files by book/chapter
│   │       └── greek/
│   │           └── tr/      # Textus Receptus
│   ├── commentaries/        # Patristic commentaries
│   │   ├── chrysostom/      # John Chrysostom (Matthew, John)
│   │   ├── cyril/           # Cyril of Alexandria (Luke)
│   │   ├── gregory_the_great/ # Gregory the Great (all Gospels)
│   │   ├── bede/            # Venerable Bede (all Gospels)
│   │   ├── nikolai/         # Nikolai Velimirovich (Prologue)
│   │   ├── maximos_the_confessor/ # Maximos (Lord's Prayer)
│   │   ├── synaxarion/      # Saints' lives
│   │   └── theophylact/     # Theophylact (in progress)
│   └── reference/           
│       ├── eusebian_canons/ # Canon tables and mappings
│       └── kjv_paragraphs/  # Paragraph divisions
├── scripts/                 # Python utility scripts
├── CLAUDE.md               # Development notes and instructions
└── README.md
```

## Commentary Index

The home page displays a comprehensive index of all available patristic commentaries, organized by Gospel book. Each book section is collapsible and shows:
- Scripture references for each homily/sermon
- Church Father attribution
- Work title (e.g., "Homilies on Matthew")
- Direct clickable links to open specific commentaries

The index provides a complete overview of the commentary coverage, making it easy to find specific homilies or sermons by scripture reference.

## Eusebian Canons

The application displays Eusebian Canon numbers in the left margin of Gospel texts. These ancient cross-references show parallel passages across the four Gospels. Hovering over a canon number reveals the specific verse references.

## Patristic Commentary

The application integrates patristic commentary on the Gospels from multiple Church Fathers:

### John Chrysostom (c. 347-407)

*Archbishop of Constantinople renowned for his eloquent preaching and his advocacy for the poor. His epithet "Chrysostom" — "golden-mouthed" in Greek — reflects his extraordinary gift for oratory. Venerated in both East and West, he is also remembered for the Divine Liturgy attributed to him, which remains central to Orthodox worship.*

- **90 Homilies on Matthew** covering the entire Gospel of Matthew
- **88 Homilies on John** covering the entire Gospel of John
- **Cross-Gospel Integration** - When reading Mark or Luke, the system automatically shows relevant Matthew and John homilies for parallel passages

### Cyril of Alexandria (c. 376-444)

*Pope (Patriarch) of Alexandria and a leading theological voice in the early Christological controversies. He led the Council of Ephesus (431) in opposing Nestorius, defending the unity of Christ and the title Theotokos ("God-bearer") for Mary. His vast body of writing earned him the honorific "Seal of all the Fathers," and his Christology remains foundational to Orthodox tradition.*

- **153 Sermons on Luke** covering the entire Gospel of Luke (manuscript contains only fragments for 154-156)
- Integrated footnotes and textual notes

### Gregory the Great (c. 540-604)

*Pope of Rome (590-604), remembered for his prolific writings and administrative leadership. He authored the Pastoral Rule, long the standard manual for Western clergy, and the Dialogues; he sent Augustine to evangelize England and is traditionally associated with Gregorian chant. In the Orthodox Church he is known as Gregory the Dialogist.*

- **40 Homilies on the Gospels** (Forty Gospel Homilies) covering passages from all four Gospels
- Spanning Matthew, Mark, Luke, and John

### Venerable Bede (c. 673-735)

*A monk of the Northumbrian monasteries of Wearmouth-Jarrow, where he spent his life in scholarship. He is best known for his Ecclesiastical History of the English People, which earned him the title "Father of English History." A prolific scholar, he also produced numerous biblical commentaries and theological works, making him one of the most learned figures of the early medieval West.*

- **50 Homilies on the Gospels** organized in two books covering passages from all four Gospels
- Book I: 25 homilies (I.1 through I.25)
- Book II: 25 homilies (II.1 through II.25)

### Nikolai Velimirovich (1880-1956)

*A Serbian Orthodox bishop (of Žiča and later Ohrid), called "Serbia's New Chrysostom" for his preaching and writing. Imprisoned by the Nazis at Dachau during World War II, he later taught at Orthodox seminaries in America. His Prologue of Ohrid, a collection of daily spiritual reflections, remains widely read; he was canonized in 2003.*

- **Daily Meditations from the Prologue of Ohrid** featuring homilies on Scripture
- Organized by calendar date (In progress)
- Each entry provides spiritual reflection on specific Scripture passages

### Maximos the Confessor (c. 580-662)

*A Byzantine monk and theologian, the Church's foremost defender against Monothelitism — the claim that Christ possessed only one will. For his witness he suffered mutilation, his tongue and right hand cut off, hence the title "Confessor." He was vindicated at the Sixth Ecumenical Council, and his spiritual and theological writings remain deeply influential in Orthodox thought.*

- **On the Lord's Prayer** - Spiritual commentary on the Our Father
- Covers both Matthew 6:9-13 and Luke 11:2-4
- Deep theological reflection on the Lord's Prayer

### Synaxarion
- **Saints' lives** linked to specific New Testament passages
- Entries organized by liturgical date with saint name and scripture reference
- **Coverage (in progress):** calendar days **September 1 through October 31** (old calendar) have been incorporated so far; work is ongoing to extend coverage through the remaining days

### Theophylact of Ohrid (c. 1050-1107)

*A Byzantine biblical scholar who served as archbishop of Ohrid for some twenty-five years. He is best known for his lucid commentaries on the Gospels, Acts, and Epistles — drawn largely from Chrysostom and long treasured in the Orthodox tradition. He is venerated as a saint, commemorated on December 31.*

- Commentary coverage in progress

### Features
- **Inline References** showing which homilies/sermons discuss each passage
- **Footnotes** with hover tooltips for additional context
- **Split-screen Reading** for studying scripture alongside commentary
- **Unified Commentary System** using common data structures for all sources

### Data Files

**Commentary Metadata:**
- `texts/commentaries/chrysostom/matthew/content/homily_*/metadata.json` - Matthew homily metadata with footnotes
- `texts/commentaries/chrysostom/john/content/homily_*/metadata.json` - John homily metadata with footnotes
- `texts/commentaries/cyril/luke/sermons/sermon_*/metadata.json` - Luke sermon metadata

**Verse Mappings:**
- `texts/commentaries/chrysostom/matthew/matthew_verse_to_homilies.json` - Verse-to-homily mapping
- `texts/commentaries/chrysostom/john/john_verse_to_homilies.json` - Verse-to-homily mapping
- `texts/commentaries/cyril/luke/luke_verse_to_sermons.json` - Verse-to-sermon mapping

**Coverage Files:**
- `texts/commentaries/chrysostom/matthew/coverage.json` - Matthew homily passage coverage
- `texts/commentaries/chrysostom/john/coverage.json` - John homily passage coverage
- `texts/commentaries/cyril/luke/coverage.json` - Luke sermon passage coverage

**Eusebian Canons:**
- `texts/reference/eusebian_canons/verse_to_canon.json` - Maps verses to canon entries
- `texts/reference/eusebian_canons/canon_lookup.json` - Maps canon entries to parallel passages
- `texts/reference/eusebian_canons/eusebian-canons.db` - SQLite database with source data

## REST API

A read-only JSON API exposes the commentary dataset for programmatic use. It is
**served by the same binary as the website** — mounted at `/api/v1`, so no
separate service is needed.

- **Production:** `https://hypomnema.online/api/v1`
- **Local:** `http://localhost:8080/api/v1`
- **Interactive docs (Swagger UI):** `/api/v1/docs`
- **OpenAPI spec:** `/api/v1/openapi.yaml`

The API lives in the `hypomnema-server/apiv1/` package (`apiv1.Init()` +
`apiv1.Handler()`), mounted in `main.go` via
`http.Handle("/api/v1/", http.StripPrefix("/api/v1", apiv1.Handler()))`. It reads
the same `texts/commentaries/` data as the website; no separate data store.

### Endpoints

#### `GET /api/v1/coverage`

Return every commentary that covers a given verse.

| Query param | Notes |
|---|---|
| `book` | Full name, directory slug, or abbreviation (`Matthew`, `matthew`, `Mt`, `Matt`; `John`, `Jn`; `1 Corinthians`, `1 Cor`, `1Co`). Required unless `ref` is given. |
| `chapter`, `verse` | Positive integers. |
| `ref` | Free-form reference parsed into book/chapter/verse, e.g. `?ref=John 3:16`. Explicit params win if both are supplied. |
| `include_text` | Default `true` — each text-available result embeds the full commentary under `text`. Set `false` for citations only. |

```bash
curl "http://localhost:8080/api/v1/coverage?book=John&chapter=3&verse=16"
curl "http://localhost:8080/api/v1/coverage?ref=Mt+8:5"
curl "http://localhost:8080/api/v1/coverage?ref=John+3:16&include_text=false"
```

Each result carries a `commentary_id` (`{author}/{work}/{id}`), the covered range,
`match_type` (`primary` = exact verse-mapping hit, `range` = coverage containment),
and `text_available`. Calendar-dated works (Synaxarion) also carry `date`/`saint`.

#### `GET /api/v1/commentary/{author}/{work}/{id}`

Return a single commentary — the path is exactly the `commentary_id` from
`/api/v1/coverage`.

| Query param | Notes |
|---|---|
| `format` | `json` (default) returns paragraphs + footnotes; `html` returns the app's rendered fragment. |
| `paragraph_start`, `paragraph_end` | 1-based inclusive slice for paging long homilies (clamps to bounds). |

```bash
curl "http://localhost:8080/api/v1/commentary/chrysostom/matthew/26"
curl "http://localhost:8080/api/v1/commentary/chrysostom/matthew/26?format=html"
curl "http://localhost:8080/api/v1/commentary/chrysostom/matthew/26?paragraph_start=1&paragraph_end=3"
```

### Text availability

Works with distributable full text (Chrysostom on Matthew/John, Cyril on Luke)
return `text_available: true` and full paragraphs. Works held as coverage-only
(Gregory, Bede, Maximos, Theophylact, Synaxarion, and Nikolai — the last for
licensing) return `text_available: false`; requesting their text yields
`404 text_not_available` with a citation.

### Errors

Errors are JSON `{ "error": "<code>", "message": "..." }` with appropriate status
codes: `400` (unknown/missing book, bad reference) and `404` (no such commentary,
or text not distributed). A valid New Testament book with no patristic coverage
returns `200` with an empty `results` array.

## Development

### Python Scripts

#### Text Processing Scripts

**generate_unified_metadata.py** - Generates standardized metadata.json files for all commentaries:
```bash
python scripts/generate_unified_metadata.py
```

**verify_kjv_completeness.py** - Verifies all KJV chapters are present and properly formatted:
```bash
python scripts/verify_kjv_completeness.py
```

**verify_commentaries_complete.py** - Verifies all commentary metadata is complete:
```bash
python scripts/verify_commentaries_complete.py
```

#### Eusebian Canon Scripts

**generate_canon_lookup_from_sql.py** - Generates the canon lookup table from SQLite database:
```bash
python scripts/generate_canon_lookup_from_sql.py
```

**generate_verse_to_canon_mapping.py** - Generates verse-to-canon mapping from SQLite database:
```bash
python scripts/generate_verse_to_canon_mapping.py
```

### Regenerating Data Files

To regenerate commentary metadata structure:
```bash
python scripts/generate_unified_metadata.py
```

This creates/updates all metadata.json files with:
- Correct verse references from source texts
- All footnotes included
- Word counts and excerpts
- Author and work information

To rebuild Eusebian Canon data:
```bash
python scripts/generate_canon_lookup_from_sql.py
python scripts/generate_verse_to_canon_mapping.py
```

### Static Assets and Caching

CSS changes appear on a normal browser reload — no hard refresh needed, and no
manual version bumping.

- Templates reference the stylesheet as `styles.css?v={{.AssetVersion}}`. The
  token comes from `assetVersion()` in `main.go`, which reads the modification
  time of `static/styles.css`, so it changes automatically whenever the file is
  edited. Never hardcode a `?v=` number.
- HTML responses send `Cache-Control: no-cache, must-revalidate`. The page is
  server-rendered and cheap, so it always revalidates; this is what allows a new
  asset version to actually reach the browser.
- Static files keep normal `Last-Modified` revalidation, so an unchanged
  stylesheet still returns `304 Not Modified` rather than re-downloading.

Any new `/static/*.js` file should use the same `?v={{.AssetVersion}}` pattern.
JavaScript currently lives inline in `index.html`, so it is covered by the
page's own no-cache header.

## Deployment

The application is configured for deployment on Render.com.

### Render Configuration

1. **Root Directory:** `hypomnema-server`
2. **Build Command:** `go build -o app`
3. **Start Command:** `./app`

The server automatically uses the PORT environment variable provided by Render.

The JSON REST API (`/api/v1`) ships as part of this same service — the OpenAPI
spec and Swagger docs are embedded in the binary (`go:embed`), so no additional
Render configuration, domain, or service is required.

### Manual Deployment

To build and run manually:
```bash
cd hypomnema-server
go build -o app
PORT=8080 ./app
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.