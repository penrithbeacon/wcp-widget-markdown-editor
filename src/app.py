import os
import json
import uuid
import zipfile
import io
import secrets
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file, redirect, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PORT          = int(os.environ.get('WIDGET_PORT', 3748))
CONTAINER     = os.environ.get('CONTAINER_NAME', 'wcp-widget-markdown-editor')
VERSION       = '1.0.0'
WORKSPACE     = '/workspace'
AGENT_PORT    = int(os.environ.get('AGENT_PORT', 3749))
AGENT_BASE    = f'http://host.docker.internal:{AGENT_PORT}'

CONFIG_FILE   = os.path.join(WORKSPACE, '.widget-config.json')
GUID_FILE     = os.path.join(WORKSPACE, '.widget-guids.json')
PUBLISHED_DIR = os.path.join(WORKSPACE, '.published')

# ── Helpers ─────────────────────────────────────────────────────────────────

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
    return all_config.get(instance_id, {'root': '', 'theme': 'default'})

def save_instance_config(instance_id, config):
    all_config = load_json(CONFIG_FILE, {})
    all_config[instance_id] = config
    save_json(CONFIG_FILE, all_config)

def instance_id_from_request():
    # Dashboard passes instance ID as Wcp-Instance-Id header for API calls,
    # but as ?wcpInstanceId= query param for iframe page loads (browsers cannot
    # add custom headers to iframe src URLs).
    return (request.headers.get('Wcp-Instance-Id')
            or request.args.get('wcpInstanceId', 'default'))

def safe_path(root, rel):
    """Resolve rel against root; return None if it escapes root."""
    root  = os.path.realpath(root)
    full  = os.path.realpath(os.path.join(root, rel.lstrip('/')))
    return full if full.startswith(root) else None

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
    return render_template('widget.html',
        version=VERSION, port=PORT, instance_id=iid,
        root=cfg.get('root', '') or WORKSPACE, agent_port=AGENT_PORT)

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

# ── File API (served to frontend; real access via agent) ─────────────────────

@app.route('/widget/api/files/list')
def list_files():
    """List files and folders at path within the mounted workspace."""
    rel  = request.args.get('path', '')
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '') or WORKSPACE
    if not root.startswith('/'):
        root = os.path.join(WORKSPACE, root)
    target = safe_path(root, rel)
    if not target or not os.path.isdir(target):
        return jsonify({'error': 'invalid path'}), 400
    entries = []
    for name in sorted(os.listdir(target)):
        full = os.path.join(target, name)
        entries.append({
            'name': name,
            'type': 'dir' if os.path.isdir(full) else 'file',
            'ext':  os.path.splitext(name)[1].lower()
        })
    return jsonify({'path': rel, 'entries': entries})

@app.route('/widget/api/files/read')
def read_file():
    rel  = request.args.get('path', '')
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '') or WORKSPACE
    if not root.startswith('/'):
        root = os.path.join(WORKSPACE, root)
    target = safe_path(root, rel)
    if not target or not os.path.isfile(target):
        return jsonify({'error': 'file not found'}), 404
    with open(target, 'r', errors='replace') as f:
        content = f.read()
    return jsonify({'path': rel, 'content': content})

@app.route('/widget/api/files/save', methods=['POST'])
def save_file():
    data    = request.get_json(force=True, silent=True) or {}
    rel     = data.get('path', '')
    content = data.get('content', '')
    iid     = instance_id_from_request()
    root    = get_instance_config(iid).get('root', '') or WORKSPACE
    if not root.startswith('/'):
        root = os.path.join(WORKSPACE, root)
    target = safe_path(root, rel)
    if not target:
        return jsonify({'error': 'invalid path'}), 400
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'w') as f:
        f.write(content)
    return jsonify({'status': 'ok', 'path': rel})

@app.route('/widget/api/files/mkdir', methods=['POST'])
def mkdir():
    data = request.get_json(force=True, silent=True) or {}
    rel  = data.get('path', '')
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '') or WORKSPACE
    if not root.startswith('/'):
        root = os.path.join(WORKSPACE, root)
    target = safe_path(root, rel)
    if not target:
        return jsonify({'error': 'invalid path'}), 400
    os.makedirs(target, exist_ok=True)
    return jsonify({'status': 'ok'})

@app.route('/widget/api/files/rename', methods=['POST'])
def rename_file():
    data     = request.get_json(force=True, silent=True) or {}
    old_rel  = data.get('old', '')
    new_rel  = data.get('new', '')
    iid      = instance_id_from_request()
    root     = get_instance_config(iid).get('root', '') or WORKSPACE
    if not root.startswith('/'):
        root = os.path.join(WORKSPACE, root)
    old_path = safe_path(root, old_rel)
    new_path = safe_path(root, new_rel)
    if not old_path or not new_path or not os.path.exists(old_path):
        return jsonify({'error': 'invalid path'}), 400
    os.rename(old_path, new_path)
    return jsonify({'status': 'ok'})

@app.route('/widget/api/files/delete', methods=['POST'])
def delete_file():
    import shutil
    data = request.get_json(force=True, silent=True) or {}
    rel  = data.get('path', '')
    iid  = instance_id_from_request()
    root = get_instance_config(iid).get('root', '') or WORKSPACE
    if not root.startswith('/'):
        root = os.path.join(WORKSPACE, root)
    target = safe_path(root, rel)
    if not target or not os.path.exists(target):
        return jsonify({'error': 'not found'}), 404
    if os.path.isdir(target):
        shutil.rmtree(target)
    else:
        os.remove(target)
    return jsonify({'status': 'ok'})

# ── Publish to Web ────────────────────────────────────────────────────────────

@app.route('/widget/publish', methods=['POST'])
def publish():
    data    = request.get_json(force=True, silent=True) or {}
    content = data.get('html', '<p>No content provided.</p>')
    title   = data.get('title', 'Published Document')
    os.makedirs(PUBLISHED_DIR, exist_ok=True)
    html = f'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{title}</title>
<style>body{{max-width:800px;margin:2rem auto;font-family:Georgia,serif;line-height:1.7;padding:0 1rem}}</style>
</head><body>{content}</body></html>'''
    with open(os.path.join(PUBLISHED_DIR, 'index.html'), 'w') as f:
        f.write(html)
    return jsonify({'status': 'ok', 'url': f'http://localhost:{PORT}/'})

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
    # The packaged .pkg installer is bundled into the image at build time.
    pkg = '/app/agent/wcp-agent-markdown-editor.pkg'
    if os.path.exists(pkg):
        return send_file(pkg, mimetype='application/octet-stream',
                         download_name='wcp-agent-markdown-editor.pkg')
    return jsonify({
        'status':  'not_packaged',
        'message': 'Agent installer not yet bundled in this image. '
                   'Download from GitHub Releases: '
                   'https://github.com/HarrisonOfTheNorth/wcp-agent-markdown-editor/releases'
    }), 503

# ── Agent Status ──────────────────────────────────────────────────────────────

@app.route('/widget/api/agent/status')
def agent_status():
    import urllib.request
    try:
        with urllib.request.urlopen(f'{AGENT_BASE}/health', timeout=2) as r:
            data = json.loads(r.read())
            return jsonify({'available': True, 'agent': data})
    except Exception:
        return jsonify({'available': False})

# ── Logs (optional WCP endpoint) ─────────────────────────────────────────────

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
