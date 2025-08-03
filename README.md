# Hypomnema

A biblical text reader with Eusebian Canon references, built with Go and HTMX.

## Features

- Browse complete KJV New Testament texts
- Chapter navigation with Previous/Next buttons
- Paragraph-based text formatting
- Eusebian Canon numbers in the margin
- Hover tooltips showing parallel Gospel passages
- Clean, responsive interface
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
├── hypomnema-server/      # Go web server
│   ├── main.go           # Main server code
│   ├── templates/        # HTML templates
│   ├── static/          # CSS and static files
│   └── tmp/             # Air build artifacts (git ignored)
├── texts/               # Biblical texts and reference data
│   ├── scripture/       # KJV text files
│   └── reference/       # Eusebian canons, paragraph divisions
├── scripts/             # Python utility scripts
└── README.md
```

## Eusebian Canons

The application displays Eusebian Canon numbers in the left margin of Gospel texts. These ancient cross-references show parallel passages across the four Gospels. Hovering over a canon number reveals the specific verse references.

### Data Files

- `texts/reference/eusebian_canons/verse_to_canon.json` - Maps verses to canon entries
- `texts/reference/eusebian_canons/canon_lookup.json` - Maps canon entries to parallel passages
- `texts/reference/eusebian_canons/eusebian-canons.db` - SQLite database with source data

## Development

### Python Scripts

#### verify_kjv_completeness.py
Verifies that all KJV New Testament books have complete chapters with verse content:
```bash
python scripts/verify_kjv_completeness.py
```

#### generate_canon_lookup_from_sql.py
Generates the Eusebian Canon lookup table from the SQLite database. Creates `canon_lookup.json` which maps canon entries (e.g., "I.1", "XIII.3") to their verse references:
```bash
python scripts/generate_canon_lookup_from_sql.py
```

#### generate_verse_to_canon_mapping.py
Generates the verse-to-canon mapping from the SQLite database. Creates `verse_to_canon.json` which maps verse references to their canon entries:
```bash
python scripts/generate_verse_to_canon_mapping.py
```

### Regenerating Eusebian Canon Data

If you need to rebuild the canon data from the SQLite database:
```bash
python scripts/generate_canon_lookup_from_sql.py
python scripts/generate_verse_to_canon_mapping.py
```

## Deployment

The application is configured for deployment on Render.com:

```bash
go build -o main .
./main
```

The `render.yaml` file contains the deployment configuration.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.