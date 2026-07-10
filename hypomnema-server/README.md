# Hypomnema Server

A Go web server for the Hypomnema biblical text reader with integrated patristic commentary.

## Features
- Go server with HTML templates and HTMX for dynamic content loading
- Paragraph formatting based on Scrivener's Cambridge Paragraph Bible
- Split-screen commentary viewing (50/50 layout)
- Eusebian canon cross-references with clickable parallel passage modals
- Footnotes with hover tooltips
- Responsive design with mobile hamburger menu
- JSON REST API at `/api/v1` (package `apiv1/`, Swagger docs at `/api/v1/docs`) — see the root README for endpoint details
- Live reload during development with Air

## Development

1. Install Air (if not already installed):
```bash
curl -sSfL https://raw.githubusercontent.com/air-verse/air/master/install.sh | sh -s -- -b ~/go/bin
```

2. Run with live reload:
```bash
cd hypomnema-server
~/go/bin/air
```

The server will start on http://localhost:8080 and automatically reload when you make changes.

### Running without Air

```bash
cd hypomnema-server
go run main.go
```

## Deployment to Render

1. **Root Directory:** `hypomnema-server`
2. **Build Command:** `go build -o app`
3. **Start Command:** `./app`

The server automatically uses the PORT environment variable provided by Render.

## Project Structure
```
hypomnema-server/
├── main.go           # Main server code with all routing and logic
├── apiv1/            # JSON REST API package (mounted at /api/v1)
├── templates/        # HTML templates
│   ├── index.html    # Main page template
│   └── homily.html   # Commentary viewing template
├── static/           # CSS and static files
│   └── styles.css    # Styling
├── .air.toml         # Air configuration
├── go.mod            # Go module file
└── render.yaml       # Render deployment config
```
