# Hypomnema Project Instructions

## Project Overview
Hypomnema is a biblical text reader and commentary system featuring Greek/Hebrew texts, English translations, and patristic commentaries.

## Key Commands
```bash
# Start the Go server with live reload
cd hypomnema-server
~/go/bin/air

# Or run directly
go run main.go
```

## Project Structure
- `/hypomnema-server/` - Go web server for Bible reader
  - `main.go` - Server code with HTMX endpoints
  - `/templates/` - HTML templates
  - `/static/` - CSS files
- `/texts/` - All text content
  - `/scripture/` - Biblical texts
    - `/old_testament/` - OT books (Septuagint, English)
    - `/new_testament/` - NT books (Greek TR, KJV)
  - `/commentaries/` - Patristic commentaries (Chrysostom)
  - `/reference/` - Supporting data (Eusebian canons, paragraph divisions)
- `/scripts/` - Python utilities for text processing

## Development Guidelines
- Server runs on http://localhost:8080
- Uses HTMX for dynamic content loading
- Paragraph formatting based on Cambridge Paragraph Bible
- Never run git commands - user manages git through IDE

## Important Notes
- Never run git commands - user will do this from terminal
- Text files are organized by language/version/book/chapter
- Each chapter is in format: `bookname_##.txt` (e.g., `matthew_01.txt`)

## Common Tasks
- To add new books: Create folder structure following existing pattern
- To deploy: Use Render with included `render.yaml` config
- To process texts: Use Python scripts in `/scripts/`