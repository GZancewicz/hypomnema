# Hypomnema

A biblical text reader featuring the King James Version (KJV) New Testament with integrated patristic commentary from Church Fathers including John Chrysostom and Cyril of Alexandria.

## Features

- **Complete KJV New Testament** with chapter-by-chapter navigation
- **Patristic Commentary Integration**:
  - John Chrysostom's 90 homilies on Matthew
  - John Chrysostom's 88 homilies on John
  - Cyril of Alexandria's 156 sermons on Luke
  - Minimal blue markers in the right margin
  - Split-screen commentary viewing (50/50 layout)
  - Hover tooltips showing commentary references
  - Smart cross-referencing to parallel Gospel passages
  - Footnotes with hover tooltips
- **Eusebian Canon System** showing parallel Gospel passages
- **Responsive Design** with mobile-friendly hamburger menu
- **Clean Typography** with paragraph-based formatting
- Live reload during development with Air

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
│   ├── templates/           # HTML templates
│   ├── static/              # CSS and static files
│   └── tmp/                 # Air build artifacts (git ignored)
├── texts/                   # Biblical texts and reference data
│   ├── scripture/           # KJV text files organized by book/chapter
│   ├── commentaries/        # Patristic commentaries
│   │   ├── chrysostom/      # John Chrysostom's works
│   │   │   ├── matthew/     # Homilies on Matthew with footnotes
│   │   │   └── john/        # Homilies on John with footnotes
│   │   └── cyril/           # Cyril of Alexandria's works
│   │       └── luke/        # Sermons on Luke
│   └── reference/           # Eusebian canons, paragraph divisions
├── scripts/                 # Python utility scripts
├── CLAUDE.md               # Development notes and instructions
└── README.md
```

## Eusebian Canons

The application displays Eusebian Canon numbers in the left margin of Gospel texts. These ancient cross-references show parallel passages across the four Gospels. Hovering over a canon number reveals the specific verse references.

## Patristic Commentary

The application integrates complete patristic commentary on the Gospels:

### John Chrysostom
- **90 Homilies on Matthew** covering the entire Gospel of Matthew
- **88 Homilies on John** covering the entire Gospel of John
- **Cross-Gospel Integration** - When reading Mark or Luke, the system automatically shows relevant Matthew and John homilies for parallel passages

### Cyril of Alexandria
- **156 Sermons on Luke** covering the entire Gospel of Luke
- Integrated footnotes and textual notes

### Features
- **Inline References** showing which homilies/sermons discuss each passage
- **Footnotes** with hover tooltips for additional context
- **Split-screen Reading** for studying scripture alongside commentary
- **Unified Commentary System** using common data structures for all sources

### Data Files

**Chrysostom Commentary:**

*Matthew Homilies:*
- `texts/commentaries/chrysostom/matthew/chrysostom_matthew_homilies.xml` - Complete homilies in ThML format
- `texts/commentaries/chrysostom/matthew/footnotes.json` - Extracted footnotes with renumbering
- `texts/commentaries/chrysostom/matthew/matthew_verse_to_homilies.json` - Verse-to-homily mapping
- `texts/commentaries/chrysostom/matthew/homily_coverage.json` - Homily passage coverage

*John Homilies:*
- `texts/commentaries/chrysostom/john/chrysostom_john_homilies.xml` - Complete homilies in ThML format
- `texts/commentaries/chrysostom/john/footnotes.json` - Extracted footnotes with renumbering
- `texts/commentaries/chrysostom/john/john_verse_to_homilies.json` - Verse-to-homily mapping
- `texts/commentaries/chrysostom/john/homily_coverage.json` - Homily passage coverage

**Cyril Commentary:**

*Luke Sermons:*
- `texts/commentaries/cyril/luke/cyril_on_luke_*.htm` - HTML sermon files (15 files)
- `texts/commentaries/cyril/luke/luke_verse_to_homilies.json` - Verse-to-sermon mapping
- `texts/commentaries/cyril/luke/homily_coverage.json` - Sermon passage coverage
- `texts/commentaries/cyril/luke/footnotes.json` - Extracted footnotes

**Eusebian Canons:**
- `texts/reference/eusebian_canons/verse_to_canon.json` - Maps verses to canon entries
- `texts/reference/eusebian_canons/canon_lookup.json` - Maps canon entries to parallel passages
- `texts/reference/eusebian_canons/eusebian-canons.db` - SQLite database with source data

## Development

### Python Scripts

#### Text Processing Scripts

**extract_footnotes_to_json.py** - Extracts footnotes from Chrysostom's Matthew homilies ThML XML:
```bash
python scripts/extract_footnotes_to_json.py
```

**extract_john_footnotes.py** - Extracts footnotes from Chrysostom's John homilies ThML XML:
```bash
python scripts/extract_john_footnotes.py
```

**split_kjv_into_chapters.py** - Splits combined KJV book files into individual chapter files:
```bash
python scripts/split_kjv_into_chapters.py
```

**check_kjv_completeness.py** - Verifies all KJV chapters are present and properly formatted:
```bash
python scripts/check_kjv_completeness.py
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

To rebuild Eusebian Canon data:
```bash
python scripts/generate_canon_lookup_from_sql.py
python scripts/generate_verse_to_canon_mapping.py
```

To extract Chrysostom footnotes:
```bash
python scripts/extract_footnotes_to_json.py
python scripts/extract_john_footnotes.py
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