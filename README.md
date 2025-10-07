# Hypomnema

A biblical text reader featuring the King James Version (KJV) New Testament with integrated patristic commentary from Church Fathers including John Chrysostom, Cyril of Alexandria, Gregory the Great, Venerable Bede, Nikolai Velimirovich, and Maximos the Confessor.

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
  - Minimal blue markers in the right margin
  - Split-screen commentary viewing (50/50 layout)
  - Hover tooltips showing commentary references
  - Smart cross-referencing to parallel Gospel passages
  - Footnotes with hover tooltips
- **Eusebian Canon System** showing parallel Gospel passages
- **Responsive Design** with mobile-friendly hamburger menu
- **Clean Typography** with paragraph-based formatting
- Live reload during development with Air

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
└── cyril/
    └── luke/
        └── sermons/
            ├── sermon_001/
            │   └── metadata.json
            └── sermon_153/
                └── metadata.json
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
│   │   ├── chrysostom/      # John Chrysostom's works
│   │   │   ├── matthew/     
│   │   │   │   ├── content/ # Homily folders with metadata.json
│   │   │   │   └── source/  # Source XML files
│   │   │   └── john/        
│   │   │       ├── content/ # Homily folders with metadata.json
│   │   │       └── source/  # Source XML files
│   │   └── cyril/           # Cyril of Alexandria's works
│   │       └── luke/        
│   │           └── sermons/ # Sermon folders with metadata.json
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
- **90 Homilies on Matthew** covering the entire Gospel of Matthew
- **88 Homilies on John** covering the entire Gospel of John
- **Cross-Gospel Integration** - When reading Mark or Luke, the system automatically shows relevant Matthew and John homilies for parallel passages

### Cyril of Alexandria (c. 376-444)
- **153 Sermons on Luke** covering the entire Gospel of Luke (manuscript contains only fragments for 154-156)
- Integrated footnotes and textual notes

### Gregory the Great (c. 540-604)
- **40 Homilies on the Gospels** (Forty Gospel Homilies) covering passages from all four Gospels
- Spanning Matthew, Mark, Luke, and John

### Venerable Bede (c. 673-735)
- **50 Homilies on the Gospels** organized in two books covering passages from all four Gospels
- Book I: 25 homilies (I.1 through I.25)
- Book II: 25 homilies (II.1 through II.25)

### Nikolai Velimirovich (1880-1956)
- **Daily Meditations from the Prologue of Ohrid** featuring homilies on Scripture
- Organized by calendar date (In progress)
- Each entry provides spiritual reflection on specific Scripture passages

### Maximos the Confessor (c. 580-662)
- **On the Lord's Prayer** - Spiritual commentary on the Our Father
- Covers both Matthew 6:9-13 and Luke 11:2-4
- Deep theological reflection on the Lord's Prayer

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

## Deployment

The application is configured for deployment on Render.com.

### Render Configuration

1. **Root Directory:** `hypomnema-server`
2. **Build Command:** `go build -o app`
3. **Start Command:** `./app`

The server automatically uses the PORT environment variable provided by Render.

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