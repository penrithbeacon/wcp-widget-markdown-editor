# Markdown Editor — Specification

> WCP Widget Specification
> Version 1.0.0 · WCP 2.1.0
> Last updated: 2026-06-09

---

## Overview

A WYSIWYG markdown file editor with an integrated folder browser sidebar. Supports
TipTap rich-text editing with Markdown round-trip conversion, per-instance root folder
configuration, Publish to Web (SPA export), and WCP package export. An optional
companion host agent (`wcp-agent-markdown-editor`) extends the widget with native
filesystem access beyond the Docker volume.

---

## Components

| Component | ID | Default Size | Role | Description |
|-----------|-----|:------------:|------|-------------|
| Markdown Explorer | `29a18781-9d6a-47bd-835b-a5e6a05dda77` | 12×12 | widget | Main editor — resizable file tree sidebar + WYSIWYG editing canvas |
| Settings | `91016224-ee5c-4bfe-9d1f-bf14f4212319` | 12×12 | widget | Per-instance config: root folder, theme, companion agent status |
| About | `c3f33fb2-a2c0-4d8b-9d88-cdb14c94ca5c` | 12×12 | widget | OCI image reference, version, publisher, agent installer download |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/wcp` | GET | Container Directory — WCP two-tier discovery |
| `/widget/wcp` | GET | Widget Manifest with runtime publish status |
| `/wcp` | OPTIONS | CORS preflight (all widget routes) |
| `/widget/<path>` | OPTIONS | CORS preflight (per-path) |
| `/widget/` | GET | Compact dashboard view — Markdown Explorer |
| `/widget/explorer/` | GET | Alias for `GET /widget/` |
| `/widget/index` | GET | Widget Index — lists all controls |
| `/widget/health` | GET | Health check: `{ status, name, container, version }` |
| `/widget/icon.svg` | GET | Widget icon (SVG) |
| `/widget/api/guids` | GET | Component UUIDs for orchestration binding |
| `/widget/settings/` | GET | Settings component |
| `/widget/about/` | GET | About component |
| `/widget/logs` | GET | WCP logs protocol — structured log envelope |
| `/widget/configure` | POST | Save per-instance configuration (JSON body) |
| `/widget/api/files/list` | GET | List files/directories: `?path=<path>` |
| `/widget/api/files/read` | GET | Read file content: `?path=<path>` |
| `/widget/api/files/save` | POST | Write file: `{ path, content }` |
| `/widget/api/files/mkdir` | POST | Create directory: `{ path }` |
| `/widget/api/files/rename` | POST | Rename: `{ old_path, new_path }` |
| `/widget/api/files/delete` | POST | Delete: `{ path }` |
| `/widget/publish` | POST | Publish document as standalone SPA |
| `/widget/publish` | DELETE | Remove published SPA |
| `/widget/export.wcp` | GET | Download widget as `.wcp` package |
| `/widget/agent/installer` | GET | Companion agent `.pkg` installer; `503` if not bundled |
| `/widget/api/agent/status` | GET | Agent reachability: `{ available: bool }` |
| `/` | GET | Root redirect / landing |

---

## Features

- WYSIWYG editing via TipTap — Bold, Italic, Underline, Strike, H1–H3, ordered/unordered lists, blockquote, inline code, code block, horizontal rule
- Markdown ↔ HTML round-trip conversion using marked.js (render) and Turndown.js (export)
- Resizable sidebar with file tree — single-click to select, double-click to navigate into folders
- Splitter layout persisted via `localStorage` per-instance
- Multi-instance support — each card slot has independent configuration scoped by `Wcp-Instance-Id`
- Root folder configuration — any subdirectory within `/workspace` can be set as the active root
- Companion agent integration — `wcp-agent-markdown-editor` on `127.0.0.1:3749` enables host filesystem browsing, drive enumeration, and remote directory creation
- Publish to Web — exports the current document as a standalone SPA served from the container
- WCP export — packages the widget as a `.wcp` file for sharing or importing into another host
- Full WCP 2.1.0 theme reception — all five theme elements implemented in every HTML template

---

## Configuration

### Per-instance (POST /widget/configure)

```json
{
  "instance_id": "<Wcp-Instance-Id>",
  "root_path": "/workspace/<subdirectory>"
}
```

Configuration is stored in memory and resets on container restart. The Docker volume persists file content independently of configuration.

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
| Tag | `1.0.0` |
| Port | `3748` |
| Volumes | `markdown_workspace:/workspace` |
| Extra hosts | `host.docker.internal:host-gateway` |

---

## Version History

| Version | WCP | Date | Notes |
|---------|-----|------|-------|
| 1.0.0 | 2.1.0 | 2026-06-09 | Initial release — full WCP 2.1.0 compliance, WYSIWYG editor, companion agent support, Publish to Web, WCP export |
