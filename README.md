# WCP Widget — Markdown Editor

WYSIWYG markdown file editor with folder browser, multi-instance configuration, Publish to Web, and optional companion host agent for native filesystem access.

**Specification:** [widgetcontextprotocol.com](https://widgetcontextprotocol.com) | **Part of the** [Penrith Beacon WCP](https://penrithbeacon.com) widget suite.

> **WCP 2.1.0 certified.** Full theme reception, orchestration-aware state, Publish to Web, WCP export.

---

## Components

| Component | Default size | Description |
|-----------|:------------:|-------------|
| Markdown Explorer | 12×12 | Main widget — WYSIWYG editor with resizable file tree sidebar |
| Settings | 12×12 | Configure root folder path, theme, and companion agent |
| About | 12×12 | OCI image reference, version, publisher |

---

## Requirements

- Docker and Docker Compose
- (Optional) `wcp-agent-markdown-editor` companion agent — enables host filesystem browsing, drive enumeration, and remote directory creation

---

## Quick Start

```bash
docker run -d \
  --name wcp-widget-markdown-editor \
  -p 3748:3748 \
  -v markdown_workspace:/workspace \
  -e CONTAINER_NAME=wcp-widget-markdown-editor \
  -e WIDGET_PORT=3748 \
  --restart unless-stopped \
  penrithbeacon/wcp-widget-markdown-editor:latest
```

---

## Docker Compose

```yaml
services:
  wcp-widget-markdown-editor:
    build: .
    image: penrithbeacon/wcp-widget-markdown-editor:latest
    container_name: wcp-widget-markdown-editor
    ports:
      - "3748:3748"
    volumes:
      - markdown_workspace:/workspace
    environment:
      - WIDGET_PORT=3748
      - CONTAINER_NAME=wcp-widget-markdown-editor
      - AGENT_PORT=3749
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  markdown_workspace:
    driver: local
```

---

## Setup Guide

### Without companion agent

The widget works immediately after starting. Files are read from and written to the
`/workspace` Docker volume. Use the Settings component to set the root folder path
within the volume.

### With companion agent

The `wcp-agent-markdown-editor` companion agent adds host filesystem access — browse
your local drives and directories from within the widget rather than being limited to
the Docker volume.

1. Download the macOS installer from the **About** component (`GET /widget/agent/installer`)
   or from [GitHub Releases](https://github.com/penrithbeacon/wcp-agent-markdown-editor/releases)
2. Run the `.pkg` installer — the agent starts automatically at login
3. The widget detects the agent automatically; the Settings component confirms its status

The agent listens on `127.0.0.1:3749` and is reachable from Docker via `host.docker.internal:3749`.

---

## WCP Request Headers

All WCP widgets accept these headers on every request. The dashboard sends them automatically.

| Header | Description |
|--------|-------------|
| `Wcp-Instance-Id` | Unique card instance identifier |
| `Wcp-Dashboard-Id` | Dashboard installation identifier |
| `Wcp-Version` | WCP protocol version of the requesting dashboard |
| `Wcp-Widget-Id` | Widget identifier within the dashboard |
| `Wcp-Orchestration-Id` | Active orchestration identifier (for state scoping) |
| `Wcp-Application-Id` | Active application identifier (for state scoping) |

---

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /wcp` | Container Directory — WCP two-tier discovery |
| `GET /widget/wcp` | Widget Manifest with runtime publish status |
| `OPTIONS /wcp` | CORS preflight (all widget routes) |
| `GET /widget/` | Compact dashboard view — Markdown Explorer |
| `GET /widget/explorer/` | Alias for `GET /widget/` |
| `GET /widget/index` | Widget Index — lists all controls |
| `GET /widget/health` | Health check with container name and version |
| `GET /widget/icon.svg` | Widget icon (SVG) |
| `GET /widget/api/guids` | Component UUIDs for orchestration binding |
| `GET /widget/settings/` | Settings component |
| `GET /widget/about/` | About component |
| `GET /widget/logs` | WCP logs protocol — structured log envelope |
| `POST /widget/configure` | Save per-instance configuration |
| `GET /widget/api/files/list` | List files and directories at a path |
| `GET /widget/api/files/read` | Read a file's content |
| `POST /widget/api/files/save` | Write content to a file |
| `POST /widget/api/files/mkdir` | Create a new directory |
| `POST /widget/api/files/rename` | Rename a file or directory |
| `POST /widget/api/files/delete` | Delete a file or directory |
| `POST /widget/publish` | Publish current document as a standalone SPA |
| `DELETE /widget/publish` | Remove published SPA |
| `GET /widget/export.wcp` | Download widget as `.wcp` package |
| `GET /widget/agent/installer` | Companion agent installer (`.pkg`); `503` if not yet bundled |
| `GET /widget/api/agent/status` | Check whether companion agent is reachable |

---

## Data Storage

| Storage | Path | Contents |
|---------|------|----------|
| `markdown_workspace` volume | `/workspace` | Markdown files and folders managed by the widget |

**Backup:**
```bash
docker run --rm \
  -v markdown_workspace:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/workspace-backup.tar.gz /data
```

---

## WCP Compatibility

| Property | Value |
|----------|-------|
| WCP Version | 2.1.0 |
| Widget Version | 1.1.0 |
| Render mode | iframe |
| Auth | None |
| Default card size | 12×12 |
| Multi-instance | Yes |

---

## Technical Details

| Property | Value |
|----------|-------|
| Base image | `python:3.12-slim` |
| Platforms | `linux/amd64`, `linux/arm64` |
| Port | 3748 |
| Framework | Flask 3.0.3 + Flask-CORS 4.0.1 |
| Dependencies | Flask, Flask-CORS, Werkzeug |
| Persistent storage | `markdown_workspace` volume at `/workspace` |

---

## Tags

| Tag | Description |
|-----|-------------|
| `latest` | Most recent stable release |
| `beta` | Current beta release |
| `1.1.0-beta` | Beta — theme card, WCP URL compliance, WCP-compliant SPA, GFM tables, agent-only model |
| `1.0.0` | Initial release — full WCP 2.1.0 compliance, WYSIWYG editor, companion agent support |

---

## Links

- [Penrith Beacon](https://penrithbeacon.com)
- [Widget Context Protocol](https://widgetcontextprotocol.com)
- [Docker Hub](https://hub.docker.com/r/penrithbeacon/wcp-widget-markdown-editor)
- [GitHub](https://github.com/penrithbeacon/wcp-widget-markdown-editor)
