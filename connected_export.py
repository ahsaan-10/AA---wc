import json
import os
import shutil
import sqlite3
import textwrap
from string import Template
from urllib.parse import urlparse

from cloner_engine import get_saved_bundle_site_dir, load_bundle_manifest, strip_preview_paths
from smart_conversion import inject_clone_bridge


DB_NAME = "users.db"
EXPORT_DEFAULT_PORT = 5010
REQUIRED_TABLES = (
    "users",
    "cloned_sites",
    "conversion_blueprints",
    "site_specs",
    "dynamic_models",
    "dynamic_records",
    "media_assets",
)


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)


def slugify_label(value):
    cleaned = []
    for char in str(value or "").strip().lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    return "".join(cleaned).strip("-") or "connected-site"


def build_site_name(site_row, spec_json):
    if spec_json:
        try:
            spec = json.loads(spec_json)
            if spec.get("siteName"):
                return spec["siteName"]
        except Exception:
            pass
    url = (site_row["url"] or "").strip()
    parsed = urlparse(url)
    return parsed.netloc or url or f"site-{site_row['id']}"


def load_site_export_context(site_id, user_id, base_dir):
    source_db = os.path.join(base_dir, DB_NAME)
    conn = sqlite3.connect(source_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT cloned_sites.id, cloned_sites.user_id, cloned_sites.url, cloned_sites.html_content, cloned_sites.cloned_at,
               users.username, users.password,
               conversion_blueprints.site_type, conversion_blueprints.confidence, conversion_blueprints.blueprint_json,
               site_specs.spec_json, site_specs.bindings_json
        FROM cloned_sites
        JOIN users ON users.id = cloned_sites.user_id
        LEFT JOIN conversion_blueprints ON conversion_blueprints.site_id = cloned_sites.id
        LEFT JOIN site_specs ON site_specs.site_id = cloned_sites.id
        WHERE cloned_sites.id = ? AND cloned_sites.user_id = ?
        """,
        (site_id, user_id),
    ).fetchone()
    conn.close()

    if not row:
        raise ValueError("The selected site was not found for the current user.")
    if not row["spec_json"]:
        raise ValueError("Generate Database + Admin Panel first so the connected system has SiteSpec, API, and admin data.")

    site_name = build_site_name(row, row["spec_json"])
    return {
        "site": row,
        "site_name": site_name,
        "site_slug": slugify_label(site_name),
        "site_type": row["site_type"] or "unknown",
        "confidence": row["confidence"] or 0,
        "spec": json.loads(row["spec_json"]),
        "bindings": json.loads(row["bindings_json"] or "[]"),
        "blueprint": json.loads(row["blueprint_json"]) if row["blueprint_json"] else None,
    }


def copytree_clean(source_dir, destination_dir):
    if os.path.isdir(destination_dir):
        shutil.rmtree(destination_dir)
    shutil.copytree(source_dir, destination_dir)


def sync_export_clone_html(site_id, clone_root, site_html, manifest):
    entry_path = (manifest.get("route_map") or {}).get(manifest.get("source_url"), "index.html")
    entry_file = os.path.join(clone_root, *entry_path.split("/"))
    if site_html and os.path.exists(entry_file):
        normalized_html = strip_preview_paths(site_html, site_id)
        with open(entry_file, "w", encoding="utf-8") as output_file:
            output_file.write(normalized_html)

    injected_count = 0
    for root, _, files in os.walk(clone_root):
        for filename in files:
            if not filename.lower().endswith(".html"):
                continue
            file_path = os.path.join(root, filename)
            with open(file_path, "r", encoding="utf-8") as input_file:
                html = input_file.read()
            rewritten = inject_clone_bridge(html, site_id)
            if rewritten != html:
                with open(file_path, "w", encoding="utf-8") as output_file:
                    output_file.write(rewritten)
                injected_count += 1

    with open(entry_file, "r", encoding="utf-8") as input_file:
        entry_html = input_file.read()

    return {
        "entry_path": entry_path,
        "entry_html": entry_html,
        "bridge_injected_pages": injected_count,
    }


def export_site_database(site_id, user_id, source_db_path, destination_db_path, generated_root):
    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    destination_conn = sqlite3.connect(destination_db_path)
    destination_conn.row_factory = sqlite3.Row

    schema_rows = source_conn.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_master
        WHERE sql IS NOT NULL
          AND name NOT LIKE 'sqlite_%'
          AND (name IN ({names}) OR tbl_name IN ({names}))
        """.format(names=",".join("?" for _ in REQUIRED_TABLES)),
        REQUIRED_TABLES + REQUIRED_TABLES,
    ).fetchall()

    table_order = {name: index for index, name in enumerate(REQUIRED_TABLES)}
    table_rows = sorted(
        [row for row in schema_rows if row["type"] == "table" and row["name"] in REQUIRED_TABLES],
        key=lambda row: table_order[row["name"]],
    )
    index_rows = [row for row in schema_rows if row["type"] == "index" and row["tbl_name"] in REQUIRED_TABLES]

    for row in table_rows:
        destination_conn.execute(row["sql"])
    for row in index_rows:
        destination_conn.execute(row["sql"])

    filters = {
        "users": ("id = ?", (user_id,)),
        "cloned_sites": ("id = ? AND user_id = ?", (site_id, user_id)),
        "conversion_blueprints": ("site_id = ? AND user_id = ?", (site_id, user_id)),
        "site_specs": ("site_id = ? AND user_id = ?", (site_id, user_id)),
        "dynamic_models": ("site_id = ? AND user_id = ?", (site_id, user_id)),
        "dynamic_records": ("site_id = ? AND user_id = ?", (site_id, user_id)),
        "media_assets": ("site_id = ? AND user_id = ?", (site_id, user_id)),
    }

    for table_name in REQUIRED_TABLES:
        columns = [row["name"] for row in source_conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
        where_clause, params = filters[table_name]
        rows = source_conn.execute(
            f"SELECT {', '.join(columns)} FROM {table_name} WHERE {where_clause}",
            params,
        ).fetchall()
        if not rows:
            continue
        placeholders = ", ".join("?" for _ in columns)
        destination_conn.executemany(
            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
            [tuple(row[column] for column in columns) for row in rows],
        )

    destination_conn.execute(
        "UPDATE media_assets SET local_path = '', updated_at = COALESCE(updated_at, uploaded_at) WHERE site_id = ?",
        (site_id,),
    )
    destination_conn.execute(
        "UPDATE conversion_blueprints SET artifact_dir = ? WHERE site_id = ?",
        (generated_root.replace('\\\\', '/'), site_id),
    )
    destination_conn.commit()
    source_conn.close()
    destination_conn.close()


BACKEND_TEMPLATE_HEAD = Template(
    textwrap.dedent(
        """
        import hashlib
        import json
        import mimetypes
        import os
        import socket
        import sqlite3
        from functools import wraps

        from flask import Flask, jsonify, redirect, request, send_file
        from flask_cors import CORS
        from itsdangerous import BadSignature, URLSafeSerializer
        from werkzeug.utils import secure_filename

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ADMIN_SYSTEM_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
        EXPORT_ROOT = os.path.abspath(os.path.join(ADMIN_SYSTEM_ROOT, ".."))
        CLONE_ROOT = os.path.join(EXPORT_ROOT, "cloned_website")
        ADMIN_DIST_DIR = os.path.join(ADMIN_SYSTEM_ROOT, "admin_panel")
        DB_NAME = os.path.join(ADMIN_SYSTEM_ROOT, "database", "site.db")
        MEDIA_ROOT = os.path.join(ADMIN_SYSTEM_ROOT, "media", "site_$SITE_ID")
        SITE_ID = $SITE_ID
        DEFAULT_PORT = int(os.environ.get("FABRICATOR_EXPORT_PORT", "$DEFAULT_PORT"))
        TOKEN_SECRET = "fabricator-connected-export"
        serializer = URLSafeSerializer(TOKEN_SECRET, salt="site-admin-auth")

        app = Flask(__name__)
        CORS(app, resources={r"/api/*": {"origins": "*"}, r"/dynamic-api/*": {"origins": "*"}})


        def get_db_connection():
            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row
            return conn


        def hash_password(password):
            return hashlib.sha256(str(password).encode("utf-8")).hexdigest()


        def slugify(value):
            return secure_filename(str(value).strip().lower().replace(" ", "-")) or "record"


        def get_token_payload():
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return None
            token = auth_header.split(" ", 1)[1]
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


        def build_site_name(row):
            spec_json = row["spec_json"] if row and "spec_json" in row.keys() else None
            if spec_json:
                try:
                    spec = json.loads(spec_json)
                    if spec.get("siteName"):
                        return spec["siteName"]
                except Exception:
                    pass
            if row and "url" in row.keys():
                return row["url"].replace("https://", "").replace("http://", "").strip("/") or "Connected Site"
            return "Connected Site"


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


        def fetch_project():
            conn = get_db_connection()
            row = conn.execute(
                '''
                SELECT cloned_sites.id, cloned_sites.user_id, cloned_sites.url, cloned_sites.cloned_at,
                       conversion_blueprints.site_type, conversion_blueprints.confidence, site_specs.spec_json
                FROM cloned_sites
                LEFT JOIN conversion_blueprints ON conversion_blueprints.site_id = cloned_sites.id
                LEFT JOIN site_specs ON site_specs.site_id = cloned_sites.id
                WHERE cloned_sites.id = ?
                ''',
                (SITE_ID,)
            ).fetchone()
            conn.close()
            return row


        def fetch_site_spec():
            conn = get_db_connection()
            row = conn.execute(
                '''
                SELECT site_specs.spec_json, site_specs.bindings_json, site_specs.updated_at, cloned_sites.url
                FROM site_specs
                LEFT JOIN cloned_sites ON cloned_sites.id = site_specs.site_id
                WHERE site_specs.site_id = ?
                ''',
                (SITE_ID,)
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


        def serve_file_safe(root_dir, requested_path=""):
            root_dir = os.path.abspath(root_dir)
            if not os.path.isdir(root_dir):
                return None
            safe_requested = requested_path or "index.html"
            candidate_path = os.path.abspath(os.path.join(root_dir, safe_requested))
            if not candidate_path.startswith(root_dir):
                return None
            if os.path.isdir(candidate_path):
                index_candidate = os.path.join(candidate_path, "index.html")
                if os.path.isfile(index_candidate):
                    return send_file(index_candidate)
            if os.path.isfile(candidate_path):
                return send_file(candidate_path)
            path_without_ext = os.path.join(root_dir, safe_requested)
            html_candidate = f"{path_without_ext}.html"
            if os.path.isfile(html_candidate):
                return send_file(html_candidate)
            index_candidate = os.path.join(path_without_ext, "index.html")
            if os.path.isfile(index_candidate):
                return send_file(index_candidate)
            return None


        def resolve_runtime_port():
            for candidate in range(DEFAULT_PORT, DEFAULT_PORT + 20):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    if sock.connect_ex(("127.0.0.1", candidate)) != 0:
                        return candidate
            return DEFAULT_PORT
        """
    )
)

BACKEND_TEMPLATE_TAIL = Template(
    textwrap.dedent(
        """

        @app.route("/")
        def root():
            return redirect("/site/")


        @app.route("/health")
        def health():
            return jsonify({
                "status": "ok",
                "siteId": SITE_ID,
                "cloneRoot": CLONE_ROOT,
                "adminRoot": ADMIN_DIST_DIR,
                "database": DB_NAME,
            })


        @app.route("/site")
        @app.route("/site/")
        @app.route("/site/<path:requested_path>")
        def exported_site(requested_path=""):
            served = serve_file_safe(CLONE_ROOT, requested_path)
            if served is not None:
                return served
            return "Cloned page not found", 404


        @app.route("/clone/<int:site_id>/")
        @app.route("/clone/<int:site_id>/<path:requested_path>")
        def clone_alias(site_id, requested_path=""):
            if site_id != SITE_ID:
                return "Site not found", 404
            served = serve_file_safe(CLONE_ROOT, requested_path)
            if served is not None:
                return served
            return "Cloned page not found", 404


        @app.route("/admin")
        @app.route("/admin/")
        @app.route("/admin/<path:path>")
        def serve_admin_app(path=""):
            requested_path = os.path.join(ADMIN_DIST_DIR, path)
            if path and os.path.isfile(requested_path):
                return send_file(requested_path)
            index_path = os.path.join(ADMIN_DIST_DIR, "index.html")
            if os.path.isfile(index_path):
                return send_file(index_path)
            return "Admin build entry not found.", 404


        @app.route("/api/admin/login", methods=["POST"])
        def admin_login():
            payload = request.json or {}
            username = payload.get("username", "").strip()
            password = payload.get("password", "")
            if not username or not password:
                return jsonify({"message": "Username and password are required."}), 400

            conn = get_db_connection()
            user = conn.execute(
                "SELECT id, username FROM users WHERE username = ? AND password = ?",
                (username, hash_password(password))
            ).fetchone()
            conn.close()
            if not user:
                return jsonify({"message": "Invalid credentials."}), 401

            token = serializer.dumps({"user_id": user["id"], "username": user["username"]})
            return jsonify({
                "token": token,
                "user": {"id": user["id"], "username": user["username"]},
            })


        @app.route("/api/admin/me", methods=["GET"])
        @require_admin_auth
        def admin_me():
            return jsonify(request.admin_user)
        """
    )
)

BACKEND_TEMPLATE_TAIL_2 = Template(
    textwrap.dedent(
        """

        @app.route("/api/projects", methods=["GET"])
        @require_admin_auth
        def api_projects():
            project = fetch_project()
            if not project or project["user_id"] != request.admin_user["user_id"]:
                return jsonify([])

            conn = get_db_connection()
            counts = conn.execute(
                '''
                SELECT model_name, COUNT(*) AS total_count,
                       SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) AS published_count
                FROM dynamic_records
                WHERE site_id = ? AND user_id = ?
                GROUP BY model_name
                ''',
                (SITE_ID, request.admin_user["user_id"])
            ).fetchall()
            conn.close()

            return jsonify([{
                "id": project["id"],
                "name": build_site_name(project),
                "url": project["url"],
                "siteType": project["site_type"] or "unknown",
                "confidence": project["confidence"] or 0,
                "resourceCount": len(counts),
                "recordCount": sum(row["total_count"] for row in counts),
                "publishedCount": sum((row["published_count"] or 0) for row in counts),
                "clonedAt": project["cloned_at"],
                "cloneUrl": "/site/",
            }])


        @app.route("/api/projects/<int:site_id>/spec", methods=["GET", "PATCH"])
        @require_admin_auth
        def api_project_spec(site_id):
            if site_id != SITE_ID:
                return jsonify({"message": "Project not found"}), 404

            project = fetch_project()
            if not project or project["user_id"] != request.admin_user["user_id"]:
                return jsonify({"message": "Project not found"}), 404

            if request.method == "PATCH":
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
                    (SITE_ID, request.admin_user["user_id"], json.dumps(spec), json.dumps(bindings)),
                )
                conn.commit()
                conn.close()
                return jsonify({"status": "updated"})

            spec_bundle = fetch_site_spec()
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
                (SITE_ID, request.admin_user["user_id"])
            ).fetchall()
            conn.close()
            resource_counts = {
                row["model_name"]: {"total": row["total_count"], "published": row["published_count"] or 0}
                for row in counts
            }
            return jsonify({
                "project": {
                    "id": project["id"],
                    "name": build_site_name(project),
                    "url": project["url"],
                    "siteType": project["site_type"] or "unknown",
                    "confidence": project["confidence"] or 0,
                    "cloneUrl": "/site/",
                },
                "spec": spec_bundle["spec"],
                "bindings": spec_bundle["bindings"],
                "resourceCounts": resource_counts,
                "updatedAt": spec_bundle["updated_at"],
            })


        def ensure_project_access(site_id):
            project = fetch_project()
            return project if site_id == SITE_ID else None
        """
    )
)

BACKEND_TEMPLATE_TAIL_3 = Template(
    textwrap.dedent(
        """

        @app.route("/api/admin/<int:site_id>/<resource_key>", methods=["GET", "POST"])
        @require_admin_auth
        def admin_resource(site_id, resource_key):
            project = ensure_project_access(site_id)
            if not project or project["user_id"] != request.admin_user["user_id"]:
                return jsonify({"message": "Project not found"}), 404

            conn = get_db_connection()
            if request.method == "GET":
                rows = conn.execute(
                    '''
                    SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
                    FROM dynamic_records
                    WHERE site_id = ? AND user_id = ? AND model_name = ?
                    ORDER BY id DESC
                    ''',
                    (SITE_ID, request.admin_user["user_id"], resource_key)
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
                (SITE_ID, request.admin_user["user_id"], resource_key, json.dumps(data), slugify(slug), status),
            )
            conn.commit()
            record_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            row = conn.execute(
                '''
                SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
                FROM dynamic_records WHERE id = ?
                ''',
                (record_id,)
            ).fetchone()
            conn.close()
            return jsonify(normalize_record_response(row)), 201


        @app.route("/api/admin/<int:site_id>/<resource_key>/<int:record_id>", methods=["PATCH", "DELETE"])
        @require_admin_auth
        def admin_resource_item(site_id, resource_key, record_id):
            project = ensure_project_access(site_id)
            if not project or project["user_id"] != request.admin_user["user_id"]:
                return jsonify({"message": "Project not found"}), 404

            conn = get_db_connection()
            existing = conn.execute(
                '''
                SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
                FROM dynamic_records
                WHERE id = ? AND site_id = ? AND user_id = ? AND model_name = ?
                ''',
                (record_id, SITE_ID, request.admin_user["user_id"], resource_key)
            ).fetchone()
            if not existing:
                conn.close()
                return jsonify({"message": "Record not found"}), 404
            if request.method == "DELETE":
                conn.execute("DELETE FROM dynamic_records WHERE id = ?", (record_id,))
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
                (json.dumps(data), slugify(slug), status, record_id),
            )
            conn.commit()
            updated = conn.execute(
                '''
                SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
                FROM dynamic_records WHERE id = ?
                ''',
                (record_id,)
            ).fetchone()
            conn.close()
            return jsonify(normalize_record_response(updated))


        @app.route("/api/admin/<int:site_id>/<resource_key>/<int:record_id>/publish", methods=["PATCH"])
        @require_admin_auth
        def admin_publish_record(site_id, resource_key, record_id):
            project = ensure_project_access(site_id)
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
                (status, record_id, SITE_ID, request.admin_user["user_id"], resource_key),
            )
            conn.commit()
            row = conn.execute(
                '''
                SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
                FROM dynamic_records WHERE id = ?
                ''',
                (record_id,)
            ).fetchone()
            conn.close()
            if not row:
                return jsonify({"message": "Record not found"}), 404
            return jsonify(normalize_record_response(row))
        """
    )
)

BACKEND_TEMPLATE_TAIL_4 = Template(
    textwrap.dedent(
        """

        @app.route("/api/admin/<int:site_id>/media", methods=["GET", "POST"])
        @require_admin_auth
        def admin_media(site_id):
            project = ensure_project_access(site_id)
            if not project or project["user_id"] != request.admin_user["user_id"]:
                return jsonify({"message": "Project not found"}), 404

            conn = get_db_connection()
            if request.method == "GET":
                search = request.args.get("search", "").strip().lower()
                media_type = request.args.get("type", "").strip().lower()
                status = request.args.get("status", "").strip().lower()
                where_clauses = ["site_id = ?", "user_id = ?", "status NOT IN ('deleted', 'archived')"]
                params = [SITE_ID, request.admin_user["user_id"]]
                if search:
                    where_clauses.append("(LOWER(original_name) LIKE ? OR LOWER(COALESCE(original_url, '')) LIKE ? OR LOWER(COALESCE(alt_text, '')) LIKE ?)")
                    like_value = f"%{search}%"
                    params.extend([like_value, like_value, like_value])
                if media_type:
                    where_clauses.append("media_type = ?")
                    params.append(media_type)
                if status:
                    where_clauses.append("status = ?")
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
                    params,
                ).fetchall()
                conn.close()
                return jsonify([media_row_payload(row) for row in rows])

            if "file" not in request.files:
                conn.close()
                return jsonify({"message": "file is required"}), 400
            file = request.files["file"]
            if not file or not file.filename:
                conn.close()
                return jsonify({"message": "A valid file is required"}), 400

            os.makedirs(MEDIA_ROOT, exist_ok=True)
            filename = secure_filename(file.filename)
            save_path = os.path.join(MEDIA_ROOT, filename)
            file.save(save_path)
            file_url = f"/media/{SITE_ID}/{filename}"
            mime_type = file.mimetype or mimetypes.guess_type(filename)[0] or ""
            media_type = guess_upload_media_type(filename, mime_type)
            with open(save_path, "rb") as saved_file:
                file_hash = hashlib.sha1(saved_file.read()).hexdigest()
            asset_key = hashlib.sha1(f"upload:{SITE_ID}:{file_hash}:{filename}".encode("utf-8")).hexdigest()
            conn.execute(
                '''
                INSERT INTO media_assets (
                    site_id, user_id, asset_key, source_kind, media_type, mime_type, filename,
                    original_name, file_url, original_url, alt_text, width, height, hash, status,
                    section_key, usage_json, metadata_json, local_path, uploaded_at, updated_at
                )
                VALUES (?, ?, ?, 'upload', ?, ?, ?, ?, ?, ?, '', NULL, NULL, ?, 'ready', '', '[]', '{}', '', datetime('now'), datetime('now'))
                ''',
                (SITE_ID, request.admin_user["user_id"], asset_key, media_type, mime_type, filename, file.filename, file_url, file_url, file_hash),
            )
            conn.commit()
            row = conn.execute(
                '''
                SELECT id, asset_key, source_kind, media_type, mime_type, filename, original_name,
                       file_url, original_url, alt_text, width, height, hash, status, section_key,
                       usage_json, metadata_json, local_path, uploaded_at, updated_at
                FROM media_assets WHERE id = last_insert_rowid()
                '''
            ).fetchone()
            conn.close()
            return jsonify(media_row_payload(row)), 201


        @app.route("/api/admin/<int:site_id>/media/<int:media_id>", methods=["PATCH", "DELETE"])
        @require_admin_auth
        def admin_media_item(site_id, media_id):
            project = ensure_project_access(site_id)
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
                (media_id, SITE_ID, request.admin_user["user_id"]),
            ).fetchone()
            if not row:
                conn.close()
                return jsonify({"message": "Media not found"}), 404
            if request.method == "DELETE":
                conn.execute("UPDATE media_assets SET status = 'deleted', updated_at = datetime('now') WHERE id = ?", (media_id,))
                conn.commit()
                conn.close()
                return jsonify({"status": "deleted"})

            file = request.files.get("file")
            payload = request.form if request.form else (request.json or {})
            if file and file.filename:
                os.makedirs(MEDIA_ROOT, exist_ok=True)
                current_filename = row["filename"] or secure_filename(file.filename)
                save_path = os.path.join(MEDIA_ROOT, current_filename)
                file.save(save_path)
                with open(save_path, "rb") as saved_file:
                    file_hash = hashlib.sha1(saved_file.read()).hexdigest()
                mime_type = file.mimetype or mimetypes.guess_type(current_filename)[0] or row["mime_type"]
                media_type = guess_upload_media_type(current_filename, mime_type)
                file_url = row["file_url"] or f"/media/{SITE_ID}/{current_filename}"
                conn.execute(
                    '''
                    UPDATE media_assets
                    SET media_type = ?, mime_type = ?, original_name = ?, file_url = ?, original_url = ?, hash = ?, updated_at = datetime('now')
                    WHERE id = ?
                    ''',
                    (media_type, mime_type, file.filename, file_url, payload.get("originalUrl", row["original_url"] or file_url), file_hash, media_id),
                )

            conn.execute(
                '''
                UPDATE media_assets
                SET alt_text = ?, section_key = ?, original_url = ?, status = ?, updated_at = datetime('now')
                WHERE id = ?
                ''',
                (
                    payload.get("altText", row["alt_text"] or ""),
                    payload.get("sectionKey", row["section_key"] or ""),
                    payload.get("originalUrl", row["original_url"] or row["file_url"] or ""),
                    payload.get("status", row["status"] or "ready"),
                    media_id,
                ),
            )
            conn.commit()
            refreshed = conn.execute(
                '''
                SELECT id, asset_key, source_kind, media_type, mime_type, filename, original_name,
                       file_url, original_url, alt_text, width, height, hash, status, section_key,
                       usage_json, metadata_json, local_path, uploaded_at, updated_at
                FROM media_assets WHERE id = ?
                ''',
                (media_id,),
            ).fetchone()
            conn.close()
            return jsonify(media_row_payload(refreshed))


        @app.route("/media/<int:site_id>/<filename>")
        def serve_media(site_id, filename):
            if site_id != SITE_ID:
                return "Media not found", 404
            file_path = os.path.join(MEDIA_ROOT, filename)
            if os.path.isfile(file_path):
                return send_file(file_path)
            return "Media not found", 404


        @app.route("/api/public/<int:site_id>/<resource_key>", methods=["GET"])
        def public_resource(site_id, resource_key):
            if site_id != SITE_ID:
                return jsonify([])
            conn = get_db_connection()
            rows = conn.execute(
                '''
                SELECT id, site_id, model_name, data_json, slug, status, created_at, updated_at
                FROM dynamic_records
                WHERE site_id = ? AND model_name = ? AND status = 'published'
                ORDER BY id DESC
                ''',
                (SITE_ID, resource_key),
            ).fetchall()
            conn.close()
            return jsonify([normalize_record_response(row) for row in rows])


        @app.route("/dynamic-api/<int:site_id>/meta", methods=["GET"])
        def dynamic_meta(site_id):
            if site_id != SITE_ID:
                return jsonify({"site_id": site_id, "collections": []})
            conn = get_db_connection()
            models = conn.execute(
                '''
                SELECT model_name, section_title, schema_json, display_order
                FROM dynamic_models
                WHERE site_id = ?
                ORDER BY display_order ASC, model_name ASC
                ''',
                (SITE_ID,),
            ).fetchall()
            conn.close()
            payload = [{
                "model_name": model["model_name"],
                "section_title": model["section_title"],
                "schema": json.loads(model["schema_json"]),
                "endpoint": f"/dynamic-api/{SITE_ID}/{model['model_name']}",
            } for model in models]
            return jsonify({"site_id": SITE_ID, "collections": payload})


        @app.route("/dynamic-api/<int:site_id>/<model_name>", methods=["GET", "POST"])
        def dynamic_collection(site_id, model_name):
            if site_id != SITE_ID:
                return jsonify({"message": "Collection not found"}), 404
            conn = get_db_connection()
            if request.method == "GET":
                rows = conn.execute(
                    '''
                    SELECT id, data_json, updated_at
                    FROM dynamic_records
                    WHERE site_id = ? AND model_name = ?
                    ORDER BY id ASC
                    ''',
                    (SITE_ID, model_name),
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
                (SITE_ID, model_name, json.dumps(payload)),
            )
            conn.commit()
            conn.close()
            return jsonify({"status": "created"}), 201


        @app.route("/dynamic-api/<int:site_id>/<model_name>/<int:record_id>", methods=["PUT", "DELETE"])
        def dynamic_item(site_id, model_name, record_id):
            if site_id != SITE_ID:
                return jsonify({"message": "Record not found"}), 404
            conn = get_db_connection()
            if request.method == "DELETE":
                conn.execute("DELETE FROM dynamic_records WHERE id = ? AND site_id = ? AND model_name = ?", (record_id, SITE_ID, model_name))
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
                (json.dumps(payload), record_id, SITE_ID, model_name),
            )
            conn.commit()
            conn.close()
            return jsonify({"status": "updated"})


        if __name__ == "__main__":
            runtime_port = resolve_runtime_port()
            print("Connected export ready")
            print(f"Clone Website: http://127.0.0.1:{runtime_port}/site/")
            print(f"Admin Panel:   http://127.0.0.1:{runtime_port}/admin/site/{SITE_ID}/login")
            app.run(host="127.0.0.1", port=runtime_port, debug=False, use_reloader=False)
        """
    )
)


def write_backend_runtime(backend_root, site_id):
    ensure_directory(backend_root)
    backend_source = (
        BACKEND_TEMPLATE_HEAD.substitute(SITE_ID=site_id, DEFAULT_PORT=EXPORT_DEFAULT_PORT)
        + BACKEND_TEMPLATE_TAIL.substitute(SITE_ID=site_id)
        + BACKEND_TEMPLATE_TAIL_2.substitute(SITE_ID=site_id)
        + BACKEND_TEMPLATE_TAIL_3.substitute(SITE_ID=site_id)
        + BACKEND_TEMPLATE_TAIL_4.substitute(SITE_ID=site_id)
    )
    with open(os.path.join(backend_root, "app.py"), "w", encoding="utf-8") as output_file:
        output_file.write(backend_source)

    requirements = "\n".join([
        "flask",
        "flask-cors",
        "itsdangerous",
    ]) + "\n"
    with open(os.path.join(backend_root, "requirements.txt"), "w", encoding="utf-8") as output_file:
        output_file.write(requirements)

    backend_batch = textwrap.dedent(
        """\
        @echo off
        cd /d "%~dp0"
        set FABRICATOR_EXPORT_PORT=5010
        python app.py
        """
    )
    with open(os.path.join(backend_root, "start_backend.bat"), "w", encoding="utf-8") as output_file:
        output_file.write(backend_batch)


def write_export_docs(package_root, context, package_manifest):
    readme = textwrap.dedent(
        f"""\
        # Fabricator Connected Export

        This package contains one complete connected clone system for:
        - Site: `{context['site_name']}`
        - Site ID: `{context['site']['id']}`
        - Source URL: `{context['site']['url']}`

        ## Folder Structure

        - `cloned_website/`
          - The cloned frontend pages and assets.
        - `admin_system/`
          - `admin_panel/`: built standalone admin website.
          - `backend/`: Flask API + static server for both the clone and admin app.
          - `database/site.db`: site-specific SQLite database.
          - `media/`: clone and admin media library files.
          - `generated_dynamic/`: SiteSpec, schema, media manifest, and scaffold files.

        ## Run

        1. Open a terminal in this exported folder.
        2. Run `start_connected_system.bat`

        Or manually:

        1. `cd admin_system\\backend`
        2. `python app.py`

        ## URLs

        - Clone website: `http://127.0.0.1:{EXPORT_DEFAULT_PORT}/site/`
        - Admin panel: `http://127.0.0.1:{EXPORT_DEFAULT_PORT}/admin/site/{context['site']['id']}/login`

        ## Login

        Use the same username/password that owned this site in the main Fabricator project.

        If port `{EXPORT_DEFAULT_PORT}` is already busy, the exported backend automatically moves to the next free port and prints the exact URLs in the terminal.
        """
    )
    with open(os.path.join(package_root, "README.md"), "w", encoding="utf-8") as output_file:
        output_file.write(readme)

    with open(os.path.join(package_root, "export_manifest.json"), "w", encoding="utf-8") as output_file:
        json.dump(package_manifest, output_file, indent=2)

    root_batch = textwrap.dedent(
        """\
        @echo off
        cd /d "%~dp0admin_system\\backend"
        set FABRICATOR_EXPORT_PORT=5010
        python app.py
        """
    )
    with open(os.path.join(package_root, "start_connected_system.bat"), "w", encoding="utf-8") as output_file:
        output_file.write(root_batch)


def build_connected_export(site_id, user_id, base_dir=None):
    base_dir = os.path.abspath(base_dir or os.getcwd())
    context = load_site_export_context(site_id, user_id, base_dir)

    admin_dist_dir = os.path.join(base_dir, "admin", "dist")
    if not os.path.isdir(admin_dist_dir):
        raise ValueError("Admin build not found. Build the admin panel first before exporting the connected system.")

    saved_site_dir = get_saved_bundle_site_dir(site_id, base_dir)
    if not os.path.isdir(saved_site_dir):
        raise ValueError("Saved clone package not found. Save the clone first before exporting the connected system.")

    generated_src = os.path.join(base_dir, "project_assets", "generated_dynamic_apps", f"site_{site_id}")
    if not os.path.isdir(generated_src):
        raise ValueError("Generated dynamic artifacts were not found. Run Generate Database + Admin Panel first.")

    media_src = os.path.join(base_dir, "project_assets", "media", f"site_{site_id}")
    export_root = os.path.join(base_dir, "project_assets", "connected_exports", f"site_{site_id}")
    ensure_directory(os.path.dirname(export_root))
    if os.path.isdir(export_root):
        shutil.rmtree(export_root)
    ensure_directory(export_root)

    bundle_name = f"{context['site_slug']}_connected_system"
    package_root = os.path.join(export_root, bundle_name)
    clone_root = os.path.join(package_root, "cloned_website")
    admin_root = os.path.join(package_root, "admin_system")
    admin_panel_root = os.path.join(admin_root, "admin_panel")
    backend_root = os.path.join(admin_root, "backend")
    database_root = os.path.join(admin_root, "database")
    generated_root = os.path.join(admin_root, "generated_dynamic")
    media_root = os.path.join(admin_root, "media")
    ensure_directory(package_root)
    ensure_directory(admin_root)
    ensure_directory(database_root)
    ensure_directory(media_root)

    copytree_clean(saved_site_dir, clone_root)
    copytree_clean(admin_dist_dir, admin_panel_root)
    copytree_clean(generated_src, generated_root)
    if os.path.isdir(media_src):
        copytree_clean(media_src, os.path.join(media_root, f"site_{site_id}"))

    saved_manifest = load_bundle_manifest(site_id, base_dir)
    fabricator_meta_root = os.path.join(clone_root, "_fabricator")
    ensure_directory(fabricator_meta_root)
    with open(os.path.join(fabricator_meta_root, "manifest.json"), "w", encoding="utf-8") as output_file:
        json.dump(saved_manifest, output_file, indent=2)

    clone_sync = sync_export_clone_html(site_id, clone_root, context["site"]["html_content"], saved_manifest)

    export_db_path = os.path.join(database_root, "site.db")
    export_site_database(site_id, user_id, os.path.join(base_dir, DB_NAME), export_db_path, "admin_system/generated_dynamic")

    destination_conn = sqlite3.connect(export_db_path)
    destination_conn.execute(
        "UPDATE cloned_sites SET html_content = ? WHERE id = ?",
        (clone_sync["entry_html"], site_id),
    )
    destination_conn.commit()
    destination_conn.close()

    write_backend_runtime(backend_root, site_id)

    package_manifest = {
        "siteId": site_id,
        "siteName": context["site_name"],
        "siteType": context["site_type"],
        "sourceUrl": context["site"]["url"],
        "confidence": context["confidence"],
        "folders": {
            "clonedWebsite": "cloned_website",
            "adminSystem": "admin_system",
            "backend": "admin_system/backend",
            "adminPanel": "admin_system/admin_panel",
            "database": "admin_system/database/site.db",
            "media": "admin_system/media",
            "generatedDynamic": "admin_system/generated_dynamic",
        },
        "urls": {
            "cloneWebsite": f"http://127.0.0.1:{EXPORT_DEFAULT_PORT}/site/",
            "adminPanel": f"http://127.0.0.1:{EXPORT_DEFAULT_PORT}/admin/site/{site_id}/login",
        },
        "bridgeInjectedPages": clone_sync["bridge_injected_pages"],
        "entryPath": clone_sync["entry_path"],
    }
    write_export_docs(package_root, context, package_manifest)

    archive_base = os.path.join(export_root, bundle_name)
    archive_path = shutil.make_archive(archive_base, "zip", export_root, bundle_name)

    return {
        "site_id": site_id,
        "site_name": context["site_name"],
        "export_root": export_root,
        "package_root": package_root,
        "archive_path": archive_path,
        "clone_root": clone_root,
        "admin_root": admin_root,
        "database_path": export_db_path,
        "manifest": package_manifest,
    }
