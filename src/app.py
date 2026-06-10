import os
import json
import uuid
import zipfile
import io
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, render_template, send_file, redirect, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PORT          = int(os.environ.get('WIDGET_PORT', 3748))
CONTAINER     = os.environ.get('CONTAINER_NAME', 'wcp-widget-markdown-editor')
VERSION       = '1.0.0'
WORKSPACE     = '/workspace'          # Docker volume — state only (config, guids, published)
AGENT_PORT    = int(os.environ.get('AGENT_PORT', 3749))
AGENT_BASE    = f'http://host.docker.internal:{AGENT_PORT}'

CONFIG_FILE   = os.path.join(WORKSPACE, '.widget-config.json')
GUID_FILE     = os.path.join(WORKSPACE, '.widget-guids.json')
PUBLISHED_DIR = os.path.join(WORKSPACE, '.published')

# Penrith Beacon built-in WCP theme vars — mirrors BUILTIN_THEMES in the dashboard client
BUILTIN_THEME_VARS = {
    'dark': {
        '--wcp-color-bg':'#0d1117','--wcp-color-surface':'#161b22','--wcp-color-surface-raised':'#1c2128',
        '--wcp-color-border':'#30363d','--wcp-color-text':'#e6edf3','--wcp-color-text-muted':'#8b949e',
        '--wcp-color-primary':'#f0883e','--wcp-color-success':'#3fb950','--wcp-color-danger':'#f85149',
        '--wcp-color-warning':'#d29922','--wcp-color-info':'#58a6ff',
        '--wcp-radius-md':'8px','--wcp-shadow-sm':'0 4px 16px rgba(0,0,0,.45)',
    },
    'light': {
        '--wcp-color-bg':'#ffffff','--wcp-color-surface':'#f6f8fa','--wcp-color-surface-raised':'#eaeef2',
        '--wcp-color-border':'#d0d7de','--wcp-color-text':'#1f2328','--wcp-color-text-muted':'#636c76',
        '--wcp-color-primary':'#f0883e','--wcp-color-success':'#1a7f37','--wcp-color-danger':'#cf222e',
        '--wcp-color-warning':'#9a6700','--wcp-color-info':'#0969da',
        '--wcp-radius-md':'8px','--wcp-shadow-sm':'0 4px 8px rgba(0,0,0,.12)',
    },
    'hc': {
        '--wcp-color-bg':'#000000','--wcp-color-surface':'#0d0d0d','--wcp-color-surface-raised':'#1a1a1a',
        '--wcp-color-border':'#ffffff','--wcp-color-text':'#ffffff','--wcp-color-text-muted':'#cccccc',
        '--wcp-color-primary':'#ff8c00','--wcp-color-success':'#00ff41','--wcp-color-danger':'#ff3333',
        '--wcp-color-warning':'#ffff00','--wcp-color-info':'#00b4ff',
        '--wcp-radius-md':'4px','--wcp-shadow-sm':'none',
    },
}

def resolve_theme_vars(instance_id):
    """Return the active theme's CSS vars dict for the given instance."""
    cfg      = get_instance_config(instance_id)
    active   = _LEGACY_THEME_MAP.get(cfg.get('theme', 'dark'), cfg.get('theme', 'dark'))
    if active in BUILTIN_THEME_VARS:
        return BUILTIN_THEME_VARS[active]
    custom = next((t for t in cfg.get('custom_themes', [])
                   if (t.get('id') or t.get('uuid')) == active), None)
    return custom.get('vars', BUILTIN_THEME_VARS['dark']) if custom else BUILTIN_THEME_VARS['dark']

# ── State helpers (volume — config, guids, published only) ───────────────────

def ensure_workspace():
    os.makedirs(WORKSPACE, exist_ok=True)

def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    ensure_workspace()
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def get_guids():
    guids = load_json(GUID_FILE, {})
    changed = False
    for key in ('explorer', 'settings', 'about'):
        if key not in guids:
            guids[key] = str(uuid.uuid4())
            changed = True
    if changed:
        save_json(GUID_FILE, guids)
    return guids

def get_instance_config(instance_id):
    all_config = load_json(CONFIG_FILE, {})
    defaults = {'root': '', 'theme': 'dark', 'custom_themes': []}
    cfg = all_config.get(instance_id, defaults)
    if 'custom_themes' not in cfg:
        cfg['custom_themes'] = []
    return cfg

def save_instance_config(instance_id, config):
    all_config = load_json(CONFIG_FILE, {})
    all_config[instance_id] = config
    save_json(CONFIG_FILE, all_config)

def instance_id_from_request():
    return (request.headers.get('Wcp-Instance-Id')
            or request.args.get('wcpInstanceId', 'default'))

# ── Agent proxy helpers ───────────────────────────────────────────────────────

def agent_get(path, params=None, timeout=5):
    """GET a path on the agent. Returns (data_dict, status_code) or raises."""
    url = AGENT_BASE + path
    if params:
        qs = '&'.join(f'{k}={urllib.request.quote(str(v), safe="")}' for k, v in params.items())
        url = url + '?' + qs
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read()), r.status

def agent_post(path, body, timeout=5):
    """POST JSON body to a path on the agent. Returns (data_dict, status_code) or raises."""
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        AGENT_BASE + path, data=payload,
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read()), r.status

def agent_available():
    """Quick liveness check — returns True if agent responds to /health."""
    try:
        agent_get('/health', timeout=2)
        return True
    except Exception:
        return False

# ── WCP Discovery ────────────────────────────────────────────────────────────

@app.route('/wcp')
def container_directory():
    return jsonify({
        'wcp':         '2.1.0',
        'container':   CONTAINER,
        'version':     VERSION,
        'widgets': [{
            'id':   'wcp-widget-markdown-editor',
            'name': 'Markdown Editor',
            'wcp':  f'http://localhost:{PORT}/widget/wcp'
        }]
    })

@app.route('/widget/wcp')
def widget_manifest():
    guids = get_guids()
    published = os.path.exists(os.path.join(PUBLISHED_DIR, 'index.html'))
    return jsonify({
        'wcp':         '2.1.0',
        'id':          'wcp-widget-markdown-editor',
        'name':        'Markdown Editor',
        'version':     VERSION,
        'description': 'WYSIWYG markdown file editor with folder browser and companion host agent.',
        'publisher':   'penrithbeacon',
        'icon':        f'http://localhost:{PORT}/widget/icon.svg',
        'components': [
            {
                'id':          guids['explorer'],
                'name':        'Markdown Explorer',
                'role':        'widget',
                'path':        f'http://localhost:{PORT}/widget/',
                'defaultSize': {'cols': 12, 'rows': 12}
            },
            {
                'id':          guids['settings'],
                'name':        'Settings',
                'role':        'widget',
                'path':        f'http://localhost:{PORT}/widget/settings/',
                'defaultSize': {'cols': 12, 'rows': 12}
            },
            {
                'id':          guids['about'],
                'name':        'About',
                'role':        'widget',
                'path':        f'http://localhost:{PORT}/widget/about/',
                'defaultSize': {'cols': 12, 'rows': 12}
            }
        ],
        'web': {'published': published}
    })

@app.route('/wcp', methods=['OPTIONS'])
@app.route('/widget/<path:p>', methods=['OPTIONS'])
def cors_preflight(p=''):
    r = Response('', status=204)
    r.headers['Access-Control-Allow-Origin']  = '*'
    r.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type, Wcp-Instance-Id'
    return r

# ── Health ───────────────────────────────────────────────────────────────────

@app.route('/widget/health')
def health():
    return jsonify({'status': 'ok', 'name': CONTAINER, 'container': CONTAINER, 'version': VERSION})

# ── Component GUIDs ──────────────────────────────────────────────────────────

@app.route('/widget/api/guids')
def guids():
    return jsonify(get_guids())

# ── Icon ─────────────────────────────────────────────────────────────────────

@app.route('/widget/icon.svg')
def icon():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none">
  <rect x="4" y="4" width="40" height="40" rx="6" fill="#4A90D9"/>
  <text x="24" y="32" font-family="monospace" font-size="22" font-weight="bold"
        fill="white" text-anchor="middle">MD</text>
</svg>'''
    return Response(svg, mimetype='image/svg+xml')

# ── Widget Index ──────────────────────────────────────────────────────────────

@app.route('/widget/index')
def widget_index():
    guids = get_guids()
    return render_template('index.html',
        version=VERSION, port=PORT, container=CONTAINER,
        guids=guids, agent_port=AGENT_PORT)

# ── Component Views ──────────────────────────────────────────────────────────

@app.route('/widget/')
@app.route('/widget/explorer/')
def explorer():
    iid = instance_id_from_request()
    cfg = get_instance_config(iid)
    # No WORKSPACE fallback — root must be configured; widget.html handles empty root
    return render_template('widget.html',
        version=VERSION, port=PORT, instance_id=iid,
        root=cfg.get('root', ''), agent_port=AGENT_PORT)

@app.route('/widget/settings/')
def settings():
    iid = instance_id_from_request()
    cfg = get_instance_config(iid)
    return render_template('settings.html',
        version=VERSION, port=PORT, instance_id=iid,
        root=cfg.get('root', ''),
        theme=cfg.get('theme', 'default'),
        agent_port=AGENT_PORT)

@app.route('/widget/about/')
def about():
    return render_template('about.html',
        version=VERSION, port=PORT, container=CONTAINER)

# ── Configuration ─────────────────────────────────────────────────────────────

@app.route('/widget/configure', methods=['POST'])
def configure():
    iid  = instance_id_from_request()
    data = request.get_json(force=True, silent=True) or {}
    cfg  = get_instance_config(iid)
    if 'root'  in data: cfg['root']  = data['root']
    if 'theme' in data: cfg['theme'] = data['theme']
    save_instance_config(iid, cfg)
    return jsonify({'status': 'ok'})

_LEGACY_THEME_MAP = {'default':'dark','mocha':'dark','latte':'light','frappe':'dark'}

@app.route('/widget/api/themes')
def themes_get():
    iid    = instance_id_from_request()
    cfg    = get_instance_config(iid)
    active = cfg.get('theme', 'dark')
    active = _LEGACY_THEME_MAP.get(active, active)
    return jsonify({
        'active':  active,
        'custom':  cfg.get('custom_themes', []),
    })

@app.route('/widget/api/themes/import', methods=['POST'])
def themes_import():
    iid  = instance_id_from_request()
    data = request.get_json(force=True, silent=True) or {}
    cfg  = get_instance_config(iid)
    incoming = data.get('themes', [])
    existing = {t.get('uuid') or t.get('id'): t for t in cfg.get('custom_themes', [])}
    for t in incoming:
        key = t.get('uuid') or t.get('id')
        if key:
            existing[key] = t
    cfg['custom_themes'] = list(existing.values())
    save_instance_config(iid, cfg)
    return jsonify({'status': 'ok', 'imported': len(incoming)})

@app.route('/widget/api/themes/<theme_id>', methods=['DELETE'])
def themes_delete(theme_id):
    iid = instance_id_from_request()
    cfg = get_instance_config(iid)
    before = len(cfg.get('custom_themes', []))
    cfg['custom_themes'] = [t for t in cfg.get('custom_themes', [])
                            if (t.get('uuid') or t.get('id')) != theme_id]
    if cfg.get('theme') == theme_id:
        cfg['theme'] = 'dark'
    save_instance_config(iid, cfg)
    return jsonify({'status': 'ok', 'removed': before - len(cfg['custom_themes'])})

# ── Root path validation ──────────────────────────────────────────────────────

@app.route('/widget/api/root/validate')
def root_validate():
    """Check that the configured root exists and the agent is reachable."""
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '')
    if not root:
        return jsonify({'valid': False, 'reason': 'no_root', 'agent': False})
    try:
        data, _ = agent_get('/files/validate', {'path': root})
        ok = bool(data.get('valid'))
        return jsonify({'valid': ok, 'reason': '' if ok else 'path_unavailable',
                        'agent': True, 'path': root})
    except Exception:
        return jsonify({'valid': False, 'reason': 'agent_offline', 'agent': False, 'path': root})

# ── File API — all ops proxied through the host agent ─────────────────────────

@app.route('/widget/api/files/list')
def list_files():
    rel  = request.args.get('path', '')
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '')
    if not root:
        return jsonify({'error': 'no root configured'}), 400
    # Build the absolute path to pass to the agent
    abs_path = root if not rel else os.path.join(root, rel.lstrip('/'))
    try:
        data, _ = agent_get('/files/browse', {'path': abs_path})
    except urllib.error.HTTPError as e:
        return jsonify({'error': f'agent error {e.code}'}), 502
    except Exception:
        return jsonify({'error': 'agent offline'}), 503

    # Filter: hide dot-names, hash-names (e.g. #Recycle Bin); show dirs + .md files only
    raw = data.get('entries', [])
    entries = []
    for e in raw:
        name = e.get('name', '')
        if name.startswith('.') or name.startswith('#'):
            continue
        is_dir = e.get('type') == 'dir'
        ext    = e.get('ext', '')
        if not is_dir and ext != '.md':
            continue
        entries.append({'name': name, 'type': e['type'], 'ext': ext})
    # Sort: dirs first, then files; both groups case-insensitive alphabetical
    entries.sort(key=lambda e: (0 if e['type'] == 'dir' else 1, e['name'].lower()))
    return jsonify({'path': rel, 'entries': entries})

@app.route('/widget/api/files/read')
def read_file():
    rel  = request.args.get('path', '')
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '')
    if not root:
        return jsonify({'error': 'no root configured'}), 400
    abs_path = root if not rel else os.path.join(root, rel.lstrip('/'))
    try:
        data, _ = agent_get('/files/read', {'path': abs_path})
        return jsonify({'path': rel, 'content': data.get('content', '')})
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            err = json.loads(body).get('error', 'agent error')
        except Exception:
            err = 'agent error'
        return jsonify({'error': err}), e.code
    except Exception:
        return jsonify({'error': 'agent offline'}), 503

@app.route('/widget/api/files/save', methods=['POST'])
def save_file():
    data    = request.get_json(force=True, silent=True) or {}
    rel     = data.get('path', '')
    content = data.get('content', '')
    iid     = instance_id_from_request()
    root    = get_instance_config(iid).get('root', '')
    if not root:
        return jsonify({'error': 'no root configured'}), 400
    abs_path = root if not rel else os.path.join(root, rel.lstrip('/'))
    try:
        agent_post('/files/write', {'path': abs_path, 'content': content})
        return jsonify({'status': 'ok', 'path': rel})
    except urllib.error.HTTPError as e:
        return jsonify({'error': f'agent error {e.code}'}), 502
    except Exception:
        return jsonify({'error': 'agent offline'}), 503

@app.route('/widget/api/files/mkdir', methods=['POST'])
def mkdir():
    data = request.get_json(force=True, silent=True) or {}
    rel  = data.get('path', '')
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '')
    if not root:
        return jsonify({'error': 'no root configured'}), 400
    abs_path = root if not rel else os.path.join(root, rel.lstrip('/'))
    try:
        agent_post('/files/mkdir', {'path': abs_path})
        return jsonify({'status': 'ok'})
    except urllib.error.HTTPError as e:
        return jsonify({'error': f'agent error {e.code}'}), 502
    except Exception:
        return jsonify({'error': 'agent offline'}), 503

@app.route('/widget/api/files/rename', methods=['POST'])
def rename_file():
    data    = request.get_json(force=True, silent=True) or {}
    old_rel = data.get('old', '')
    new_rel = data.get('new', '')
    iid     = instance_id_from_request()
    root    = get_instance_config(iid).get('root', '')
    if not root:
        return jsonify({'error': 'no root configured'}), 400
    old_abs = os.path.join(root, old_rel.lstrip('/'))
    new_abs = os.path.join(root, new_rel.lstrip('/'))
    try:
        agent_post('/files/rename', {'old': old_abs, 'new': new_abs})
        return jsonify({'status': 'ok'})
    except urllib.error.HTTPError as e:
        return jsonify({'error': f'agent error {e.code}'}), 502
    except Exception:
        return jsonify({'error': 'agent offline'}), 503

@app.route('/widget/api/files/delete', methods=['POST'])
def delete_file():
    data = request.get_json(force=True, silent=True) or {}
    rel  = data.get('path', '')
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '')
    if not root:
        return jsonify({'error': 'no root configured'}), 400
    abs_path = os.path.join(root, rel.lstrip('/'))
    try:
        agent_post('/files/delete', {'path': abs_path})
        return jsonify({'status': 'ok'})
    except urllib.error.HTTPError as e:
        return jsonify({'error': f'agent error {e.code}'}), 502
    except Exception:
        return jsonify({'error': 'agent offline'}), 503

# ── Publish to Web ────────────────────────────────────────────────────────────

@app.route('/widget/publish', methods=['POST'])
def publish():
    from datetime import datetime as dt
    data        = request.get_json(force=True, silent=True) or {}
    content     = data.get('html', '<p>No content provided.</p>')
    title       = data.get('title', 'Published Document')
    source_path = data.get('source_path', '')
    iid         = instance_id_from_request()
    theme_vars  = resolve_theme_vars(iid)

    # Build baked-in :root block from active theme (URL params override at runtime)
    root_css = ':root{' + ''.join(f'{k}:{v};' for k, v in theme_vars.items()) + '}'

    # WCP theme URL reception snippet — supports both
    #   ?com.doc.widgetcontextprotocol=<base64>  (query string form)
    #   #wcp-theme=<base64>                      (hash fragment form)
    wcp_snippet = """\
<script>(function(){
  var QK='com.doc.widgetcontextprotocol';
  var raw=new URLSearchParams(location.search).get(QK)
      ||(location.hash.startsWith('#wcp-theme=')?location.hash.slice(11):null);
  if(!raw)return;
  try{var p=JSON.parse(atob(raw)),vars=p.vars||p;
    for(var k in vars)document.documentElement.style.setProperty(k,vars[k]);}
  catch(e){}
})();</script>"""

    os.makedirs(PUBLISHED_DIR, exist_ok=True)
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
{root_css}
*,*::before,*::after{{box-sizing:border-box}}
body{{background:var(--wcp-color-bg,#0d1117);color:var(--wcp-color-text,#e6edf3);font-family:system-ui,-apple-system,sans-serif;line-height:1.7;max-width:800px;margin:2rem auto;padding:0 1.5rem}}
h1,h2,h3,h4,h5,h6{{color:var(--wcp-color-text,#e6edf3);line-height:1.3;margin:1.5em 0 .5em}}
h1{{font-size:2em;border-bottom:1px solid var(--wcp-color-border,#30363d);padding-bottom:.3em}}
h2{{font-size:1.5em;border-bottom:1px solid var(--wcp-color-border,#30363d);padding-bottom:.2em}}
a{{color:var(--wcp-color-primary,#f0883e)}}
p{{margin:.75em 0}}
code{{background:var(--wcp-color-surface,#161b22);border:1px solid var(--wcp-color-border,#30363d);border-radius:4px;padding:2px 6px;font-family:ui-monospace,monospace;font-size:.9em}}
pre{{background:var(--wcp-color-surface,#161b22);border:1px solid var(--wcp-color-border,#30363d);border-radius:6px;padding:1rem;overflow-x:auto;margin:1em 0}}
pre code{{background:none;border:none;padding:0}}
blockquote{{border-left:3px solid var(--wcp-color-primary,#f0883e);margin:1em 0;padding:.5em 1em;color:var(--wcp-color-text-muted,#8b949e);background:var(--wcp-color-surface,#161b22);border-radius:0 4px 4px 0}}
table{{border-collapse:collapse;width:100%;margin:1em 0}}
th,td{{border:1px solid var(--wcp-color-border,#30363d);padding:8px 12px;text-align:left}}
th{{background:var(--wcp-color-surface,#161b22);font-weight:600}}
img{{max-width:100%;border-radius:4px}}
hr{{border:none;border-top:1px solid var(--wcp-color-border,#30363d);margin:2em 0}}
</style>
{wcp_snippet}
</head>
<body>{content}</body>
</html>'''
    with open(os.path.join(PUBLISHED_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    # Save metadata so settings page can show what's published
    meta = {
        'title':       title,
        'source_path': source_path,
        'published_at': dt.utcnow().isoformat() + 'Z',
        'url':         f'http://localhost:{PORT}/'
    }
    save_json(os.path.join(PUBLISHED_DIR, 'meta.json'), meta)
    return jsonify({'status': 'ok', 'url': meta['url']})

@app.route('/widget/api/publish/status')
def publish_status():
    meta_path = os.path.join(PUBLISHED_DIR, 'meta.json')
    if os.path.exists(meta_path):
        meta = load_json(meta_path, {})
        return jsonify({'published': True, **meta})
    return jsonify({'published': False})

@app.route('/widget/publish', methods=['DELETE'])
def unpublish():
    import shutil
    if os.path.exists(PUBLISHED_DIR):
        shutil.rmtree(PUBLISHED_DIR)
    return jsonify({'status': 'ok'})

@app.route('/')
def root():
    idx = os.path.join(PUBLISHED_DIR, 'index.html')
    if os.path.exists(idx):
        with open(idx) as f:
            return f.read()
    return redirect(f'/widget/')

# ── WCP Export ────────────────────────────────────────────────────────────────

@app.route('/widget/export.wcp')
def export_wcp():
    guids   = get_guids()
    manifest = {
        'wcp':       '2.1.0',
        'id':        'wcp-widget-markdown-editor',
        'version':   VERSION,
        'publisher': 'penrithbeacon',
        'components': list(guids.values())
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(manifest, indent=2))
    buf.seek(0)
    return send_file(buf, mimetype='application/zip',
                     download_name='wcp-widget-markdown-editor.wcp')

# ── Agent Installer ───────────────────────────────────────────────────────────

@app.route('/widget/agent/installer')
def agent_installer():
    pkg = '/app/src/installers/wcp-agent-markdown-editor.pkg'
    if os.path.exists(pkg):
        return send_file(pkg, mimetype='application/octet-stream',
                         download_name='wcp-agent-markdown-editor.pkg')
    return jsonify({
        'status':  'not_packaged',
        'message': 'Agent installer not yet bundled in this image. '
                   'Download from GitHub Releases: '
                   'https://github.com/HarrisonOfTheNorth/wcp-agent-markdown-editor/releases'
    }), 503

# ── Agent Status + picker proxies ─────────────────────────────────────────────

@app.route('/widget/api/agent/status')
def agent_status():
    try:
        data, _ = agent_get('/health', timeout=2)
        return jsonify({'available': True, 'agent': data})
    except Exception:
        return jsonify({'available': False})

@app.route('/widget/api/agent/browse')
def agent_browse():
    """Proxy /files/browse from the agent for the folder picker."""
    path = request.args.get('path', '')
    if not path:
        path = os.path.expanduser('~')
    # Expand ~ server-side (the widget can't do it)
    if path.startswith('~'):
        # Ask the agent to resolve it by passing the literal path — agent calls expanduser
        pass
    try:
        data, _ = agent_get('/files/browse', {'path': path})
        return jsonify(data)
    except urllib.error.HTTPError as e:
        return jsonify({'error': f'agent error {e.code}'}), 502
    except Exception:
        return jsonify({'error': 'agent offline'}), 503

@app.route('/widget/api/agent/drives')
def agent_drives():
    """Proxy /files/drives from the agent for the picker sidebar."""
    try:
        data, _ = agent_get('/files/drives')
        return jsonify(data)
    except Exception:
        return jsonify({'drives': []})

# ── Logs ─────────────────────────────────────────────────────────────────────

@app.route('/widget/logs')
def logs():
    return jsonify({
        'wcp_logs':  '1.0',
        'component': {'type': 'widget', 'name': CONTAINER, 'version': VERSION},
        'schema': {
            'fields': [
                {'name': 'timestamp', 'type': 'iso8601',  'required': True},
                {'name': 'level',     'type': 'enum',
                 'values': ['debug','info','warn','error'], 'required': True},
                {'name': 'message',   'type': 'string',    'required': True},
                {'name': 'source',    'type': 'string',    'required': False}
            ]
        },
        'entries': []
    })

# ── Boot ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    ensure_workspace()
    app.run(host='0.0.0.0', port=PORT, debug=False)
