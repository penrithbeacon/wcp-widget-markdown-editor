# wcp-widget-markdown-editor

A WCP 2.1.0 compliant widget that provides a WYSIWYG Markdown editor with file explorer,
folder navigation, and optional Publish to Web functionality.

Designed for [Penrith Beacon](https://penrithbeacon.com) and any WCP 2.1.0 compatible host.

---

## Features

- **WYSIWYG editing** via TipTap (Bold, Italic, Underline, Strike, H1–H3, lists, blockquote, code, HR)
- **File explorer** with single-click selection and double-click folder navigation
- **Splitter layout** — resizable sidebar, persisted via localStorage
- **Markdown ↔ HTML conversion** using marked.js and Turndown.js
- **Multi-instance support** — each pinboard slot has independent config
- **Root folder configuration** — set any path within the Docker volume
- **Companion agent** — `wcp-agent-markdown-editor` enables host filesystem browsing and drive enumeration
- **Publish to Web** — export the current document as a standalone SPA served from the container
- **WCP export** — download a `.wcp` package for sharing/importing
- **Three components**: Explorer (main), Settings, About

---

## Quick Start

```bash
# Pull and run
docker compose up -d

# Verify
curl -s http://localhost:3748/widget/health | python3 -m json.tool
```

Open Penrith Beacon → Pinboard → Add Widget → `http://localhost:3748/widget/wcp`

---

## Ports

| Service | Port |
|---------|------|
| Widget | `3748` |
| Companion agent (optional) | `3749` |

---

## Companion Agent

The `wcp-agent-markdown-editor` companion agent enables:

- Host filesystem browsing (folder picker in Settings)
- Drive/volume enumeration
- Directory creation from within the widget

Download the macOS installer from the Settings component or from
[GitHub Releases](https://github.com/penrithbeacon/wcp-agent-markdown-editor/releases).

---

## Components

| Component | Path | Role |
|-----------|------|------|
| Markdown Explorer | `/widget/` | Main widget — editor + file tree |
| Settings | `/widget/settings/` | Configure root path, theme, agent |
| About | `/widget/about/` | OCI reference, version, author |

---

## Docker Image

```
penrithbeacon/wcp-widget-markdown-editor:latest
```

[Docker Hub](https://hub.docker.com/r/penrithbeacon/wcp-widget-markdown-editor)

---

## Author

Anthony Harrison · [widgets@penrithbeacon.com](mailto:widgets@penrithbeacon.com) · [penrithbeacon.com](https://penrithbeacon.com)

GitHub: [penrithbeacon/wcp-widget-markdown-editor](https://github.com/penrithbeacon/wcp-widget-markdown-editor)
