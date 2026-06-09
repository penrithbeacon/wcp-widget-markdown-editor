# Markdown Editor — Audit Record

---

## Latest Audit

- **Date:** 2026-06-09
- **Version:** 1.0.0
- **WCP:** 2.1.0
- **Result:** PASS (one issue found and fixed during this audit run)

## Checklist

| Category | Checks | Passed | Status |
|----------|:------:|:------:|:------:|
| Container | 9 | 9 | PASS |
| Discovery endpoints | 14 | 14 | PASS |
| Standard endpoints | 6 | 6 | PASS |
| Theme reception | 20 (5 × 4 templates) | 20 | PASS |
| Manifest consistency | 8 | 8 | PASS |
| Companion agent | 2 | 2 | PASS |
| Documentation | 4 | 4 | PASS |

## Notes

### Issue found and fixed during audit

**Theme reception — missing `#wcp-theme=` hash block (all 4 templates)**

All four HTML templates (`widget.html`, `about.html`, `settings.html`, `index.html`)
contained the legacy `wcp:theme=` (colon, URL-encoded) hash reading pattern but were
missing the WCP 2.x standard `#wcp-theme=` (hyphen, base64-encoded) block.

Fixed by adding the standard block to all four templates immediately after the
`wcp:request-theme` postMessage call:

```javascript
if (window.location.hash.startsWith('#wcp-theme=')) {
  try {
    const _fvars = JSON.parse(atob(window.location.hash.slice(11)));
    for (const [k, v] of Object.entries(_fvars)) document.documentElement.style.setProperty(k, v);
  } catch {}
}
```

Container rebuilt and re-verified after fix. All 5 theme reception elements now
present in all 4 templates.

### Companion agent installer

`GET /widget/agent/installer` returns `503` — correct and expected. The companion
agent (`wcp-agent-markdown-editor`) has not yet been built. The endpoint returns
503 (not 404) signalling "not yet available" rather than "does not exist". This
is compliant behaviour per the WCP spec.

### File API path format

The file API (`/widget/api/files/*`) uses **relative paths** within the workspace
root. Absolute paths (e.g. `/workspace`) are correctly rejected with 400 via the
`safe_path()` path traversal guard. This is correct security behaviour; documentation
updated to reflect relative-path usage.

---

## Dry-Run Beta Release Summary (2026-06-09)

**Stage:** Beta | **Mode:** Dry Run

### Checks that passed ✅

- Container starts cleanly from `docker compose up -d`
- `GET /wcp` → 200, correct JSON structure
- `GET /widget/wcp` → 200, all required manifest fields present, 3 components
- `OPTIONS /wcp` → 200
- `GET /widget/` → 200 HTML
- `GET /widget/explorer/` → 200 HTML
- `GET /widget/index` → 200 HTML
- `GET /widget/health` → 200, `status: ok`, container name correct
- `GET /widget/icon.svg` → 200 `image/svg+xml`
- `GET /widget/api/guids` → 200, all 3 component UUIDs present
- `GET /widget/settings/` → 200 HTML
- `GET /widget/about/` → 200 HTML
- `GET /widget/logs` → 200, WCP logs 1.0 schema, `wcp_logs`, `component`, `schema`, `entries` all present
- `GET /widget/export.wcp` → 200
- `GET /widget/agent/installer` → 503 (correct graceful degradation)
- `GET /widget/api/agent/status` → 200, `{ "available": false }` (correct, no agent running)
- Theme reception: all 5 elements in all 4 templates (after fix applied)
- README.md generated in standard template format
- DOCKER.md generated in standard template format
- specification.md generated with full endpoint table and component UUIDs

### Issue found and fixed ❌→✅

- `#wcp-theme=` hash reading missing from all 4 templates — **fixed** (see Notes above)

### DRY RUN — commands that would execute in a live beta release

```bash
# Docker Hub — would execute:
docker buildx create --use --name wcp-builder
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t penrithbeacon/wcp-widget-markdown-editor:1.0.0-beta \
  -t penrithbeacon/wcp-widget-markdown-editor:beta \
  --push \
  /Volumes/dashboard/wcp-widget-markdown-editor/

# Docker Hub description — would execute:
# PATCH https://hub.docker.com/v2/repositories/penrithbeacon/wcp-widget-markdown-editor/
# with DOCKER.md content as full_description

# GitHub tag — would execute:
git tag v1.0.0-beta
git push origin v1.0.0-beta
gh release create v1.0.0-beta \
  --title "v1.0.0-beta" \
  --prerelease \
  --notes "Beta release — first public build. WCP 2.1.0 certified." \
  --repo penrithbeacon/wcp-widget-markdown-editor
```

### Verdict

> **This release is ready to go live** (pending developer consent for each public push).
> The one issue found (`#wcp-theme=` hash reading) was identified and fixed during this
> dry run. Container is rebuilt and re-verified. All checks now pass.

---

## History

| Date | Version | WCP | Result |
|------|---------|-----|--------|
| 2026-06-09 | 1.0.0 | 2.1.0 | PASS (1 issue found and fixed) |
