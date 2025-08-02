# Hypomnema Server

A Go-based Bible reader with live reload for development and easy deployment to Render.

## Features
- Fast Go server with embedded templates
- HTMX for dynamic content loading without page refreshes
- Paragraph formatting based on Scrivener's Cambridge Paragraph Bible
- Small gray superscript verse numbers
- Live reload during development with Air

## Development

1. Install Air (if not already installed):
```bash
curl -sSfL https://raw.githubusercontent.com/air-verse/air/master/install.sh | sh -s -- -b ~/go/bin
```

2. Run with live reload:
```bash
cd hypomnema-server
air
```

The server will start on http://localhost:8080 and automatically reload when you make changes.

## Deployment to Render

1. Push to GitHub
2. Connect your repo to Render
3. Render will automatically detect Go and use the `render.yaml` config
4. Your app will be live!

## Project Structure
```
hypomnema-server/
├── main.go           # Main server code
├── templates/        # HTML templates
│   └── index.html   # Main page template
├── static/          # CSS and static files
│   └── styles.css   # Styling
├── .air.toml        # Air configuration
├── go.mod           # Go module file
└── render.yaml      # Render deployment config
```

## Future Features
- Greek/Hebrew text on hover
- Commentary windows
- Cross-references
- Search functionality