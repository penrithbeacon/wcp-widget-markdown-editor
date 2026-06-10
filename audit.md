# Markdown Editor — Audit Record

---

## Latest Audit

- **Date:** 2026-06-10
- **Version:** 1.1.0
- **WCP:** 2.1.0
- **Result:** PASS — clean run, no issues found

## Checklist

| Category | Checks | Passed | Status |
|----------|:------:|:------:|:------:|
| Container | 9 | 9 | PASS |
| Discovery endpoints | 14 | 14 | PASS |
| Standard endpoints | 10 | 10 | PASS |
| New 1.1.0 endpoints | 4 | 4 | PASS |
| Theme reception | 24 (6 × 4 templates) | 24 | PASS |
| Manifest consistency | 10 | 10 | PASS |
| Companion agent installer | 2 | 2 | PASS |
| Security | 1 | 1 | PASS |
| UI standards | 1 | 1 | PASS |
| Documentation | 5 | 5 | PASS |

## Verified Endpoints

```
GET /wcp                          200  type=directory ✓
GET /widget/wcp                   200  uuid+container fields present ✓
OPTIONS /wcp                      200  ✓
GET /widget/                      200  ✓
GET /widget/explorer/             200  ✓
GET /widget/index                 200  ✓
GET /widget/health                200  status=ok, container=wcp-widget-markdown-editor, version=1.1.0 ✓
GET /widget/icon.svg              200  ✓
GET /widget/api/guids             200  explorer+settings+about ✓
GET /widget/settings/             200  ✓
GET /widget/about/                200  ✓
GET /widget/logs                  200  wcp_logs schema ✓
GET /widget/export.wcp            200  ✓
GET /widget/agent/installer       200  (pkg bundled) ✓
GET /widget/api/agent/status      200  available field present ✓
GET /widget/api/themes            200  active+custom fields ✓
GET /widget/api/publish/status    200  published field present ✓
GET /                             200  ✓
```

## Theme Reception (all 4 templates)

All six theme reception elements verified in every template:

| Template | wcp:ready | wcp:request-theme | #wcp-theme= | ?com.doc.wcp | wcp:context | setProperty |
|----------|:---------:|:-----------------:|:-----------:|:------------:|:-----------:|:-----------:|
| widget.html | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| settings.html | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| about.html | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| index.html | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Note: `?com.doc.widgetcontextprotocol=<base64>` is now the primary URL theme form (added in 1.1.0). The `#wcp-theme=` hash form is retained for backward compatibility with dashboard "open in window" links.

## Notes

### No issues found

This was a clean audit pass. All checks passed first time with no fixes required during the run.

### Companion agent installer

`GET /widget/agent/installer` returns `200` — the current `.pkg` (v1.0.0, built 2026-06-10)
is bundled in `src/installers/`. This release includes the encoding fix (UTF-8-sig + latin-1
fallback), new file endpoints (`/files/read`, `/files/write`, `/files/delete`, `/files/rename`),
and the `Uninstall WCP Markdown Editor Agent.app` uninstaller.

### Agent live during audit

The companion agent was running during this audit (`GET /widget/api/agent/status` returned
`available: true`). File browsing and read/write operations verified against a live agent
instance.

---

## History

| Date | Version | WCP | Result |
|------|---------|-----|--------|
| 2026-06-10 | 1.1.0 | 2.1.0 | PASS — clean, no issues |
| 2026-06-09 | 1.0.0 | 2.1.0 | PASS (1 issue found and fixed during audit) |
