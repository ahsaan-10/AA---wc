"""
AI Website Fabricator - Complete End-to-End Code Flow Document
Generates a jury-ready PDF with file references, diagrams, and explanations.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, ListFlowable, ListItem
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics import renderPDF
import os

# ── Colors ──
DARK = HexColor("#1a1a2e")
ACCENT = HexColor("#3b82f6")
ACCENT2 = HexColor("#8b5cf6")
LIGHT_BG = HexColor("#f0f4ff")
BORDER = HexColor("#cbd5e1")
GREEN = HexColor("#22c55e")
ORANGE = HexColor("#f59e0b")
RED = HexColor("#ef4444")
GRAY = HexColor("#64748b")
WHITE = white

W, H = A4

# ── Styles ──
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    "DocTitle", parent=styles["Title"], fontSize=22, leading=28,
    textColor=DARK, spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold"
))
styles.add(ParagraphStyle(
    "DocSubtitle", parent=styles["Normal"], fontSize=11, leading=14,
    textColor=GRAY, spaceAfter=20, alignment=TA_CENTER
))
styles.add(ParagraphStyle(
    "H1", parent=styles["Heading1"], fontSize=16, leading=20,
    textColor=DARK, spaceBefore=18, spaceAfter=8, fontName="Helvetica-Bold"
))
styles.add(ParagraphStyle(
    "H2", parent=styles["Heading2"], fontSize=13, leading=17,
    textColor=ACCENT, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"
))
styles.add(ParagraphStyle(
    "H3", parent=styles["Heading3"], fontSize=11, leading=14,
    textColor=ACCENT2, spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold"
))
styles.add(ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=9.5, leading=13,
    textColor=black, spaceAfter=6, alignment=TA_JUSTIFY
))
styles.add(ParagraphStyle(
    "CodeBlock", parent=styles["Normal"], fontSize=8, leading=10,
    fontName="Courier", textColor=HexColor("#334155"), backColor=LIGHT_BG,
    spaceAfter=6, leftIndent=12, borderPadding=4
))
styles.add(ParagraphStyle(
    "FileRef", parent=styles["Normal"], fontSize=8, leading=10,
    fontName="Courier-Bold", textColor=ACCENT, spaceAfter=2
))
styles.add(ParagraphStyle(
    "Caption", parent=styles["Normal"], fontSize=8.5, leading=11,
    textColor=GRAY, alignment=TA_CENTER, spaceAfter=10, spaceBefore=4
))
styles.add(ParagraphStyle(
    "BulletBody", parent=styles["Normal"], fontSize=9.5, leading=13,
    textColor=black, spaceAfter=3, leftIndent=20, bulletIndent=8
))
styles.add(ParagraphStyle(
    "TableCell", parent=styles["Normal"], fontSize=8, leading=10, textColor=black
))
styles.add(ParagraphStyle(
    "TableHeader", parent=styles["Normal"], fontSize=8, leading=10,
    textColor=WHITE, fontName="Helvetica-Bold"
))

# ── Helper functions ──
def heading(text, level=1):
    return Paragraph(text, styles[f"H{level}"])

def body(text):
    return Paragraph(text, styles["Body"])

def code(text):
    return Paragraph(text, styles["CodeBlock"])

def fileref(path):
    return Paragraph(f"File: {path}", styles["FileRef"])

def caption(text):
    return Paragraph(text, styles["Caption"])

def bullet(text):
    return Paragraph(f"\u2022 {text}", styles["BulletBody"])

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=8, spaceBefore=8)

def make_table(headers, rows, col_widths=None):
    data = [headers] + rows
    if col_widths is None:
        col_widths = [W * 0.85 / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t

def box_diagram(labels_and_arrows, width=480, row_height=32):
    """Draw a vertical flow diagram with boxes and arrows."""
    d = Drawing(width, row_height * len(labels_and_arrows) + 10)
    bw, bh = 280, 24
    x_center = width / 2
    for i, label in enumerate(labels_and_arrows):
        y = (len(labels_and_arrows) - 1 - i) * row_height + 5
        if label.startswith("->"):
            # Arrow label
            d.add(String(x_center, y + 6, label[2:].strip(),
                         fontSize=7, fillColor=GRAY, textAnchor="middle"))
            d.add(Line(x_center, y + 2, x_center, y - 4, strokeColor=GRAY, strokeWidth=0.8))
        else:
            # Box
            bx = x_center - bw / 2
            color = ACCENT if "[" not in label else ACCENT2
            d.add(Rect(bx, y, bw, bh, fillColor=color, strokeColor=color, rx=4, ry=4))
            d.add(String(x_center, y + 8, label, fontSize=8, fillColor=WHITE, textAnchor="middle"))
    return d


# ══════════════════════════════════════════════
#   BUILD PDF
# ══════════════════════════════════════════════
output_path = os.path.join(os.path.dirname(__file__), "AI_Website_Fabricator_Code_Flow.pdf")

doc = SimpleDocTemplate(
    output_path, pagesize=A4,
    leftMargin=0.7*inch, rightMargin=0.7*inch,
    topMargin=0.6*inch, bottomMargin=0.6*inch
)

story = []

# ── TITLE PAGE ──
story.append(Spacer(1, 80))
story.append(Paragraph("AI Website Fabricator", styles["DocTitle"]))
story.append(Paragraph("Complete End-to-End Code Flow Document", styles["DocSubtitle"]))
story.append(Spacer(1, 10))
story.append(Paragraph("Jury-Ready Technical Reference with File References", styles["DocSubtitle"]))
story.append(Spacer(1, 30))
story.append(hr())

# Quick project summary
story.append(body(
    "This document provides a <b>complete, end-to-end technical walkthrough</b> of the AI Website Fabricator project. "
    "It covers every module, algorithm, database schema, and data flow with exact file references. "
    "The project is a <b>Streamlit + Flask hybrid system</b> that clones any website, analyzes its structure, "
    "auto-generates a database schema and admin panel, and packages everything as a standalone deployable system."
))
story.append(Spacer(1, 10))

# File map table
story.append(heading("Project File Map", 2))
story.append(make_table(
    ["File", "Size", "Role"],
    [
        ["app.py", "~99 KB", "Main Streamlit UI, auth, database, orchestration"],
        ["cloner_engine.py", "~74 KB", "Website crawling, asset download, HTML rewriting"],
        ["smart_conversion.py", "~69 KB", "Site analysis, model inference, blueprint generation"],
        ["connected_export.py", "~50 KB", "Standalone export packaging with Flask backend"],
        ["dragdrop_flask.py", "~50 KB", "Flask server, GrapesJS editor, admin API"],
        ["admin/src/ (React+TS)", "~20 files", "Admin panel SPA (React 19, TypeScript, Vite)"],
        ["users.db", "SQLite", "All user data, sites, models, records, media"],
    ],
    col_widths=[140, 60, 280]
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   TABLE OF CONTENTS
# ══════════════════════════════════════════════
story.append(heading("Table of Contents", 1))
toc_items = [
    "1. System Architecture Overview",
    "2. Application Startup Flow",
    "3. Authentication System",
    "4. Database Schema (All 8 Tables)",
    "5. Module 1: Website Cloning Engine (cloner_engine.py)",
    "6. Module 2: Smart Dynamic Conversion (smart_conversion.py)",
    "7. Module 3: Main Application Orchestrator (app.py)",
    "8. Module 4: Drag & Drop Visual Editor (dragdrop_flask.py)",
    "9. Module 5: Connected Export Packager (connected_export.py)",
    "10. Module 6: Admin Panel Frontend (admin/src/)",
    "11. End-to-End User Journey Flow",
    "12. API Endpoints Reference",
    "13. Key Algorithms Deep Dive",
    "14. Diagram Explanations",
]
for item in toc_items:
    story.append(body(item))
story.append(PageBreak())

# ══════════════════════════════════════════════
#   1. SYSTEM ARCHITECTURE
# ══════════════════════════════════════════════
story.append(heading("1. System Architecture Overview", 1))
story.append(body(
    "The system is a <b>hybrid Streamlit + Flask architecture</b>. Streamlit (app.py) serves the main UI on port 8501. "
    "Flask (dragdrop_flask.py) runs on port 5001 for the visual editor and admin API. "
    "Both share the same SQLite database (users.db). The exported system runs standalone Flask on port 5010."
))

story.append(heading("Architecture Diagram", 2))
arch_items = [
    "USER BROWSER",
    "-> Requests page",
    "STREAMLIT UI (app.py : port 8501)",
    "-> Cloning / Conversion / Editor",
    "FLASK BACKEND (dragdrop_flask.py : port 5001)",
    "-> Reads/Writes",
    "SQLite DATABASE (users.db : 8 tables)",
    "-> Exports to",
    "STANDALONE PACKAGE (connected_export.py : port 5010)",
]
story.append(box_diagram(arch_items))
story.append(caption(
    "Diagram: The user interacts with Streamlit. Streamlit calls cloner_engine and smart_conversion modules. "
    "Flask provides the drag-drop editor (embedded as iframe) and the admin API. "
    "connected_export packages everything into a standalone ZIP with its own Flask server."
))

story.append(heading("Module Dependency Graph", 2))
story.append(make_table(
    ["Module", "Imports From", "Purpose of Import"],
    [
        ["app.py", "cloner_engine", "clone_site_bundle, persist_bundle, load_bundle, normalize_url"],
        ["app.py", "smart_conversion", "build_conversion_blueprint, build_site_spec, create_scaffold_files, inject_clone_bridge"],
        ["app.py", "connected_export", "build_connected_export (packaging)"],
        ["dragdrop_flask.py", "cloner_engine", "get_saved_bundle_site_dir, load/update_saved_bundle_entry"],
        ["dragdrop_flask.py", "smart_conversion", "inject_clone_bridge"],
        ["connected_export.py", "cloner_engine", "get_saved_bundle_site_dir, load_bundle_manifest, strip_preview_paths"],
        ["connected_export.py", "smart_conversion", "inject_clone_bridge"],
    ],
    col_widths=[100, 100, 280]
))
story.append(caption("Every module dependency with the specific functions imported."))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   2. STARTUP FLOW
# ══════════════════════════════════════════════
story.append(heading("2. Application Startup Flow", 1))
story.append(fileref("app.py (bottom of file), dragdrop_flask.py (bottom of file)"))
story.append(body(
    "The system starts in two stages:"
))
story.append(bullet("<b>Stage 1 - Streamlit</b>: User runs <font face='Courier'>streamlit run app.py</font>. "
    "This initializes the database via <font face='Courier'>init_db()</font> which creates all 8 tables if they don't exist. "
    "Then it checks session state and shows either the login page or the main app."))
story.append(bullet("<b>Stage 2 - Flask</b>: When the user navigates to 'Drag &amp; Drop Builder', "
    "<font face='Courier'>ensure_flask_running()</font> checks if port 5001 is active via <font face='Courier'>socket.connect_ex()</font>. "
    "If not, it spawns <font face='Courier'>dragdrop_flask.py</font> as a subprocess."))
story.append(Spacer(1, 6))
story.append(fileref("app.py : init_db() - lines ~50-120"))
story.append(code(
    "def init_db():<br/>"
    "&nbsp;&nbsp;conn = sqlite3.connect(DB_NAME)  # 'users.db'<br/>"
    "&nbsp;&nbsp;c = conn.cursor()<br/>"
    "&nbsp;&nbsp;c.execute('CREATE TABLE IF NOT EXISTS users ...')<br/>"
    "&nbsp;&nbsp;c.execute('CREATE TABLE IF NOT EXISTS cloned_sites ...')<br/>"
    "&nbsp;&nbsp;# ... creates all 8 tables<br/>"
    "&nbsp;&nbsp;conn.commit(); conn.close()"
))
story.append(fileref("app.py : ensure_flask_running()"))
story.append(code(
    "def ensure_flask_running():<br/>"
    "&nbsp;&nbsp;if not flask_running(FLASK_PORT):  # socket check port 5001<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;subprocess.Popen([sys.executable, 'dragdrop_flask.py'])"
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   3. AUTHENTICATION
# ══════════════════════════════════════════════
story.append(heading("3. Authentication System", 1))

story.append(heading("3.1 Streamlit Auth (Main App)", 2))
story.append(fileref("app.py : hash_password(), login_user(), create_user()"))
story.append(body(
    "Passwords are hashed with <b>SHA-256</b> via <font face='Courier'>hashlib.sha256(password.encode()).hexdigest()</font>. "
    "Login queries the <font face='Courier'>users</font> table matching username AND password hash. "
    "On success, <font face='Courier'>st.session_state['logged_in'] = True</font> and user tuple is stored in "
    "<font face='Courier'>st.session_state['user_info']</font> = (id, username, hash, created_at)."
))

story.append(heading("3.2 Flask Admin Auth (API)", 2))
story.append(fileref("dragdrop_flask.py : /api/admin/login, require_admin_auth decorator"))
story.append(body(
    "The Flask admin API uses <b>token-based auth</b> via <font face='Courier'>itsdangerous.URLSafeSerializer</font>. "
    "On POST to <font face='Courier'>/api/admin/login</font>, credentials are verified against the database. "
    "If valid, a token is generated: <font face='Courier'>serializer.dumps({user_id, username})</font>. "
    "All protected endpoints use <font face='Courier'>@require_admin_auth</font> which extracts the Bearer token "
    "from the Authorization header and validates it."
))

story.append(heading("Auth Flow Diagram", 2))
auth_items = [
    "User enters username + password",
    "-> POST /api/admin/login",
    "Server: hash_password(password) with SHA-256",
    "-> Query: SELECT * FROM users WHERE username=? AND password=?",
    "Match found: Generate token via URLSafeSerializer",
    "-> Return {token, user} to client",
    "Client stores token in localStorage",
    "-> All subsequent requests: Authorization: Bearer <token>",
    "Server: @require_admin_auth validates token on every request",
]
story.append(box_diagram(auth_items))
story.append(caption("Auth flow: Login generates a serialized token. All admin API calls require this token in the Authorization header."))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   4. DATABASE SCHEMA
# ══════════════════════════════════════════════
story.append(heading("4. Database Schema (SQLite - users.db)", 1))
story.append(fileref("app.py : init_db() | dragdrop_flask.py : ensure_dynamic_tables()"))
story.append(body(
    "The database has <b>8 tables</b>. The first 3 are created in app.py's init_db(). "
    "The remaining 5 are created/migrated by dragdrop_flask.py's ensure_dynamic_tables(). "
    "All tables share user_id and site_id as foreign keys for multi-user isolation."
))

# Table 1: users
story.append(heading("4.1 users", 2))
story.append(make_table(
    ["Column", "Type", "Constraint", "Purpose"],
    [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Unique user ID"],
        ["username", "TEXT", "UNIQUE NOT NULL", "Login username"],
        ["password", "TEXT", "NOT NULL", "SHA-256 hashed password"],
        ["created_at", "TEXT", "", "Registration timestamp"],
    ],
    col_widths=[70, 60, 150, 200]
))

# Table 2: cloned_sites
story.append(heading("4.2 cloned_sites", 2))
story.append(make_table(
    ["Column", "Type", "Purpose"],
    [
        ["id", "INTEGER PK", "Unique site ID"],
        ["user_id", "INTEGER FK->users.id", "Owner"],
        ["url", "TEXT", "Original website URL that was cloned"],
        ["html_content", "TEXT", "Full cloned HTML with bridge injected"],
        ["cloned_at", "TEXT", "Clone timestamp"],
    ],
    col_widths=[80, 120, 280]
))

# Table 3: conversion_blueprints
story.append(heading("4.3 conversion_blueprints", 2))
story.append(make_table(
    ["Column", "Type", "Purpose"],
    [
        ["id", "INTEGER PK", "Blueprint ID"],
        ["site_id", "INTEGER UNIQUE FK", "One blueprint per site"],
        ["user_id", "INTEGER FK", "Owner"],
        ["site_type", "TEXT", "Detected type: blog, ecommerce, portfolio, etc."],
        ["confidence", "REAL", "Detection confidence 0.0-1.0"],
        ["blueprint_json", "TEXT", "Full blueprint (models, fields, routes, bindings)"],
        ["generated_at", "TEXT", "Generation timestamp"],
        ["artifact_dir", "TEXT", "Path to generated scaffold files"],
    ],
    col_widths=[80, 100, 300]
))

story.append(PageBreak())

# Table 4: site_specs
story.append(heading("4.4 site_specs", 2))
story.append(make_table(
    ["Column", "Type", "Purpose"],
    [
        ["id", "INTEGER PK", "Spec ID"],
        ["site_id", "INTEGER UNIQUE FK", "One spec per site"],
        ["user_id", "INTEGER FK", "Owner"],
        ["spec_json", "TEXT", "Full SiteSpec: projectId, resources, bindings"],
        ["bindings_json", "TEXT", "Frontend data bindings array (selector -> API mapping)"],
        ["updated_at", "TEXT", "Last update timestamp"],
    ],
    col_widths=[80, 110, 290]
))

# Table 5: dynamic_models
story.append(heading("4.5 dynamic_models", 2))
story.append(make_table(
    ["Column", "Type", "Purpose"],
    [
        ["id", "INTEGER PK", "Model ID"],
        ["site_id", "INTEGER FK", "Parent site"],
        ["user_id", "INTEGER FK", "Owner"],
        ["model_name", "TEXT", "e.g., 'products', 'posts', 'courses'"],
        ["section_title", "TEXT", "Admin panel section label"],
        ["schema_json", "TEXT", "Field definitions: [{name, type, label, required}]"],
        ["display_order", "INTEGER", "UI ordering in admin sidebar"],
        ["updated_at", "TEXT", "Last update"],
    ],
    col_widths=[80, 80, 320]
))
story.append(body("UNIQUE constraint on (site_id, model_name) prevents duplicate models per site."))

# Table 6: dynamic_records
story.append(heading("4.6 dynamic_records", 2))
story.append(make_table(
    ["Column", "Type", "Purpose"],
    [
        ["id", "INTEGER PK", "Record ID"],
        ["site_id", "INTEGER FK", "Parent site"],
        ["user_id", "INTEGER FK", "Owner"],
        ["model_name", "TEXT", "References dynamic_models.model_name"],
        ["data_json", "TEXT", "Record payload as arbitrary JSON"],
        ["slug", "TEXT", "URL-friendly identifier (auto-generated)"],
        ["status", "TEXT DEFAULT 'draft'", "Workflow state: 'draft' or 'published'"],
        ["created_at / updated_at", "TEXT", "Timestamps"],
    ],
    col_widths=[100, 100, 280]
))

# Table 7: media_assets
story.append(heading("4.7 media_assets", 2))
story.append(make_table(
    ["Column", "Type", "Purpose"],
    [
        ["id", "INTEGER PK", "Asset ID"],
        ["site_id, user_id", "INTEGER FKs", "Owner references"],
        ["asset_key", "TEXT", "Unique identifier (content hash)"],
        ["source_kind", "TEXT", "'upload' or 'clone'"],
        ["media_type", "TEXT", "'image', 'svg', 'icon', 'video', 'audio'"],
        ["mime_type", "TEXT", "e.g., 'image/png'"],
        ["filename / original_name", "TEXT", "Local and original filenames"],
        ["file_url / original_url", "TEXT", "Serve path and source URL"],
        ["alt_text", "TEXT", "Image accessibility text"],
        ["width, height", "INTEGER", "Pixel dimensions"],
        ["hash", "TEXT", "SHA-1 content hash for deduplication"],
        ["status", "TEXT", "'ready', 'custom', 'deleted', 'archived'"],
        ["usage_json", "TEXT", "Array of usage contexts [{selector, section}]"],
        ["metadata_json", "TEXT", "Extra metadata as JSON"],
    ],
    col_widths=[110, 80, 290]
))
story.append(body("Indexed: idx_media_assets_site_user_asset_key on (site_id, user_id, asset_key)."))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   5. CLONER ENGINE
# ══════════════════════════════════════════════
story.append(heading("5. Module 1: Website Cloning Engine", 1))
story.append(fileref("cloner_engine.py (~74 KB, ~1800 lines)"))
story.append(body(
    "This module performs the actual website cloning. It crawls pages via BFS, downloads all assets "
    "(CSS, JS, images, fonts, video, audio), rewrites URLs to local paths, and packages everything into a bundle."
))

story.append(heading("5.1 Cloning Algorithm (6 Phases)", 2))

# Phase 1
story.append(heading("Phase 1: Initialization", 3))
story.append(fileref("cloner_engine.py : clone_site_bundle()"))
story.append(body(
    "Entry point is <font face='Courier'>clone_site_bundle(root_url, base_dir, max_pages, max_depth, progress_callback)</font>. "
    "It validates the URL, creates a temp staging directory at "
    "<font face='Courier'>project_assets/staged_clones/{domain}-{timestamp}-{hash}/</font>, "
    "and initializes a <font face='Courier'>requests.Session</font> with Chrome user-agent, "
    "connection pooling (12 workers), and keep-alive."
))

# Phase 2
story.append(heading("Phase 2: Page Discovery &amp; Crawl (BFS)", 3))
story.append(fileref("cloner_engine.py : crawl_site_pages(), collect_internal_navigation_urls()"))
story.append(body(
    "Uses <b>Breadth-First Search</b> with <font face='Courier'>collections.deque</font>. "
    "Steps: (a) Check <font face='Courier'>/robots.txt</font> and <font face='Courier'>/sitemap.xml</font> for seed URLs. "
    "(b) For each page, fetch HTML with 15s timeout. (c) Extract links from: <font face='Courier'>&lt;a href&gt;</font>, "
    "<font face='Courier'>data-href</font>, <font face='Courier'>onclick</font> handlers (3 regex patterns for window.location), "
    "<font face='Courier'>&lt;link rel='next/prev'&gt;</font>, <font face='Courier'>&lt;meta refresh&gt;</font>. "
    "(d) Deduplicate and enqueue if within max_pages and max_depth. "
    "Skips: non-HTML extensions, wp-admin, wp-json, feed, xmlrpc paths."
))

# Phase 3
story.append(heading("Phase 3: Asset Collection &amp; Parallel Prefetch", 3))
story.append(fileref("cloner_engine.py : collect_page_asset_requests(), prefetch_assets()"))
story.append(body(
    "For each crawled page, scans for assets via <font face='Courier'>iter_asset_attributes()</font> which checks: "
    "src, data-src, data-original, data-lazy-src, data-bg, poster, srcset, and any attribute containing "
    "'src|image|lazy|background|thumb'. Detects asset kind (css/js/image/font/video/audio/icon). "
    "Then <font face='Courier'>prefetch_assets()</font> downloads all assets in parallel using "
    "<font face='Courier'>ThreadPoolExecutor(max_workers=12)</font>."
))

# Phase 4
story.append(heading("Phase 4: HTML Rewriting", 3))
story.append(fileref("cloner_engine.py : rewrite_page_html()"))
story.append(body(
    "For each page: (a) Removes &lt;base&gt; tags, CSP meta tags, integrity attributes. "
    "(b) Rewrites ALL URLs in link href, img src, script src, inline styles url(), srcset, meta refresh. "
    "(c) Converts absolute URLs to relative local paths. "
    "(d) Creates placeholder pages for unreachable internal links. "
    "(e) Injects a <b>navigation bridge script</b> that handles dropdown toggles, data-href clicks, "
    "and keyboard navigation."
))

# Phase 5
story.append(heading("Phase 5: Asset Download &amp; CSS Rewriting", 3))
story.append(fileref("cloner_engine.py : clone_asset(), clone_binary_asset(), clone_stylesheet_asset()"))
story.append(body(
    "Binary assets (images, fonts, JS) are written to output with SHA-1 hash deduplication. "
    "CSS files get special treatment: <font face='Courier'>rewrite_css_text()</font> processes all "
    "<font face='Courier'>@import</font> and <font face='Courier'>url()</font> references, converting absolute URLs "
    "to relative paths. Hash index prevents writing the same file twice."
))

# Phase 6
story.append(heading("Phase 6: Bundling &amp; Export", 3))
story.append(fileref("cloner_engine.py : clone_site_bundle() (end section)"))
story.append(body(
    "Writes all rewritten pages to <font face='Courier'>site/</font> directory. Creates "
    "<font face='Courier'>manifest.json</font> with source_url, page/asset counts, route_map (source->local), "
    "and full diagnostics. Generates <font face='Courier'>clone-export.zip</font> archive. "
    "Returns result dict with entry_html, page_count, asset_count, bundle_dir, archive_path."
))

story.append(heading("5.2 Output File Structure", 2))
story.append(code(
    "project_assets/staged_clones/{domain}-{timestamp}-{hash}/<br/>"
    "&nbsp;&nbsp;site/<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;index.html&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Root page<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;pages/{slug}-{hash}.html&nbsp;&nbsp;# Deep-nested pages<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;assets/<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;css/{name}-{hash}.css<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;js/{name}-{hash}.js<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;images/{name}-{hash}.png<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;fonts/{name}-{hash}.woff2<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;video/{name}-{hash}.mp4<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;audio/{name}-{hash}.mp3<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;icons/{name}-{hash}.ico<br/>"
    "&nbsp;&nbsp;manifest.json<br/>"
    "&nbsp;&nbsp;clone-export.zip"
))
story.append(caption("Each asset name is slugified (max 24 chars) + 8-char SHA-1 hash for uniqueness."))

story.append(heading("5.3 Key Constants", 2))
story.append(make_table(
    ["Constant", "Value", "Purpose"],
    [
        ["PAGE_REQUEST_TIMEOUT", "15 seconds", "HTTP timeout for page fetches"],
        ["ASSET_REQUEST_TIMEOUT", "20 seconds", "HTTP timeout for asset fetches"],
        ["ASSET_PREFETCH_WORKERS", "12", "Parallel download threads"],
        ["DEFAULT_MAX_PAGES", "300 (deep) / 60 (fast)", "Crawl page limit"],
        ["DEFAULT_MAX_DEPTH", "8 (deep) / 4 (fast)", "Crawl depth limit"],
        ["TRACKING_QUERY_PREFIXES", "utm_, fbclid, gclid, mc_", "Stripped from URLs"],
    ],
    col_widths=[140, 130, 210]
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   6. SMART CONVERSION
# ══════════════════════════════════════════════
story.append(heading("6. Module 2: Smart Dynamic Conversion", 1))
story.append(fileref("smart_conversion.py (~69 KB, ~1700 lines)"))
story.append(body(
    "This module transforms a static cloned website into a <b>data-driven, editable CMS</b>. "
    "It analyzes the HTML, detects the website type, extracts content into structured models, "
    "generates a database schema, CRUD API routes, admin panel spec, and injects a JavaScript bridge "
    "for live data binding. <b>No AI/ML is used</b> - it is entirely heuristic-based (regex, pattern matching, keyword spotting)."
))

story.append(heading("6.1 Conversion Pipeline (12 Steps)", 2))
story.append(fileref("smart_conversion.py : build_conversion_blueprint()"))

pipeline_steps = [
    ("1. Parse HTML", "BeautifulSoup('html.parser') parses the cloned HTML into a DOM tree."),
    ("2. Detect Site Type", "detect_site_type() classifies into 8 types: ecommerce, restaurant, portfolio, blog, education, saas, real_estate, agency. Uses keyword frequency in visible text, form detection, price pattern matching."),
    ("3. Extract Sections", "extract_sections() identifies 24+ semantic sections (hero, banner, gallery, features, testimonials, footer, etc.) using tag names, class/id patterns, and ARIA roles. Each section gets a CSS selector and unique section_key."),
    ("4. Extract Media", "extract_media_assets() scans all &lt;img&gt;, &lt;video&gt;, &lt;audio&gt;, &lt;source&gt;, CSS url(), &lt;svg&gt; with usage tracking. Builds asset_key, media_type, section assignment."),
    ("5. Localize Media", "materialize_media_asset() downloads each asset with SHA-1 hashing. localize_clone_html() replaces original URLs with local paths in the HTML."),
    ("6. Extract Navigation", "extract_navigation() pulls up to 30 nav links with CSS selectors and section context."),
    ("7. Extract Content", "extract_text_blocks() pulls headings/paragraphs. extract_price_tokens() finds currency patterns. extract_forms() identifies form fields."),
    ("8. Infer Data Models", "extract_content_models() generates models based on site type. infer_fields_for_model() provides 25+ predefined schemas (products, courses, posts, etc.)."),
    ("9. Generate Seed Records", "extract_seed_records() creates initial records by mapping extracted text, prices, and media to model fields. build_record_from_source() handles the mapping."),
    ("10. Build API Routes", "build_backend_routes() generates CRUD endpoints for every model: GET list, GET by id, POST create, PATCH update, DELETE remove."),
    ("11. Build Admin Spec", "build_admin_sections() creates admin panel section definitions with columns, actions, and display config."),
    ("12. Calculate Confidence", "calculate_confidence_breakdown() scores extraction quality across 9 components: DOM depth, text coverage, section count, style extraction, layout quality, media recovery, link coverage, interactivity, type detection."),
]
for step, desc in pipeline_steps:
    story.append(heading(step, 3))
    story.append(body(desc))

story.append(PageBreak())

story.append(heading("6.2 Site Type Detection", 2))
story.append(fileref("smart_conversion.py : detect_site_type()"))
story.append(make_table(
    ["Site Type", "Detection Signals"],
    [
        ["ecommerce", "Keywords: cart, checkout, add to cart, price, buy. Price patterns. Product forms."],
        ["restaurant", "Keywords: menu, reservation, cuisine, chef, dine. Booking forms."],
        ["portfolio", "Keywords: portfolio, projects, works, gallery, showcase."],
        ["blog", "Keywords: blog, article, post, author, published, read more."],
        ["education", "Keywords: course, enroll, student, faculty, semester, campus."],
        ["saas", "Keywords: pricing, features, plans, subscribe, API, dashboard."],
        ["real_estate", "Keywords: property, listing, bedroom, sqft, agent, rent."],
        ["agency", "Keywords: services, clients, case study, team, solutions."],
    ],
    col_widths=[80, 400]
))

story.append(heading("6.3 Confidence Scoring (9 Components)", 2))
story.append(fileref("smart_conversion.py : calculate_confidence_breakdown()"))
story.append(make_table(
    ["Component", "What It Measures", "How"],
    [
        ["DOM Depth", "HTML structure complexity", "Counts nested elements, min threshold"],
        ["Text Coverage", "Extractable text volume", "Word count vs minimum threshold"],
        ["Sections", "Identifiable page regions", "Count of detected semantic sections"],
        ["Styles", "CSS extraction success", "Colors, fonts, logos found"],
        ["Layout", "Page structure quality", "Header/nav/main/footer presence"],
        ["Media Recovery", "Asset download success rate", "Downloaded / total assets ratio"],
        ["Links", "Navigation completeness", "Internal links found and resolved"],
        ["Interactivity", "Interactive elements found", "Forms, buttons, dropdowns count"],
        ["Type Detection", "Classification confidence", "Signal strength for detected type"],
    ],
    col_widths=[80, 140, 260]
))

story.append(heading("6.4 JavaScript Clone Bridge", 2))
story.append(fileref("smart_conversion.py : inject_clone_bridge()"))
story.append(body(
    "A &lt;script&gt; block is injected into the cloned HTML that runs on DOMContentLoaded. "
    "It fetches data from the API and updates the DOM live:"
))
story.append(bullet("<font face='Courier'>/api/public/{site_id}/site_sections</font> - Updates section titles, summaries, and media via CSS selectors"))
story.append(bullet("<font face='Courier'>/api/public/{site_id}/navigation_items</font> - Updates nav links"))
story.append(bullet("<font face='Courier'>/api/public/{site_id}/theme_styles</font> - Applies CSS custom properties (colors, fonts)"))
story.append(bullet("<font face='Courier'>/api/public/{site_id}/site_pages</font> - Updates page metadata"))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   7. MAIN APP ORCHESTRATOR
# ══════════════════════════════════════════════
story.append(heading("7. Module 3: Main Application Orchestrator", 1))
story.append(fileref("app.py (~99 KB, ~2400 lines)"))
story.append(body(
    "This is the <b>main Streamlit application</b> - the central orchestrator that ties all modules together. "
    "It provides the UI, manages user sessions, and coordinates the cloning, conversion, editing, and export workflows."
))

story.append(heading("7.1 Streamlit Menu Pages", 2))
story.append(make_table(
    ["Menu Item", "What It Does", "Modules Used"],
    [
        ["Clone New Site", "Enter URL, select mode (Deep/Fast), clone website, preview, save to DB", "cloner_engine"],
        ["Manage My Sites", "List sites, live HTML editor with preview, commit changes, download HTML", "None (direct DB)"],
        ["Smart Dynamic Conversion", "Select theme, generate blueprint, view architecture, build export", "smart_conversion, connected_export"],
        ["Drag & Drop Builder", "Visual page editor via GrapesJS in iframe", "dragdrop_flask (subprocess)"],
    ],
    col_widths=[110, 210, 160]
))

story.append(heading("7.2 Cloning Workflow (Clone New Site)", 2))
story.append(fileref("app.py : scrape_website(), build_clone_progress_callback()"))
story.append(body(
    "User selects Deep (300 pages, depth 8) or Fast (60 pages, depth 4) mode from CLONE_MODE_PRESETS. "
    "Calls <font face='Courier'>clone_site_bundle()</font> with a progress callback that updates a Streamlit progress bar "
    "through 4 phases: crawl (0-50%), prefetch (50-72%), rewrite (72-96%), archive (96-100%). "
    "Result is stored in session_state. User clicks 'SAVE TO PROJECT DATABASE' to persist."
))

story.append(heading("7.3 Conversion Workflow (Smart Dynamic Conversion)", 2))
story.append(fileref("app.py : generate_clone_runtime()"))
story.append(body(
    "The most complex workflow. Steps: "
    "(1) User selects a saved site and an admin theme (5 options: fabricator-current, saas-minimal, glass-premium, enterprise-command, creative-studio). "
    "(2) Calls <font face='Courier'>build_conversion_blueprint()</font>. "
    "(3) <font face='Courier'>load_saved_bundle_snapshot()</font> reads cloned pages/assets from disk. "
    "(4) <font face='Courier'>apply_bundle_runtime_context()</font> merges cloned data into blueprint: processes navigation items, "
    "merges media assets via <font face='Courier'>merge_clone_media_assets()</font> with identity-based deduplication, "
    "builds page records with SEO metadata. "
    "(5) <font face='Courier'>create_scaffold_files()</font> writes JSON/Python files. "
    "(6) Saves to DB: blueprint, spec, models, records, media. "
    "(7) Displays results in 4 tabs: Architecture, Admin App, API+Files, Pipeline."
))

story.append(heading("7.4 Media Asset Merge Algorithm", 2))
story.append(fileref("app.py : merge_clone_media_assets(), media_identity_tokens()"))
story.append(body(
    "Merges blueprint media (user uploads) with bundle media (cloned assets) using identity tokens. "
    "<font face='Courier'>media_identity_tokens()</font> generates tokens: [hash, asset_key, original_url, file_url, local_path]. "
    "For each bundle asset, checks if any token matches an existing asset. "
    "If match: merge metadata and usage info, preserve custom uploads. "
    "If no match: append as new asset. This ensures no duplicates while preserving all sources."
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   8. DRAG & DROP EDITOR
# ══════════════════════════════════════════════
story.append(heading("8. Module 4: Drag &amp; Drop Visual Editor", 1))
story.append(fileref("dragdrop_flask.py (~50 KB, ~1280 lines)"))
story.append(body(
    "A Flask application serving on port 5001 that provides: (a) A GrapesJS visual page editor, "
    "(b) Full CRUD admin API for dynamic content, (c) Media upload/management, (d) Clone preview serving. "
    "Embedded in the main Streamlit app as an iframe."
))

story.append(heading("8.1 GrapesJS Editor", 2))
story.append(fileref("dragdrop_flask.py : EDITOR_TEMPLATE, /editor/<site_id>"))
story.append(body(
    "The editor loads via <font face='Courier'>GET /editor/&lt;site_id&gt;</font>. "
    "HTML template embeds GrapesJS from CDN with Bootstrap 4 blocks plugin. "
    "Layout: 240px left sidebar (blocks + layers) | flexible canvas | 260px right sidebar (styles + traits). "
    "User can drag components, edit text, change styles, switch device preview (Desktop/Tablet/Mobile at 375x812). "
    "Save posts HTML+CSS to <font face='Courier'>POST /save_site/&lt;site_id&gt;</font> which stores to DB and updates the bundle archive."
))

story.append(heading("8.2 Editor Save Flow", 2))
story.append(code(
    "User clicks Save -> JS extracts editor.getHtml() + editor.getCss()<br/>"
    "-> POST /save_site/{site_id} with {html, css} body<br/>"
    "-> Server: UPDATE cloned_sites SET html_content = ? WHERE id = ?<br/>"
    "-> Server: update_saved_bundle_entry() writes to disk bundle<br/>"
    "-> Response: {ok: true}"
))

story.append(heading("8.3 Clone Preview Serving", 2))
story.append(fileref("dragdrop_flask.py : /clone/<site_id>/, /clone/<site_id>/<path>"))
story.append(body(
    "Serves the cloned website for live preview. <font face='Courier'>GET /clone/{site_id}/</font> returns the entry HTML "
    "(from bundle or DB). <font face='Courier'>GET /clone/{site_id}/{path}</font> serves specific assets or sub-pages "
    "from <font face='Courier'>project_assets/clone_packages/site_{id}/site/</font>."
))

story.append(heading("8.4 Dynamic Content API", 2))
story.append(make_table(
    ["Endpoint", "Method", "Purpose"],
    [
        ["/api/admin/login", "POST", "Authenticate admin user, return token"],
        ["/api/admin/me", "GET", "Get current user from token"],
        ["/api/projects", "GET", "List user's projects with record counts"],
        ["/api/projects/{id}/spec", "GET/PATCH", "Read/update SiteSpec and bindings"],
        ["/api/admin/{sid}/{resource}", "GET/POST", "List or create records for a resource"],
        ["/api/admin/{sid}/{resource}/{id}", "PATCH/DEL", "Update or delete a specific record"],
        ["/api/admin/{sid}/{resource}/{id}/publish", "PATCH", "Toggle draft/published status"],
        ["/api/admin/{sid}/media", "GET/POST", "List media or upload new files"],
        ["/api/admin/{sid}/media/{id}", "PATCH/DEL", "Edit metadata or delete media"],
        ["/api/public/{sid}/{resource}", "GET", "Public API - only published records (no auth)"],
        ["/dynamic-api/{sid}/meta", "GET", "Collection metadata for a site"],
        ["/dynamic-api/{sid}/{model}", "GET/POST", "Dynamic CRUD for any model"],
    ],
    col_widths=[180, 60, 240]
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   9. CONNECTED EXPORT
# ══════════════════════════════════════════════
story.append(heading("9. Module 5: Connected Export Packager", 1))
story.append(fileref("connected_export.py (~50 KB, ~1200 lines)"))
story.append(body(
    "Packages everything into a <b>self-contained, deployable system</b> - a ZIP file with its own "
    "Flask backend, SQLite database, admin panel, and cloned website. Runs standalone on port 5010."
))

story.append(heading("9.1 Export Algorithm", 2))
story.append(fileref("connected_export.py : build_connected_export()"))
export_steps = [
    "1. Validate prerequisites: admin build exists, clone saved, dynamic artifacts generated",
    "2. Load context: site metadata, user credentials, SiteSpec from DB",
    "3. Create directory structure: cloned_website/, admin_system/",
    "4. Copy cloned assets via copytree_clean() to cloned_website/",
    "5. sync_export_clone_html(): Strip preview paths, inject clone bridge into ALL HTML files",
    "6. Copy admin panel build (React dist) to admin_system/admin_panel/",
    "7. export_site_database(): Filter DB to user-owned records only, write to site.db",
    "8. write_backend_runtime(): Generate Flask app.py from 4 template segments",
    "9. write_export_docs(): Create README.md, export_manifest.json, startup scripts",
    "10. ZIP everything with shutil.make_archive()",
]
for step in export_steps:
    story.append(bullet(step))

story.append(heading("9.2 Export Package Structure", 2))
story.append(code(
    "{site_name}_connected_system/<br/>"
    "&nbsp;&nbsp;cloned_website/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Static HTML/CSS/JS/assets<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;index.html<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;assets/css/, js/, images/, fonts/<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;_fabricator/manifest.json<br/>"
    "&nbsp;&nbsp;admin_system/<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;admin_panel/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# React SPA build<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;backend/<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;app.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Generated Flask server<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;requirements.txt&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# flask, flask-cors, itsdangerous<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;start_backend.bat<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;database/site.db&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Standalone SQLite<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;generated_dynamic/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Schema, spec, media manifest JSONs<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;media/site_{id}/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Cloned media files<br/>"
    "&nbsp;&nbsp;README.md<br/>"
    "&nbsp;&nbsp;export_manifest.json<br/>"
    "&nbsp;&nbsp;start_connected_system.bat"
))

story.append(heading("9.3 Generated Backend Routes", 2))
story.append(body(
    "The generated <font face='Courier'>app.py</font> is built from 4 template segments "
    "(BACKEND_TEMPLATE_HEAD through BACKEND_TEMPLATE_TAIL_4). It includes: "
    "clone website serving at <font face='Courier'>/site/</font>, admin panel at <font face='Courier'>/admin/</font>, "
    "full CRUD API at <font face='Courier'>/api/admin/{sid}/{resource}</font>, "
    "media upload at <font face='Courier'>/api/admin/{sid}/media</font>, "
    "and public read API at <font face='Courier'>/api/public/{sid}/{resource}</font>. "
    "Auth uses the same URLSafeSerializer token system."
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   10. ADMIN PANEL FRONTEND
# ══════════════════════════════════════════════
story.append(heading("10. Module 6: Admin Panel Frontend", 1))
story.append(fileref("admin/src/ (React 19 + TypeScript + Vite)"))
story.append(body(
    "A modern React SPA that provides the CMS admin interface. Built with React 19, TypeScript 5.9, "
    "React Router 7 for routing, and Vite 8 for bundling. Served from <font face='Courier'>/admin/</font> path."
))

story.append(heading("10.1 Route Structure", 2))
story.append(make_table(
    ["Route", "Component", "Purpose"],
    [
        ["/admin/login", "LoginPage", "Username/password auth form"],
        ["/admin/site/:projectId", "AdminShell", "Main layout with sidebar + content area"],
        ["/admin/site/:projectId/ (index)", "ProjectDetailPage", "Overview: metrics, resources, diagnostics"],
        ["/admin/site/:projectId/resources/:key", "ResourceListPage", "Table of records with search/filter/publish"],
        ["/admin/site/:projectId/resources/:key/new", "RecordEditorPage", "Create new record (form from schema)"],
        ["/admin/site/:projectId/resources/:key/:id", "RecordEditorPage", "Edit existing record"],
        ["/admin/site/:projectId/media", "MediaPage", "Media library grid with preview/upload"],
    ],
    col_widths=[170, 100, 210]
))

story.append(heading("10.2 Component Architecture", 2))
story.append(bullet("<b>AdminShell</b> (admin/src/AdminShell.tsx): Two-panel layout. Left sidebar with project card, nav sections (Workspace, Content, Structure), resource counts. Top bar with theme/mode toggle. Fetches ProjectSpecResponse on mount."))
story.append(bullet("<b>LoginPage</b> (admin/src/LoginPage.tsx): Posts to /api/admin/login. Stores token + user in localStorage. Redirects to /site/:projectId."))
story.append(bullet("<b>ResourceListPage</b> (admin/src/ResourceListPage.tsx): Data table from schema. Search, status filter (all/draft/published). Row actions: Edit, Publish, Delete. Metric cards."))
story.append(bullet("<b>RecordEditorPage</b> (admin/src/RecordEditorPage.tsx): Dynamic form from SiteSpec field schema. Field types: text->textarea, number->input, boolean->select, media->URL+picker dropdown. Auto-slugifies title fields."))
story.append(bullet("<b>MediaPage</b> (admin/src/MediaPage.tsx): Grid view with type filtering (image/svg/icon/video/audio). Preview panel. Upload, replace, delete actions."))

story.append(heading("10.3 Theming System", 2))
story.append(fileref("admin/src/lib/themes.ts"))
story.append(body(
    "5 built-in themes with light/dark modes each. Applied via CSS custom properties "
    "(<font face='Courier'>--accent, --border, --text-h</font>) on HTML data-theme + data-mode attributes. "
    "Theme choice persisted per-project in localStorage."
))
story.append(make_table(
    ["Theme ID", "Name", "Default Mode"],
    [
        ["fabricator-current", "Neon Depth Premium CMS", "Dark"],
        ["saas-minimal", "Clean SaaS Dashboard", "Light"],
        ["glass-premium", "Commerce Operations", "Dark"],
        ["enterprise-command", "Executive Workspace", "Light"],
        ["creative-studio", "Campus Education", "Dark"],
    ],
    col_widths=[130, 170, 80]
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   11. END-TO-END USER JOURNEY
# ══════════════════════════════════════════════
story.append(heading("11. End-to-End User Journey Flow", 1))
story.append(body(
    "This section traces a complete user journey from registration to a deployed standalone system."
))

journey_items = [
    "STEP 1: User registers (app.py -> create_user -> INSERT users)",
    "-> Credentials stored",
    "STEP 2: User enters URL, clicks Clone (app.py -> clone_site_bundle)",
    "-> BFS crawl + parallel asset download",
    "STEP 3: Cloner returns bundle (cloner_engine.py -> manifest.json + site/)",
    "-> Preview shown in iframe via /staged-clone/",
    "STEP 4: User saves to DB (app.py -> save_site_to_db + persist_bundle_for_site)",
    "-> INSERT cloned_sites + copy to clone_packages/",
    "STEP 5: User runs Smart Conversion (app.py -> generate_clone_runtime)",
    "-> Calls build_conversion_blueprint + saves models/records/media",
    "STEP 6: Blueprint created (smart_conversion.py -> 12-step pipeline)",
    "-> Site type detected, models inferred, seed records created",
    "STEP 7: User edits in Drag & Drop Builder (dragdrop_flask.py -> GrapesJS)",
    "-> Visual editing, save to DB + bundle",
    "STEP 8: User manages content in Admin Panel (admin/src/ -> React SPA)",
    "-> CRUD records via API, upload media, publish content",
    "STEP 9: User builds Connected Export (connected_export.py)",
    "-> Packages clone + admin + DB + Flask into ZIP",
    "STEP 10: Deploy standalone system on any machine (port 5010)",
]
story.append(box_diagram(journey_items, width=490, row_height=28))
story.append(caption(
    "Complete user journey: Register -> Clone -> Save -> Convert -> Edit -> Manage -> Export -> Deploy. "
    "Each step shows the module responsible and the database/file operations performed."
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   12. API ENDPOINTS
# ══════════════════════════════════════════════
story.append(heading("12. Complete API Endpoints Reference", 1))
story.append(fileref("dragdrop_flask.py (development) | connected_export.py (generated production)"))

story.append(heading("12.1 Authentication Endpoints", 2))
story.append(make_table(
    ["Method", "Path", "Auth", "Request", "Response"],
    [
        ["POST", "/api/admin/login", "None", "{username, password}", "{token, user: {id, username}}"],
        ["GET", "/api/admin/me", "Bearer", "-", "{id, username}"],
    ],
    col_widths=[40, 110, 40, 120, 170]
))

story.append(heading("12.2 Project Endpoints", 2))
story.append(make_table(
    ["Method", "Path", "Purpose"],
    [
        ["GET", "/api/projects", "List all projects with record counts per resource"],
        ["GET", "/api/projects/{id}/spec", "Get full SiteSpec + bindings + resources"],
        ["PATCH", "/api/projects/{id}/spec", "Update SiteSpec bindings"],
    ],
    col_widths=[40, 170, 270]
))

story.append(heading("12.3 Content CRUD Endpoints", 2))
story.append(make_table(
    ["Method", "Path", "Purpose"],
    [
        ["GET", "/api/admin/{sid}/{resource}", "List all records (with ?q= search, ?status= filter)"],
        ["POST", "/api/admin/{sid}/{resource}", "Create new record with auto-slug"],
        ["PATCH", "/api/admin/{sid}/{resource}/{id}", "Update record fields + regenerate slug"],
        ["DELETE", "/api/admin/{sid}/{resource}/{id}", "Delete record permanently"],
        ["PATCH", "/api/admin/{sid}/{resource}/{id}/publish", "Toggle status: draft <-> published"],
    ],
    col_widths=[40, 195, 245]
))

story.append(heading("12.4 Media Endpoints", 2))
story.append(make_table(
    ["Method", "Path", "Purpose"],
    [
        ["GET", "/api/admin/{sid}/media", "List media (with ?q= search, ?type= filter)"],
        ["POST", "/api/admin/{sid}/media", "Upload file (multipart/form-data) with SHA-1 hash"],
        ["PATCH", "/api/admin/{sid}/media/{id}", "Update alt_text, section_key, or replace file"],
        ["DELETE", "/api/admin/{sid}/media/{id}", "Soft-delete (status='deleted')"],
        ["GET", "/media/{sid}/{filename}", "Serve media file directly"],
    ],
    col_widths=[40, 170, 270]
))

story.append(heading("12.5 Public Read-Only API", 2))
story.append(make_table(
    ["Method", "Path", "Auth", "Purpose"],
    [
        ["GET", "/api/public/{sid}/{resource}", "None", "Fetch published records only. Used by clone bridge JS."],
    ],
    col_widths=[40, 180, 40, 220]
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   13. KEY ALGORITHMS
# ══════════════════════════════════════════════
story.append(heading("13. Key Algorithms Deep Dive", 1))

story.append(heading("13.1 BFS Web Crawling", 2))
story.append(fileref("cloner_engine.py : crawl_site_pages()"))
story.append(body(
    "<b>Algorithm</b>: Breadth-First Search using <font face='Courier'>collections.deque</font>. "
    "Starts with root URL at depth 0. For each page: fetch HTML, extract all internal links, "
    "add unseen links to queue with depth+1. Also processes sitemaps from robots.txt as a secondary queue. "
    "Terminates when queue is empty OR page count reaches max_pages OR all pages at max_depth are processed."
))
story.append(code(
    "queue = deque([(root_url, 0)])&nbsp;&nbsp;# (url, depth)<br/>"
    "visited = set()<br/>"
    "while queue and len(pages) &lt; max_pages:<br/>"
    "&nbsp;&nbsp;url, depth = queue.popleft()<br/>"
    "&nbsp;&nbsp;if url in visited or depth &gt; max_depth: continue<br/>"
    "&nbsp;&nbsp;visited.add(url)<br/>"
    "&nbsp;&nbsp;html = fetch_html_page(url)<br/>"
    "&nbsp;&nbsp;links = collect_internal_navigation_urls(html, base_url)<br/>"
    "&nbsp;&nbsp;for link in links:<br/>"
    "&nbsp;&nbsp;&nbsp;&nbsp;if link not in visited: queue.append((link, depth + 1))"
))

story.append(heading("13.2 Asset Deduplication (SHA-1 Hash Index)", 2))
story.append(fileref("cloner_engine.py : clone_binary_asset(), clone_stylesheet_asset()"))
story.append(body(
    "Every downloaded asset is hashed with SHA-1. A hash index maps hash -> output path. "
    "Before writing a file, the engine checks if the hash already exists. If yes, the new reference "
    "points to the existing file (no duplicate write). The manifest marks these as 'deduplicated'. "
    "This significantly reduces bundle size when sites reuse the same image across pages."
))

story.append(heading("13.3 CSS URL Rewriting", 2))
story.append(fileref("cloner_engine.py : rewrite_css_text()"))
story.append(body(
    "Processes all <font face='Courier'>@import url(...)</font> and <font face='Courier'>url(...)</font> patterns in CSS. "
    "For each URL: resolves relative to CSS file location, checks if the asset was downloaded, "
    "and replaces with a relative path from the CSS output location to the asset output location. "
    "Uses <font face='Courier'>posixpath.relpath()</font> for correct relative path calculation."
))

story.append(heading("13.4 Media Identity Merge", 2))
story.append(fileref("app.py : merge_clone_media_assets(), media_identity_tokens()"))
story.append(body(
    "When merging blueprint media with bundle media, each asset generates identity tokens: "
    "[hash, asset_key, original_url, file_url, local_path]. Two assets are considered identical if ANY token matches. "
    "This handles the case where the same image has different URLs (CDN vs local) or different filenames."
))

story.append(heading("13.5 Site Type Classification (Heuristic)", 2))
story.append(fileref("smart_conversion.py : detect_site_type()"))
story.append(body(
    "Extracts visible text from HTML, converts to lowercase, counts keyword occurrences for each of 8 categories. "
    "Also checks: form presence (contact/order/reservation), price patterns (RS, PKR, $, numbers), "
    "domain name signals. The type with highest weighted score wins. Confidence = weighted score / max possible."
))

story.append(heading("13.6 Section Extraction (DOM Walking)", 2))
story.append(fileref("smart_conversion.py : extract_sections()"))
story.append(body(
    "Walks the DOM looking for semantic markers: <font face='Courier'>&lt;header&gt;, &lt;nav&gt;, &lt;main&gt;, "
    "&lt;footer&gt;, &lt;section&gt;, &lt;article&gt;</font>, plus divs with class/id containing keywords like "
    "'hero', 'banner', 'features', 'testimonials', 'gallery', 'pricing', 'contact'. "
    "24+ section types are recognized. Each gets a CSS selector via <font face='Courier'>build_element_selector()</font> "
    "and a unique section_key via <font face='Courier'>build_section_key()</font>."
))

story.append(heading("13.7 Parallel Asset Prefetching", 2))
story.append(fileref("cloner_engine.py : prefetch_assets()"))
story.append(body(
    "Uses <font face='Courier'>concurrent.futures.ThreadPoolExecutor(max_workers=12)</font> to download all discovered "
    "assets in parallel before the rewriting phase. Results cached in <font face='Courier'>prefetched_payloads</font> dict. "
    "During rewriting, assets are read from cache instead of making additional HTTP requests. "
    "This dramatically speeds up cloning of asset-heavy sites."
))

story.append(PageBreak())

# ══════════════════════════════════════════════
#   14. DIAGRAM EXPLANATIONS
# ══════════════════════════════════════════════
story.append(heading("14. Diagram Explanations", 1))
story.append(body(
    "This section provides plain-English explanations for every diagram in this document."
))

story.append(heading("14.1 Architecture Diagram (Section 1)", 2))
story.append(body(
    "<b>What it shows</b>: The system has 4 layers. The <b>User Browser</b> at the top connects to "
    "<b>Streamlit UI</b> (app.py on port 8501) which handles the main interface. Streamlit communicates with "
    "<b>Flask Backend</b> (dragdrop_flask.py on port 5001) which provides the visual editor and API. "
    "Both read/write to the <b>SQLite Database</b> (users.db with 8 tables). "
    "The connected_export module packages everything into a <b>Standalone Package</b> that runs independently on port 5010. "
    "Arrows show the direction of data flow between layers."
))

story.append(heading("14.2 Auth Flow Diagram (Section 3)", 2))
story.append(body(
    "<b>What it shows</b>: The complete login process step-by-step. "
    "User submits credentials -> Server hashes password with SHA-256 -> Queries database for match -> "
    "If found, generates a token using URLSafeSerializer -> Returns token to client -> "
    "Client stores in localStorage -> Every subsequent API call includes the token in the Authorization header -> "
    "Server validates token before processing any admin request. "
    "This is a <b>stateless token-based auth</b> system (no server-side sessions)."
))

story.append(heading("14.3 User Journey Diagram (Section 11)", 2))
story.append(body(
    "<b>What it shows</b>: The 10-step lifecycle of using the application from start to finish. "
    "Steps 1-2: Registration and URL input. "
    "Steps 3-4: The cloning engine crawls the website and saves results. "
    "Steps 5-6: Smart conversion analyzes the clone and generates database models. "
    "Steps 7-8: User refines using the visual editor and admin panel. "
    "Steps 9-10: Everything is packaged into a standalone ZIP and deployed. "
    "Each step lists the exact Python module and database operation involved, "
    "so a jury member can trace any step back to specific code."
))

story.append(heading("14.4 Module Dependency Table (Section 1)", 2))
story.append(body(
    "<b>What it shows</b>: Which module imports from which other module, and the specific functions used. "
    "app.py is the central hub that imports from all three utility modules. "
    "dragdrop_flask.py and connected_export.py both import from cloner_engine (for bundle management) "
    "and smart_conversion (for the clone bridge injection). "
    "No circular dependencies exist - the dependency graph is a clean DAG (Directed Acyclic Graph)."
))

story.append(heading("14.5 Database Schema Tables (Section 4)", 2))
story.append(body(
    "<b>What they show</b>: Every column in all 8 database tables with types, constraints, and purposes. "
    "The <b>users</b> table stores credentials. <b>cloned_sites</b> stores the raw cloned HTML. "
    "<b>conversion_blueprints</b> stores the analysis result. <b>site_specs</b> stores the frontend binding config. "
    "<b>dynamic_models</b> defines content schemas (like a CMS content type). "
    "<b>dynamic_records</b> holds actual content data (like CMS entries). "
    "<b>media_assets</b> tracks all images/videos/files. "
    "Foreign keys (user_id, site_id) ensure each user only accesses their own data."
))

story.append(heading("14.6 API Endpoints Tables (Section 12)", 2))
story.append(body(
    "<b>What they show</b>: Every HTTP endpoint in the system organized by category. "
    "Auth endpoints handle login/token. Project endpoints manage site metadata. "
    "Content CRUD endpoints allow creating, reading, updating, deleting records for any dynamic model. "
    "Media endpoints handle file uploads with deduplication. "
    "Public endpoints serve published-only data without authentication (used by the clone bridge script "
    "to update the cloned website's DOM with fresh content from the database)."
))

# ── Final page ──
story.append(PageBreak())
story.append(Spacer(1, 100))
story.append(Paragraph("End of Document", styles["DocTitle"]))
story.append(Spacer(1, 20))
story.append(body(
    "This document covers every module, algorithm, database table, API endpoint, and data flow in the "
    "AI Website Fabricator project. All file references point to exact source files in the project directory. "
    "For any jury question, cross-reference the relevant section number with the file path provided."
))

# ── Build ──
doc.build(story)
print(f"PDF generated: {output_path}")
