# Markdown Editor — Specification

> WCP Widget Specification
> Version 1.1.0 · WCP 2.1.0
> Last updated: 2026-06-10

---

## Overview

A WYSIWYG markdown file editor with an integrated folder browser sidebar. Supports
TipTap rich-text editing with Markdown round-trip conversion (including GFM tables),
per-instance root folder configuration, Publish to Web (WCP-compliant SPA export with
baked-in theme and URL theme reception), and WCP package export. Requires the companion
host agent (`wcp-agent-markdown-editor`) for filesystem access — all file operations
proxy through the agent; the Docker volume stores widget state only (config, published SPA).

---

## Components

| Component | ID | Default Size | Role | Description |
|-----------|-----|:------------:|------|-------------|
| Markdown Explorer | `29a18781-9d6a-47bd-835b-a5e6a05dda77` | 12×12 | widget | Main editor — resizable file tree sidebar + WYSIWYG editing canvas |
| Settings | `91016224-ee5c-4bfe-9d1f-bf14f4212319` | 12×12 | widget | Per-instance config: root folder, theme card (built-ins + WCPT import), companion agent status, published page card |
| About | `c3f33fb2-a2c0-4d8b-9d88-cdb14c94ca5c` | 12×12 | widget | OCI image reference, version, publisher, agent installer download |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/wcp` | GET | Container Directory — WCP two-tier discovery (`type: "directory"`) |
| `/widget/wcp` | GET | Widget Manifest with runtime publish status and container metadata |
| `/wcp` | OPTIONS | CORS preflight |
| `/widget/<path>` | OPTIONS | CORS preflight (per-path) |
| `/widget/` | GET | Markdown Explorer component |
| `/widget/explorer/` | GET | Alias for `GET /widget/` |
| `/widget/index` | GET | Widget Index — lists all components |
| `/widget/health` | GET | Health check: `{ status, name, container, version }` |
| `/widget/icon.svg` | GET | Widget icon (SVG) |
| `/widget/api/guids` | GET | Component UUIDs for orchestration binding |
| `/widget/settings/` | GET | Settings component |
| `/widget/about/` | GET | About component |
| `/widget/logs` | GET | WCP logs protocol — structured log envelope |
| `/widget/configure` | POST | Save per-instance configuration: `{ root, theme }` |
| `/widget/api/root/validate` | GET | Validate configured root path and agent reachability |
| `/widget/api/files/list` | GET | List files/directories via agent: `?path=<abs-path>` |
| `/widget/api/files/read` | GET | Read file content via agent: `?path=<abs-path>` |
| `/widget/api/files/save` | POST | Write file via agent: `{ path, content }` |
| `/widget/api/files/mkdir` | POST | Create directory via agent: `{ path }` |
| `/widget/api/files/rename` | POST | Rename via agent: `{ old_path, new_path }` |
| `/widget/api/files/delete` | POST | Delete via agent: `{ path }` |
| `/widget/api/agent/status` | GET | Agent reachability: `{ available: bool, agent: {...} }` |
| `/widget/api/agent/browse` | GET | Proxy to agent directory listing: `?path=<path>` |
| `/widget/api/agent/drives` | GET | Proxy to agent drives/volumes list |
| `/widget/api/themes` | GET | Active theme ID and custom theme list for instance |
| `/widget/api/themes/import` | POST | Import themes from WCPT: `{ themes: [...] }` — deduplicates by UUID |
| `/widget/api/themes/<id>` | DELETE | Remove a custom theme by ID or UUID |
| `/widget/publish` | POST | Publish document as WCP-compliant standalone SPA: `{ html, title, source_path }` |
| `/widget/publish` | DELETE | Remove published SPA |
| `/widget/api/publish/status` | GET | Published SPA state: `{ published, title, source_path, published_at, url }` |
| `/widget/export.wcp` | GET | Download widget as `.wcp` package |
| `/widget/agent/installer` | GET | Companion agent `.pkg` installer; `503` if not bundled |
| `/` | GET | Serves published SPA; `404` if nothing published |

---

## Features

### Editor
- WYSIWYG editing via TipTap — Bold, Italic, Underline, Strike, H1–H3, ordered/unordered lists, blockquote, inline code, code block, horizontal rule, **tables** (GFM round-trip)
- Markdown ↔ HTML round-trip: `marked.js` (render) + `Turndown.js` with `turndown-plugin-gfm` (export — preserves pipe table format)
- Resizable sidebar file tree — single-click to select, double-click to navigate; `#`-prefixed and dot-prefixed entries hidden; case-insensitive alphabetical sort, directories first
- Splitter layout persisted via `localStorage` per-instance
- Unpublish button removes the published SPA from the container root

### Agent integration (required for file access)
- All file operations (list, read, write, mkdir, rename, delete) proxy through `wcp-agent-markdown-editor` on `127.0.0.1:3749`
- Agent gate page shown when agent is unreachable; no-root gate page shown when root is unconfigured
- Full-screen folder picker with Favourites + Locations sidebar, resizable splitter, and path-in-header display
- Companion agent installer bundled at `GET /widget/agent/installer`
- Uninstaller app (`Uninstall WCP Markdown Editor Agent.app`) bundled in the agent `.pkg`

### Theme system
- Settings page theme card: 3 Penrith Beacon WCP built-in themes (Dark / Light / High Contrast) with "Built-in" badge
- Custom theme import from `.wcpt` files (ZIP archives) via JSZip — checkbox select modal with Select All / Deselect All
- Selected theme broadcasts `wcp:theme-apply` to `window.top` — updates full dashboard (podium, stave tabs, all widgets)
- Legacy theme IDs (`default`, `mocha`, `latte`, `frappe`) normalised to `dark` server-side

### WCP compliance
- Full WCP 2.1.0 theme reception in all four HTML templates
- Both URL theme forms supported: `?com.doc.widgetcontextprotocol=<base64>` and `#wcp-theme=<base64>`
- Published SPA bakes in active theme CSS vars + injects URL reception snippet at publish time

### Multi-instance
- Each card slot has independent configuration scoped by `Wcp-Instance-Id`
- Config persisted to `/workspace/.widget-config.json` on the Docker volume

---

## Configuration

### Per-instance (`POST /widget/configure`)

```json
{
  "root":          "/Users/you/Documents/notes",
  "theme":         "dark"
}
```

Configuration is persisted to `/workspace/.widget-config.json` and survives container restarts.
File access requires the companion agent — the `root` value is an absolute path on the host machine,
not a path within the Docker volume.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WIDGET_PORT` | `3748` | Port the Flask server listens on |
| `CONTAINER_NAME` | `wcp-widget-markdown-editor` | Container name reported in health responses |
| `AGENT_PORT` | `3749` | Port where the companion agent is expected |

---

## Docker

| Property | Value |
|----------|-------|
| Image | `docker.io/penrithbeacon/wcp-widget-markdown-editor` |
| Tag | `1.1.0-wcp2.1.0` |
| Port | `3748` |
| Volumes | `markdown_workspace:/workspace` |
| Extra hosts | `host.docker.internal:host-gateway` |

---

## Version History

| Version | WCP | Date | Notes |
|---------|-----|------|-------|
| 1.1.0 | 2.1.0 | 2026-06-10 | Theme card (3 PB built-ins + WCPT import modal), WCP URL theme compliance (both forms, all templates), WCP-compliant published SPA (baked theme + URL reception), full-dashboard theme broadcast, GFM table round-trip, encoding fix (UTF-8-sig + latin-1 fallback), agent-only file model, uninstaller app in agent .pkg, published page card in settings, unpublish button |
| 1.0.0 | 2.1.0 | 2026-06-09 | Initial release — full WCP 2.1.0 compliance, WYSIWYG editor, companion agent support, Publish to Web, WCP export |
