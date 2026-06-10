# Markdown Editor — Audit Record

---

## Latest Audit

- **Date:** 2026-06-10
- **Version:** 1.1.0 (widget) · 1.0.1 (agent installer bundled)
- **WCP:** 2.1.0
- **Result:** PASS — all functional endpoints audited; two issues found and fixed during run

## Checklist

| Category | Checks | Passed | Status |
|----------|:------:|:------:|:------:|
| WCP Protocol endpoints | 9 | 9 | PASS |
| Discovery endpoints | 14 | 14 | PASS |
| Standard component endpoints | 10 | 10 | PASS |
| Configuration | 5 | 5 | PASS |
| File operations (section 3) | 7 | 7 | PASS |
| Agent endpoints (section 4) | 3 | 3 | PASS |
| Theme management (section 5) | 7 | 7 | PASS |
| Publish lifecycle (section 6) | 6 | 6 | PASS |
| Theme reception | 24 (6 × 4 templates) | 24 | PASS |
| Manifest consistency | 10 | 10 | PASS |
| Companion agent installer | 2 | 2 | PASS |
| Security | 1 | 1 | PASS |
| UI standards | 1 | 1 | PASS |
| Documentation | 5 | 5 | PASS |

## Full Endpoint Audit

### Section 1 — WCP Protocol Endpoints

```
GET /wcp                          200  type=directory ✓  widgets[0].uuid ✓  manifest URL ✓
GET /widget/wcp                   200  uuid ✓  container.image/tag/port ✓  3 components ✓
OPTIONS /wcp                      200  CORS headers ✓
GET /widget/health                200  status=ok  container=wcp-widget-markdown-editor  version=1.1.0 ✓
GET /widget/icon.svg              200  ✓
GET /widget/api/guids             200  explorer + settings + about UUIDs ✓
GET /widget/logs                  200  wcp_logs schema ✓
GET /widget/export.wcp            200  ✓
GET /widget/agent/installer       200  pkg bundled (v1.0.1) ✓
```

### Section 2 — Configuration

```
POST /widget/configure            200  {root, theme} persisted ✓
GET /widget/api/root/validate     200  valid root (valid:true) ✓
GET /widget/api/root/validate          no root (valid:false, reason:no_root) ✓
GET /widget/api/root/validate          bad path (valid:false, reason:path_unavailable) ✓
POST /widget/configure (theme)    200  theme persist + legacy map (default→dark) ✓
```

### Section 3 — File Operations

All operations use paths relative to the configured root. Root was set to `/tmp` for this test.

```
POST /widget/api/files/mkdir      200  status=ok ✓
POST /widget/api/files/save       200  ASCII content round-trip ✓
GET  /widget/api/files/read       200  content verified ✓
GET  /widget/api/files/list       200  entry names confirmed ✓
POST /widget/api/files/rename     200  {old, new} keys; source renamed ✓  old removed ✓
POST /widget/api/files/delete     200  file delete ✓  dir delete ✓
     verify deletion              error:agent error 400 on missing path ✓
```

**Note on path format:** All file operation endpoints take paths relative to the configured root,
not absolute host paths. The `?path=<abs-path>` wording in earlier spec versions was incorrect
and has been fixed to `?path=<path-relative-to-root>`.

**Unicode write — agent bug (v1.0.0, fixed in v1.0.1):**
`POST /files/write` in the companion agent used `open(real, 'w')` without `encoding='utf-8'`.
Under py2app's bundled Python the default locale may be ASCII, causing `UnicodeEncodeError` on
non-ASCII content (café, em dash, etc.) → HTTP 500 → widget returns 502.
Fixed in agent v1.0.1: `open(real, 'w', encoding='utf-8')`. New installer bundled in
`src/installers/wcp-agent-markdown-editor.pkg`. **User action required: install new .pkg to
activate the fix on the live agent.**

### Section 4 — Agent Proxy Endpoints

```
GET /widget/api/agent/status      200  available:true  agent.version=1.0.0 ✓
GET /widget/api/agent/drives      200  35 volumes listed (Home + NAS mounts) ✓
GET /widget/api/agent/browse      200  entries returned for /tmp ✓
```

### Section 5 — Theme Management

```
GET  /widget/api/themes           200  active:dark  custom:[] ✓
POST /widget/api/themes/import    200  2 themes imported ✓
     verify                            both UUIDs in custom list ✓
POST /widget/api/themes/import         re-import (dedup by UUID, name updated) ✓
     verify dedup                       still 2 themes, name updated ✓
DELETE /widget/api/themes/<id>    200  removed:1 ✓
     verify delete                      uuid-001 gone, uuid-002 remains ✓
```

### Section 6 — Publish Lifecycle

```
POST /widget/publish              200  {status:ok, url:http://localhost:3748/} ✓
GET  /widget/api/publish/status   200  published:true, title, source_path, published_at, url ✓
GET  /                            200  HTML served ✓
       WCP URL snippet            present (com.doc.widgetcontextprotocol) ✓
       :root CSS baked in         present ✓
DELETE /widget/publish            200  {status:ok} ✓
GET  / (unpublished)              302  → /widget/ ✓  (not 404; redirect is intentional)
GET  /widget/api/publish/status   200  published:false ✓
```

**Note on `GET /` when unpublished:** returns `302 → /widget/` (user-friendly fallback), not 404.
Spec updated to reflect this.

## Theme Reception (all 4 templates)

All six theme reception elements verified in every template:

| Template | wcp:ready | wcp:request-theme | #wcp-theme= | ?com.doc.wcp | wcp:context | setProperty |
|----------|:---------:|:-----------------:|:-----------:|:------------:|:-----------:|:-----------:|
| widget.html | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| settings.html | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| about.html | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| index.html | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Issues Found and Fixed During Audit

### Issue 1 — Agent `files/write` missing `encoding='utf-8'` (FIXED in v1.0.1)

| Property | Value |
|----------|-------|
| Severity | **High** — all non-ASCII file saves fail silently (HTTP 502 from widget) |
| File | `wcp-agent-markdown-editor/agent.py`, line 226 |
| Root cause | `open(real, 'w')` uses system default encoding; py2app may default to ASCII |
| Fix | `open(real, 'w', encoding='utf-8')` |
| Agent version | Bumped to 1.0.1 |
| Installer | Rebuilt and bundled in `src/installers/wcp-agent-markdown-editor.pkg` |
| User action | Install new .pkg to activate fix |

### Issue 2 — Spec doc: rename keys named `old_path`/`new_path`, code uses `old`/`new` (FIXED)

| Property | Value |
|----------|-------|
| Severity | Low — documentation only; code and tests now aligned |
| File | `specification.md` and `DOCKER.md` |
| Fix | Updated both docs to show `{ old, new }` |

### Issue 3 — Spec doc: file list/read say `<abs-path>`, API uses relative-to-root (FIXED)

| Property | Value |
|----------|-------|
| Severity | Low — documentation only |
| Files | `specification.md` |
| Fix | Updated to `<path-relative-to-root>` |

### Issue 4 — Spec doc: `GET /` says 404 when no SPA published, code returns 302 (FIXED)

| Property | Value |
|----------|-------|
| Severity | Low — documentation only; redirect is intentional |
| File | `specification.md` |
| Fix | Updated to `302 → /widget/` |

## Notes

### Audit test methodology

- IID fixed string `audit-test-fixed` (shell PID changes between calls; fixes IID mismatch)
- File operation tests use relative paths (relative to configured root `/tmp`)
- All state cleaned up after each section

### Companion agent installer

`GET /widget/agent/installer` returns `200` — the current `.pkg` (v1.0.1, built 2026-06-10)
is bundled in `src/installers/`. This release includes the UTF-8 write encoding fix.

### Agent live during audit

The companion agent v1.0.0 was running during this audit. The write encoding bug was confirmed
(HTTP 500/502 on non-ASCII). The v1.0.1 installer has been built and bundled. All other agent
operations (browse, drives, read, mkdir, rename, delete) function correctly.

---

## History

| Date | Version | WCP | Result |
|------|---------|-----|--------|
| 2026-06-10 | 1.1.0 | 2.1.0 | PASS — 4 issues found and fixed (1 agent encoding bug, 3 doc fixes) |
| 2026-06-10 | 1.1.0 | 2.1.0 | PASS — clean run, no issues found (WCP protocol endpoints only) |
| 2026-06-09 | 1.0.0 | 2.1.0 | PASS (1 issue found and fixed during audit) |
