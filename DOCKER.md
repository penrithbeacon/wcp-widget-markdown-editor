# WCP Widget: Markdown Editor

WYSIWYG markdown file editor with folder browser, multi-instance configuration, Publish to Web, and companion host agent for native filesystem access.

**Specification:** [widgetcontextprotocol.com](https://widgetcontextprotocol.com) | **Part of the** [Penrith Beacon WCP](https://penrithbeacon.com) widget suite.

> **WCP 2.1.0 certified.** Full theme reception (both URL forms), orchestration-aware state, Publish to Web (WCP-compliant SPA), WCP export.

---

## Components

| Component | Default size | Description |
|-----------|:------------:|-------------|
| Markdown Explorer | 12×12 | Main widget — WYSIWYG editor with resizable file tree sidebar |
| Settings | 12×12 | Configure root folder, theme (built-ins + WCPT import), companion agent status |
| About | 12×12 | OCI image reference, version, publisher, agent installer download |

---

## Quick Start

```bash
docker run -d \
  --name wcp-widget-markdown-editor \
  -p 127.0.0.1:3748:3748 \
  -v markdown_workspace:/workspace \
  -e CONTAINER_NAME=wcp-widget-markdown-editor \
  -e WIDGET_PORT=3748 \
  --add-host host.docker.internal:host-gateway \
  --restart unless-stopped \
  docker.io/penrithbeacon/wcp-widget-markdown-editor:latest
```

---

## Docker Compose

```yaml
services:
  wcp-widget-markdown-editor:
    image: docker.io/penrithbeacon/wcp-widget-markdown-editor:latest
    container_name: wcp-widget-markdown-editor
    ports:
      - "127.0.0.1:3748:3748"
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

The widget UI loads, but file browsing requires the companion agent. Configure the agent first for full functionality.

### With companion agent

The `wcp-agent-markdown-editor` companion agent provides host filesystem access — browse your local drives from within the widget.

1. Download the macOS installer from the **About** component (`GET /widget/agent/installer`) or from [GitHub Releases](https://github.com/penrithbeacon/wcp-agent-markdown-editor/releases)
2. Run the `.pkg` installer — the agent starts automatically at login on `127.0.0.1:3749`
3. The widget detects the agent automatically via `host.docker.internal:3749`
4. Open Settings → set the Root Folder using the Browse picker (shows your host filesystem)

The installer includes `Uninstall WCP Markdown Editor Agent.app` in `/Applications/` for clean removal.

---

## WCP Request Headers

| Header | Required | Description |
|--------|:--------:|-------------|
| `Wcp-Instance-Id` | Yes | Unique card instance identifier |
| `Wcp-Dashboard-Id` | Yes | Dashboard installation identifier |
| `Wcp-Version` | Yes | WCP protocol version of the requesting dashboard |
| `Wcp-Widget-Id` | Yes | Widget identifier within the dashboard |
| `Wcp-Orchestration-Id` | No | Active orchestration identifier |
| `Wcp-Application-Id` | No | Active application identifier |

---

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /wcp` | Container Directory — WCP two-tier discovery |
| `GET /widget/wcp` | Widget Manifest with runtime publish status |
| `GET /widget/` | Markdown Explorer component |
| `GET /widget/settings/` | Settings component |
| `GET /widget/about/` | About component |
| `GET /widget/index` | Widget Index |
| `GET /widget/health` | Health check |
| `GET /widget/icon.svg` | Widget icon |
| `GET /widget/api/guids` | Component UUIDs |
| `GET /widget/logs` | WCP logs protocol |
| `POST /widget/configure` | Save per-instance config: `{ root, theme }` |
| `GET /widget/api/root/validate` | Validate root path + agent reachability |
| `GET /widget/api/files/list` | List files/dirs via agent |
| `GET /widget/api/files/read` | Read file via agent |
| `POST /widget/api/files/save` | Write file via agent |
| `POST /widget/api/files/mkdir` | Create directory via agent |
| `POST /widget/api/files/rename` | Rename via agent: `{ old, new }` |
| `POST /widget/api/files/delete` | Delete via agent |
| `GET /widget/api/agent/status` | Agent reachability check |
| `GET /widget/api/agent/browse` | Proxy: agent directory listing |
| `GET /widget/api/agent/drives` | Proxy: agent volumes/drives |
| `GET /widget/api/themes` | Active theme + custom theme list |
| `POST /widget/api/themes/import` | Import themes from `.wcpt` |
| `DELETE /widget/api/themes/<id>` | Delete a custom theme |
| `POST /widget/publish` | Publish document as WCP-compliant SPA |
| `DELETE /widget/publish` | Remove published SPA |
| `GET /widget/api/publish/status` | Published SPA state + metadata |
| `GET /widget/export.wcp` | Download as `.wcp` package |
| `GET /widget/agent/installer` | Companion agent `.pkg` installer |
| `GET /` | Serves published SPA |

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
| Persistent storage | `markdown_workspace` volume at `/workspace` |

---

## Tags

| Tag | Description |
|-----|-------------|
| `latest` | Most recent stable release |
| `1.1.0-wcp2.1.0` | Theme card, WCP URL compliance, WCP-compliant SPA, GFM tables, agent-only model |
| `1.0.0-wcp2.1.0` | Initial release |

---

## Changelog

### 1.1.0 (2026-06-10) — *includes companion agent v1.0.2 installer*
- **Theme card** — Settings page now shows 3 Penrith Beacon WCP built-in themes (Dark / Light / High Contrast) with "Built-in" badge; custom theme import from `.wcpt` files via checkbox modal with Select All / Deselect All
- **Full-dashboard theme broadcast** — selecting a theme in Settings posts `wcp:theme-apply` to `window.top`, updating the entire dashboard (podium, stave tabs, all widgets)
- **WCP URL theme compliance** — all four HTML templates now support both `?com.doc.widgetcontextprotocol=<base64>` (query string) and `#wcp-theme=<base64>` (hash) forms
- **WCP-compliant published SPA** — `POST /widget/publish` generates HTML with baked-in active theme CSS vars and inline URL reception snippet; full `var(--wcp-color-*)` typography
- **GFM table round-trip** — TipTap Table/TableRow/TableHeader/TableCell extensions added; Turndown GFM plugin preserves pipe table format on save
- **Encoding fix** — agent file reads use `utf-8-sig` with `latin-1` fallback, eliminating `�` replacement characters in files with non-ASCII content
- **Agent-only file model** — all file operations proxy through the companion agent; Docker volume stores widget state only
- **Uninstaller app** — `Uninstall WCP Markdown Editor Agent.app` bundled in agent `.pkg` for clean one-click removal
- **Published page card** — Settings page shows current publish state, source `.md` path, published timestamp, View and Unpublish actions
- **Unpublish button** — toolbar Unpublish button removes the published SPA; settings card updates immediately
- **Manifest fixes** — `/wcp` now includes `type: "directory"`; `/widget/wcp` now includes `uuid` and `container` fields
- **Theme delete fix** — replaced `window.confirm()` with a custom inline modal; `confirm()` is silently blocked in cross-origin iframes by Chromium/Electron 35; delete button now works correctly
- **Companion agent v1.0.2** — (a) fixes UTF-8 write encoding, resolves HTTP 502 on non-ASCII saves; (b) uses `os.scandir()` + `threaded=True`, resolves blank sidecar caused by SMB cold-start latency exceeding browse timeout; (c) installer now shows a welcome screen with product name and version; (d) `preinstall` uses `launchctl bootout` + `pkill` to reliably stop any running agent before upgrade

### 1.0.0 (2026-06-09)
- Initial release — full WCP 2.1.0 compliance, WYSIWYG editor, companion agent support, Publish to Web, WCP export

---

## Source

- [GitHub](https://github.com/penrithbeacon/wcp-widget-markdown-editor)
- [Widget Context Protocol](https://widgetcontextprotocol.com)
- [Penrith Beacon](https://penrithbeacon.com)
