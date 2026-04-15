import streamlit as st
import streamlit.components.v1
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import sqlite3
import json
import os
import posixpath
import sys
import html
import hashlib
import time
import textwrap
import subprocess
import socket
from datetime import datetime
from smart_conversion import build_conversion_blueprint, build_site_spec, create_scaffold_files, inject_clone_bridge, build_media_summary
from cloner_engine import clone_site_bundle, persist_bundle_for_site, load_saved_bundle_entry, load_bundle_manifest, get_saved_bundle_site_dir, get_saved_bundle_dir, normalize_source_url
from connected_export import build_connected_export

# ============================================
# 0. PAGE CONFIG & STYLING (OPERATOR UI THEME)
# ============================================
st.set_page_config(
    page_title="AI Website Cloner & Admin Panel",
    page_icon="🛠️",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- Product-facing UI polish for operator surfaces ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Sora:wght@500;600;700;800&display=swap');

    :root {
        --bg: #f3f6fb;
        --bg-highlight: #e7eefc;
        --surface: rgba(255, 255, 255, 0.88);
        --surface-strong: rgba(255, 255, 255, 0.97);
        --surface-soft: rgba(241, 245, 252, 0.9);
        --sidebar-bg: rgba(10, 18, 33, 0.94);
        --sidebar-border: rgba(148, 163, 184, 0.15);
        --border: rgba(15, 23, 42, 0.1);
        --border-strong: rgba(37, 99, 235, 0.18);
        --text: #0f172a;
        --muted: #5a6880;
        --soft: #7c8aa1;
        --primary: #2563eb;
        --primary-strong: #1d4ed8;
        --primary-soft: #e8f0ff;
        --success: #0f9f6e;
        --success-soft: #e8fbf2;
        --warning-soft: #fff5dc;
        --danger-soft: #ffe7ea;
        --shadow-lg: 0 28px 60px rgba(15, 23, 42, 0.12);
        --shadow-md: 0 18px 34px rgba(15, 23, 42, 0.08);
        --radius-lg: 24px;
        --radius-md: 18px;
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .stApp {
        color: var(--text);
        background:
            radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 30%),
            radial-gradient(circle at top right, rgba(15, 159, 110, 0.10), transparent 24%),
            linear-gradient(180deg, #f8fbff 0%, var(--bg) 52%, #eef3fb 100%);
    }

    .block-container {
        max-width: 1320px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--text);
        font-family: 'Sora', sans-serif;
        letter-spacing: -0.02em;
    }

    p, li, label, span, div[data-testid="stCaptionContainer"] {
        color: var(--muted);
    }

    section[data-testid="stSidebar"] {
        background:
            radial-gradient(circle at top, rgba(59, 130, 246, 0.16), transparent 28%),
            linear-gradient(180deg, rgba(10, 18, 33, 0.98) 0%, rgba(9, 15, 26, 0.96) 100%);
        border-right: 1px solid var(--sidebar-border);
        box-shadow: 18px 0 40px rgba(2, 6, 23, 0.2);
    }

    section[data-testid="stSidebar"] * {
        color: #dbe7f6;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #eff6ff !important;
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
        box-shadow: none !important;
    }

    .brand-header {
        margin-bottom: 1.4rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.14);
    }

    .brand-title {
        font-family: 'Sora', sans-serif;
        font-size: 1.85rem;
        font-weight: 800;
        color: #f8fbff;
        letter-spacing: -0.04em;
    }

    .brand-title .brand-highlight {
        color: #60a5fa;
    }

    .sidebar-kicker {
        margin: 0 0 0.55rem 0;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #7dd3fc;
    }

    .user-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 18px;
        padding: 0.95rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.9rem;
        margin-bottom: 1.6rem;
        box-shadow: 0 16px 30px rgba(2, 6, 23, 0.18);
    }

    .user-avatar {
        width: 46px;
        height: 46px;
        border-radius: 14px;
        background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #f8fbff;
        font-size: 1.05rem;
        font-weight: 800;
        box-shadow: 0 12px 24px rgba(37, 99, 235, 0.24);
    }

    .user-info h4 {
        margin: 0;
        font-size: 0.98rem;
        color: #f8fbff;
        font-weight: 700;
    }

    .user-info span {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #93c5fd;
    }

    [data-testid="stRadio"] > div {
        gap: 0.55rem;
    }

    div[role="radiogroup"] label[data-baseweb="radio"] {
        border-radius: 14px !important;
        border: 1px solid rgba(148, 163, 184, 0.14) !important;
        background: rgba(255, 255, 255, 0.7) !important;
        padding: 0.75rem 0.9rem !important;
        transition: all 0.18s ease;
    }

    div[role="radiogroup"] label[data-baseweb="radio"]:hover {
        border-color: rgba(37, 99, 235, 0.22) !important;
        background: rgba(255, 255, 255, 0.92) !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid transparent !important;
        color: #c4d2e6 !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"]:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(96, 165, 250, 0.24) !important;
    }

    div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] {
        background: linear-gradient(180deg, rgba(232, 240, 255, 0.98) 0%, rgba(244, 248, 255, 0.98) 100%) !important;
        border-color: rgba(37, 99, 235, 0.22) !important;
        box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.04);
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] {
        background: linear-gradient(90deg, rgba(37, 99, 235, 0.22) 0%, rgba(37, 99, 235, 0.06) 100%) !important;
        border-color: rgba(96, 165, 250, 0.34) !important;
        color: #f8fbff !important;
    }

    div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        width: 100%;
        min-height: 3.15rem;
        border-radius: 16px !important;
        font-family: 'Sora', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
        transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease !important;
    }

    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%) !important;
        color: #f8fbff !important;
        border: 1px solid rgba(37, 99, 235, 0.18) !important;
        box-shadow: 0 16px 28px rgba(37, 99, 235, 0.2) !important;
    }

    .stButton > button[kind="secondary"],
    .stDownloadButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.92) !important;
        color: var(--text) !important;
        border: 1px solid rgba(15, 23, 42, 0.12) !important;
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.05) !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.14) !important;
    }

    .stButton > button:disabled,
    .stDownloadButton > button:disabled {
        opacity: 0.55 !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] > div {
        background: rgba(255, 255, 255, 0.96) !important;
        color: var(--text) !important;
        border: 1px solid rgba(148, 163, 184, 0.26) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input,
    .stTextArea textarea {
        padding: 0.82rem 0.95rem !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="base-input"] > div:focus-within {
        border-color: rgba(37, 99, 235, 0.34) !important;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.08) !important;
    }

    .stTextArea textarea {
        font-family: 'JetBrains Mono', monospace !important;
        line-height: 1.5;
    }

    [data-testid="stMetric"] {
        background: var(--surface-strong);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1rem 1.1rem;
        box-shadow: var(--shadow-md);
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {
        color: var(--text) !important;
    }

    [data-testid="stMetricDelta"] {
        color: var(--muted) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.45rem;
        background: rgba(255, 255, 255, 0.76);
        padding: 0.35rem;
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 18px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 14px;
        min-height: 44px;
        padding: 0.55rem 0.95rem;
        color: var(--muted);
        font-weight: 700;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.95) !important;
        color: var(--text) !important;
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
    }

    .streamlit-expanderHeader,
    [data-testid="stExpander"] {
        background: var(--surface-strong);
        border-radius: 18px;
    }

    div[data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.15);
        background: var(--surface-strong);
        color: var(--text);
        box-shadow: var(--shadow-md);
    }

    [data-testid="stCodeBlock"],
    .stCodeBlock,
    pre {
        border-radius: 18px !important;
        border: 1px solid rgba(148, 163, 184, 0.18) !important;
    }

    iframe {
        border-radius: 22px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background: #ffffff;
        box-shadow: var(--shadow-md);
    }

    .loader-container,
    .page-hero,
    .surface-note,
    .result-banner {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
    }

    .loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.55rem;
        margin: 1rem 0 1.5rem;
        padding: 1.5rem 1.25rem;
    }

    .neon-ring {
        width: 62px;
        height: 62px;
        border: 5px solid rgba(37, 99, 235, 0.12);
        border-top: 5px solid #2563eb;
        border-right: 5px solid #38bdf8;
        border-radius: 50%;
        animation: spin 0.9s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loader-text {
        color: var(--text);
        font-family: 'Sora', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
    }

    .loader-subtext {
        color: var(--muted);
        font-size: 0.92rem;
    }

    .page-hero {
        padding: 1.6rem 1.6rem 1.4rem;
        margin-bottom: 1.1rem;
    }

    .page-eyebrow {
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--primary);
        margin-bottom: 0.6rem;
    }

    .page-title {
        margin: 0;
        font-size: 2.25rem;
        line-height: 1.05;
        color: var(--text);
    }

    .page-description {
        margin: 0.75rem 0 0;
        font-size: 1rem;
        line-height: 1.65;
        color: var(--muted);
        max-width: 900px;
    }

    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1rem;
    }

    .badge-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.48rem 0.82rem;
        border-radius: 999px;
        background: var(--primary-soft);
        border: 1px solid rgba(37, 99, 235, 0.12);
        color: var(--primary-strong);
        font-size: 0.8rem;
        font-weight: 700;
    }

    .badge-chip.success {
        background: var(--success-soft);
        color: var(--success);
        border-color: rgba(15, 159, 110, 0.16);
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 0.85rem;
        margin: 0 0 1.2rem;
    }

    .metric-tile {
        padding: 1rem 1.05rem;
        border-radius: 18px;
        border: 1px solid var(--border);
        background: var(--surface-strong);
        box-shadow: var(--shadow-md);
    }

    .metric-label {
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--soft);
        margin-bottom: 0.45rem;
    }

    .metric-value {
        font-family: 'Sora', sans-serif;
        font-size: 1.22rem;
        font-weight: 700;
        color: var(--text);
    }

    .metric-note {
        margin-top: 0.4rem;
        font-size: 0.88rem;
        line-height: 1.5;
        color: var(--muted);
    }

    .surface-note {
        padding: 1rem 1.1rem;
        margin: 0.55rem 0 1rem;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(246, 249, 255, 0.96));
    }

    .surface-note strong {
        display: block;
        color: var(--text);
        margin-bottom: 0.2rem;
        font-weight: 700;
    }

    .result-banner {
        padding: 1.15rem 1.2rem;
        margin: 0.8rem 0 1rem;
        background: linear-gradient(180deg, rgba(232, 251, 242, 0.98), rgba(255, 255, 255, 0.96));
        border-color: rgba(15, 159, 110, 0.18);
    }

    .result-banner h3 {
        margin: 0;
        font-size: 1.2rem;
        color: var(--text);
    }

    .result-banner p {
        margin: 0.4rem 0 0;
        color: var(--muted);
    }

    .progress-banner,
    .progress-detail {
        border-radius: 18px;
        border: 1px solid var(--border);
        background: var(--surface-strong);
        box-shadow: var(--shadow-md);
    }

    .progress-banner {
        padding: 0.95rem 1rem;
        margin-bottom: 0.55rem;
    }

    .progress-banner strong {
        display: block;
        color: var(--text);
        font-size: 1rem;
        font-family: 'Sora', sans-serif;
    }

    .progress-banner span {
        display: inline-flex;
        margin-top: 0.45rem;
        padding: 0.3rem 0.62rem;
        border-radius: 999px;
        background: var(--primary-soft);
        color: var(--primary-strong);
        font-size: 0.76rem;
        font-weight: 700;
    }

    .progress-detail {
        padding: 0.8rem 1rem;
        color: var(--muted);
        line-height: 1.55;
        margin-bottom: 0.75rem;
    }

    .subtle-divider {
        margin: 0.4rem 0 1rem;
        border-top: 1px solid rgba(148, 163, 184, 0.18);
    }

    .mini-heading {
        margin: 0.15rem 0 0.6rem;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--soft);
    }

    .auth-shell {
        max-width: 920px;
        margin: 0 auto 1.4rem;
        text-align: center;
    }

    .auth-shell .page-title {
        font-size: 2.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# UI HELPERS
# ============================================
def render_page_hero(eyebrow: str, title: str, description: str, badges=None):
    badges = badges or []
    badge_html = "".join(
        f'<span class="badge-chip{" success" if badge.get("tone") == "success" else ""}">{html.escape(str(badge.get("label", "")))}</span>'
        for badge in badges
        if badge.get("label")
    )
    st.markdown(
        f"""
        <section class="page-hero">
            <div class="page-eyebrow">{html.escape(eyebrow)}</div>
            <h1 class="page-title">{html.escape(title)}</h1>
            <p class="page-description">{html.escape(description)}</p>
            {f'<div class="badge-row">{badge_html}</div>' if badge_html else ''}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(items):
    card_html = "".join(
        f"""
        <div class="metric-tile">
            <div class="metric-label">{html.escape(str(item.get("label", "")))}</div>
            <div class="metric-value">{html.escape(str(item.get("value", "")))}</div>
            <div class="metric-note">{html.escape(str(item.get("note", "")))}</div>
        </div>
        """
        for item in items
    )
    st.markdown(f'<div class="metric-grid">{card_html}</div>', unsafe_allow_html=True)


def render_surface_note(title: str, description: str):
    st.markdown(
        f"""
        <div class="surface-note">
            <strong>{html.escape(title)}</strong>
            <span>{html.escape(description)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_banner(title: str, description: str):
    st.markdown(
        f"""
        <div class="result-banner">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_admin_panel_url(site_id: int) -> str:
    return f"http://127.0.0.1:{FLASK_PORT}/admin/site/{site_id}/login"


def build_admin_access_state(site_id: int, user_id: int, site_spec=None):
    resolved_site_spec = site_spec
    if resolved_site_spec is None:
        stored_bundle = get_site_spec(site_id, user_id)
        resolved_site_spec = (stored_bundle or {}).get("spec") if stored_bundle else None

    generated = bool(resolved_site_spec)
    return {
        "site_id": site_id,
        "generated": generated,
        "url": get_admin_panel_url(site_id),
        "site_spec": resolved_site_spec,
        "status_label": "Admin ready" if generated else "Admin not generated yet",
        "status_note": (
            "Open the site-specific admin login for this project."
            if generated
            else "Generate the admin panel for this project to unlock the separate CMS."
        ),
    }


def render_admin_access_panel(admin_state, key_prefix: str, empty_message: str, title: str = "Admin Panel Access"):
    if admin_state["generated"]:
        render_result_banner(
            title,
            "The separate admin website is ready for this project. Use the button below to open the correct site-specific admin login.",
        )
        action_col1, action_col2 = st.columns([1.1, 1])
        with action_col1:
            st.link_button(
                "Open Admin Panel",
                admin_state["url"],
                use_container_width=True,
                type="primary",
            )
        with action_col2:
            st.text_input(
                "Admin URL",
                value=admin_state["url"],
                key=f"{key_prefix}_admin_url",
                disabled=True,
            )
    else:
        render_surface_note("Admin not generated yet", empty_message)


# ============================================
# 1. DATABASE & AUTHENTICATION SETUP
# ============================================
DB_NAME = 'users.db'
FLASK_PORT = 5001

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS cloned_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT,
            html_content TEXT,
            cloned_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversion_blueprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER UNIQUE,
            user_id INTEGER,
            site_type TEXT,
            confidence REAL,
            blueprint_json TEXT,
            generated_at TEXT,
            artifact_dir TEXT,
            FOREIGN KEY(site_id) REFERENCES cloned_sites(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS site_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER UNIQUE,
            user_id INTEGER,
            spec_json TEXT,
            bindings_json TEXT,
            updated_at TEXT,
            FOREIGN KEY(site_id) REFERENCES cloned_sites(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dynamic_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            user_id INTEGER,
            model_name TEXT,
            section_title TEXT,
            schema_json TEXT,
            display_order INTEGER DEFAULT 0,
            updated_at TEXT,
            UNIQUE(site_id, model_name),
            FOREIGN KEY(site_id) REFERENCES cloned_sites(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dynamic_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            user_id INTEGER,
            model_name TEXT,
            data_json TEXT,
            slug TEXT,
            status TEXT DEFAULT 'draft',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(site_id) REFERENCES cloned_sites(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
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
            updated_at TEXT,
            FOREIGN KEY(site_id) REFERENCES cloned_sites(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    existing_columns = {row[1] for row in c.execute("PRAGMA table_info(dynamic_records)").fetchall()}
    if 'slug' not in existing_columns:
        c.execute("ALTER TABLE dynamic_records ADD COLUMN slug TEXT")
    if 'status' not in existing_columns:
        c.execute("ALTER TABLE dynamic_records ADD COLUMN status TEXT DEFAULT 'draft'")
    media_columns = {row[1] for row in c.execute("PRAGMA table_info(media_assets)").fetchall()}
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
            c.execute(sql)
    c.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_media_assets_site_user_asset_key ON media_assets(site_id, user_id, asset_key)"
    )
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)', 
                  (username, hash_password(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    data = c.fetchone()
    conn.close()
    return data

init_db()

def flask_running(port=FLASK_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    return result == 0

def ensure_flask_running():
    if flask_running():
        return

    subprocess.Popen(
        [sys.executable, "dragdrop_flask.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)

# ============================================
# 2. DATA MANAGEMENT FUNCTIONS
# ============================================

def save_site_to_db(user_id, url, html):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO cloned_sites (user_id, url, html_content, cloned_at) VALUES (?, ?, ?, ?)', 
              (user_id, url, html, timestamp))
    site_id = c.lastrowid
    conn.commit()
    conn.close()
    return site_id

def get_user_sites(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, url, cloned_at FROM cloned_sites WHERE user_id = ? ORDER BY id DESC', (user_id,))
    data = c.fetchall()
    conn.close()
    return data

def get_html_by_id(site_id, user_id, preview_bundle=False):
    if preview_bundle:
        bundle_html = load_saved_bundle_entry(site_id, base_dir=os.getcwd(), preview=True)
        if bundle_html:
            return bundle_html
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT html_content FROM cloned_sites WHERE id = ? AND user_id = ?', (site_id, user_id))
    result = c.fetchone()
    conn.close()
    text = result[0] if result else ""
    if text and len(text) > 50:
        replacements = text.count("\ufffd")
        if replacements / len(text) > 0.03:
            return ""
    return text

def update_html_in_db(site_id, user_id, new_html, ensure_bridge=True):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    html_to_store = inject_clone_bridge(new_html, site_id) if ensure_bridge else new_html
    c.execute('UPDATE cloned_sites SET html_content = ? WHERE id = ? AND user_id = ?', (html_to_store, site_id, user_id))
    conn.commit()
    conn.close()

def _safe_read_html(file_path):
    """Read a file as UTF-8 text. Returns empty string if binary or garbled."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except (UnicodeDecodeError, ValueError, OSError):
        return ""
    if not text or len(text) < 10:
        return text
    replacements = text.count("\ufffd")
    if replacements / max(len(text), 1) > 0.03:
        return ""
    printable = sum(1 for ch in text[:500] if ch.isprintable() or ch in "\n\r\t")
    if printable / min(len(text), 500) < 0.5:
        return ""
    return text


# --- Bundle file browser helpers ---
TEXT_EXTENSIONS = {
    ".html", ".htm", ".css", ".js", ".json", ".xml", ".svg", ".txt",
    ".md", ".csv", ".tsv", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".map", ".mjs", ".cjs", ".jsx", ".tsx", ".ts",
}

def _is_text_file(file_path):
    """Check if a file is likely a text file by extension."""
    _, ext = os.path.splitext(file_path.lower())
    return ext in TEXT_EXTENSIONS

def list_bundle_files(site_id, base_dir=None):
    """List all files in a bundle's site/ directory with their relative paths.
    Returns list of dicts: [{"rel_path": "index.html", "abs_path": "...", "is_text": True, "size": 1234}]
    """
    site_dir = get_saved_bundle_site_dir(site_id, base_dir)
    if not os.path.isdir(site_dir):
        return []
    files = []
    for root, _dirs, filenames in os.walk(site_dir):
        for fname in sorted(filenames):
            abs_path = os.path.join(root, fname)
            rel_path = os.path.relpath(abs_path, site_dir).replace("\\", "/")
            try:
                size = os.path.getsize(abs_path)
            except OSError:
                size = 0
            files.append({
                "rel_path": rel_path,
                "abs_path": abs_path,
                "is_text": _is_text_file(fname),
                "size": size,
            })
    # Sort: index.html first, then other HTML, then CSS, then JS, then rest
    def sort_key(f):
        rp = f["rel_path"]
        if rp == "index.html":
            return (0, rp)
        _, ext = os.path.splitext(rp.lower())
        order = {".html": 1, ".htm": 1, ".css": 2, ".js": 3, ".json": 4}.get(ext, 9)
        return (order, rp)
    files.sort(key=sort_key)
    return files

def load_bundle_file_raw(site_id, rel_path, base_dir=None):
    """Load a specific file from the bundle as raw text. Returns (content, error_msg)."""
    site_dir = get_saved_bundle_site_dir(site_id, base_dir)
    abs_path = os.path.normpath(os.path.join(site_dir, rel_path))
    # Security: ensure path stays within site_dir
    if not abs_path.startswith(os.path.normpath(site_dir)):
        return "", "Access denied: path outside bundle directory."
    if not os.path.exists(abs_path):
        return "", f"File not found: {rel_path}"
    if not _is_text_file(abs_path):
        size_kb = os.path.getsize(abs_path) / 1024
        return "", f"This file ({rel_path}, {size_kb:.0f} KB) is a binary asset and cannot be edited here. Binary files like images, fonts, and compiled assets are served directly by the preview."
    content = _safe_read_html(abs_path)
    if not content and os.path.getsize(abs_path) > 0:
        return "", f"This file could not be read as text. It may contain unsupported encoding or binary content."
    return content, ""


def load_saved_bundle_snapshot(site_id, base_dir=None):
    manifest = load_bundle_manifest(site_id, base_dir) or {}
    site_dir = get_saved_bundle_site_dir(site_id, base_dir)
    snapshot = {
        "manifest": manifest,
        "site_dir": site_dir,
        "pages": [],
        "entry_html": "",
    }

    if not manifest or not os.path.isdir(site_dir):
        return snapshot

    entry_path = (manifest.get("route_map") or {}).get(manifest.get("source_url"), "index.html")
    entry_file = os.path.join(site_dir, *entry_path.split("/"))
    if os.path.isfile(entry_file):
        snapshot["entry_html"] = _safe_read_html(entry_file)

    for page in manifest.get("pages", []):
        local_path = page.get("local_path") or ""
        if not local_path or page.get("title") == "Placeholder route":
            continue
        file_path = os.path.join(site_dir, *local_path.split("/"))
        if not os.path.isfile(file_path):
            continue
        html = _safe_read_html(file_path)
        if not html:
            continue
        snapshot["pages"].append(
            {
                "source_url": page.get("source_url", ""),
                "local_path": local_path,
                "title": page.get("title", ""),
                "html": html,
            }
        )

    return snapshot


def build_clone_route_from_local_path(local_path):
    normalized = str(local_path or "").replace("\\", "/").lstrip("/")
    if not normalized or normalized == "index.html":
        return "/"
    if normalized.endswith("/index.html"):
        route = "/" + normalized[: -len("index.html")]
        return route if route.endswith("/") else route + "/"
    return "/" + normalized


def resolve_bundle_asset_reference(page_local_path, candidate):
    raw = str(candidate or "").strip()
    if not raw or raw.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
        return ""
    if raw.startswith(("http://", "https://", "/clone/", "/site/")):
        return raw
    normalized = raw.split("#", 1)[0].split("?", 1)[0].strip()
    if not normalized:
        return ""
    if normalized.startswith("/"):
        return normalized.lstrip("/")
    base_dir = posixpath.dirname(page_local_path or "") or "."
    resolved = posixpath.normpath(posixpath.join(base_dir, normalized)).replace("\\", "/")
    if resolved.startswith("../"):
        return ""
    return resolved.lstrip("./")


def extract_bundle_page_preview(site_id, page_local_path, page_html):
    soup = BeautifulSoup(page_html, "html.parser")
    preview_sources = []

    og_image = soup.find("meta", attrs={"property": "og:image"})
    if og_image and og_image.get("content"):
        preview_sources.append(og_image.get("content"))

    for tag_name, attribute in [("img", "src"), ("video", "poster"), ("source", "src"), ("source", "srcset")]:
        tag = soup.find(tag_name)
        if not tag:
            continue
        value = tag.get(attribute)
        if value:
            preview_sources.append(value)

    for candidate in preview_sources:
        resolved = resolve_bundle_asset_reference(page_local_path, candidate)
        if not resolved:
            continue
        if resolved.startswith(("http://", "https://", "/clone/", "/site/")):
            return resolved
        return f"/clone/{site_id}/{resolved}"

    return ""


def guess_bundle_media_type(asset):
    source_hint = f"{asset.get('source_url', '')} {asset.get('local_path', '')}".lower()
    content_type = (asset.get("content_type") or "").lower()
    kind = (asset.get("kind") or "").lower()
    if "svg" in content_type or source_hint.endswith(".svg"):
        return "svg"
    if kind == "icon" or source_hint.endswith(".ico") or "favicon" in source_hint:
        return "icon"
    if kind == "video":
        return "video"
    if kind == "audio":
        return "audio"
    return "image"


def build_bundle_media_assets(site_id, bundle_snapshot):
    manifest = bundle_snapshot.get("manifest") or {}
    bundle_assets = []
    for asset in manifest.get("assets", []):
        if asset.get("kind") not in {"image", "icon", "video", "audio"}:
            continue
        local_path = asset.get("local_path") or ""
        if not local_path:
            continue
        source_url = asset.get("source_url", "")
        file_name = os.path.basename(local_path) or os.path.basename(urlparse(source_url).path) or "asset"
        media_type = guess_bundle_media_type(asset)
        bundle_assets.append(
            {
                "asset_key": asset.get("hash") or hashlib.sha1(
                    f"bundle:{site_id}:{source_url}:{local_path}".encode("utf-8")
                ).hexdigest(),
                "source_kind": "clone",
                "media_type": media_type,
                "mime_type": asset.get("content_type", ""),
                "filename": file_name,
                "original_name": os.path.basename(urlparse(source_url).path) or file_name,
                "file_url": f"/clone/{site_id}/{local_path.lstrip('/')}",
                "original_url": source_url,
                "alt_text": "",
                "width": None,
                "height": None,
                "hash": asset.get("hash", ""),
                "status": "ready" if asset.get("status") == "downloaded" else asset.get("status", "ready"),
                "download_status": asset.get("status", "downloaded"),
                "section_key": "",
                "usage": [],
                "metadata": {
                    "bundleLocalPath": local_path,
                    "bundleKind": asset.get("kind", ""),
                    "contentType": asset.get("content_type", ""),
                    "size": asset.get("size", 0),
                    "bundleStatus": asset.get("status", ""),
                },
                "local_path": local_path,
            }
        )
    return bundle_assets


def media_identity_tokens(asset):
    tokens = []
    original_url = normalize_source_url(asset.get("original_url", "")) or asset.get("original_url", "")
    for value in [
        asset.get("hash", ""),
        asset.get("asset_key", ""),
        original_url,
        asset.get("file_url", ""),
        asset.get("local_path", ""),
    ]:
        cleaned = str(value or "").strip()
        if cleaned:
            tokens.append(cleaned)
    return tokens


def merge_clone_media_assets(primary_assets, bundle_assets):
    merged = [json.loads(json.dumps(asset)) for asset in (primary_assets or [])]
    index = {}

    def register(asset_index):
        for token in media_identity_tokens(merged[asset_index]):
            index.setdefault(token, asset_index)

    for asset_index in range(len(merged)):
        register(asset_index)

    for bundle_asset in bundle_assets:
        bundle_copy = json.loads(json.dumps(bundle_asset))
        match_index = None
        for token in media_identity_tokens(bundle_copy):
            if token in index:
                match_index = index[token]
                break

        if match_index is None:
            merged.append(bundle_copy)
            register(len(merged) - 1)
            continue

        target = merged[match_index]
        if (
            bundle_copy.get("file_url")
            and (not target.get("file_url") or target.get("download_status") in {"external_reference", "pending"})
        ):
            target["file_url"] = bundle_copy["file_url"]
        if bundle_copy.get("local_path") and not target.get("local_path"):
            target["local_path"] = bundle_copy["local_path"]
        if bundle_copy.get("hash") and not target.get("hash"):
            target["hash"] = bundle_copy["hash"]
        if bundle_copy.get("mime_type") and not target.get("mime_type"):
            target["mime_type"] = bundle_copy["mime_type"]
        if bundle_copy.get("media_type") in {"svg", "icon", "video", "audio"} and target.get("media_type") == "image":
            target["media_type"] = bundle_copy["media_type"]
        if bundle_copy.get("status") == "ready":
            target["status"] = "ready"
        if bundle_copy.get("download_status") == "downloaded":
            target["download_status"] = "downloaded"
        if bundle_copy.get("section_key") and not target.get("section_key"):
            target["section_key"] = bundle_copy["section_key"]
        target_metadata = target.setdefault("metadata", {})
        target_metadata.update(bundle_copy.get("metadata", {}))

        usage = target.setdefault("usage", [])
        usage_signatures = {json.dumps(item, sort_keys=True) for item in usage}
        for usage_item in bundle_copy.get("usage", []):
            signature = json.dumps(usage_item, sort_keys=True)
            if signature not in usage_signatures:
                usage_signatures.add(signature)
                usage.append(usage_item)

        register(match_index)

    return merged


def build_bundle_site_page_records(site_id, bundle_snapshot):
    records = []
    seen_routes = set()

    for page in bundle_snapshot.get("pages", []):
        clone_path = build_clone_route_from_local_path(page.get("local_path", ""))
        if clone_path in seen_routes:
            continue
        seen_routes.add(clone_path)

        page_html = page.get("html", "")
        soup = BeautifulSoup(page_html, "html.parser")
        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_description = meta_tag.get("content")

        slug = clone_path.strip("/").replace("/", "-").replace(".html", "") or "home"
        title = page.get("title") or clone_path or page.get("source_url", "")
        records.append(
            {
                "title": title,
                "slug": slug,
                "path": clone_path,
                "clone_path": clone_path,
                "source_url": page.get("source_url", ""),
                "meta_title": title,
                "meta_description": (meta_description or title)[:220],
                "hero_media_url": extract_bundle_page_preview(site_id, page.get("local_path", ""), page_html),
            }
        )

    return records


def apply_bundle_runtime_context(site_id, site_url, blueprint, bundle_snapshot):
    manifest = bundle_snapshot.get("manifest") or {}
    route_map = manifest.get("route_map") or {}

    if route_map:
        navigation_items = blueprint.get("navigation", []) or []
        for item in navigation_items:
            source_href = item.get("source_url") or item.get("href") or ""
            resolved_source = normalize_source_url(source_href, site_url) or source_href
            clone_local_path = route_map.get(resolved_source, "")
            clone_path = build_clone_route_from_local_path(clone_local_path) if clone_local_path else ""
            item["source_url"] = resolved_source
            if clone_path:
                item["clone_path"] = clone_path
                item["href"] = clone_path

        if navigation_items:
            blueprint["seed_records"]["navigation_items"] = [
                {
                    "label": item.get("label", ""),
                    "href": item.get("href", ""),
                    "clone_path": item.get("clone_path", ""),
                    "source_url": item.get("source_url", item.get("href", "")),
                    "selector": item.get("selector", ""),
                    "section_key": item.get("section_key", ""),
                    "display_order": index,
                }
                for index, item in enumerate(navigation_items, start=1)
            ]

    bundle_page_records = build_bundle_site_page_records(site_id, bundle_snapshot)
    if bundle_page_records:
        blueprint.setdefault("seed_records", {})["site_pages"] = bundle_page_records

    bundle_media_assets = build_bundle_media_assets(site_id, bundle_snapshot)
    if bundle_media_assets:
        merged_media_assets = merge_clone_media_assets(blueprint.get("media_assets", []), bundle_media_assets)
        blueprint["media_assets"] = merged_media_assets
        blueprint["media_summary"] = build_media_summary(merged_media_assets)
    else:
        merged_media_assets = blueprint.get("media_assets", [])

    diagnostics = blueprint.setdefault("clone_diagnostics", {})
    diagnostics["bundlePages"] = len(bundle_snapshot.get("pages", []))
    diagnostics["bundleAssets"] = len(manifest.get("assets", []))
    diagnostics["bundleMediaAssets"] = len(bundle_media_assets)
    diagnostics["adminSyncedMedia"] = len(merged_media_assets)
    diagnostics["routeMapEntries"] = len(route_map)
    diagnostics["navigationLinks"] = len(blueprint.get("navigation", []))

    return blueprint

def sync_media_assets(site_id, user_id, media_assets):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seen_asset_keys = []

    for asset in media_assets:
        asset_key = asset.get("asset_key") or asset.get("hash") or hashlib.sha1(
            json.dumps(asset, sort_keys=True).encode("utf-8")
        ).hexdigest()
        seen_asset_keys.append(asset_key)
        c.execute(
            '''
            INSERT INTO media_assets (
                site_id, user_id, asset_key, source_kind, media_type, mime_type, filename,
                original_name, file_url, original_url, alt_text, width, height, hash, status,
                section_key, usage_json, metadata_json, local_path, uploaded_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(site_id, user_id, asset_key) DO UPDATE SET
                source_kind = excluded.source_kind,
                media_type = excluded.media_type,
                mime_type = excluded.mime_type,
                filename = CASE WHEN media_assets.status = 'custom' THEN media_assets.filename ELSE excluded.filename END,
                original_name = excluded.original_name,
                file_url = CASE WHEN media_assets.status = 'custom' THEN media_assets.file_url ELSE excluded.file_url END,
                original_url = excluded.original_url,
                alt_text = excluded.alt_text,
                width = excluded.width,
                height = excluded.height,
                hash = excluded.hash,
                status = CASE WHEN media_assets.status = 'custom' THEN media_assets.status ELSE excluded.status END,
                section_key = excluded.section_key,
                usage_json = excluded.usage_json,
                metadata_json = excluded.metadata_json,
                local_path = CASE WHEN media_assets.status = 'custom' THEN media_assets.local_path ELSE excluded.local_path END,
                uploaded_at = media_assets.uploaded_at,
                updated_at = excluded.updated_at
            ''',
            (
                site_id,
                user_id,
                asset_key,
                asset.get("source_kind", "clone"),
                asset.get("media_type"),
                asset.get("mime_type"),
                asset.get("filename"),
                asset.get("original_name"),
                asset.get("file_url") or asset.get("original_url"),
                asset.get("original_url"),
                asset.get("alt_text"),
                asset.get("width"),
                asset.get("height"),
                asset.get("hash"),
                asset.get("status", "ready"),
                asset.get("section_key"),
                json.dumps(asset.get("usage", [])),
                json.dumps(asset.get("metadata", {})),
                asset.get("local_path"),
                timestamp,
                timestamp,
            )
        )

    if seen_asset_keys:
        placeholders = ",".join("?" for _ in seen_asset_keys)
        c.execute(
            f'''
            UPDATE media_assets
            SET status = CASE WHEN status = 'custom' THEN status ELSE 'archived' END,
                updated_at = ?
            WHERE site_id = ? AND user_id = ? AND source_kind = 'clone' AND asset_key NOT IN ({placeholders})
            ''',
            [timestamp, site_id, user_id, *seen_asset_keys]
        )
    else:
        c.execute(
            '''
            UPDATE media_assets
            SET status = CASE WHEN status = 'custom' THEN status ELSE 'archived' END,
                updated_at = ?
            WHERE site_id = ? AND user_id = ? AND source_kind = 'clone'
            ''',
            (timestamp, site_id, user_id)
        )

    conn.commit()
    conn.close()

def generate_clone_runtime(site_id, user_id, site_url, site_html, admin_theme_id=None):
    if not admin_theme_id:
        admin_theme_id = DEFAULT_ADMIN_THEME_ID
    media_dir = os.path.join("project_assets", "media", f"site_{site_id}")
    blueprint = build_conversion_blueprint(site_url, site_html, site_id=site_id, media_output_dir=media_dir)
    blueprint["admin_theme"] = get_admin_theme_option(admin_theme_id)
    bundle_snapshot = load_saved_bundle_snapshot(site_id, base_dir=os.getcwd())
    blueprint = apply_bundle_runtime_context(site_id, site_url, blueprint, bundle_snapshot)
    localized_html = blueprint.get("localized_html", site_html)
    artifact_dir = os.path.join("project_assets", "generated_dynamic_apps", f"site_{site_id}")
    artifact_paths = create_scaffold_files(artifact_dir, site_id, blueprint)
    site_spec = build_site_spec(site_id, site_url, blueprint)
    update_html_in_db(site_id, user_id, localized_html, ensure_bridge=False)
    save_conversion_blueprint(site_id, user_id, blueprint, artifact_dir)
    save_site_spec(site_id, user_id, site_spec)
    rebuild_dynamic_site_data(site_id, user_id, blueprint)
    sync_media_assets(site_id, user_id, blueprint.get("media_assets", []))
    return {
        "blueprint": blueprint,
        "site_spec": site_spec,
        "artifact_dir": artifact_dir,
        "artifact_paths": artifact_paths,
    }

def save_conversion_blueprint(site_id, user_id, blueprint, artifact_dir):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        '''
        INSERT INTO conversion_blueprints (site_id, user_id, site_type, confidence, blueprint_json, generated_at, artifact_dir)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(site_id) DO UPDATE SET
            user_id = excluded.user_id,
            site_type = excluded.site_type,
            confidence = excluded.confidence,
            blueprint_json = excluded.blueprint_json,
            generated_at = excluded.generated_at,
            artifact_dir = excluded.artifact_dir
        ''',
        (
            site_id,
            user_id,
            blueprint["site_type"],
            blueprint["confidence"],
            json.dumps(blueprint),
            timestamp,
            artifact_dir,
        )
    )
    conn.commit()
    conn.close()

def save_site_spec(site_id, user_id, site_spec):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        '''
        INSERT INTO site_specs (site_id, user_id, spec_json, bindings_json, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(site_id) DO UPDATE SET
            user_id = excluded.user_id,
            spec_json = excluded.spec_json,
            bindings_json = excluded.bindings_json,
            updated_at = excluded.updated_at
        ''',
        (
            site_id,
            user_id,
            json.dumps(site_spec),
            json.dumps(site_spec.get("bindings", [])),
            timestamp,
        )
    )
    conn.commit()
    conn.close()

def get_site_spec(site_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        'SELECT spec_json, bindings_json, updated_at FROM site_specs WHERE site_id = ? AND user_id = ?',
        (site_id, user_id)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "spec": json.loads(row[0]),
        "bindings": json.loads(row[1]),
        "updated_at": row[2],
    }

def get_conversion_blueprint(site_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        'SELECT site_type, confidence, blueprint_json, generated_at, artifact_dir FROM conversion_blueprints WHERE site_id = ? AND user_id = ?',
        (site_id, user_id)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "site_type": row[0],
        "confidence": row[1],
        "blueprint": json.loads(row[2]),
        "generated_at": row[3],
        "artifact_dir": row[4],
    }

def build_section_title(model_name):
    return model_name.replace("_", " ").title()

def rebuild_dynamic_site_data(site_id, user_id, blueprint):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute('DELETE FROM dynamic_models WHERE site_id = ? AND user_id = ?', (site_id, user_id))
    c.execute('DELETE FROM dynamic_records WHERE site_id = ? AND user_id = ?', (site_id, user_id))

    admin_titles = {
        section["title"].lower(): section["title"]
        for section in blueprint.get("admin_sections", [])
    }

    for index, model in enumerate(blueprint.get("database_models", []), start=1):
        section_title = admin_titles.get(model["name"].replace("_", " "), build_section_title(model["name"]))
        c.execute(
            '''
            INSERT INTO dynamic_models (site_id, user_id, model_name, section_title, schema_json, display_order, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                site_id,
                user_id,
                model["name"],
                section_title,
                json.dumps(model),
                index,
                timestamp,
            )
        )

        for record in blueprint.get("seed_records", {}).get(model["name"], []):
            slug_source = record.get("slug") or record.get("title") or record.get("name") or f"{model['name']}-{index}"
            slug = str(slug_source).strip().lower().replace(" ", "-")
            c.execute(
                '''
                INSERT INTO dynamic_records (site_id, user_id, model_name, data_json, slug, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    site_id,
                    user_id,
                    model["name"],
                    json.dumps(record),
                    slug,
                    'published',
                    timestamp,
                    timestamp,
                )
            )

    conn.commit()
    conn.close()

def get_dynamic_models(site_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''
        SELECT model_name, section_title, schema_json, display_order
        FROM dynamic_models
        WHERE site_id = ? AND user_id = ?
        ORDER BY display_order ASC, model_name ASC
        ''',
        (site_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "model_name": row[0],
            "section_title": row[1],
            "schema": json.loads(row[2]),
            "display_order": row[3],
        }
        for row in rows
    ]

def get_dynamic_record_counts(site_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''
        SELECT model_name, COUNT(*)
        FROM dynamic_records
        WHERE site_id = ? AND user_id = ?
        GROUP BY model_name
        ''',
        (site_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def get_dynamic_records(site_id, user_id, model_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''
        SELECT id, data_json, updated_at
        , slug, status
        FROM dynamic_records
        WHERE site_id = ? AND user_id = ? AND model_name = ?
        ORDER BY id ASC
        ''',
        (site_id, user_id, model_name)
    )
    rows = c.fetchall()
    conn.close()

    records = []
    for row in rows:
        payload = json.loads(row[1])
        payload["_record_id"] = row[0]
        payload["_updated_at"] = row[2]
        payload["_slug"] = row[3]
        payload["_status"] = row[4]
        records.append(payload)
    return records

def create_dynamic_record(site_id, user_id, model_name, payload, status='draft'):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    slug_source = payload.get("slug") or payload.get("title") or payload.get("name") or f"{model_name}-{timestamp}"
    slug = str(slug_source).strip().lower().replace(" ", "-")
    c.execute(
        '''
        INSERT INTO dynamic_records (site_id, user_id, model_name, data_json, slug, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (site_id, user_id, model_name, json.dumps(payload), slug, status, timestamp, timestamp)
    )
    conn.commit()
    conn.close()

def update_dynamic_record(record_id, site_id, user_id, payload, status=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    slug_source = payload.get("slug") or payload.get("title") or payload.get("name") or f"record-{record_id}"
    slug = str(slug_source).strip().lower().replace(" ", "-")
    if status is None:
        current = c.execute(
            'SELECT status FROM dynamic_records WHERE id = ? AND site_id = ? AND user_id = ?',
            (record_id, site_id, user_id)
        ).fetchone()
        status = current[0] if current else 'draft'
    c.execute(
        '''
        UPDATE dynamic_records
        SET data_json = ?, slug = ?, status = ?, updated_at = ?
        WHERE id = ? AND site_id = ? AND user_id = ?
        ''',
        (json.dumps(payload), slug, status, timestamp, record_id, site_id, user_id)
    )
    conn.commit()
    conn.close()

def set_dynamic_record_status(record_id, site_id, user_id, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        '''
        UPDATE dynamic_records
        SET status = ?, updated_at = ?
        WHERE id = ? AND site_id = ? AND user_id = ?
        ''',
        (status, timestamp, record_id, site_id, user_id)
    )
    conn.commit()
    conn.close()

def get_media_assets(site_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        '''
        SELECT id, asset_key, source_kind, media_type, mime_type, filename, original_name,
               file_url, original_url, alt_text, width, height, hash, status, section_key,
               usage_json, metadata_json, local_path, uploaded_at, updated_at
        FROM media_assets
        WHERE site_id = ? AND user_id = ?
          AND status NOT IN ('deleted', 'archived')
        ORDER BY COALESCE(updated_at, uploaded_at) DESC, id DESC
        ''',
        (site_id, user_id)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "asset_key": row[1],
            "source_kind": row[2],
            "media_type": row[3],
            "mime_type": row[4],
            "filename": row[5],
            "original_name": row[6],
            "file_url": row[7],
            "original_url": row[8],
            "alt_text": row[9],
            "width": row[10],
            "height": row[11],
            "hash": row[12],
            "status": row[13],
            "section_key": row[14],
            "usage": json.loads(row[15] or "[]"),
            "metadata": json.loads(row[16] or "{}"),
            "local_path": row[17],
            "uploaded_at": row[18],
            "updated_at": row[19],
        }
        for row in rows
    ]

def delete_dynamic_record(record_id, site_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        'DELETE FROM dynamic_records WHERE id = ? AND site_id = ? AND user_id = ?',
        (record_id, site_id, user_id)
    )
    conn.commit()
    conn.close()

# ============================================
# 3. SCRAPER FUNCTION
# ============================================
CLONE_MODE_PRESETS = {
    "deep": {
        "label": "Deep Clone",
        "max_pages": 300,
        "max_depth": 8,
        "description": "Many pages + more assets. Slower, but gathers much more of the website.",
    },
    "fast": {
        "label": "Fast Clone",
        "max_pages": 140,
        "max_depth": 5,
        "description": "Prioritized core pages with stronger visual completeness. Still faster than Deep Clone, but much closer in quality.",
    },
}

ADMIN_THEME_OPTIONS = [
    {
        "id": "fabricator-current",
        "name": "Fabricator Current",
        "tagline": "Current premium CMS dashboard",
        "description": "The current Fabricator CMS design with neon depth, premium metrics, and a polished command-center feel.",
        "family": "Current Design",
        "best_for": "Universal CMS, content teams, all sectors",
        "layout_style": "Command sidebar workspace",
        "mockup_style": "fabricator",
        "default_mode": "dark",
        "preview": {
            "dark": ["#08111d", "#48b8ff", "#16d3a5"],
            "light": ["#f5fbff", "#2b8dff", "#0f172a"],
        },
    },
    {
        "id": "saas-minimal",
        "name": "SaaS Horizon",
        "tagline": "Clean product and service dashboard",
        "description": "Minimal, sharp, and modern with spacious layouts, crisp surfaces, and calm product-led clarity.",
        "family": "SaaS / Services",
        "best_for": "SaaS, agency, startup, service business",
        "layout_style": "Top navigation analytics layout",
        "mockup_style": "saas",
        "default_mode": "light",
        "preview": {
            "dark": ["#0d1420", "#6ea8ff", "#8cf0d0"],
            "light": ["#f7fafc", "#3563ff", "#0f172a"],
        },
    },
    {
        "id": "glass-premium",
        "name": "Commerce Pulse",
        "tagline": "Semi-dark commerce operations dashboard",
        "description": "A high-clarity commerce layout with bold analytics, product signals, and premium semi-dark surfaces.",
        "family": "Ecommerce / Store",
        "best_for": "Ecommerce, retail, product catalogs, marketplaces",
        "layout_style": "Semi-dark operations layout",
        "mockup_style": "commerce",
        "default_mode": "dark",
        "preview": {
            "dark": ["#0b1020", "#7c6cff", "#4de2c5"],
            "light": ["#fbf9ff", "#6854ff", "#16324f"],
        },
    },
    {
        "id": "enterprise-command",
        "name": "Atlas Enterprise",
        "tagline": "Executive operations workspace",
        "description": "Structured, boardroom-grade dashboard styling with strong hierarchy, dense signal, and enterprise polish.",
        "family": "Enterprise / Corporate",
        "best_for": "Corporate, operations, internal systems, large teams",
        "layout_style": "Structured executive sidebar",
        "mockup_style": "enterprise",
        "default_mode": "light",
        "preview": {
            "dark": ["#12161d", "#22c55e", "#f59e0b"],
            "light": ["#f4f6f8", "#0f766e", "#111827"],
        },
    },
    {
        "id": "creative-studio",
        "name": "Campus Education",
        "tagline": "Bright academic admin suite",
        "description": "A vibrant, approachable dashboard feel for schools, institutes, and university-style content workflows.",
        "family": "Education / Campus",
        "best_for": "Universities, schools, colleges, institutes",
        "layout_style": "Academic sidebar workspace",
        "mockup_style": "education",
        "default_mode": "dark",
        "preview": {
            "dark": ["#150f1f", "#ff7a59", "#ffd166"],
            "light": ["#fff7f1", "#ff5c35", "#1d1a2f"],
        },
    },
]

DEFAULT_ADMIN_THEME_ID = ADMIN_THEME_OPTIONS[0]["id"]


def get_admin_theme_option(theme_id):
    for option in ADMIN_THEME_OPTIONS:
        if option["id"] == theme_id:
            return {
                "id": option["id"],
                "name": option["name"],
                "tagline": option["tagline"],
                "description": option["description"],
                "family": option["family"],
                "bestFor": option.get("best_for", ""),
                "layoutStyle": option.get("layout_style", ""),
                "defaultMode": option["default_mode"],
                "modes": ["light", "dark"],
            }
    return get_admin_theme_option(DEFAULT_ADMIN_THEME_ID) if theme_id != DEFAULT_ADMIN_THEME_ID else {
        "id": DEFAULT_ADMIN_THEME_ID,
        "name": "Fabricator Current",
        "tagline": "Current premium CMS dashboard",
        "description": "The current Fabricator CMS design with neon depth, premium metrics, and a polished command-center feel.",
        "family": "Current Design",
        "bestFor": "Universal CMS, content teams, all sectors",
        "layoutStyle": "Command sidebar workspace",
        "defaultMode": "dark",
        "modes": ["light", "dark"],
    }


def render_admin_theme_preview_card(theme_option, selected=False):
    dark_a, dark_b, dark_c = theme_option["preview"]["dark"]
    light_a, light_b, light_c = theme_option["preview"]["light"]
    border = "#6366f1" if selected else "rgba(148, 163, 184, 0.18)"
    glow = "0 20px 44px rgba(99, 102, 241, 0.18)" if selected else "0 12px 30px rgba(15, 23, 42, 0.10)"
    selected_badge = "Selected Theme" if selected else "Light + Dark Ready"
    mockup_style = theme_option.get("mockup_style", "fabricator")

    if mockup_style == "saas":
        mockup = f"""
        <div style="background:#ffffff; border-radius:18px; border:1px solid rgba(148,163,184,0.18); min-height:156px; overflow:hidden; box-shadow:0 14px 28px rgba(148,163,184,0.14);">
            <div style="height:34px; background:#f8fafc; border-bottom:1px solid rgba(226,232,240,0.9); display:flex; align-items:center; justify-content:space-between; padding:0 12px;">
                <div style="display:flex; gap:10px; align-items:center;">
                    <div style="width:22px; height:22px; border-radius:8px; background:linear-gradient(135deg, {light_b}, {dark_b});"></div>
                    <div style="width:92px; height:10px; border-radius:999px; background:#e2e8f0;"></div>
                </div>
                <div style="display:flex; gap:8px;">
                    <span style="width:8px; height:8px; border-radius:999px; background:#cbd5e1;"></span>
                    <span style="width:8px; height:8px; border-radius:999px; background:#cbd5e1;"></span>
                    <span style="width:8px; height:8px; border-radius:999px; background:#cbd5e1;"></span>
                </div>
            </div>
            <div style="padding:12px;">
                <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px;">
                    <div style="height:50px; border-radius:14px; background:linear-gradient(180deg, #ffffff, #f8fafc); border:1px solid rgba(226,232,240,0.9);"></div>
                    <div style="height:50px; border-radius:14px; background:linear-gradient(180deg, #ffffff, #f8fafc); border:1px solid rgba(226,232,240,0.9);"></div>
                    <div style="height:50px; border-radius:14px; background:linear-gradient(180deg, rgba(83,108,255,0.12), rgba(83,108,255,0.04)); border:1px solid rgba(83,108,255,0.18);"></div>
                    <div style="height:50px; border-radius:14px; background:linear-gradient(180deg, rgba(20,184,166,0.14), rgba(20,184,166,0.05)); border:1px solid rgba(20,184,166,0.16);"></div>
                </div>
                <div style="display:grid; grid-template-columns:1.35fr 1fr; gap:10px; margin-top:10px;">
                    <div style="height:58px; border-radius:14px; background:linear-gradient(180deg, #ffffff, #f8fafc); border:1px solid rgba(226,232,240,0.9); position:relative;">
                        <div style="position:absolute; left:12px; right:12px; bottom:12px; height:24px; border-radius:10px; background:linear-gradient(180deg, rgba(83,108,255,0.22), rgba(83,108,255,0.03));"></div>
                    </div>
                    <div style="height:58px; border-radius:14px; background:linear-gradient(180deg, #ffffff, #f8fafc); border:1px solid rgba(226,232,240,0.9);"></div>
                </div>
            </div>
        </div>
        """
    elif mockup_style == "commerce":
        mockup = f"""
        <div style="background:linear-gradient(180deg, #23263a, #111827); border-radius:18px; min-height:156px; overflow:hidden; border:1px solid rgba(99,102,241,0.18); box-shadow:0 16px 30px rgba(17,24,39,0.28);">
            <div style="display:grid; grid-template-columns:56px 1fr; min-height:156px;">
                <div style="background:rgba(15,23,42,0.78); padding:10px 8px; display:flex; flex-direction:column; gap:8px;">
                    <div style="height:20px; width:20px; border-radius:8px; background:{dark_b};"></div>
                    <div style="height:28px; border-radius:10px; background:rgba(124,108,255,0.26);"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(255,255,255,0.12);"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(255,255,255,0.09);"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(255,255,255,0.09);"></div>
                </div>
                <div style="padding:12px;">
                    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px;">
                        <div style="height:38px; border-radius:12px; background:rgba(255,255,255,0.07);"></div>
                        <div style="height:38px; border-radius:12px; background:rgba(255,255,255,0.07);"></div>
                        <div style="height:38px; border-radius:12px; background:rgba(255,255,255,0.07);"></div>
                        <div style="height:38px; border-radius:12px; background:rgba(77,226,197,0.16); border:1px solid rgba(77,226,197,0.18);"></div>
                    </div>
                    <div style="display:grid; grid-template-columns:1.1fr 1fr; gap:10px; margin-top:10px;">
                        <div style="height:72px; border-radius:14px; background:rgba(255,255,255,0.06); position:relative;">
                            <div style="position:absolute; left:12px; right:12px; bottom:12px; display:flex; align-items:flex-end; gap:6px;">
                                <span style="width:9px; height:24px; border-radius:999px; background:{dark_b};"></span>
                                <span style="width:9px; height:34px; border-radius:999px; background:rgba(124,108,255,0.70);"></span>
                                <span style="width:9px; height:42px; border-radius:999px; background:{dark_c};"></span>
                                <span style="width:9px; height:28px; border-radius:999px; background:rgba(255,255,255,0.16);"></span>
                            </div>
                        </div>
                        <div style="height:72px; border-radius:14px; background:rgba(255,255,255,0.06);"></div>
                    </div>
                </div>
            </div>
        </div>
        """
    elif mockup_style == "enterprise":
        mockup = f"""
        <div style="background:#f8fafc; border-radius:18px; min-height:156px; overflow:hidden; border:1px solid rgba(203,213,225,0.92); box-shadow:0 14px 28px rgba(148,163,184,0.16);">
            <div style="display:grid; grid-template-columns:72px 1fr; min-height:156px;">
                <div style="background:#07120f; padding:12px 10px; display:flex; flex-direction:column; gap:8px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <div style="width:28px; height:28px; border-radius:12px; background:{light_b};"></div>
                        <div style="width:34px; height:8px; border-radius:999px; background:rgba(255,255,255,0.10);"></div>
                    </div>
                    <div style="height:40px; border-radius:14px; background:rgba(15,118,110,0.22); border:1px solid rgba(15,118,110,0.35);"></div>
                    <div style="height:12px; border-radius:999px; background:rgba(255,255,255,0.14);"></div>
                    <div style="height:12px; border-radius:999px; background:rgba(255,255,255,0.10);"></div>
                    <div style="height:12px; border-radius:999px; background:rgba(255,255,255,0.10);"></div>
                    <div style="height:12px; border-radius:999px; background:rgba(255,255,255,0.10);"></div>
                </div>
                <div style="padding:12px; background:#f8fafc;">
                    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px;">
                        <div style="height:50px; border-radius:14px; background:#ffffff; border:1px solid rgba(226,232,240,0.95);"></div>
                        <div style="height:50px; border-radius:14px; background:#ffffff; border:1px solid rgba(226,232,240,0.95);"></div>
                        <div style="height:50px; border-radius:14px; background:#ffffff; border:1px solid rgba(226,232,240,0.95);"></div>
                        <div style="height:50px; border-radius:14px; background:#ffffff; border:1px solid rgba(226,232,240,0.95);"></div>
                    </div>
                    <div style="display:grid; grid-template-columns:1.45fr 1fr; gap:10px; margin-top:10px;">
                        <div style="height:66px; border-radius:16px; background:#ffffff; border:1px solid rgba(226,232,240,0.95); position:relative;">
                            <div style="position:absolute; left:12px; right:12px; bottom:12px; height:30px; border-radius:12px; background:linear-gradient(180deg, rgba(15,118,110,0.16), rgba(15,118,110,0.04));"></div>
                        </div>
                        <div style="height:66px; border-radius:16px; background:#ffffff; border:1px solid rgba(226,232,240,0.95);"></div>
                    </div>
                </div>
            </div>
        </div>
        """
    elif mockup_style == "education":
        mockup = f"""
        <div style="background:#ffffff; border-radius:18px; min-height:156px; overflow:hidden; border:1px solid rgba(226,232,240,0.95); box-shadow:0 14px 28px rgba(148,163,184,0.16);">
            <div style="display:grid; grid-template-columns:64px 1fr 84px; min-height:156px;">
                <div style="background:#faf5ff; border-right:1px solid rgba(233,213,255,0.72); padding:12px 8px; display:flex; flex-direction:column; gap:8px;">
                    <div style="height:18px; width:40px; border-radius:999px; background:rgba(37,99,235,0.18);"></div>
                    <div style="height:34px; border-radius:12px; background:linear-gradient(135deg, {light_b}, {dark_b});"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(15,23,42,0.12);"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(15,23,42,0.12);"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(15,23,42,0.12);"></div>
                </div>
                <div style="padding:12px;">
                    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px;">
                        <div style="height:38px; border-radius:12px; background:rgba(99,102,241,0.12);"></div>
                        <div style="height:38px; border-radius:12px; background:rgba(236,72,153,0.10);"></div>
                        <div style="height:38px; border-radius:12px; background:rgba(59,130,246,0.10);"></div>
                    </div>
                    <div style="display:grid; grid-template-columns:1.2fr 0.9fr; gap:10px; margin-top:10px;">
                        <div style="height:72px; border-radius:14px; background:#fbfbff; border:1px solid rgba(233,213,255,0.72);"></div>
                        <div style="height:72px; border-radius:14px; background:#fbfbff; border:1px solid rgba(233,213,255,0.72);"></div>
                    </div>
                </div>
                <div style="background:#fcfbff; border-left:1px solid rgba(233,213,255,0.72); padding:12px 10px;">
                    <div style="height:18px; border-radius:999px; background:rgba(15,23,42,0.08);"></div>
                    <div style="margin-top:12px; display:grid; gap:10px;">
                        <div style="height:24px; border-radius:10px; background:#ffffff; border:1px solid rgba(233,213,255,0.82);"></div>
                        <div style="height:24px; border-radius:10px; background:#ffffff; border:1px solid rgba(233,213,255,0.82);"></div>
                        <div style="height:24px; border-radius:10px; background:#ffffff; border:1px solid rgba(233,213,255,0.82);"></div>
                    </div>
                </div>
            </div>
        </div>
        """
    else:
        mockup = f"""
        <div style="background:linear-gradient(180deg, #0b1324, #121b2e); border-radius:18px; min-height:156px; overflow:hidden; border:1px solid rgba(71,85,105,0.35); box-shadow:0 14px 28px rgba(15,23,42,0.24);">
            <div style="display:grid; grid-template-columns:58px 1fr; min-height:156px;">
                <div style="background:rgba(2,6,23,0.62); padding:10px 8px; display:flex; flex-direction:column; gap:8px;">
                    <div style="height:24px; width:24px; border-radius:10px; background:{dark_b};"></div>
                    <div style="height:34px; border-radius:12px; background:rgba(56,189,248,0.18);"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(255,255,255,0.10);"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(255,255,255,0.10);"></div>
                    <div style="height:10px; border-radius:999px; background:rgba(255,255,255,0.10);"></div>
                </div>
                <div style="padding:12px;">
                    <div style="display:grid; grid-template-columns:1.2fr 1fr; gap:10px;">
                        <div style="height:60px; border-radius:14px; background:linear-gradient(135deg, {dark_b}, {dark_c});"></div>
                        <div style="display:grid; gap:10px;">
                            <div style="height:25px; border-radius:10px; background:rgba(255,255,255,0.08);"></div>
                            <div style="height:25px; border-radius:10px; background:rgba(255,255,255,0.08);"></div>
                        </div>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
                        <div style="height:56px; border-radius:14px; background:rgba(255,255,255,0.07);"></div>
                        <div style="height:56px; border-radius:14px; background:rgba(255,255,255,0.07);"></div>
                    </div>
                </div>
            </div>
        </div>
        """
    mockup = textwrap.dedent(mockup).strip()
    return textwrap.dedent(f"""
    <div style="
        border:1px solid {border};
        border-radius:22px;
        padding:14px;
        background:linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
        box-shadow:{glow};
        min-height:286px;
    ">
        <div style="display:flex; gap:12px; align-items:flex-start;">
            <div>
                <div style="color:#0f172a; font-size:1rem; font-weight:800;">{theme_option['name']}</div>
            </div>
        </div>
        <div style="margin-top:12px;">{mockup}</div>
        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:10px;">
            <span style="padding:6px 10px; border-radius:999px; background:#eff6ff; color:#1d4ed8; font-size:0.74rem; font-weight:700;">{theme_option.get('layout_style', 'Premium dashboard')}</span>
            <span style="padding:6px 10px; border-radius:999px; background:#f8fafc; color:#475569; font-size:0.74rem; font-weight:700;">Light + Dark</span>
        </div>
        <div style="margin-top:10px; color:#475569; line-height:1.45; font-size:0.82rem;">{theme_option['description']}</div>
        <div style="margin-top:10px; color:{'#4f46e5' if selected else '#64748b'}; font-size:0.8rem; font-weight:700;">{selected_badge}</div>
    </div>
    """).strip()


def scrape_website(url: str, progress_callback=None, clone_mode="deep"):
    preset = CLONE_MODE_PRESETS.get(clone_mode, CLONE_MODE_PRESETS["deep"])
    try:
        return clone_site_bundle(
            url,
            base_dir=os.getcwd(),
            max_pages=preset["max_pages"],
            max_depth=preset["max_depth"],
            progress_callback=progress_callback,
        )
    except Exception as e:
        return {"error": str(e)}


def format_time_left(seconds):
    if seconds is None:
        return "calculating..."
    seconds = max(0, int(seconds))
    minutes, remaining_seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {remaining_seconds}s"
    return f"{remaining_seconds}s"


def build_clone_progress_callback(status_placeholder, detail_placeholder, progress_bar, clone_mode_label):
    runtime = {
        "started_at": time.time(),
        "phase_started_at": {},
        "last_render_at": 0.0,
    }

    def render(payload):
        phase = payload.get("phase", "crawl")
        now = time.time()
        if phase not in runtime["phase_started_at"]:
            runtime["phase_started_at"][phase] = now
        if phase not in {"complete", "archive"} and now - runtime["last_render_at"] < 0.2:
            return
        runtime["last_render_at"] = now

        current_url = payload.get("current_url") or payload.get("root_url") or ""
        current_label = current_url[:120] + ("..." if len(current_url) > 120 else "")

        if phase in {"start", "crawl"}:
            pages_crawled = int(payload.get("pages_crawled", 0))
            queue_size = int(payload.get("queue_size", 0))
            backlog_size = int(payload.get("backlog_size", 0))
            max_pages = int(payload.get("max_pages", 60))
            estimated_total = min(max_pages, max(pages_crawled + queue_size + backlog_size, max(pages_crawled, 1)))
            completed = max(pages_crawled, 1 if phase == "crawl" else 0)
            crawl_elapsed = max(now - runtime["phase_started_at"].get("crawl", runtime["started_at"]), 0.1)
            rate = completed / crawl_elapsed if completed else 0
            remaining = max(estimated_total - completed, 0)
            eta_seconds = (remaining / rate) if rate > 0 else None
            progress_value = 0.08 + (0.42 * min(completed / max(estimated_total, 1), 1))
            status_placeholder.markdown(
                f"""
                <div class="progress-banner">
                    <strong>{html.escape(clone_mode_label)} is running</strong>
                    <span>Crawling pages and mapping local routes</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            detail_placeholder.markdown(
                f"""
                <div class="progress-detail">
                    Time left: {html.escape(format_time_left(eta_seconds))}<br>
                    Pages discovered: {pages_crawled}/{estimated_total} | Queued: {queue_size + backlog_size}<br>
                    Current: {html.escape(current_label or 'starting')}
                </div>
                """,
                unsafe_allow_html=True,
            )
            progress_bar.progress(progress_value)
            return

        if phase == "rewrite":
            pages_total = max(int(payload.get("pages_total", 0)), 1)
            pages_rewritten = int(payload.get("pages_rewritten", 0))
            rewrite_elapsed = max(now - runtime["phase_started_at"].get("rewrite", runtime["started_at"]), 0.1)
            rate = pages_rewritten / rewrite_elapsed if pages_rewritten else 0
            remaining = max(pages_total - pages_rewritten, 0)
            eta_seconds = (remaining / rate) if rate > 0 else None
            assets_downloaded = int(payload.get("assets_downloaded", 0))
            assets_deduplicated = int(payload.get("assets_deduplicated", 0))
            assets_failed = int(payload.get("assets_failed", 0))
            assets_external = int(payload.get("assets_external", 0))
            progress_value = 0.72 + (0.24 * min(pages_rewritten / pages_total, 1))
            status_placeholder.markdown(
                f"""
                <div class="progress-banner">
                    <strong>{html.escape(clone_mode_label)} is rebuilding the local clone</strong>
                    <span>Rewriting pages, assets, and local navigation</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            detail_placeholder.markdown(
                f"""
                <div class="progress-detail">
                    Time left: {html.escape(format_time_left(eta_seconds))}<br>
                    Pages rebuilt: {pages_rewritten}/{pages_total}<br>
                    Assets: {assets_downloaded} downloaded, {assets_deduplicated} reused, {assets_failed} failed, {assets_external} external<br>
                    Current: {html.escape(current_label or 'rewriting pages')}
                </div>
                """,
                unsafe_allow_html=True,
            )
            progress_bar.progress(progress_value)
            return

        if phase == "prefetch":
            total = max(int(payload.get("total", 0)), 1)
            prefetched = int(payload.get("prefetched", 0))
            prefetch_elapsed = max(now - runtime["phase_started_at"].get("prefetch", runtime["started_at"]), 0.1)
            rate = prefetched / prefetch_elapsed if prefetched else 0
            remaining = max(total - prefetched, 0)
            eta_seconds = (remaining / rate) if rate > 0 else None
            progress_value = 0.50 + (0.22 * min(prefetched / total, 1))
            status_placeholder.markdown(
                f"""
                <div class="progress-banner">
                    <strong>{html.escape(clone_mode_label)} is gathering assets</strong>
                    <span>Prefetching styles, scripts, and media for the local bundle</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            detail_placeholder.markdown(
                f"""
                <div class="progress-detail">
                    Time left: {html.escape(format_time_left(eta_seconds))}<br>
                    Prefetching assets: {prefetched}/{total}<br>
                    Current: {html.escape(current_label or 'gathering site assets')}
                </div>
                """,
                unsafe_allow_html=True,
            )
            progress_bar.progress(progress_value)
            return

        if phase == "archive":
            status_placeholder.markdown(
                f"""
                <div class="progress-banner">
                    <strong>{html.escape(clone_mode_label)} is finalizing</strong>
                    <span>Packaging the staged clone and archive</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            detail_placeholder.markdown(
                '<div class="progress-detail">Time left: a few seconds<br>Finalizing clone package and archive...</div>',
                unsafe_allow_html=True,
            )
            progress_bar.progress(0.98)
            return

        if phase == "complete":
            progress_bar.progress(1.0)
            status_placeholder.markdown(
                f"""
                <div class="progress-banner">
                    <strong>{html.escape(clone_mode_label)} completed</strong>
                    <span>Local clone bundle is ready for preview and saving</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            detail_placeholder.markdown(
                f"""
                <div class="progress-detail">
                    Pages: {int(payload.get('page_count', 0))}<br>
                    Assets: {int(payload.get('asset_count', 0))}
                </div>
                """,
                unsafe_allow_html=True,
            )

    return render

# ============================================
# 4. APP FLOW CONTROL
# ============================================

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'main_menu' not in st.session_state:
    st.session_state['main_menu'] = "Clone New Site"

def main_app():
    user_id = st.session_state['user_info'][0]

    with st.sidebar:
        st.markdown("""
            <div class="brand-header">
                <div class="sidebar-kicker">Operator Console</div>
                <div class="brand-title">AI <span class="brand-highlight">Fabricator</span></div>
            </div>
        """, unsafe_allow_html=True)

        user_name = st.session_state['user_info'][1]
        initial = user_name[0].upper() if user_name else "U"
        
        st.markdown(f"""
            <div class="user-card">
                <div class="user-avatar">{initial}</div>
                <div class="user-info">
                    <h4>{user_name}</h4>
                    <span>Operator Workspace</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<p class="mini-heading">Main Menu</p>', unsafe_allow_html=True)
        
        menu = st.radio(
            "Navigation", 
            ["Clone New Site", "Manage My Sites", "Smart Dynamic Conversion", "Drag & Drop Builder"],
            label_visibility="collapsed",
            key="main_menu",
        )

        st.markdown("---")
        
        if st.button("LOGOUT"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    # --- TAB A: CLONE NEW SITE ---
    if menu == "Clone New Site":
        render_page_hero(
            "Clone Workspace",
            "Clone New Site",
            "Run a Deep or Fast clone, review the localized result, and save the package into your working library without leaving the dashboard.",
            badges=[
                {"label": "Deep correctness"},
                {"label": "Fast visual coverage"},
                {"label": "Verified local routing", "tone": "success"},
            ],
        )
        render_metric_grid([
            {"label": "Deep Clone", "value": "300 pages / depth 8", "note": "Best coverage when correctness matters most."},
            {"label": "Fast Clone", "value": "140 pages / depth 5", "note": "Prioritized core pages for faster high-quality results."},
            {"label": "Output", "value": "Local bundle + ZIP", "note": "Preview locally first, then download or save to the project database."},
        ])

        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            render_surface_note(
                "Target setup",
                "Paste the source URL, choose the crawl mode, and launch the clone. Status updates will appear live while the bundle is being prepared.",
            )
            url_input = st.text_input("Enter Website URL", placeholder="https://example.com")
            clone_mode = st.radio(
                "Clone Mode",
                options=["Deep Clone", "Fast Clone"],
                index=0,
                horizontal=True,
                help="Deep Clone crawls more pages and assets. Fast Clone is quicker but less exhaustive.",
            )
            selected_preset = CLONE_MODE_PRESETS["deep"] if clone_mode == "Deep Clone" else CLONE_MODE_PRESETS["fast"]
            render_surface_note(selected_preset["label"], selected_preset["description"])
            clone_button = st.button("Start Clone", use_container_width=True, type="primary")

        if clone_button and not url_input:
            st.warning("Please enter a website URL before starting the clone.")

        if clone_button and url_input:
            status_placeholder = st.empty()
            detail_placeholder = st.empty()
            progress_bar = st.progress(0.0)
            clone_progress_callback = build_clone_progress_callback(
                status_placeholder,
                detail_placeholder,
                progress_bar,
                selected_preset["label"],
            )
            clone_result = scrape_website(
                url_input,
                progress_callback=clone_progress_callback,
                clone_mode="deep" if clone_mode == "Deep Clone" else "fast",
            )

            if clone_result.get("error"):
                progress_bar.empty()
                status_placeholder.empty()
                detail_placeholder.empty()
                st.error(f"Error: {clone_result['error']}")
            else:
                progress_bar.empty()
                status_placeholder.empty()
                detail_placeholder.empty()
                st.session_state["scraped_html"] = clone_result["entry_html"]
                st.session_state["scraped_url"] = url_input
                st.session_state["scraped_bundle"] = clone_result
                render_result_banner(
                    f"{selected_preset['label']} ready",
                    f"The local clone opened successfully with {clone_result['page_count']} pages and {clone_result['asset_count']} localized assets. Review the preview, then download or save it.",
                )
                render_metric_grid([
                    {"label": "Mode", "value": selected_preset["label"], "note": "Current bundle was built with the selected crawl preset."},
                    {"label": "Pages", "value": clone_result["page_count"], "note": "Internal routes were mapped into the local bundle."},
                    {"label": "Localized assets", "value": clone_result["asset_count"], "note": "Styles, scripts, and media captured for the preview package."},
                ])

    # Preview & Save Section
        if "scraped_html" in st.session_state:
            bundle = st.session_state.get("scraped_bundle", {})
            stage_key = os.path.basename(bundle.get("bundle_dir", "")) if bundle else ""
            render_surface_note(
                "Clone result",
                "Scan the summary, inspect the raw HTML if needed, then download the archive or save the bundle into your project database before moving on to editing or conversion.",
            )
            if bundle:
                render_metric_grid([
                    {"label": "Internal routes mapped", "value": bundle.get('page_count', 0), "note": "Local navigation paths prepared for localhost preview."},
                    {"label": "Dependencies captured", "value": bundle.get('asset_count', 0), "note": "Downloaded or reused assets inside the staged clone."},
                    {"label": "Preview mode", "value": "Local staged clone" if stage_key else "Inline HTML", "note": "The preview below reflects the current bundle state."},
                ])
            with st.expander("View Raw HTML", expanded=False):
                st.code(st.session_state["scraped_html"][:1000] + "...", language="html")
        
        # ====================================================
        # >>> DOWNLOAD AND SAVE BUTTONS <<<
        # ====================================================
            btn_col1, btn_col2 = st.columns(2)
        


            with btn_col2:
                archive_bytes = b""
                archive_path = bundle.get("archive_path")
                if archive_path and os.path.exists(archive_path):
                    with open(archive_path, "rb") as archive_file:
                        archive_bytes = archive_file.read()
                download_name = f"{urlparse(st.session_state['scraped_url']).netloc.replace(':', '_')}_clone.zip"
            # THIS ADDS THE DOWNLOAD BUTTON FUNCTIONALITY
                st.download_button(
                    label="Download Clone Package",
                    data=archive_bytes,
                    file_name=download_name,
                    mime="application/zip",
                    use_container_width=True,
                    type="primary",
                    disabled=not archive_bytes
            )

            with btn_col1:
                if st.button("Save To Project Database", use_container_width=True):
                    saved_ok = False
                    with st.spinner("Saving to project database..."):
                        if not bundle:
                            st.error("Clone package is missing. Clone the website again before saving.")
                        else:
                            site_id = save_site_to_db(user_id, st.session_state["scraped_url"], bundle.get("source_entry_html") or bundle["entry_html"])
                            persist_bundle_for_site(site_id, bundle["bundle_dir"], base_dir=os.getcwd())
                            saved_ok = True
                        time.sleep(1)
                    if saved_ok:
                        st.balloons()
                        st.success("Project Saved! Generate Database + Admin Panel later from Smart Dynamic Conversion when you want to create the admin side.")

            if bundle and stage_key:
                render_surface_note(
                    "Local preview",
                    "This iframe shows the staged localhost-ready clone with internal routing preserved inside the bundle.",
                )
                st.components.v1.iframe(
                    f"http://127.0.0.1:{FLASK_PORT}/staged-clone/{stage_key}/",
                    height=600,
                    scrolling=True,
                )
            else:
                render_surface_note(
                    "Inline preview",
                    "The staged bundle was not available, so the current HTML snapshot is rendered directly below.",
                )
                st.components.v1.html(st.session_state["scraped_html"], height=600, scrolling=True)

    # --- TAB B: MANAGE SAVED SITES ---
    elif menu == "Manage My Sites":
        render_page_hero(
            "Project Maintenance",
            "Manage My Sites",
            "Open a saved clone, edit the stored source directly, and compare the code against a live render before committing your update.",
            badges=[
                {"label": "Direct HTML editing"},
                {"label": "Live render"},
                {"label": "Database sync", "tone": "success"},
            ],
        )
    
        saved_sites = get_user_sites(user_id)
    
        if not saved_sites:
            st.warning("No projects found. Navigate to 'Clone New Site' to begin.")
        else:
            options = {f"{site[1]} (ID: {site[0]}) - {site[2]}": site[0] for site in saved_sites}
            selected_label = st.selectbox("Select Project", list(options.keys()))
            site_id = options[selected_label]
            admin_state = build_admin_access_state(site_id, user_id)
            render_metric_grid([
                {"label": "Saved projects", "value": len(saved_sites), "note": "Every saved clone is available here for code editing and previewing."},
                {"label": "Active project", "value": f"ID {site_id}", "note": "Only the selected project is loaded into the editor below."},
                {"label": "Workspace", "value": "Code + preview", "note": "Edit the source on the left and inspect the live render on the right."},
                {"label": "Admin status", "value": admin_state["status_label"], "note": admin_state["status_note"]},
            ])
            render_surface_note(
                "Editing flow",
                "Change the stored HTML, review the render side by side, then commit when you are satisfied with the updated result.",
            )
            render_admin_access_panel(
                admin_state,
                key_prefix=f"manage_{site_id}",
                empty_message="Generate the database and admin panel from Smart Dynamic Conversion for this selected project, then return here to open it anytime.",
                title="Project Admin Access",
            )
            if not admin_state["generated"]:
                if st.button("Go To Smart Dynamic Conversion", key=f"manage_to_conversion_{site_id}", use_container_width=True):
                    st.session_state["conversion_site"] = selected_label
                    st.session_state["main_menu"] = "Smart Dynamic Conversion"
                    st.rerun()
        
            # --- Ensure Flask is running for preview ---
            ensure_flask_running()

            # --- File browser: list available files in the bundle ---
            bundle_files = list_bundle_files(site_id, base_dir=os.getcwd())
            text_files = [f for f in bundle_files if f["is_text"]]
            binary_files = [f for f in bundle_files if not f["is_text"]]

            # --- Track current project and selected file ---
            project_changed = ("current_site_id" not in st.session_state or st.session_state["current_site_id"] != site_id)
            if project_changed:
                st.session_state["current_site_id"] = site_id
                st.session_state["editor_file"] = "index.html"
                st.session_state.pop("editor_code", None)

            # --- File selector ---
            if text_files:
                file_options = [f["rel_path"] for f in text_files]
                current_file = st.session_state.get("editor_file", "index.html")
                if current_file not in file_options:
                    current_file = file_options[0]
                selected_file = st.selectbox(
                    "Edit File",
                    file_options,
                    index=file_options.index(current_file) if current_file in file_options else 0,
                    key=f"file_select_{site_id}",
                    help=f"{len(text_files)} editable text file(s), {len(binary_files)} binary asset(s) in this bundle."
                )
                file_changed = (st.session_state.get("editor_file") != selected_file)
                st.session_state["editor_file"] = selected_file
            else:
                selected_file = None
                file_changed = False

            # --- Load file content into editor ---
            if selected_file and (project_changed or file_changed or "editor_code" not in st.session_state):
                content, error_msg = load_bundle_file_raw(site_id, selected_file, base_dir=os.getcwd())
                if error_msg:
                    st.session_state["editor_code"] = f"<!-- {error_msg} -->"
                    st.session_state["editor_error"] = error_msg
                elif not content or not content.strip():
                    # Fallback to DB for the main entry page
                    if selected_file in ("index.html", "index.htm"):
                        db_html = get_html_by_id(site_id, user_id, preview_bundle=False)
                        if db_html and db_html.strip():
                            st.session_state["editor_code"] = db_html
                            st.session_state.pop("editor_error", None)
                        else:
                            st.session_state["editor_code"] = "<!-- No valid HTML content available for this project. Try re-cloning the site. -->"
                            st.session_state["editor_error"] = "No content available."
                    else:
                        st.session_state["editor_code"] = ""
                        st.session_state.pop("editor_error", None)
                else:
                    st.session_state["editor_code"] = content
                    st.session_state.pop("editor_error", None)
            elif not selected_file and "editor_code" not in st.session_state:
                # No bundle files at all — try DB
                db_html = get_html_by_id(site_id, user_id, preview_bundle=False)
                if db_html and db_html.strip():
                    st.session_state["editor_code"] = db_html
                else:
                    st.session_state["editor_code"] = "<!-- No valid HTML content available for this project. Try re-cloning the site. -->"
                st.session_state.pop("editor_error", None)

            # --- Show error banner if file is problematic ---
            if st.session_state.get("editor_error"):
                st.warning(st.session_state["editor_error"])

            col_edit, col_view = st.columns([1, 1])

            with col_edit:
                st.subheader("Code Editor")
                st.text_area("Source Code", key="editor_code", height=800)

                # --- Action buttons ---
                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    if st.button("Commit Changes", type="primary", use_container_width=True):
                        with st.spinner("Saving to project database..."):
                            update_html_in_db(site_id, user_id, st.session_state["editor_code"])
                            # Also write back to the bundle file if it exists
                            if selected_file:
                                bundle_site_dir = get_saved_bundle_site_dir(site_id, base_dir=os.getcwd())
                                target_path = os.path.join(bundle_site_dir, selected_file.replace("/", os.sep))
                                if os.path.isdir(bundle_site_dir):
                                    try:
                                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                        with open(target_path, "w", encoding="utf-8") as f:
                                            f.write(st.session_state["editor_code"])
                                    except OSError:
                                        pass
                            time.sleep(0.5)
                        st.toast("Changes committed!", icon="")
                        st.success("Project synced to database and bundle.")
                        time.sleep(1)
                        st.rerun()

                with action_col2:
                    file_ext = os.path.splitext(selected_file or "file.html")[1]
                    mime_map = {".html": "text/html", ".htm": "text/html", ".css": "text/css", ".js": "application/javascript", ".json": "application/json", ".xml": "text/xml", ".svg": "image/svg+xml", ".txt": "text/plain"}
                    dl_mime = mime_map.get(file_ext, "text/plain")
                    st.download_button(
                        label="Download File",
                        data=st.session_state.get("editor_code", ""),
                        file_name=os.path.basename(selected_file or f"site_{site_id}.html"),
                        mime=dl_mime,
                        use_container_width=True
                    )

            with col_view:
                st.subheader("Live Render")

                # --- Preview controls ---
                preview_url = f"http://127.0.0.1:{FLASK_PORT}/clone/{site_id}/"
                ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
                with ctrl_col1:
                    if st.button("Refresh Preview", use_container_width=True, key=f"refresh_preview_{site_id}"):
                        st.session_state["preview_refresh_count"] = st.session_state.get("preview_refresh_count", 0) + 1
                with ctrl_col2:
                    st.link_button("View Cloned Website", preview_url, use_container_width=True)
                with ctrl_col3:
                    st.link_button("Open in Drag & Drop", f"http://127.0.0.1:{FLASK_PORT}/editor/{site_id}", use_container_width=True)

                # --- Live preview iframe (served by Flask with full CSS/JS/images) ---
                refresh_count = st.session_state.get("preview_refresh_count", 0)
                iframe_url = f"{preview_url}?_r={refresh_count}"
                iframe_html = f'''<iframe src="{iframe_url}"
                    style="width:100%;height:780px;border:1px solid #e0e0e0;border-radius:8px;background:#fff;"
                    sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
                    loading="lazy"></iframe>'''
                st.components.v1.html(iframe_html, height=800, scrolling=False)

    elif menu == "Smart Dynamic Conversion":
        render_page_hero(
            "Dynamic Content Setup",
            "Smart Dynamic Conversion",
            "Keep the clone-first workflow intact while generating SiteSpec, content records, APIs, and the separate admin website for the selected project.",
            badges=[
                {"label": "SiteSpec generation"},
                {"label": "Record seeding"},
                {"label": "Separate admin app", "tone": "success"},
            ],
        )

        saved_sites = get_user_sites(user_id)
        if not saved_sites:
            st.warning("No cloned sites found yet. Save a site first, then return here.")
        else:
            options = {f"{site[1]} (ID: {site[0]}) - {site[2]}": site[0] for site in saved_sites}
            selected_label = st.selectbox("Choose Saved Clone", list(options.keys()), key="conversion_site")
            site_id = options[selected_label]
            site_url = next(site[1] for site in saved_sites if site[0] == site_id)
            site_html = get_html_by_id(site_id, user_id)
            existing_blueprint = get_conversion_blueprint(site_id, user_id)
            stored_site_spec = get_site_spec(site_id, user_id)
            current_site_spec = stored_site_spec["spec"] if stored_site_spec else None
            stored_admin_state = build_admin_access_state(site_id, user_id, site_spec=current_site_spec)
            stored_admin_theme = (
                (current_site_spec or {}).get("adminTheme", {}).get("id", DEFAULT_ADMIN_THEME_ID)
            )
            theme_state_key = f"admin_theme_selection_{site_id}"
            if theme_state_key not in st.session_state:
                st.session_state[theme_state_key] = stored_admin_theme

            render_surface_note(
                "Admin theme selection",
                "Choose the standalone admin style before generation. The selected theme is saved into the project spec and remains available in light and dark mode.",
            )

            selected_admin_theme = st.session_state.get(theme_state_key, DEFAULT_ADMIN_THEME_ID)
            theme_rows = [ADMIN_THEME_OPTIONS[:3], ADMIN_THEME_OPTIONS[3:]]
            for row_index, theme_row in enumerate(theme_rows):
                preview_columns = st.columns(len(theme_row))
                for column, theme_option in zip(preview_columns, theme_row):
                    with column:
                        st.markdown(
                            render_admin_theme_preview_card(
                                theme_option,
                                selected=selected_admin_theme == theme_option["id"],
                            ),
                            unsafe_allow_html=True,
                        )
                        button_label = "Selected" if selected_admin_theme == theme_option["id"] else f"Use {theme_option['name']}"
                        if st.button(
                            button_label,
                            key=f"choose_admin_theme_{site_id}_{row_index}_{theme_option['id']}",
                            use_container_width=True,
                        ):
                            st.session_state[theme_state_key] = theme_option["id"]
                            st.rerun()

            selected_admin_theme = st.session_state.get(theme_state_key, DEFAULT_ADMIN_THEME_ID)
            selected_theme_option = next(
                (theme for theme in ADMIN_THEME_OPTIONS if theme["id"] == selected_admin_theme),
                ADMIN_THEME_OPTIONS[0],
            )
            st.info(
                f"Selected theme: {selected_theme_option['name']} | {selected_theme_option['family']} | Best for {selected_theme_option.get('best_for', 'all sectors')}"
            )
            render_metric_grid([
                {"label": "Selected project", "value": f"ID {site_id}", "note": site_url},
                {"label": "Admin status", "value": stored_admin_state["status_label"], "note": stored_admin_state["status_note"]},
                {"label": "Theme", "value": selected_theme_option["name"], "note": "This theme is applied to the generated separate admin website."},
            ])
            if not stored_admin_state["generated"]:
                render_admin_access_panel(
                    stored_admin_state,
                    key_prefix=f"conversion_existing_{site_id}",
                    empty_message="This project does not have a generated admin panel yet. Use the generation button below to create it for this exact site.",
                )

            col_a, col_b = st.columns([1, 1])
            with col_a:
                generate_label = "Regenerate Database + Admin Panel" if stored_admin_state["generated"] else "Generate Database + Admin Panel"
                if st.button(generate_label, type="primary", use_container_width=True):
                    with st.spinner("Understanding site structure and generating backend plan..."):
                        conversion_result = generate_clone_runtime(
                            site_id,
                            user_id,
                            site_url,
                            site_html,
                            admin_theme_id=selected_admin_theme,
                        )
                    st.session_state["latest_conversion"] = {
                        "site_id": site_id,
                        **conversion_result,
                    }
                    selected_theme_name = get_admin_theme_option(selected_admin_theme)["name"]
                    st.success(f"SiteSpec, media library, seeded records, and separate admin app data generated with the {selected_theme_name} theme.")

            with col_b:
                if existing_blueprint:
                    st.info(f"Last generated: {existing_blueprint['generated_at']}")

            active_conversion = None
            latest_conversion = st.session_state.get("latest_conversion")
            if latest_conversion and latest_conversion.get("site_id") == site_id:
                active_conversion = latest_conversion
            elif existing_blueprint:
                active_conversion = {
                    "site_id": site_id,
                    "blueprint": existing_blueprint["blueprint"],
                    "site_spec": stored_site_spec["spec"] if stored_site_spec else None,
                    "artifact_dir": existing_blueprint["artifact_dir"],
                    "artifact_paths": None,
                }

            if active_conversion:
                blueprint = active_conversion["blueprint"]
                site_spec = active_conversion.get("site_spec")
                active_admin_state = build_admin_access_state(site_id, user_id, site_spec=site_spec)
                summary_col1, summary_col2, summary_col3 = st.columns(3)
                with summary_col1:
                    st.metric("Detected Type", blueprint["site_type"].replace("_", " ").title())
                with summary_col2:
                    st.metric("Collections", len(blueprint["database_models"]))
                with summary_col3:
                    st.metric("API Routes", len(blueprint["backend_routes"]))

                render_admin_access_panel(
                    active_admin_state,
                    key_prefix=f"conversion_active_{site_id}",
                    empty_message="Generate the admin panel to unlock the site-specific login and admin URL for this project.",
                    title="Generated Admin Access",
                )

                st.progress(min(int(blueprint["confidence"] * 100), 100))
                st.caption(f"Confidence score: {blueprint['confidence']}")
                if blueprint.get("media_summary"):
                    media_summary = blueprint["media_summary"]
                    st.caption(
                        f"Media indexed: {media_summary.get('total', 0)} | "
                        f"Localized: {media_summary.get('downloaded', 0)} | "
                        f"Fallback refs: {media_summary.get('fallbackReferences', 0)}"
                    )

                tab_overview, tab_admin_app, tab_api, tab_pipeline = st.tabs([
                    "Architecture",
                    "Separate Admin App",
                    "API + Files",
                    "Pipeline"
                ])

                with tab_overview:
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.subheader("Database Models")
                        for model in blueprint["database_models"]:
                            field_summary = ", ".join(field["name"] for field in model["fields"][:5])
                            seed_count = len(blueprint.get("seed_records", {}).get(model["name"], []))
                            st.markdown(f"- **{model['name']}**: {field_summary}")
                            st.caption(f"Seeded records: {seed_count}")

                    with info_col2:
                        st.subheader("Frontend Bindings")
                        for binding in blueprint["frontend_bindings"]:
                            st.markdown(f"- **{binding['component']}** -> `{binding['data_source']}`")
                            st.caption(binding["strategy"])

                        if blueprint.get("confidence_breakdown"):
                            st.subheader("Confidence Breakdown")
                            for component in blueprint["confidence_breakdown"].get("components", []):
                                st.markdown(f"- **{component['label']}**: {int(component['score'] * 100)}%")
                                st.caption(component["details"])

                    st.subheader("Admin Sections")
                    for section in blueprint["admin_sections"]:
                        st.markdown(f"- **{section['title']}**: {', '.join(section['columns'])}")

                    if blueprint.get("media_assets"):
                        st.subheader("Indexed Media")
                        media_preview = [
                            {
                                "name": asset.get("original_name"),
                                "type": asset.get("media_type"),
                                "status": asset.get("download_status"),
                                "url": asset.get("file_url") or asset.get("original_url"),
                            }
                            for asset in blueprint["media_assets"][:12]
                        ]
                        st.dataframe(media_preview, use_container_width=True)

                with tab_admin_app:
                    st.subheader("Standalone Admin Website")
                    ensure_flask_running()
                    admin_url = active_admin_state["url"]
                    admin_theme = (site_spec or {}).get("adminTheme", {}) if site_spec else {}
                    st.markdown("The admin app is served automatically by Flask and tied to this cloned site only.")
                    if admin_theme:
                        st.caption(f"Selected theme: {admin_theme.get('name', 'Fabricator Current')} | Light + Dark mode ready")
                    st.link_button("Open Admin Panel", admin_url, use_container_width=True, type="primary")
                    st.text_input(
                        "Admin URL",
                        value=admin_url,
                        key=f"tab_admin_url_{site_id}",
                        disabled=True,
                    )
                    st.caption("Use this exact site-specific login URL for demos and project access later.")

                    export_state_key = f"connected_export_{site_id}"
                    if st.button("Build Connected Download Package", use_container_width=True):
                        try:
                            with st.spinner("Packaging cloned website + admin system into one connected export..."):
                                export_result = build_connected_export(site_id, user_id, os.getcwd())
                            st.session_state[export_state_key] = export_result
                            st.success("Connected export package is ready.")
                        except Exception as export_error:
                            st.error(f"Connected export failed: {export_error}")

                    connected_export = st.session_state.get(export_state_key)
                    if connected_export and os.path.exists(connected_export["archive_path"]):
                        with open(connected_export["archive_path"], "rb") as export_file:
                            connected_export_bytes = export_file.read()
                        st.download_button(
                            label="Download Connected System ZIP",
                            data=connected_export_bytes,
                            file_name=os.path.basename(connected_export["archive_path"]),
                            mime="application/zip",
                            use_container_width=True,
                            type="primary",
                        )
                        st.caption("This zip includes two linked folders: `cloned_website` and `admin_system`.")
                        st.code(
                            "\n".join([
                                connected_export["manifest"]["folders"]["clonedWebsite"],
                                connected_export["manifest"]["folders"]["adminSystem"],
                                connected_export["manifest"]["folders"]["backend"],
                                connected_export["manifest"]["folders"]["database"],
                            ]),
                            language="text",
                        )

                    if site_spec:
                        st.subheader("SiteSpec Summary")
                        st.json({
                            "projectId": site_spec.get("projectId"),
                            "siteName": site_spec.get("siteName"),
                            "siteType": site_spec.get("siteType"),
                            "adminTheme": (site_spec.get("adminTheme") or {}).get("name", "Fabricator Current"),
                            "resources": [resource["key"] for resource in site_spec.get("resources", [])],
                        })

                with tab_api:
                    st.subheader("Backend Route Plan")
                    route_preview = [
                        {"method": route["method"], "path": route["path"], "purpose": route["purpose"]}
                        for route in blueprint["backend_routes"][:16]
                    ]
                    st.dataframe(route_preview, use_container_width=True)

                    st.subheader("Live Dynamic API")
                    model_names = [model["name"] for model in blueprint["database_models"]]
                    if model_names:
                        sample_model = model_names[0]
                        st.code(
                            "\n".join([
                                f"GET  /dynamic-api/{site_id}/meta",
                                f"GET  /dynamic-api/{site_id}/{sample_model}",
                                f"POST /dynamic-api/{site_id}/{sample_model}",
                                f"PUT  /dynamic-api/{site_id}/{sample_model}/<record_id>",
                                f"DELETE /dynamic-api/{site_id}/{sample_model}/<record_id>",
                                f"GET  /api/projects/{site_id}/spec",
                                f"GET  /api/admin/{site_id}/{sample_model}",
                                f"PATCH /api/admin/{site_id}/{sample_model}/<record_id>/publish",
                            ]),
                            language="text"
                        )

                    artifact_dir = active_conversion["artifact_dir"]
                    if artifact_dir:
                        st.subheader("Generated Files")
                        st.code(
                            "\n".join([
                                os.path.join(artifact_dir, "generated_backend.py"),
                                os.path.join(artifact_dir, "schema.json"),
                                os.path.join(artifact_dir, "admin_sections.json"),
                                os.path.join(artifact_dir, "site_spec.json"),
                                os.path.join(artifact_dir, "integration_notes.md"),
                            ]),
                            language="text"
                        )

                    with st.expander("View Full Blueprint JSON", expanded=False):
                        st.json(blueprint)

                with tab_pipeline:
                    for step_number, step_name in enumerate(blueprint.get("pipeline", []), start=1):
                        st.markdown(f"{step_number}. {step_name}")
    

    # --- TAB C: DRAG & DROP (FLASK INTEGRATION) ---
    elif menu == "Drag & Drop Builder":
        render_page_hero(
            "Visual Editing",
            "Drag & Drop Builder",
            "Launch the visual builder for saved clones, edit structure in the canvas, and sync the result back into the same project database.",
            badges=[
                {"label": "Components + layers"},
                {"label": "Responsive canvas"},
                {"label": "Visual save workflow", "tone": "success"},
            ],
        )
        render_metric_grid([
            {"label": "Left panel", "value": "Components + layers", "note": "Browse blocks, then inspect the page structure while building."},
            {"label": "Center canvas", "value": "Live visual editing", "note": "Adjust layout directly in the builder without leaving the workflow."},
            {"label": "Right panel", "value": "Design + properties", "note": "Style the selected element and update its editable traits clearly."},
        ])
        if not flask_running(FLASK_PORT):
            st.info("Initializing Visual Engine...")
            ensure_flask_running()
        
        # Simple Loader for Flask
            with st.spinner("Connecting to Graphic Engine..."):
                time.sleep(3)

    # --- FIX: Pass the user_id to the Flask App ---
        # We append ?user_id={user_id} to the URL.
        # Your 'dragdrop_flask.py' must be set up to read this parameter.
        builder_url = f"http://127.0.0.1:{FLASK_PORT}?user_id={user_id}"
        render_surface_note(
            "Builder access",
            "The builder runs in the Flask visual studio. Choose a saved site there, edit the layout, and use save to sync the update back into the project.",
        )
        st.code(builder_url, language="text")
    
        st.components.v1.iframe(
            src=builder_url,
            height=950,
            scrolling=True
    )

# ============================================
# 5. LOGIN / REGISTER SCREEN
# ============================================

def login_page():
    render_page_hero(
        "Operator Access",
        "AI Website Fabricator",
        "Clone websites, review localized bundles, launch the visual builder, and generate the separate admin system from one operator dashboard.",
        badges=[
            {"label": "Clone-first workflow"},
            {"label": "Local preview"},
            {"label": "Admin generation", "tone": "success"},
        ],
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        render_surface_note(
            "Sign in to continue",
            "Use your existing operator account to access clone operations, visual editing, and dynamic conversion tools. New users can create an account below.",
        )
        tab1, tab2 = st.tabs(["LOGIN", "REGISTER"])
        
        with tab1:
            st.subheader("Welcome Back")
            login_user_name = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type='password', key="login_pass")
            
            if st.button("Authenticate", use_container_width=True, type="primary"):
                if not login_user_name:
                      st.warning("⚠️ Please enter your username.")
                elif not login_password:
                      st.error("⚠️ Password is required to login.")
                else:
                    # Stylish Loader for Login
                    with st.spinner("Verifying Biometrics..."):
                        time.sleep(1)
                        result = login_user(login_user_name, login_password)
                    
                    if result:
                        st.session_state['logged_in'] = True
                        st.session_state['user_info'] = result 
                        st.rerun()
                    else:
                        st.error("Access Denied: Invalid Credentials")
        
        with tab2:
            st.subheader("New Account")
            new_user = st.text_input("New Username", key="new_user")
            new_password = st.text_input("New Password", type='password', key="new_pass")
            
            if st.button("Create Account", use_container_width=True):
                if not new_user:
                    st.warning("⚠️ Please choose a username.")
                elif not new_password:
                    st.error("⚠️ Please choose a password.")
                else:
                    with st.spinner("Generating Identity..."):
                        time.sleep(1)
                        created = create_user(new_user, new_password)
                        
                    if created:
                        st.success("Identity Created. Proceed to Login.")
                    else:
                        st.error("Username Unavailable.")

# ============================================
# 6. EXECUTION
# ============================================

if __name__ == "__main__":
    ensure_flask_running()
    if st.session_state['logged_in']:
        main_app()
    else:
        login_page()
