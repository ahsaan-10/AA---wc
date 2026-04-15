import os
import sys
import sqlite3
import json
import hashlib
import mimetypes
from functools import wraps

from flask import Flask, request, render_template_string, jsonify, send_from_directory, redirect, send_file, url_for
from flask_cors import CORS
from itsdangerous import URLSafeSerializer, BadSignature
from werkzeug.utils import secure_filename
from smart_conversion import inject_clone_bridge
from cloner_engine import get_saved_bundle_archive, get_saved_bundle_site_dir, update_saved_bundle_entry, default_workspace_roots, load_saved_bundle_entry, strip_preview_paths

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
UPLOAD_FOLDER = 'project_assets'
DB_NAME = 'users.db'
TOKEN_SECRET = 'ai-website-fabricator-admin'
serializer = URLSafeSerializer(TOKEN_SECRET, salt='admin-auth')
ADMIN_DIST_DIR = os.path.join(BASE_DIR, 'admin', 'dist')

if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
    except:
        pass

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/dynamic-api/*": {"origins": "*"}})

# ==========================================
# DATABASE HELPER
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def slugify(value):
    return secure_filename(str(value).strip().lower().replace(" ", "-")) or "record"


def build_site_name(row):
    if not row:
        return "Untitled Site"

    spec_json = row.get("spec_json") if isinstance(row, dict) else row["spec_json"] if "spec_json" in row.keys() else None
    if spec_json:
        try:
            spec = json.loads(spec_json)
            if spec.get("siteName"):
                return spec["siteName"]
        except Exception:
            pass

    url = row["url"]
    return url.replace("https://", "").replace("http://", "").strip("/") or "Untitled Site"


def build_clone_preview_url(site_id):
    preview_path = url_for('clone_preview', site_id=site_id)
    return f"{request.host_url.rstrip('/')}{preview_path}"


def get_token_payload():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    try:
        return serializer.loads(token)
    except BadSignature:
        return None


def require_admin_auth(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        payload = get_token_payload()
        if not payload:
            return jsonify({"message": "Unauthorized"}), 401
        request.admin_user = payload
        return handler(*args, **kwargs)

    return wrapper


def normalize_record_response(row):
    return {
        "id": row["id"],
        "projectId": row["site_id"],
        "resourceKey": row["model_name"],
        "slug": row["slug"],
        "status": row["status"],
        "data": json.loads(row["data_json"]),
        "updatedAt": row["updated_at"],
        "createdAt": row["created_at"],
    }


def guess_upload_media_type(filename, mime_type):
    name = (filename or "").lower()
    mime_type = (mime_type or "").lower()
    if mime_type.startswith("image/svg") or name.endswith(".svg"):
        return "svg"
    if mime_type.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".avif")):
        return "image"
    if mime_type.startswith("video/") or name.endswith((".mp4", ".webm", ".mov", ".m3u8")):
        return "video"
    if mime_type.startswith("audio/") or name.endswith((".mp3", ".wav", ".ogg", ".m4a")):
        return "audio"
    if name.endswith(".ico") or "icon" in name or "favicon" in name:
        return "icon"
    return "file"


def media_row_payload(row):
    return {
        "id": row["id"],
        "assetKey": row["asset_key"],
        "sourceKind": row["source_kind"],
        "mediaType": row["media_type"],
        "mimeType": row["mime_type"],
        "filename": row["filename"],
        "originalName": row["original_name"],
        "fileUrl": row["file_url"],
        "originalUrl": row["original_url"],
        "altText": row["alt_text"],
        "width": row["width"],
        "height": row["height"],
        "hash": row["hash"],
        "status": row["status"],
        "sectionKey": row["section_key"],
        "usage": json.loads(row["usage_json"] or "[]"),
        "metadata": json.loads(row["metadata_json"] or "{}"),
        "localPath": row["local_path"],
        "uploadedAt": row["uploaded_at"],
        "updatedAt": row["updated_at"],
        "previewUrl": row["file_url"] or row["original_url"],
    }

def ensure_dynamic_tables():
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS site_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER UNIQUE,
            user_id INTEGER,
            spec_json TEXT,
            bindings_json TEXT,
            updated_at TEXT
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS dynamic_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            user_id INTEGER,
            model_name TEXT,
            section_title TEXT,
            schema_json TEXT,
            display_order INTEGER DEFAULT 0,
            updated_at TEXT,
            UNIQUE(site_id, model_name)
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS dynamic_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            user_id INTEGER,
            model_name TEXT,
            data_json TEXT,
            slug TEXT,
            status TEXT DEFAULT 'draft',
            created_at TEXT,
            updated_at TEXT
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS media_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            user_id INTEGER,
            asset_key TEXT,
            source_kind TEXT DEFAULT 'upload',
            media_type TEXT,
            mime_type TEXT,
            filename TEXT,
            original_name TEXT,
            file_url TEXT,
            original_url TEXT,
            alt_text TEXT,
            width INTEGER,
            height INTEGER,
            hash TEXT,
            status TEXT DEFAULT 'ready',
            section_key TEXT,
            usage_json TEXT,
            metadata_json TEXT,
            local_path TEXT,
            uploaded_at TEXT,
            updated_at TEXT
        )
        '''
    )
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(dynamic_records)").fetchall()}
    if 'slug' not in existing_columns:
        conn.execute("ALTER TABLE dynamic_records ADD COLUMN slug TEXT")
    if 'status' not in existing_columns:
        conn.execute("ALTER TABLE dynamic_records ADD COLUMN status TEXT DEFAULT 'draft'")
    media_columns = {row["name"] for row in conn.execute("PRAGMA table_info(media_assets)").fetchall()}
    media_migrations = {
        'asset_key': "ALTER TABLE media_assets ADD COLUMN asset_key TEXT",
        'source_kind': "ALTER TABLE media_assets ADD COLUMN source_kind TEXT DEFAULT 'upload'",
        'media_type': "ALTER TABLE media_assets ADD COLUMN media_type TEXT",
        'mime_type': "ALTER TABLE media_assets ADD COLUMN mime_type TEXT",
        'original_url': "ALTER TABLE media_assets ADD COLUMN original_url TEXT",
        'alt_text': "ALTER TABLE media_assets ADD COLUMN alt_text TEXT",
        'width': "ALTER TABLE media_assets ADD COLUMN width INTEGER",
        'height': "ALTER TABLE media_assets ADD COLUMN height INTEGER",
        'hash': "ALTER TABLE media_assets ADD COLUMN hash TEXT",
        'status': "ALTER TABLE media_assets ADD COLUMN status TEXT DEFAULT 'ready'",
        'section_key': "ALTER TABLE media_assets ADD COLUMN section_key TEXT",
        'usage_json': "ALTER TABLE media_assets ADD COLUMN usage_json TEXT",
        'metadata_json': "ALTER TABLE media_assets ADD COLUMN metadata_json TEXT",
        'local_path': "ALTER TABLE media_assets ADD COLUMN local_path TEXT",
        'updated_at': "ALTER TABLE media_assets ADD COLUMN updated_at TEXT",
    }
    for column_name, sql in media_migrations.items():
        if column_name not in media_columns:
            conn.execute(sql)
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_media_assets_site_user_asset_key ON media_assets(site_id, user_id, asset_key)"
    )
    conn.commit()
    conn.close()


def fetch_site_spec(site_id):
    conn = get_db_connection()
    row = conn.execute(
        '''
        SELECT site_specs.spec_json, site_specs.bindings_json, site_specs.updated_at, cloned_sites.url
        FROM site_specs
        LEFT JOIN cloned_sites ON cloned_sites.id = site_specs.site_id
        WHERE site_specs.site_id = ?
        ''',
        (site_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "spec": json.loads(row["spec_json"]),
        "bindings": json.loads(row["bindings_json"] or "[]"),
        "updated_at": row["updated_at"],
        "url": row["url"],
    }


def fetch_project(site_id):
    conn = get_db_connection()
    row = conn.execute(
        '''
        SELECT cloned_sites.id, cloned_sites.user_id, cloned_sites.url, cloned_sites.cloned_at,
               conversion_blueprints.site_type, conversion_blueprints.confidence,
               site_specs.spec_json
        FROM cloned_sites
        LEFT JOIN conversion_blueprints ON conversion_blueprints.site_id = cloned_sites.id
        LEFT JOIN site_specs ON site_specs.site_id = cloned_sites.id
        WHERE cloned_sites.id = ?
        ''',
        (site_id,)
    ).fetchone()
    conn.close()
    return row

# ==========================================
# 1. LANDING PAGE (Select a Site)
# ==========================================
# This replaces your "Launcher" with a list of the user's sites
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Builder Workspace</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --bg: #f3f7fd;
            --surface: rgba(255, 255, 255, 0.9);
            --surface-strong: rgba(255, 255, 255, 0.97);
            --text: #0f172a;
            --muted: #5f6d83;
            --border: rgba(15, 23, 42, 0.09);
            --primary: #2563eb;
            --primary-strong: #1d4ed8;
            --shadow-lg: 0 28px 60px rgba(15, 23, 42, 0.14);
            --shadow-md: 0 18px 34px rgba(15, 23, 42, 0.08);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            padding: 28px;
            font-family: 'Outfit', sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 24%),
                radial-gradient(circle at top right, rgba(15, 159, 110, 0.1), transparent 20%),
                linear-gradient(180deg, #f9fbff 0%, var(--bg) 100%);
        }

        .launcher-shell {
            max-width: 1180px;
            margin: 0 auto;
        }

        .launcher {
            display: grid;
            grid-template-columns: minmax(320px, 0.95fr) minmax(420px, 1.05fr);
            min-height: calc(100vh - 56px);
            background: var(--surface);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 30px;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            backdrop-filter: blur(18px);
        }

        .left {
            padding: 42px 38px;
            background:
                radial-gradient(circle at top, rgba(96, 165, 250, 0.24), transparent 26%),
                linear-gradient(180deg, rgba(10, 18, 33, 0.97) 0%, rgba(12, 19, 30, 0.94) 100%);
            color: #eff6ff;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .kicker {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(148, 163, 184, 0.16);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #93c5fd;
            width: fit-content;
        }

        .left h1,
        .panel-heading h2 {
            margin: 18px 0 14px;
            font-family: 'Sora', sans-serif;
            font-size: 40px;
            line-height: 1.05;
            letter-spacing: -0.04em;
        }

        .left p {
            margin: 0;
            color: #c9d6e7;
            line-height: 1.7;
            font-size: 16px;
        }

        .feature-list {
            display: grid;
            gap: 14px;
            margin-top: 28px;
        }

        .feature-card {
            padding: 16px 18px;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(148, 163, 184, 0.12);
        }

        .feature-card strong {
            display: block;
            margin-bottom: 6px;
            color: #f8fbff;
            font-size: 15px;
        }

        .feature-card span {
            color: #c6d3e5;
            font-size: 14px;
            line-height: 1.6;
        }

        .right {
            padding: 28px;
            background: var(--surface-strong);
            display: flex;
            flex-direction: column;
            min-width: 0;
        }

        .panel-heading {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 18px;
        }

        .panel-heading .sub-kicker {
            margin: 0 0 8px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--primary);
        }

        .panel-heading h2 {
            margin: 0;
            font-size: 26px;
            color: var(--text);
        }

        .panel-heading p {
            margin: 10px 0 0;
            color: var(--muted);
            line-height: 1.65;
        }

        .count-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            border-radius: 999px;
            background: #eef4ff;
            border: 1px solid rgba(37, 99, 235, 0.14);
            color: var(--primary-strong);
            font-size: 13px;
            font-weight: 700;
            white-space: nowrap;
        }

        .site-list {
            display: grid;
            gap: 14px;
            overflow-y: auto;
            padding-right: 4px;
        }

        .site-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 18px;
            border-radius: 22px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: #ffffff;
            box-shadow: var(--shadow-md);
            transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
        }

        .site-item:hover {
            transform: translateY(-1px);
            border-color: rgba(37, 99, 235, 0.2);
            box-shadow: 0 20px 38px rgba(15, 23, 42, 0.1);
        }

        .site-info {
            min-width: 0;
        }

        .site-info strong {
            display: block;
            color: var(--text);
            font-size: 16px;
            font-weight: 700;
            word-break: break-word;
            margin-bottom: 6px;
        }

        .site-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .site-meta span {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 10px;
            border-radius: 999px;
            background: #f8fafc;
            border: 1px solid rgba(148, 163, 184, 0.14);
            color: var(--muted);
            font-size: 12px;
            font-weight: 600;
        }

        .btn-edit {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            border-radius: 16px;
            background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%);
            color: #f8fbff;
            text-decoration: none;
            font-size: 14px;
            font-weight: 700;
            white-space: nowrap;
            box-shadow: 0 16px 30px rgba(37, 99, 235, 0.2);
        }

        .btn-edit:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #0ea5e9 100%);
        }

        .empty-state {
            padding: 28px 24px;
            border-radius: 22px;
            border: 1px dashed rgba(148, 163, 184, 0.32);
            text-align: center;
            color: var(--muted);
            background: rgba(248, 250, 252, 0.76);
            line-height: 1.7;
        }

        @media (max-width: 960px) {
            body { padding: 16px; }
            .launcher {
                grid-template-columns: 1fr;
                min-height: auto;
            }
            .left, .right { padding: 24px 22px; }
            .panel-heading {
                flex-direction: column;
                align-items: flex-start;
            }
            .site-item {
                flex-direction: column;
                align-items: flex-start;
            }
            .btn-edit { width: 100%; justify-content: center; }
        }
    </style>
</head>
<body>
    <div class="launcher-shell">
        <div class="launcher">
            <section class="left">
                <span class="kicker"><i class="fas fa-pen-ruler"></i> Visual Builder</span>
                <h1>Choose a cloned site and open the builder with confidence.</h1>
                <p>
                    This workspace is intentionally focused on editing. Pick one saved clone,
                    launch the drag-and-drop builder, and keep the structure, styling, and save
                    flow easy to scan.
                </p>
                <div class="feature-list">
                    <div class="feature-card">
                        <strong>Clear builder handoff</strong>
                        <span>Open the exact saved clone you want to edit without mixing projects.</span>
                    </div>
                    <div class="feature-card">
                        <strong>Safer visual workflow</strong>
                        <span>Use the builder for layout and component changes while keeping the clone package intact.</span>
                    </div>
                    <div class="feature-card">
                        <strong>Database-backed saving</strong>
                        <span>Save from the builder and sync the updated HTML back into the same project record.</span>
                    </div>
                </div>
            </section>
            <section class="right">
                <div class="panel-heading">
                    <div>
                        <div class="sub-kicker">Saved Clones</div>
                        <h2>Select a project for the visual editor</h2>
                        <p>Your latest cloned websites are listed below. Open one project at a time and continue editing inside the builder workspace.</p>
                    </div>
                    <span class="count-pill"><i class="fas fa-layer-group"></i> {{ sites|length }} site{{ '' if sites|length == 1 else 's' }}</span>
                </div>
                <div class="site-list">
                    {% for site in sites %}
                    <article class="site-item">
                        <div class="site-info">
                            <strong>{{ site.url }}</strong>
                            <div class="site-meta">
                                <span><i class="fas fa-hashtag"></i> ID {{ site.id }}</span>
                                <span><i class="fas fa-clock"></i> {{ site.cloned_at }}</span>
                            </div>
                        </div>
                        <a href="/editor/{{ site.id }}" class="btn-edit">Launch Editor <i class="fas fa-arrow-right"></i></a>
                    </article>
                    {% else %}
                    <div class="empty-state">
                        No saved clones are available yet.<br>
                        Create and save a clone in the main dashboard first, then return here to launch the visual builder.
                    </div>
                    {% endfor %}
                </div>
            </section>
        </div>
    </div>
</body>
</html>
"""

# ==========================================
# 2. THE EDITOR (GrapesJS with DB Loading)
# ==========================================
EDITOR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Builder Editor</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="//unpkg.com/grapesjs/dist/css/grapes.min.css">
    <script src="//unpkg.com/grapesjs"></script>
    <script src="https://unpkg.com/grapesjs-blocks-bootstrap4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">

    <style>
        :root {
            --bg: #eaf0fa;
            --surface-dark: rgba(11, 18, 30, 0.96);
            --surface-dark-strong: rgba(8, 14, 24, 0.98);
            --surface-soft: rgba(255, 255, 255, 0.88);
            --surface-soft-strong: rgba(255, 255, 255, 0.96);
            --text-light: #eef5ff;
            --muted-light: #a7b6cb;
            --text-dark: #0f172a;
            --muted-dark: #546377;
            --primary: #2563eb;
            --primary-strong: #1d4ed8;
            --success: #12a06d;
            --success-strong: #0f8c60;
            --danger: #dc2626;
            --shadow-lg: 0 24px 60px rgba(15, 23, 42, 0.18);
            --shadow-md: 0 18px 34px rgba(15, 23, 42, 0.12);
        }

        * { box-sizing: border-box; }

        html, body {
            height: 100%;
            margin: 0;
            overflow: hidden;
            font-family: 'Outfit', sans-serif;
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.14), transparent 22%),
                linear-gradient(180deg, #f5f8fe 0%, var(--bg) 100%);
        }

        .app-layout {
            display: grid;
            grid-template-columns: 280px minmax(0, 1fr) 310px;
            grid-template-rows: 78px minmax(0, 1fr);
            width: 100vw;
            height: 100vh;
        }

        .header-bar {
            grid-column: 1 / 4;
            grid-row: 1 / 2;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 0 20px;
            background:
                radial-gradient(circle at top, rgba(96, 165, 250, 0.2), transparent 30%),
                linear-gradient(180deg, rgba(11, 18, 30, 0.98) 0%, rgba(8, 14, 24, 0.98) 100%);
            border-bottom: 1px solid rgba(148, 163, 184, 0.14);
            color: var(--text-light);
            box-shadow: 0 16px 28px rgba(2, 6, 23, 0.18);
            z-index: 10;
        }

        .header-left,
        .header-right,
        .toolbar-group {
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 0;
        }

        .header-copy {
            display: flex;
            flex-direction: column;
            min-width: 0;
        }

        .header-kicker {
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #93c5fd;
        }

        .header-title {
            font-family: 'Sora', sans-serif;
            font-size: 16px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #f8fbff;
        }

        .header-subtitle {
            font-size: 12px;
            color: var(--muted-light);
            max-width: 420px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .sidebar-left,
        .sidebar-right {
            display: flex;
            flex-direction: column;
            min-height: 0;
            overflow: hidden;
            background: linear-gradient(180deg, rgba(11, 18, 30, 0.98) 0%, rgba(13, 20, 33, 0.96) 100%);
        }

        .sidebar-left {
            grid-column: 1 / 2;
            grid-row: 2 / 3;
            border-right: 1px solid rgba(148, 163, 184, 0.14);
        }

        .sidebar-right {
            grid-column: 3 / 4;
            grid-row: 2 / 3;
            border-left: 1px solid rgba(148, 163, 184, 0.14);
        }

        .main-stage {
            grid-column: 2 / 3;
            grid-row: 2 / 3;
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 16px;
            min-width: 0;
            min-height: 0;
        }

        .stage-banner {
            padding: 14px 16px;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            background: rgba(255, 255, 255, 0.84);
            box-shadow: var(--shadow-md);
            color: var(--muted-dark);
            line-height: 1.55;
        }

        .stage-banner strong {
            display: block;
            margin-bottom: 4px;
            color: var(--text-dark);
            font-size: 14px;
        }

        .canvas-wrapper {
            flex: 1;
            min-height: 0;
            padding: 16px;
            border-radius: 28px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 251, 255, 0.96) 100%);
            box-shadow: var(--shadow-lg);
        }

        #gjs {
            height: 100%;
            border-radius: 20px;
            overflow: hidden;
            background: #ffffff;
        }

        .panel-header {
            padding: 14px 16px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            background: rgba(255, 255, 255, 0.04);
        }

        .panel-header strong {
            display: block;
            font-family: 'Sora', sans-serif;
            font-size: 13px;
            font-weight: 700;
            color: #f8fbff;
        }

        .panel-header span {
            display: block;
            margin-top: 5px;
            color: var(--muted-light);
            font-size: 12px;
            line-height: 1.45;
        }

        #blocks-container,
        #layers-container,
        #styles-container,
        #traits-container {
            overflow-y: auto;
            flex: 1;
            min-height: 0;
            scrollbar-width: thin;
            scrollbar-color: rgba(148, 163, 184, 0.3) transparent;
        }

        .utility-panel {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            background: rgba(255, 255, 255, 0.03);
        }

        .back-btn,
        .device-btn,
        .action-btn,
        .save-btn,
        .save-state {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            border-radius: 14px;
            font-size: 13px;
            font-weight: 700;
            transition: transform 0.16s ease, background 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
        }

        .back-btn {
            padding: 10px 14px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            color: #eff6ff;
            text-decoration: none;
            background: rgba(255, 255, 255, 0.05);
        }

        .back-btn:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .device-btn,
        .action-btn {
            height: 42px;
            min-width: 42px;
            padding: 0 13px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(255, 255, 255, 0.05);
            color: #dbe7f6;
            cursor: pointer;
        }

        .device-btn:hover,
        .action-btn:hover,
        .save-btn:hover {
            transform: translateY(-1px);
        }

        .device-btn.active {
            background: rgba(37, 99, 235, 0.2);
            border-color: rgba(96, 165, 250, 0.32);
            color: #f8fbff;
            box-shadow: 0 14px 24px rgba(37, 99, 235, 0.18);
        }

        .save-btn {
            height: 42px;
            padding: 0 18px;
            border: 1px solid rgba(18, 160, 109, 0.18);
            background: linear-gradient(135deg, var(--success) 0%, #34d399 100%);
            color: #f8fbff;
            box-shadow: 0 16px 28px rgba(18, 160, 109, 0.22);
            cursor: pointer;
        }

        .save-btn.saving {
            background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%);
            border-color: rgba(148, 163, 184, 0.24);
            box-shadow: none;
            cursor: progress;
        }

        .save-state {
            min-width: 126px;
            padding: 10px 14px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(255, 255, 255, 0.05);
            color: #dbe7f6;
        }

        .save-state.ready { color: #dbe7f6; }
        .save-state.saving { color: #fef3c7; background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.2); }
        .save-state.saved { color: #d1fae5; background: rgba(18, 160, 109, 0.12); border-color: rgba(18, 160, 109, 0.2); }
        .save-state.error { color: #fee2e2; background: rgba(220, 38, 38, 0.12); border-color: rgba(220, 38, 38, 0.2); }

        .toast-msg {
            position: fixed;
            top: 18px;
            right: 18px;
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 13px;
            font-weight: 700;
            color: #f8fbff;
            z-index: 9999;
            opacity: 0;
            transform: translateY(-10px);
            transition: opacity 0.28s ease, transform 0.28s ease;
            pointer-events: none;
            box-shadow: var(--shadow-md);
        }

        .toast-msg.show { opacity: 1; transform: translateY(0); }
        .toast-msg.success { background: linear-gradient(135deg, var(--success) 0%, #34d399 100%); }
        .toast-msg.error { background: linear-gradient(135deg, #dc2626 0%, #fb7185 100%); }

        .gjs-cv-canvas { width: 100%; height: 100%; top: 0; }
        .gjs-one-bg,
        .gjs-two-color,
        .gjs-four-color {
            background-color: transparent !important;
            color: #dbe7f6 !important;
        }
        .gjs-three-bg {
            background: rgba(37, 99, 235, 0.2) !important;
            color: #f8fbff !important;
        }
        .gjs-block {
            width: calc(100% - 18px);
            margin: 9px;
            padding: 12px 12px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(148, 163, 184, 0.14);
            color: #e2e8f0;
            border-radius: 16px;
            display: flex;
            align-items: center;
            cursor: grab;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        }
        .gjs-block:hover {
            border-color: rgba(96, 165, 250, 0.3);
            background: rgba(255, 255, 255, 0.09);
        }
        .gjs-field {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid rgba(148, 163, 184, 0.18);
            color: var(--text-dark);
            border-radius: 12px;
        }
        .gjs-sm-sector-title {
            background: rgba(255, 255, 255, 0.04);
            color: #f8fbff;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
        }
        .gjs-sm-properties,
        .gjs-trt-traits,
        .gjs-sm-sectors {
            color: #dbe7f6;
        }

        @media (max-width: 1180px) {
            .app-layout {
                grid-template-columns: 250px minmax(0, 1fr) 280px;
            }
            .header-right {
                gap: 8px;
                flex-wrap: wrap;
                justify-content: flex-end;
            }
            .header-subtitle {
                max-width: 260px;
            }
        }
    </style>
</head>
<body>

    <div id="hidden-html" style="display:none;">{{ user_html | safe }}</div>

    <div class="app-layout">
        <div id="toast" class="toast-msg"></div>
        <div class="header-bar">
            <div class="header-left">
                <a href="/?user_id={{ user_id }}" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Sites</a>
                <div class="header-copy">
                    <div class="header-kicker">Visual Builder</div>
                    <div class="header-title">Editing cloned site</div>
                    <div class="header-subtitle">{{ site_url }}</div>
                </div>
            </div>

            <div class="header-right">
                <div class="toolbar-group">
                    <button class="device-btn active" onclick="setDevice('Desktop')" id="btn-d" title="Desktop view"><i class="fas fa-desktop"></i></button>
                    <button class="device-btn" onclick="setDevice('Tablet')" id="btn-t" title="Tablet view"><i class="fas fa-tablet-alt"></i></button>
                    <button class="device-btn" onclick="setDevice('Mobile portrait')" id="btn-m" title="Mobile view"><i class="fas fa-mobile-alt"></i></button>
                </div>
                <div class="toolbar-group">
                    <button class="action-btn" onclick="editor.runCommand('sw-visibility')" title="Toggle component borders"><i class="fas fa-border-none"></i></button>
                    <button class="action-btn" onclick="editor.runCommand('preview')" title="Full-screen preview (Escape to exit)"><i class="fas fa-eye"></i></button>
                    <button class="action-btn" onclick="editor.runCommand('core:undo')" title="Undo (Ctrl+Z)"><i class="fas fa-undo"></i></button>
                    <button class="action-btn" onclick="editor.runCommand('core:redo')" title="Redo (Ctrl+Y)"><i class="fas fa-redo"></i></button>
                </div>
                <div class="save-state ready" id="save-state">Ready to save</div>
                <button class="save-btn" id="save-btn" onclick="saveProject()" title="Save changes (Ctrl+S)"><i class="fas fa-save"></i> Save</button>
            </div>
        </div>

        <div class="sidebar-left">
            <div class="panel-header"><strong>Components</strong><span>Drag blocks into the canvas to build or refine structure.</span></div>
            <div id="blocks-container"></div>
            <div class="panel-header"><strong>Layers</strong><span>Review the page tree and select nested elements more precisely.</span></div>
            <div id="layers-container" style="height: 34%;"></div>
        </div>

        <div class="main-stage">
            <div class="stage-banner">
                <strong>Builder workspace</strong>
                Use the left panel for components and structure, the center canvas for the layout itself, and the right panel for styling plus editable properties.
            </div>
            <div class="canvas-wrapper">
                <div id="gjs"></div>
            </div>
        </div>

        <div class="sidebar-right">
            <div class="panel-header"><strong>Design</strong><span>Change selectors and styling for the currently selected element.</span></div>
            <div id="selectors-container" class="utility-panel"></div>
            <div id="styles-container"></div>
            <div class="panel-header"><strong>Properties</strong><span>Update links, content, media, and component traits clearly.</span></div>
            <div id="traits-container" style="flex:0.45;"></div>
        </div>
    </div>

    <script type="text/javascript">
        const editor = grapesjs.init({
            container: '#gjs',
            height: '100%',
            fromElement: false,
            storageManager: false,
            blockManager: { appendTo: '#blocks-container' },
            layerManager: { appendTo: '#layers-container' },
            selectorManager: { appendTo: '#selectors-container' },
            styleManager: { appendTo: '#styles-container' },
            traitManager: { appendTo: '#traits-container' },
            plugins: ['grapesjs-blocks-bootstrap4'],
            pluginsOpts: {
                'grapesjs-blocks-bootstrap4': {
                    blocks: {},
                    blockCategories: { 'Layout': true, 'Components': true, 'Forms': true }
                }
            },
            assetManager: { upload: '/upload-assets', uploadName: 'files', autoAdd: true },
            canvas: {
                styles: [
                    'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
                    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css'
                ],
                scripts: [
                    'https://code.jquery.com/jquery-3.5.1.slim.min.js',
                    'https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js',
                    'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js'
                ]
            }
        });

        // LOAD CONTENT FROM DB
        const userContent = document.getElementById('hidden-html').innerHTML;
        if(userContent.trim().length > 0) editor.setComponents(userContent);

        // DEVICE SWITCHER
        function setDevice(dev) {
            editor.setDevice(dev);
            document.querySelectorAll('.device-btn').forEach(b => b.classList.remove('active'));
            if(dev.includes('Mobile')) document.getElementById('btn-m').classList.add('active');
            else if(dev.includes('Tablet')) document.getElementById('btn-t').classList.add('active');
            else document.getElementById('btn-d').classList.add('active');
        }

        function showToast(message, type='success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `toast-msg ${type}`;
            requestAnimationFrame(() => toast.classList.add('show'));
            clearTimeout(showToast._timer);
            showToast._timer = setTimeout(() => toast.classList.remove('show'), 2200);
        }

        function setSaveState(message, tone='ready') {
            const stateEl = document.getElementById('save-state');
            stateEl.textContent = message;
            stateEl.className = `save-state ${tone}`;
        }

        let saveInFlight = false;

        // SAVE FUNCTION (API CALL)
        async function saveProject() {
            if (saveInFlight) return;
            saveInFlight = true;
            const saveButton = document.getElementById('save-btn');
            saveButton.classList.add('saving');
            saveButton.disabled = true;
            setSaveState('Saving changes...', 'saving');

            const html = editor.getHtml();
            const css = editor.getCss();
            const fullContent = `<style>${css}</style>` + html;

            try {
                const response = await fetch('/save_site/{{ site_id }}', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ html: fullContent })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    setSaveState('Saved', 'saved');
                    showToast('Saved to database.', 'success');
                } else {
                    throw new Error(data.message || 'Unable to save the project.');
                }
            } catch (error) {
                setSaveState('Save failed', 'error');
                showToast(error.message || 'Save failed.', 'error');
            } finally {
                saveInFlight = false;
                saveButton.disabled = false;
                saveButton.classList.remove('saving');
                setTimeout(() => {
                    if (!saveInFlight) setSaveState('Ready to save', 'ready');
                }, 2200);
            }
        }

        document.addEventListener('keydown', function (event) {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
                event.preventDefault();
                saveProject();
            }
        });
    </script>
</body>
</html>
"""

# ==========================================
# 3. ROUTING LOGIC
# ==========================================

@app.route('/', methods=['GET'])
def index():
    """Fetches sites filtered by the User ID passed from Streamlit."""
    user_id = request.args.get('user_id') # Capture the ID from URL
    conn = get_db_connection()
    
    if user_id:
        # Fetch ONLY this user's sites
        sites = conn.execute('SELECT * FROM cloned_sites WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    else:
        # Fallback if no ID is provided (e.g. direct access)
        sites = [] 

    conn.close()
    return render_template_string(DASHBOARD_TEMPLATE, sites=sites)

@app.route('/editor/<int:site_id>', methods=['GET'])
def open_editor(site_id):
    """Loads a specific site from DB into the editor."""
    conn = get_db_connection()
    site = conn.execute('SELECT * FROM cloned_sites WHERE id = ?', (site_id,)).fetchone()
    conn.close()

    if not site:
        return "Site not found", 404

    bundle_html = load_saved_bundle_entry(site_id, BASE_DIR, preview=True)
    db_html = site['html_content'] or ""
    # Guard against garbled/binary content in the DB fallback
    if db_html and len(db_html) > 50 and db_html.count("\ufffd") / len(db_html) > 0.03:
        db_html = "<!-- This clone contains corrupted content. Please re-clone the site. -->"
    editor_html = bundle_html or db_html
    return render_template_string(
        EDITOR_TEMPLATE,
        user_html=inject_clone_bridge(editor_html, site_id),
        site_id=site_id,
        user_id=site["user_id"],
        site_url=site["url"],
    )

@app.route('/save_site/<int:site_id>', methods=['POST'])
def save_site(site_id):
    """Saves the edited HTML back to the database."""
    try:
        data = request.json
        new_html = data.get('html')
        stored_html = strip_preview_paths(new_html, site_id)
        conn = get_db_connection()
        conn.execute('UPDATE cloned_sites SET html_content = ? WHERE id = ?', (stored_html, site_id))
        conn.commit()
        conn.close()
        update_saved_bundle_entry(site_id, new_html, BASE_DIR)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/upload-assets', methods=['POST'])
def upload_file():
    try:
        if 'files' not in request.files: return jsonify({"data": []})
        files = request.files.getlist('files')
        uploaded_urls = []
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                uploaded_urls.append(f"/assets/{filename}")
        return jsonify({"data": uploaded_urls})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/assets/<filename>')
def serve_asset(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def apply_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def serve_clone_file(file_path, site_id=None):
    _, extension = os.path.splitext(file_path.lower())
    if site_id is not None and extension in {".html", ".htm"}:
        try:
            with open(file_path, "r", encoding="utf-8") as input_file:
                html = input_file.read()
        except (UnicodeDecodeError, ValueError, OSError):
            return send_file(file_path)
        response = app.response_class(
            inject_clone_bridge(html, site_id),
            mimetype="text/html",
        )
        return apply_no_cache_headers(response)
    return send_file(file_path)


def serve_clone_directory(root_dir, requested_path="", site_id=None):
    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        return None

    safe_requested = requested_path or "index.html"
    candidate_path = os.path.abspath(os.path.join(root_dir, safe_requested))
    if not candidate_path.startswith(root_dir):
        return "Not found", 404

    if os.path.isdir(candidate_path):
        index_candidate = os.path.join(candidate_path, "index.html")
        if os.path.isfile(index_candidate):
            return serve_clone_file(index_candidate, site_id=site_id)

    if os.path.isfile(candidate_path):
        return serve_clone_file(candidate_path, site_id=site_id)

    path_without_ext = os.path.join(root_dir, safe_requested)
    html_candidate = f"{path_without_ext}.html"
    if os.path.isfile(html_candidate):
        return serve_clone_file(html_candidate, site_id=site_id)

    index_candidate = os.path.join(path_without_ext, "index.html")
    if os.path.isfile(index_candidate):
        return serve_clone_file(index_candidate, site_id=site_id)

    # Fuzzy fallback: look for flattened pages in pages/ directory.
    # The cloner flattens deep paths like /a/b/c to pages/{slug}-{hash}.html.
    # Try to match by finding a file whose name starts with the last path segment.
    pages_dir = os.path.join(root_dir, "pages")
    if os.path.isdir(pages_dir):
        segments = [s for s in safe_requested.replace("\\", "/").split("/") if s]
        if segments:
            slug_hint = segments[-1].lower().replace(".html", "").replace(".htm", "")
            for fname in os.listdir(pages_dir):
                if fname.lower().startswith(slug_hint) and fname.endswith(".html"):
                    return serve_clone_file(os.path.join(pages_dir, fname), site_id=site_id)

    return None


@app.route('/staged-clone/<clone_key>/', methods=['GET'])
@app.route('/staged-clone/<clone_key>/<path:requested_path>', methods=['GET'])
def staged_clone_preview(clone_key, requested_path=""):
    staging_root, _ = default_workspace_roots(BASE_DIR)
    clone_root = os.path.join(staging_root, clone_key, "site")
    served = serve_clone_directory(clone_root, requested_path)
    if served is not None:
        return served
    return "Staged clone not found", 404


@app.route('/clone/<int:site_id>/export.zip', methods=['GET'])
def clone_export(site_id):
    archive_path = get_saved_bundle_archive(site_id, BASE_DIR)
    if os.path.exists(archive_path):
        return send_file(archive_path, as_attachment=True, download_name=f"clone_site_{site_id}.zip")
    return "Clone export not found", 404


@app.route('/clone/<int:site_id>/', methods=['GET'])
@app.route('/clone/<int:site_id>/<path:requested_path>', methods=['GET'])
def clone_preview(site_id, requested_path=""):
    saved_site_dir = get_saved_bundle_site_dir(site_id, BASE_DIR)
    served = serve_clone_directory(saved_site_dir, requested_path, site_id=site_id)
    if served is not None:
        return served

    _, requested_ext = os.path.splitext((requested_path or "").lower())
    if requested_ext and requested_ext not in {".html", ".htm"}:
        return "Asset not found", 404
    if requested_path and requested_path.strip("/"):
        return "Page not found", 404

    conn = get_db_connection()
    site = conn.execute('SELECT html_content FROM cloned_sites WHERE id = ?', (site_id,)).fetchone()
    conn.close()
    if not site:
        return "Site not found", 404
    response = app.response_class(
        inject_clone_bridge(site["html_content"], site_id),
        mimetype="text/html",
    )
    return apply_no_cache_headers(response)


@app.route('/admin')
@app.route('/admin/')
@app.route('/admin/<path:path>')
def serve_admin_app(path=''):
    if not os.path.exists(ADMIN_DIST_DIR):
        return "Admin build not found. Build the admin app first.", 404

    requested_path = os.path.join(ADMIN_DIST_DIR, path)
    if path and os.path.isfile(requested_path):
        return send_file(requested_path)

    index_path = os.path.join(ADMIN_DIST_DIR, 'index.html')
    if os.path.isfile(index_path):
        return send_file(index_path)
    return "Admin build entry not found.", 404


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    payload = request.json or {}
    username = payload.get('username', '').strip()
    password = payload.get('password', '')

    if not username or not password:
        return jsonify({"message": "Username and password are required."}), 400

    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username FROM users WHERE username = ? AND password = ?',
        (username, hash_password(password))
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"message": "Invalid credentials."}), 401

    token = serializer.dumps({"user_id": user["id"], "username": user["username"]})
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
        }
    })


@app.route('/api/admin/me', methods=['GET'])
@require_admin_auth
def admin_me():
    return jsonify(request.admin_user)


@app.route('/api/projects', methods=['GET'])
@require_admin_auth
def api_projects():
    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT cloned_sites.id, cloned_sites.url, cloned_sites.cloned_at,
               conversion_blueprints.site_type, conversion_blueprints.confidence,
               site_specs.spec_json
        FROM cloned_sites
        LEFT JOIN conversion_blueprints ON conversion_blueprints.site_id = cloned_sites.id
        LEFT JOIN site_specs ON site_specs.site_id = cloned_sites.id
        WHERE cloned_sites.user_id = ?
        ORDER BY cloned_sites.id DESC
        ''',
        (request.admin_user["user_id"],)
    ).fetchall()
    counts = conn.execute(
        '''
        SELECT site_id, model_name, COUNT(*) AS total_count,
               SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) AS published_count
        FROM dynamic_records
        WHERE user_id = ?
        GROUP BY site_id, model_name
        ''',
        (request.admin_user["user_id"],)
    ).fetchall()
    conn.close()

    count_map = {}
    for row in counts:
        site_counts = count_map.setdefault(row["site_id"], {"records": 0, "published": 0, "resources": set()})
        site_counts["records"] += row["total_count"]
        site_counts["published"] += row["published_count"] or 0
        site_counts["resources"].add(row["model_name"])

    projects = []
    for row in rows:
        site_counts = count_map.get(row["id"], {"records": 0, "published": 0, "resources": set()})
        projects.append({
            "id": row["id"],
            "name": build_site_name(row),
            "url": row["url"],
            "siteType": row["site_type"] or "unknown",
            "confidence": row["confidence"] or 0,
            "resourceCount": len(site_counts["resources"]),
            "recordCount": site_counts["records"],
            "publishedCount": site_counts["published"],
            "clonedAt": row["cloned_at"],
            "cloneUrl": build_clone_preview_url(row["id"]),
        })

    return jsonify(projects)


@app.route('/api/projects/<int:site_id>/spec', methods=['GET', 'PATCH'])
@require_admin_auth
def api_project_spec(site_id):
    if request.method == 'PATCH':
        payload = request.json or {}
        spec = payload.get("spec")
        bindings = payload.get("bindings", [])
        if not spec:
            return jsonify({"message": "spec is required"}), 400

        conn = get_db_connection()
        conn.execute(
            '''
            INSERT INTO site_specs (site_id, user_id, spec_json, bindings_json, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(site_id) DO UPDATE SET
                user_id = excluded.user_id,
                spec_json = excluded.spec_json,
                bindings_json = excluded.bindings_json,
                updated_at = excluded.updated_at
            ''',
            (
                site_id,
                request.admin_user["user_id"],
                json.dumps(spec),
                json.dumps(bindings),
            )
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "updated"})

    project = fetch_project(site_id)
    spec_bundle = fetch_site_spec(site_id)
    if not project or project["user_id"] != request.admin_user["user_id"]:
        return jsonify({"message": "Project not found"}), 404
    if not spec_bundle:
        return jsonify({"message": "SiteSpec not found"}), 404

    conn = get_db_connection()
    counts = conn.execute(
        '''
        SELECT model_name, COUNT(*) AS total_count,
               SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) AS published_count
        FROM dynamic_records
        WHERE site_id = ? AND user_id = ?
        GROUP BY model_name
        ''',
        (site_id, request.admin_user["user_id"])
    ).fetchall()
    conn.close()

    resource_counts = {
        row["model_name"]: {
            "total": row["total_count"],
            "published": row["published_count"] or 0,
        }
        for row in counts
    }

    return jsonify({
        "project": {
            "id": project["id"],
            "name": build_site_name(project),
            "url": project["url"],
            "siteType": project["site_type"] or "unknown",
            "confidence": project["confidence"] or 0,
            "cloneUrl": build_clone_preview_url(project["id"]),
        },
        "spec": spec_bundle["spec"],
        "bindings": spec_bundle["bindings"],
        "resourceCounts": resource_counts,
        "updatedAt": spec_bundle["updated_at"],
    })


@app.route('/api/admin/<int:site_id>/<resource_key>', methods=['GET', 'POST'])
@require_admin_auth
def admin_resource(site_id, resource_key):
    project = fetch_project(site_id)
    if not project or project["user_id"] != request.admin_user["user_id"]:
        return jsonify({"message": "Project not found"}), 404

    conn = get_db_connection()

    if request.method == 'GET':
        rows = conn.execute(
            '''
            SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
            FROM dynamic_records
            WHERE site_id = ? AND user_id = ? AND model_name = ?
            ORDER BY id DESC
            ''',
            (site_id, request.admin_user["user_id"], resource_key)
        ).fetchall()
        conn.close()
        return jsonify([normalize_record_response(row) for row in rows])

    payload = request.json or {}
    data = payload.get("data", {})
    status = payload.get("status", "draft")
    slug = payload.get("slug") or data.get("slug") or data.get("title") or data.get("name") or resource_key
    conn.execute(
        '''
        INSERT INTO dynamic_records (site_id, user_id, model_name, data_json, slug, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        ''',
        (
            site_id,
            request.admin_user["user_id"],
            resource_key,
            json.dumps(data),
            slugify(slug),
            status,
        )
    )
    conn.commit()
    record_id = conn.execute('SELECT last_insert_rowid() AS id').fetchone()["id"]
    row = conn.execute(
        '''
        SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
        FROM dynamic_records
        WHERE id = ?
        ''',
        (record_id,)
    ).fetchone()
    conn.close()
    return jsonify(normalize_record_response(row)), 201


@app.route('/api/admin/<int:site_id>/<resource_key>/<int:record_id>', methods=['PATCH', 'DELETE'])
@require_admin_auth
def admin_resource_item(site_id, resource_key, record_id):
    project = fetch_project(site_id)
    if not project or project["user_id"] != request.admin_user["user_id"]:
        return jsonify({"message": "Project not found"}), 404

    conn = get_db_connection()
    existing = conn.execute(
        '''
        SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
        FROM dynamic_records
        WHERE id = ? AND site_id = ? AND user_id = ? AND model_name = ?
        ''',
        (record_id, site_id, request.admin_user["user_id"], resource_key)
    ).fetchone()
    if not existing:
        conn.close()
        return jsonify({"message": "Record not found"}), 404

    if request.method == 'DELETE':
        conn.execute('DELETE FROM dynamic_records WHERE id = ?', (record_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})

    payload = request.json or {}
    data = payload.get("data", json.loads(existing["data_json"]))
    status = payload.get("status", existing["status"])
    slug = payload.get("slug") or data.get("slug") or data.get("title") or data.get("name") or existing["slug"]
    conn.execute(
        '''
        UPDATE dynamic_records
        SET data_json = ?, slug = ?, status = ?, updated_at = datetime('now')
        WHERE id = ?
        ''',
        (json.dumps(data), slugify(slug), status, record_id)
    )
    conn.commit()
    updated = conn.execute(
        '''
        SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
        FROM dynamic_records
        WHERE id = ?
        ''',
        (record_id,)
    ).fetchone()
    conn.close()
    return jsonify(normalize_record_response(updated))


@app.route('/api/admin/<int:site_id>/<resource_key>/<int:record_id>/publish', methods=['PATCH'])
@require_admin_auth
def admin_publish_record(site_id, resource_key, record_id):
    project = fetch_project(site_id)
    if not project or project["user_id"] != request.admin_user["user_id"]:
        return jsonify({"message": "Project not found"}), 404

    payload = request.json or {}
    status = payload.get("status", "published")
    if status not in {"draft", "published"}:
        return jsonify({"message": "Invalid status"}), 400

    conn = get_db_connection()
    conn.execute(
        '''
        UPDATE dynamic_records
        SET status = ?, updated_at = datetime('now')
        WHERE id = ? AND site_id = ? AND user_id = ? AND model_name = ?
        ''',
        (status, record_id, site_id, request.admin_user["user_id"], resource_key)
    )
    conn.commit()
    row = conn.execute(
        '''
        SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
        FROM dynamic_records
        WHERE id = ?
        ''',
        (record_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"message": "Record not found"}), 404
    return jsonify(normalize_record_response(row))


@app.route('/api/admin/<int:site_id>/media', methods=['GET', 'POST'])
@require_admin_auth
def admin_media(site_id):
    project = fetch_project(site_id)
    if not project or project["user_id"] != request.admin_user["user_id"]:
        return jsonify({"message": "Project not found"}), 404

    conn = get_db_connection()

    if request.method == 'GET':
        search = request.args.get('search', '').strip().lower()
        media_type = request.args.get('type', '').strip().lower()
        status = request.args.get('status', '').strip().lower()
        where_clauses = ['site_id = ?', 'user_id = ?', "status NOT IN ('deleted', 'archived')"]
        params = [site_id, request.admin_user["user_id"]]
        if search:
            where_clauses.append('(LOWER(original_name) LIKE ? OR LOWER(COALESCE(original_url, \'\')) LIKE ? OR LOWER(COALESCE(alt_text, \'\')) LIKE ?)')
            like_value = f"%{search}%"
            params.extend([like_value, like_value, like_value])
        if media_type:
            where_clauses.append('media_type = ?')
            params.append(media_type)
        if status:
            where_clauses.append('status = ?')
            params.append(status)
        rows = conn.execute(
            f'''
            SELECT id, asset_key, source_kind, media_type, mime_type, filename, original_name,
                   file_url, original_url, alt_text, width, height, hash, status, section_key,
                   usage_json, metadata_json, local_path, uploaded_at, updated_at
            FROM media_assets
            WHERE {' AND '.join(where_clauses)}
            ORDER BY COALESCE(updated_at, uploaded_at) DESC, id DESC
            ''',
            params
        ).fetchall()
        conn.close()
        return jsonify([media_row_payload(row) for row in rows])

    if 'file' not in request.files:
        conn.close()
        return jsonify({"message": "file is required"}), 400

    file = request.files['file']
    if not file or not file.filename:
        conn.close()
        return jsonify({"message": "A valid file is required"}), 400

    site_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'media', f'site_{site_id}')
    os.makedirs(site_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    save_path = os.path.join(site_dir, filename)
    file.save(save_path)
    file_url = f"/media/{site_id}/{filename}"
    mime_type = file.mimetype or mimetypes.guess_type(filename)[0] or ''
    media_type = guess_upload_media_type(filename, mime_type)
    with open(save_path, 'rb') as saved_file:
        file_hash = hashlib.sha1(saved_file.read()).hexdigest()
    asset_key = hashlib.sha1(f"upload:{site_id}:{file_hash}:{filename}".encode('utf-8')).hexdigest()

    conn.execute(
        '''
        INSERT INTO media_assets (
            site_id, user_id, asset_key, source_kind, media_type, mime_type, filename,
            original_name, file_url, original_url, alt_text, width, height, hash, status,
            section_key, usage_json, metadata_json, local_path, uploaded_at, updated_at
        )
        VALUES (?, ?, ?, 'upload', ?, ?, ?, ?, ?, ?, '', NULL, NULL, ?, 'ready', '', '[]', '{}', ?, datetime('now'), datetime('now'))
        ''',
        (
            site_id,
            request.admin_user["user_id"],
            asset_key,
            media_type,
            mime_type,
            filename,
            file.filename,
            file_url,
            file_url,
            file_hash,
            save_path,
        )
    )
    conn.commit()
    row = conn.execute(
        '''
        SELECT id, asset_key, source_kind, media_type, mime_type, filename, original_name,
               file_url, original_url, alt_text, width, height, hash, status, section_key,
               usage_json, metadata_json, local_path, uploaded_at, updated_at
        FROM media_assets
        WHERE id = last_insert_rowid()
        '''
    ).fetchone()
    conn.close()

    return jsonify(media_row_payload(row)), 201


@app.route('/api/admin/<int:site_id>/media/<int:media_id>', methods=['PATCH', 'DELETE'])
@require_admin_auth
def admin_media_item(site_id, media_id):
    project = fetch_project(site_id)
    if not project or project["user_id"] != request.admin_user["user_id"]:
        return jsonify({"message": "Project not found"}), 404

    conn = get_db_connection()
    row = conn.execute(
        '''
        SELECT id, asset_key, source_kind, media_type, mime_type, filename, original_name,
               file_url, original_url, alt_text, width, height, hash, status, section_key,
               usage_json, metadata_json, local_path, uploaded_at, updated_at
        FROM media_assets
        WHERE id = ? AND site_id = ? AND user_id = ?
        ''',
        (media_id, site_id, request.admin_user["user_id"])
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"message": "Media not found"}), 404

    if request.method == 'DELETE':
        conn.execute(
            "UPDATE media_assets SET status = 'deleted', updated_at = datetime('now') WHERE id = ?",
            (media_id,)
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})

    file = request.files.get('file')
    payload = request.form.to_dict() if request.form else {}
    if not payload:
        payload = request.get_json(silent=True) or {}

    if file and file.filename:
        current_filename = row["filename"] or secure_filename(file.filename)
        site_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'media', f'site_{site_id}')
        os.makedirs(site_dir, exist_ok=True)
        save_path = row["local_path"] or os.path.join(site_dir, current_filename)
        file.save(save_path)
        with open(save_path, 'rb') as saved_file:
            file_hash = hashlib.sha1(saved_file.read()).hexdigest()
        mime_type = file.mimetype or mimetypes.guess_type(current_filename)[0] or row["mime_type"]
        media_type = guess_upload_media_type(current_filename, mime_type)
        file_url = row["file_url"] or f"/media/{site_id}/{current_filename}"
        conn.execute(
            '''
            UPDATE media_assets
            SET media_type = ?, mime_type = ?, original_name = ?, file_url = ?, local_path = ?,
                hash = ?, status = 'custom', updated_at = datetime('now')
            WHERE id = ?
            ''',
            (media_type, mime_type, file.filename, file_url, save_path, file_hash, media_id)
        )

    if payload:
        conn.execute(
            '''
            UPDATE media_assets
            SET alt_text = COALESCE(?, alt_text),
                section_key = COALESCE(?, section_key),
                original_url = COALESCE(?, original_url),
                status = COALESCE(?, status),
                updated_at = datetime('now')
            WHERE id = ?
            ''',
            (
                payload.get('altText'),
                payload.get('sectionKey'),
                payload.get('originalUrl'),
                payload.get('status'),
                media_id,
            )
        )

    conn.commit()
    refreshed = conn.execute(
        '''
        SELECT id, asset_key, source_kind, media_type, mime_type, filename, original_name,
               file_url, original_url, alt_text, width, height, hash, status, section_key,
               usage_json, metadata_json, local_path, uploaded_at, updated_at
        FROM media_assets
        WHERE id = ?
        ''',
        (media_id,)
    ).fetchone()
    conn.close()
    return jsonify(media_row_payload(refreshed))


@app.route('/media/<int:site_id>/<filename>')
def serve_media(site_id, filename):
    media_root = os.path.join(app.config['UPLOAD_FOLDER'], 'media', f'site_{site_id}')
    response = send_from_directory(media_root, filename)
    return apply_no_cache_headers(response)


@app.route('/api/public/<int:site_id>/<resource_key>', methods=['GET'])
def public_resource(site_id, resource_key):
    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
        FROM dynamic_records
        WHERE site_id = ? AND model_name = ? AND status = 'published'
        ORDER BY id DESC
        ''',
        (site_id, resource_key)
    ).fetchall()
    conn.close()
    return jsonify([normalize_record_response(row) for row in rows])

@app.route('/dynamic-api/<int:site_id>/meta', methods=['GET'])
def dynamic_meta(site_id):
    conn = get_db_connection()
    models = conn.execute(
        '''
        SELECT model_name, section_title, schema_json, display_order
        FROM dynamic_models
        WHERE site_id = ?
        ORDER BY display_order ASC, model_name ASC
        ''',
        (site_id,)
    ).fetchall()
    conn.close()

    payload = []
    for model in models:
        payload.append({
            "model_name": model["model_name"],
            "section_title": model["section_title"],
            "schema": json.loads(model["schema_json"]),
            "endpoint": f"/dynamic-api/{site_id}/{model['model_name']}",
        })

    return jsonify({"site_id": site_id, "collections": payload})

@app.route('/dynamic-api/<int:site_id>/<model_name>', methods=['GET', 'POST'])
def dynamic_collection(site_id, model_name):
    conn = get_db_connection()

    if request.method == 'GET':
        rows = conn.execute(
            '''
            SELECT id, data_json, updated_at
            FROM dynamic_records
            WHERE site_id = ? AND model_name = ?
            ORDER BY id ASC
            ''',
            (site_id, model_name)
        ).fetchall()
        conn.close()

        records = []
        for row in rows:
            payload = json.loads(row["data_json"])
            payload["id"] = row["id"]
            payload["_updated_at"] = row["updated_at"]
            records.append(payload)
        return jsonify(records)

    payload = request.json or {}
    conn.execute(
        '''
        INSERT INTO dynamic_records (site_id, user_id, model_name, data_json, created_at, updated_at)
        VALUES (?, 0, ?, ?, datetime('now'), datetime('now'))
        ''',
        (site_id, model_name, json.dumps(payload))
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "created"}), 201

@app.route('/dynamic-api/<int:site_id>/<model_name>/<int:record_id>', methods=['PUT', 'DELETE'])
def dynamic_item(site_id, model_name, record_id):
    conn = get_db_connection()

    if request.method == 'DELETE':
        conn.execute(
            'DELETE FROM dynamic_records WHERE id = ? AND site_id = ? AND model_name = ?',
            (record_id, site_id, model_name)
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})

    payload = request.json or {}
    conn.execute(
        '''
        UPDATE dynamic_records
        SET data_json = ?, updated_at = datetime('now')
        WHERE id = ? AND site_id = ? AND model_name = ?
        ''',
        (json.dumps(payload), record_id, site_id, model_name)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})

if __name__ == '__main__':
    ensure_dynamic_tables()
    print("--------------------------------------------------")
    print(" STUDIO READY: http://127.0.0.1:5001")
    print("--------------------------------------------------")
    debug_enabled = os.environ.get("AA_FLASK_DEBUG", "").strip() == "1"
    app.run(host='127.0.0.1', port=5001, debug=debug_enabled, use_reloader=False)
