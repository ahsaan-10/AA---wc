import hashlib
import json
import mimetypes
import os
import posixpath
import re
import shutil
import time
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse, unquote
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
PAGE_FILE_EXTENSIONS = {"", ".html", ".htm", ".php", ".asp", ".aspx", ".jsp", ".cfm", ".shtml"}
ASSET_EXTENSIONS = {
    ".css",
    ".js",
    ".mjs",
    ".json",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".svg",
    ".bmp",
    ".ico",
    ".avif",
    ".mp4",
    ".webm",
    ".mov",
    ".m4v",
    ".mp3",
    ".wav",
    ".ogg",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".pdf",
    ".zip",
    ".rar",
}
TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid")
ASSET_ATTRS = [
    "src",
    "data-src",
    "data-original",
    "data-lazy-src",
    "data-bg",
    "data-background-image",
    "poster",
]
SRCSET_ATTRS = ["srcset", "data-srcset"]
LINK_ATTRS = ["href", "data-href", "data-url", "formaction", "action"]
EVENT_HANDLER_ATTRS = ["onclick", "data-onclick"]
CSS_URL_PATTERN = re.compile(r"url\(([^)]+)\)", flags=re.I)
CSS_IMPORT_PATTERN = re.compile(
    r"@import\s+(?:url\()?\s*(['\"]?)([^'\"\);]+)\1\s*\)?([^;]*);",
    flags=re.I,
)
QUOTED_STRING_PATTERN = re.compile(r"(['\"])(.+?)\1")
DEFAULT_MAX_PAGES = 300
DEFAULT_MAX_DEPTH = 8
PAGE_REQUEST_TIMEOUT = 12
ASSET_REQUEST_TIMEOUT = 15
SITEMAP_REQUEST_TIMEOUT = 8
ASSET_PREFETCH_WORKERS = 16
PAGE_CRAWL_WORKERS = 8
MAX_DIAGNOSTIC_ITEMS = 600
PAGE_DISCOVERY_ATTRS = ["data-href", "data-url", "data-link", "data-path", "data-permalink", "formaction", "action"]
LAZY_ASSET_HINTS = ("src", "image", "img", "lazy", "poster", "background", "thumb", "icon", "logo")
NAVIGATION_JS_PATTERNS = [
    re.compile(r"(?:window|document|top)?\.?location(?:\.href)?\s*=\s*(['\"])([^'\"]+)\1", flags=re.I),
    re.compile(r"(?:window|document|top)?\.?location\.(?:assign|replace)\(\s*(['\"])([^'\"]+)\1\s*\)", flags=re.I),
    re.compile(r"(?:window\.)?open\(\s*(['\"])([^'\"]+)\1", flags=re.I),
]
WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}
CORE_PAGE_HINTS = {
    "about",
    "admissions",
    "blog",
    "careers",
    "contact",
    "courses",
    "departments",
    "faq",
    "features",
    "gallery",
    "home",
    "portfolio",
    "pricing",
    "products",
    "programs",
    "projects",
    "research",
    "services",
    "solutions",
    "team",
}
LOW_PRIORITY_PAGE_HINTS = {
    "amp",
    "archive",
    "author",
    "cart",
    "category",
    "checkout",
    "feed",
    "login",
    "page",
    "privacy-policy",
    "search",
    "tag",
    "terms",
    "wp-admin",
    "wp-content",
    "wp-json",
}


def slugify(value):
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return cleaned or "item"


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)


def append_diag(diagnostics, section, key, item, limit=MAX_DIAGNOSTIC_ITEMS):
    if not diagnostics:
        return
    bucket = diagnostics.setdefault(section, {}).setdefault(key, [])
    if len(bucket) < limit:
        bucket.append(item)


def increment_diag(diagnostics, section, key, amount=1):
    if not diagnostics:
        return
    section_bucket = diagnostics.setdefault(section, {})
    section_bucket[key] = int(section_bucket.get(key, 0)) + amount


def build_diagnostics(root_url, max_pages, max_depth):
    return {
        "crawl": {
            "root_url": root_url,
            "max_pages": max_pages,
            "max_depth": max_depth,
            "discovered_pages": [],
            "queued_pages": [],
            "page_failures": [],
            "skipped_pages": [],
            "sitemaps": [],
        },
        "links": {
            "discovered": [],
            "rewritten": [],
            "fallback_pages": [],
            "rewritten_count": 0,
            "internal_links_seen": 0,
            "external_links_seen": 0,
        },
        "assets": {
            "downloaded": [],
            "failed": [],
            "deduplicated": [],
            "rewritten_references": [],
            "downloaded_count": 0,
            "failed_count": 0,
            "deduplicated_count": 0,
        },
    }


def emit_progress(progress_callback, **payload):
    if not callable(progress_callback):
        return
    try:
        progress_callback(payload)
    except Exception:
        pass


def emit_state_progress(state, phase, **payload):
    progress_state = state.get("progress") or {}
    callback = progress_state.get("callback")
    if not callable(callback):
        return
    snapshot = {
        "phase": phase,
        "root_url": state.get("root_url", ""),
        "pages_total": progress_state.get("pages_total", 0),
        "pages_rewritten": progress_state.get("pages_rewritten", 0),
        "assets_downloaded": progress_state.get("assets_downloaded", 0),
        "assets_deduplicated": progress_state.get("assets_deduplicated", 0),
        "assets_failed": progress_state.get("assets_failed", 0),
        "assets_external": progress_state.get("assets_external", 0),
    }
    snapshot.update(payload)
    emit_progress(callback, **snapshot)


def normalized_host(url):
    host = urlparse(url).netloc.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def normalize_source_url(candidate, base_url=""):
    if not candidate:
        return ""

    resolved = urljoin(base_url, str(candidate).strip())
    parsed = urlparse(resolved)
    if parsed.scheme not in {"http", "https"}:
        return ""

    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if any(key.lower().startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES):
            continue
        query_items.append((key, value))

    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
        query=urlencode(query_items, doseq=True),
    )
    return urlunparse(normalized)


def split_fragment(candidate, base_url=""):
    raw = urljoin(base_url, str(candidate or "").strip())
    parsed = urlparse(raw)
    fragment = parsed.fragment or ""
    without_fragment = normalize_source_url(urlunparse(parsed._replace(fragment="")))
    return without_fragment, fragment


def is_internal_url(candidate_url, root_url):
    if not candidate_url:
        return False
    return normalized_host(candidate_url) == normalized_host(root_url)


def extension_from_url(url):
    path = urlparse(url).path or ""
    _, ext = os.path.splitext(path)
    return ext.lower()


def looks_like_html_page(url):
    ext = extension_from_url(url)
    return ext in PAGE_FILE_EXTENSIONS


def sanitize_segment(value):
    raw = unquote(str(value or "").strip())
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw).strip("-._")
    if not cleaned:
        cleaned = "page"
    if cleaned.lower() in WINDOWS_RESERVED_NAMES:
        cleaned = f"{cleaned}-item"
    if len(cleaned) > 32:
        digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
        cleaned = f"{cleaned[:20].rstrip('-._')}-{digest}"
    return cleaned or "page"


def shorten_page_slug(parts, source_url, max_len=42):
    candidate = "-".join(part for part in parts if part) or "page"
    candidate = candidate[:max_len].rstrip("-._")
    digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:10]
    return f"{candidate}-{digest}" if candidate else f"page-{digest}"


def build_page_output_path(source_url, used_paths):
    parsed = urlparse(source_url)
    segments = [sanitize_segment(segment) for segment in parsed.path.split("/") if segment.strip()]
    query_hash = hashlib.sha1(parsed.query.encode("utf-8")).hexdigest()[:8] if parsed.query else ""

    if segments:
        last_segment = segments[-1]
        stem, ext = os.path.splitext(last_segment)
        if ext:
            clean_stem = sanitize_segment(stem)
            if clean_stem == "index":
                segments = segments[:-1]
            else:
                segments[-1] = clean_stem

    if query_hash:
        if segments:
            segments[-1] = f"{segments[-1]}-{query_hash}"
        else:
            segments = [f"index-{query_hash}"]

    if not segments:
        base_path = "index.html"
    else:
        keep_nested = len(segments) <= 2 and all(len(segment) <= 28 for segment in segments)
        if keep_nested:
            base_path = posixpath.join(*segments, "index.html")
        else:
            slug = shorten_page_slug(segments[-2:] if len(segments) > 1 else segments, source_url)
            base_path = posixpath.join("pages", f"{slug}.html")

    if len(base_path) > 120:
        slug = shorten_page_slug(segments[-2:] if segments else ["index"], source_url, max_len=30)
        base_path = posixpath.join("pages", f"{slug}.html")

    if base_path not in used_paths:
        used_paths.add(base_path)
        return base_path

    suffix = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:8]
    if base_path == "index.html":
        candidate = f"index-{suffix}.html"
    elif base_path.startswith("pages/"):
        stem, ext = os.path.splitext(posixpath.basename(base_path))
        candidate = posixpath.join("pages", f"{stem}-{suffix}{ext}")
    else:
        candidate = posixpath.join(posixpath.dirname(base_path), f"index-{suffix}.html")
    used_paths.add(candidate)
    return candidate


def iter_page_url_aliases(source_url):
    normalized = normalize_source_url(source_url)
    if not normalized:
        return []

    parsed = urlparse(normalized)
    path = parsed.path or "/"
    aliases = []
    seen = set()

    def append_path(candidate_path):
        candidate_path = candidate_path or "/"
        if not candidate_path.startswith("/"):
            candidate_path = f"/{candidate_path}"
        candidate = urlunparse(parsed._replace(path=candidate_path))
        normalized_candidate = normalize_source_url(candidate)
        if normalized_candidate and normalized_candidate not in seen:
            seen.add(normalized_candidate)
            aliases.append(normalized_candidate)

    append_path(path)
    ext = extension_from_url(normalized)

    if path == "/":
        append_path("/index.html")
        return aliases

    stripped = path.rstrip("/")
    if path.endswith("/"):
        append_path(stripped or "/")
        append_path(posixpath.join(path, "index.html"))
        return aliases

    if ext in {".html", ".htm"}:
        stem = path[: -len(ext)]
        if stem:
            append_path(stem)
            append_path(f"{stem}/")
        base_name = posixpath.basename(path).lower()
        if base_name in {"index.html", "index.htm", "default.html", "default.htm"}:
            parent = posixpath.dirname(path) or "/"
            append_path(parent)
            append_path(f"{parent.rstrip('/')}/" if parent != "/" else "/")
        return aliases

    if ext in PAGE_FILE_EXTENSIONS:
        append_path(f"{path}/")
        append_path(posixpath.join(path, "index.html"))
        append_path(f"{path}.html")

    # For clean URLs with no extension (e.g. /about, /services/web-design),
    # generate slash and index.html variants so links match regardless of
    # whether the source site uses trailing slashes or not.
    if not ext and not path.endswith("/"):
        append_path(f"{stripped}/")
        append_path(posixpath.join(stripped, "index.html"))
        append_path(f"{stripped}.html")

    return aliases


def register_page_aliases(page_aliases, source_url, page_info):
    for alias in iter_page_url_aliases(source_url):
        page_aliases.setdefault(alias, page_info)


def build_asset_output_path(source_url, asset_kind, used_paths, content_type=""):
    parsed = urlparse(source_url)
    base_name = os.path.basename(parsed.path) or asset_kind
    stem, ext = os.path.splitext(base_name)
    ext = ext.lower()

    if not ext:
        guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
        if guessed:
            ext = guessed
    if not ext:
        ext = {
            "css": ".css",
            "js": ".js",
            "image": ".png",
            "icon": ".ico",
            "font": ".woff2",
            "video": ".mp4",
            "audio": ".mp3",
        }.get(asset_kind, ".bin")

    folders = {
        "css": "assets/css",
        "js": "assets/js",
        "image": "assets/images",
        "icon": "assets/icons",
        "font": "assets/fonts",
        "video": "assets/video",
        "audio": "assets/audio",
    }
    folder = folders.get(asset_kind, "assets/files")
    safe_name = slugify(os.path.splitext(stem or asset_kind)[0])
    if len(safe_name) > 24:
        safe_name = f"{safe_name[:16].rstrip('-')}-{hashlib.sha1((stem or asset_kind).encode('utf-8')).hexdigest()[:6]}"
    suffix = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:8]
    candidate = posixpath.join(folder, f"{safe_name}-{suffix}{ext}")
    while candidate in used_paths:
        suffix = hashlib.sha1(f"{source_url}:{candidate}".encode("utf-8")).hexdigest()[:8]
        candidate = posixpath.join(folder, f"{safe_name}-{suffix}{ext}")
    used_paths.add(candidate)
    return candidate


def relative_url(from_path, to_path):
    from_dir = posixpath.dirname(from_path) or "."
    return posixpath.relpath(to_path, from_dir).replace("\\", "/")


def decode_response_body(response):
    raw = response.content
    if not raw:
        return ""
    # Safety: if the transport layer did not decompress (e.g. brotli without
    # library), try manual decompression before decoding.
    ce = (response.headers.get("Content-Encoding") or "").strip().lower()
    if ce == "br":
        try:
            import brotli
            raw = brotli.decompress(raw)
        except ImportError:
            # No brotli library — attempt gzip as last resort, otherwise the
            # raw bytes will produce garbled text.  Signal the problem clearly.
            import gzip as _gzip, io as _io
            try:
                raw = _gzip.decompress(raw)
            except Exception:
                pass  # will be caught by the sanity check below
    elif ce == "gzip":
        import gzip as _gzip
        try:
            raw = _gzip.decompress(raw)
        except Exception:
            pass
    elif ce == "deflate":
        import zlib as _zlib
        try:
            raw = _zlib.decompress(raw)
        except Exception:
            try:
                raw = _zlib.decompress(raw, -_zlib.MAX_WBITS)
            except Exception:
                pass
    # Sanity: if after everything the content still looks like binary junk,
    # return empty string rather than garbled replacement characters.
    encoding = response.encoding or response.apparent_encoding or "utf-8"
    text = raw.decode(encoding, errors="replace")
    # A high ratio of replacement characters means undecoded binary.
    if len(text) > 50:
        replacements = text.count("\ufffd")
        if replacements / len(text) > 0.05:
            return ""
    return text


def detect_asset_kind(source_url, tag_name="", rel_values=None, as_attr="", content_type=""):
    rel_values = [str(item).lower() for item in (rel_values or [])]
    as_attr = (as_attr or "").lower()
    content_type = (content_type or "").lower()
    ext = extension_from_url(source_url)

    if "css" in content_type or "stylesheet" in rel_values or ext == ".css":
        return "css"
    if "javascript" in content_type or as_attr == "script" or ext in {".js", ".mjs"} or tag_name == "script":
        return "js"
    if "font" in content_type or as_attr == "font" or ext in {".woff", ".woff2", ".ttf", ".otf", ".eot"}:
        return "font"
    if "video" in content_type or as_attr == "video" or ext in {".mp4", ".webm", ".mov", ".m4v"}:
        return "video"
    if "audio" in content_type or as_attr == "audio" or ext in {".mp3", ".wav", ".ogg"}:
        return "audio"
    if "icon" in content_type or any("icon" in rel for rel in rel_values) or ext == ".ico":
        return "icon"
    if "image" in content_type or ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".bmp", ".avif"}:
        return "image"
    return "file"


def extract_document_base(page_url, soup):
    base_tag = soup.find("base", href=True)
    if base_tag:
        return normalize_source_url(base_tag.get("href"), page_url) or page_url
    return page_url


def extract_quoted_urls(text, base_url):
    matches = []
    for match in QUOTED_STRING_PATTERN.finditer(text or ""):
        candidate = match.group(2).strip()
        if not candidate or candidate.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
            continue
        resolved = normalize_source_url(candidate, base_url)
        if resolved:
            matches.append((candidate, resolved))
    return matches


def looks_like_navigation_candidate(raw_value):
    raw = str(raw_value or "").strip()
    if not raw or raw.startswith(("javascript:", "mailto:", "tel:", "data:", "#")):
        return False
    if raw.startswith(("http://", "https://", "/", "./", "../", "?")):
        return True
    if " " in raw:
        return False
    if "/" in raw:
        return True
    if re.search(r"\.(html?|php|aspx?|jsp|cfm)(?:$|\?)", raw, flags=re.I):
        return True
    return False


def should_clone_as_page(url, raw_value=""):
    if not url:
        return False

    if raw_value and not looks_like_navigation_candidate(raw_value):
        return False

    parsed = urlparse(url)
    ext = extension_from_url(url)
    path = parsed.path or "/"
    lower_path = path.lower()
    segments = [segment.lower() for segment in path.split("/") if segment]

    if ext and ext not in PAGE_FILE_EXTENSIONS:
        return False
    if any(segment in {"feed", "wp-json", "wp-admin", "wp-content", "wp-includes"} for segment in segments):
        return False
    if lower_path.endswith("xmlrpc.php"):
        return False

    query_map = {key.lower(): value.lower() for key, value in parse_qsl(parsed.query, keep_blank_values=True)}
    if "rest_route" in query_map:
        return False
    if query_map.get("format") in {"json", "xml"} or query_map.get("output") in {"json", "xml"}:
        return False

    return True


def navigation_candidate_priority(url):
    parsed = urlparse(url)
    segments = [segment.lower() for segment in parsed.path.split("/") if segment]
    score = len(segments) * 3

    if not segments:
        score -= 20
    if parsed.query:
        score += 10
    if any(segment in CORE_PAGE_HINTS for segment in segments):
        score -= 12
    if any(segment in LOW_PRIORITY_PAGE_HINTS for segment in segments):
        score += 16
    if any(re.fullmatch(r"\d+", segment) or re.fullmatch(r"\d{4}", segment) for segment in segments):
        score += 10
    if any(re.search(r"(post|article|blog|news|press|event)-?\d+", segment) for segment in segments):
        score += 8
    if len(segments) >= 3:
        score += 6

    return score


def extract_navigation_script_targets(text, base_url):
    results = []
    payload = str(text or "")
    for pattern in NAVIGATION_JS_PATTERNS:
        for match in pattern.finditer(payload):
            candidate = match.group(2).strip()
            if not looks_like_navigation_candidate(candidate):
                continue
            resolved = normalize_source_url(candidate, base_url)
            if resolved:
                results.append((candidate, resolved))
    deduped = []
    seen = set()
    for item in results:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def extract_meta_refresh_url(content, base_url):
    text = str(content or "").strip()
    match = re.search(r"url\s*=\s*([^;]+)", text, flags=re.I)
    if not match:
        return ""
    return normalize_source_url(match.group(1).strip().strip("\"'"), base_url)


def extract_sitemap_urls(sitemap_xml, base_url):
    urls = []
    try:
        root = ET.fromstring(sitemap_xml)
    except ET.ParseError:
        return urls

    for loc in root.iterfind(".//{*}loc"):
        resolved = normalize_source_url(loc.text or "", base_url)
        if resolved:
            urls.append(resolved)
    return list(dict.fromkeys(urls))


def discover_sitemap_page_urls(root_url, session, diagnostics=None, max_sitemaps=6):
    parsed_root = urlparse(root_url)
    site_root = f"{parsed_root.scheme}://{parsed_root.netloc}"
    sitemap_candidates = []

    try:
        robots_response = session.get(urljoin(site_root, "/robots.txt"), timeout=SITEMAP_REQUEST_TIMEOUT, allow_redirects=True)
        if robots_response.ok:
            for line in robots_response.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemap_url = normalize_source_url(line.split(":", 1)[1].strip(), site_root)
                    if sitemap_url:
                        sitemap_candidates.append(sitemap_url)
    except Exception as exc:
        append_diag(diagnostics, "crawl", "skipped_pages", {"kind": "robots", "url": urljoin(site_root, "/robots.txt"), "reason": str(exc)})

    sitemap_candidates.append(urljoin(site_root, "/sitemap.xml"))
    queue = deque(dict.fromkeys(sitemap_candidates))
    visited = set()
    page_urls = []

    while queue and len(visited) < max_sitemaps:
        sitemap_url = queue.popleft()
        normalized_sitemap = normalize_source_url(sitemap_url)
        if not normalized_sitemap or normalized_sitemap in visited:
            continue
        visited.add(normalized_sitemap)
        try:
            response = session.get(normalized_sitemap, timeout=SITEMAP_REQUEST_TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            sitemap_text = decode_response_body(response)
            discovered = extract_sitemap_urls(sitemap_text, normalized_sitemap)
            append_diag(diagnostics, "crawl", "sitemaps", {"url": normalized_sitemap, "discovered": len(discovered)})
            for candidate in discovered:
                if candidate.endswith(".xml"):
                    if candidate not in visited and len(visited) + len(queue) < max_sitemaps:
                        queue.append(candidate)
                elif is_internal_url(candidate, root_url) and looks_like_html_page(candidate):
                    page_urls.append(candidate)
        except Exception as exc:
            append_diag(diagnostics, "crawl", "skipped_pages", {"kind": "sitemap", "url": normalized_sitemap, "reason": str(exc)})

    return list(dict.fromkeys(page_urls))


def fetch_html_page_request(url, headers, cookies=None):
    with requests.Session() as session:
        session.trust_env = False
        response = session.get(
            url,
            headers=headers,
            cookies=cookies or None,
            timeout=PAGE_REQUEST_TIMEOUT,
            allow_redirects=True,
        )
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    if "html" not in content_type and not looks_like_html_page(response.url):
        raise ValueError(f"Non-HTML response for page crawl: {response.url}")
    return normalize_source_url(response.url), decode_response_body(response)


def collect_internal_navigation_urls(soup, page_url, root_url, diagnostics=None):
    document_base = extract_document_base(page_url, soup)
    discovered = []

    for anchor in soup.find_all(["a", "area"], href=True):
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        resolved = normalize_source_url(href, document_base)
        if resolved and is_internal_url(resolved, root_url) and should_clone_as_page(resolved, href):
            discovered.append(resolved)
            append_diag(diagnostics, "links", "discovered", {"page": page_url, "attribute": "href", "raw": href, "resolved": resolved, "kind": anchor.name})

    for tag in soup.find_all(True):
        for attribute in PAGE_DISCOVERY_ATTRS:
            value = tag.get(attribute, "").strip()
            if not value:
                continue
            resolved = normalize_source_url(value, document_base)
            if resolved and is_internal_url(resolved, root_url) and should_clone_as_page(resolved, value):
                discovered.append(resolved)
                append_diag(diagnostics, "links", "discovered", {"page": page_url, "attribute": attribute, "raw": value, "resolved": resolved, "kind": tag.name})

    for tag in soup.find_all(True):
        for attribute in EVENT_HANDLER_ATTRS:
            handler_value = tag.get(attribute, "")
            if not handler_value:
                continue
            for raw_value, resolved in extract_navigation_script_targets(handler_value, document_base):
                if is_internal_url(resolved, root_url) and should_clone_as_page(resolved, raw_value):
                    discovered.append(resolved)
                    append_diag(
                        diagnostics,
                        "links",
                        "discovered",
                        {"page": page_url, "attribute": attribute, "raw": raw_value, "resolved": resolved, "kind": tag.name},
                    )

    for script_tag in soup.find_all("script"):
        if script_tag.get("src"):
            continue
        for raw_value, resolved in extract_navigation_script_targets(script_tag.get_text() or "", document_base):
            if is_internal_url(resolved, root_url) and should_clone_as_page(resolved, raw_value):
                discovered.append(resolved)
                append_diag(
                    diagnostics,
                    "links",
                    "discovered",
                    {"page": page_url, "attribute": "script", "raw": raw_value, "resolved": resolved, "kind": "script"},
                )

    for link_tag in soup.find_all("link", href=True):
        rel_values = [str(item).lower() for item in (link_tag.get("rel") or [])]
        link_type = (link_tag.get("type") or "").lower()
        if not any(rel in {"next", "prev", "canonical", "alternate"} for rel in rel_values):
            continue
        if any(token in link_type for token in {"rss", "xml", "json"}):
            continue
        href = link_tag.get("href", "").strip()
        resolved = normalize_source_url(href, document_base)
        if resolved and is_internal_url(resolved, root_url) and should_clone_as_page(resolved, href):
            discovered.append(resolved)
            append_diag(diagnostics, "links", "discovered", {"page": page_url, "attribute": "link-rel", "raw": href, "resolved": resolved, "kind": ",".join(rel_values)})

    for meta_tag in soup.find_all("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)}):
        resolved = extract_meta_refresh_url(meta_tag.get("content", ""), document_base)
        if resolved and is_internal_url(resolved, root_url) and should_clone_as_page(resolved, meta_tag.get("content", "")):
            discovered.append(resolved)
            append_diag(diagnostics, "links", "discovered", {"page": page_url, "attribute": "meta-refresh", "resolved": resolved, "kind": "meta"})

    deduped = list(dict.fromkeys(discovered))
    return sorted(deduped, key=navigation_candidate_priority)


def fetch_html_page(url, session):
    response = session.get(url, timeout=PAGE_REQUEST_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    if "html" not in content_type and not looks_like_html_page(response.url):
        raise ValueError(f"Non-HTML response for page crawl: {response.url}")
    return normalize_source_url(response.url), decode_response_body(response)


def crawl_site_pages(root_url, session, max_pages=DEFAULT_MAX_PAGES, max_depth=DEFAULT_MAX_DEPTH, diagnostics=None, progress_callback=None):
    root_url = normalize_source_url(root_url)
    visited = set()
    queue = deque([(root_url, 0, "", "root")])
    queued_urls = {root_url}
    sitemap_backlog = deque()
    pages = {}
    crawl_order = []

    for sitemap_url in discover_sitemap_page_urls(root_url, session, diagnostics=diagnostics):
        if sitemap_url != root_url:
            sitemap_backlog.append((sitemap_url, 1, "", "sitemap"))
            queued_urls.add(sitemap_url)
            append_diag(diagnostics, "crawl", "queued_pages", {"url": sitemap_url, "depth": 1, "via": "sitemap_backlog"})

    emit_progress(
        progress_callback,
        phase="crawl",
        root_url=root_url,
        current_url=root_url,
        pages_crawled=0,
        queue_size=len(queue),
        backlog_size=len(sitemap_backlog),
        max_pages=max_pages,
        max_depth=max_depth,
    )

    while (queue or sitemap_backlog) and len(crawl_order) < max_pages:
        # Interleave sitemap backlog into queue so important sitemap-discovered
        # pages don't wait until all link-discovered pages are processed.
        if not queue and sitemap_backlog:
            while sitemap_backlog and len(queue) < PAGE_CRAWL_WORKERS:
                queue.append(sitemap_backlog.popleft())
        elif sitemap_backlog and len(queue) < PAGE_CRAWL_WORKERS * 2:
            queue.append(sitemap_backlog.popleft())

        batch = []
        while queue and len(batch) < PAGE_CRAWL_WORKERS:
            current, depth, discovered_from, via = queue.popleft()
            if depth > max_depth:
                append_diag(diagnostics, "crawl", "skipped_pages", {"url": current, "reason": "depth_limit", "depth": depth})
                continue
            if current in visited:
                continue
            visited.add(current)
            batch.append((current, depth, discovered_from, via))

        if not batch:
            continue

        fetched_pages = {}
        headers = dict(session.headers)
        cookies = session.cookies.get_dict()
        with ThreadPoolExecutor(max_workers=min(PAGE_CRAWL_WORKERS, len(batch))) as executor:
            futures = {
                executor.submit(fetch_html_page_request, current, headers, cookies): current
                for current, _, _, _ in batch
            }
            for future in as_completed(futures):
                current = futures[future]
                try:
                    fetched_pages[current] = future.result()
                except Exception as exc:
                    fetched_pages[current] = exc

        for current, depth, discovered_from, via in batch:
            fetched = fetched_pages.get(current)
            if isinstance(fetched, Exception):
                append_diag(diagnostics, "crawl", "page_failures", {"url": current, "depth": depth, "via": via, "error": str(fetched)})
                continue

            final_url, html = fetched
            if final_url and final_url != current:
                visited.add(final_url)

            if not is_internal_url(final_url, root_url):
                append_diag(diagnostics, "crawl", "skipped_pages", {"url": current, "resolved_to": final_url, "reason": "redirected_external"})
                continue
            if final_url in pages:
                continue

            soup = BeautifulSoup(html, "html.parser")
            page_title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else (urlparse(final_url).path or "/")
            )
            pages[final_url] = {
                "source_url": final_url,
                "html": html,
                "depth": depth,
                "discovered_from": discovered_from,
                "via": via,
                "title": page_title,
                "asset_requests": collect_page_asset_requests_from_soup(soup, final_url),
            }
            crawl_order.append(final_url)
            append_diag(
                diagnostics,
                "crawl",
                "discovered_pages",
                {"url": final_url, "depth": depth, "discovered_from": discovered_from, "via": via},
            )
            emit_progress(
                progress_callback,
                phase="crawl",
                root_url=root_url,
                current_url=final_url,
                pages_crawled=len(crawl_order),
                queue_size=len(queue),
                backlog_size=len(sitemap_backlog),
                max_pages=max_pages,
                max_depth=max_depth,
            )

            for candidate in collect_internal_navigation_urls(soup, final_url, root_url, diagnostics=diagnostics):
                if candidate in visited or candidate in queued_urls:
                    continue
                if len(crawl_order) + len(queue) >= max_pages and candidate not in pages:
                    append_diag(diagnostics, "crawl", "skipped_pages", {"url": candidate, "reason": "page_limit", "from": final_url})
                    continue
                queue.append((candidate, depth + 1, final_url, "link"))
                queued_urls.add(candidate)
                append_diag(diagnostics, "crawl", "queued_pages", {"url": candidate, "depth": depth + 1, "from": final_url, "via": "link"})

    return pages, crawl_order


def clone_binary_asset(source_url, asset_kind, state):
    asset_cache = state["asset_cache"]
    if source_url in asset_cache:
        return asset_cache[source_url]

    session = state["session"]
    used_paths = state["used_paths"]
    bundle_root = state["bundle_root"]
    diagnostics = state.get("diagnostics")

    try:
        prefetched = consume_prefetched_payload(state, source_url)
        if prefetched:
            final_url = prefetched.get("final_url") or source_url
            content_type = prefetched.get("content_type") or ""
            content_bytes = prefetched.get("content") or b""
        else:
            response = session.get(source_url, timeout=ASSET_REQUEST_TIMEOUT, allow_redirects=True, stream=True)
            response.raise_for_status()
            final_url = normalize_source_url(response.url)
            content_type = response.headers.get("content-type") or ""
        local_path = build_asset_output_path(final_url, asset_kind, used_paths, content_type)
        file_path = os.path.join(bundle_root, *local_path.split("/"))
        ensure_directory(os.path.dirname(file_path))
        content_hash = hashlib.sha1()
        with open(file_path, "wb") as output_file:
            if prefetched:
                if content_bytes:
                    content_hash.update(content_bytes)
                    output_file.write(content_bytes)
            else:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        content_hash.update(chunk)
                        output_file.write(chunk)
        digest = content_hash.hexdigest()
        existing_path = state["asset_hash_index"].get(digest)
        status = "downloaded"
        if existing_path and existing_path != local_path and os.path.exists(file_path):
            os.remove(file_path)
            local_path = existing_path
            status = "deduplicated"
            increment_diag(diagnostics, "assets", "deduplicated_count")
            append_diag(
                diagnostics,
                "assets",
                "deduplicated",
                {"source_url": final_url, "kind": asset_kind, "existing_local_path": existing_path, "hash": digest},
            )
        else:
            state["asset_hash_index"][digest] = local_path
            increment_diag(diagnostics, "assets", "downloaded_count")
            append_diag(
                diagnostics,
                "assets",
                "downloaded",
                {"source_url": final_url, "local_path": local_path, "kind": asset_kind, "content_type": content_type},
            )
        asset_info = {
            "source_url": final_url,
            "local_path": local_path,
            "kind": asset_kind,
            "status": status,
            "content_type": content_type,
            "size": os.path.getsize(os.path.join(bundle_root, *local_path.split("/"))) if status == "deduplicated" else os.path.getsize(file_path),
            "hash": digest,
        }
    except Exception as exc:
        increment_diag(diagnostics, "assets", "failed_count")
        append_diag(diagnostics, "assets", "failed", {"source_url": source_url, "kind": asset_kind, "error": str(exc)})
        asset_info = {
            "source_url": source_url,
            "local_path": source_url,
            "kind": asset_kind,
            "status": "external_reference",
            "content_type": "",
            "size": 0,
        }

    asset_cache[source_url] = asset_info
    if asset_info["source_url"] != source_url:
        asset_cache[asset_info["source_url"]] = asset_info
    progress_state = state.get("progress")
    if progress_state is not None:
        status = asset_info.get("status")
        if status == "downloaded":
            progress_state["assets_downloaded"] += 1
        elif status == "deduplicated":
            progress_state["assets_deduplicated"] += 1
        elif status == "external_reference":
            progress_state["assets_external"] += 1
        else:
            progress_state["assets_failed"] += 1
        emit_state_progress(
            state,
            "rewrite",
            current_url=asset_info.get("source_url", source_url),
            pages_crawled=progress_state.get("pages_total", 0),
        )
    return asset_info


def rewrite_css_text(css_text, source_url, css_local_path, state):
    diagnostics = state.get("diagnostics")
    def replace_import(match):
        raw_value = match.group(2).strip()
        resolved = normalize_source_url(raw_value, source_url)
        if not resolved:
            return match.group(0)
        imported_asset = clone_asset(resolved, state, preferred_kind="css")
        if imported_asset.get("status") != "downloaded":
            return match.group(0)
        replacement = relative_url(css_local_path, imported_asset["local_path"])
        append_diag(
            diagnostics,
            "assets",
            "rewritten_references",
            {"owner": source_url, "attribute": "@import", "from": resolved, "to": replacement},
        )
        return f'@import url("{replacement}"){match.group(3)};'

    rewritten = CSS_IMPORT_PATTERN.sub(replace_import, css_text)

    def replace_url(match):
        raw_value = match.group(1).strip().strip("\"'")
        if not raw_value or raw_value.startswith(("data:", "#", "javascript:")):
            return match.group(0)
        resolved = normalize_source_url(raw_value, source_url)
        if not resolved:
            return match.group(0)
        asset = clone_asset(resolved, state)
        if asset.get("status") != "downloaded":
            return match.group(0)
        replacement = relative_url(css_local_path, asset["local_path"])
        append_diag(
            diagnostics,
            "assets",
            "rewritten_references",
            {"owner": source_url, "attribute": "url()", "from": resolved, "to": replacement},
        )
        return f'url("{replacement}")'

    return CSS_URL_PATTERN.sub(replace_url, rewritten)


def clone_stylesheet_asset(source_url, state):
    asset_cache = state["asset_cache"]
    if source_url in asset_cache:
        return asset_cache[source_url]

    session = state["session"]
    used_paths = state["used_paths"]
    bundle_root = state["bundle_root"]
    diagnostics = state.get("diagnostics")
    local_path = build_asset_output_path(source_url, "css", used_paths, "text/css")
    file_path = os.path.join(bundle_root, *local_path.split("/"))
    ensure_directory(os.path.dirname(file_path))

    asset_info = {
        "source_url": source_url,
        "local_path": local_path,
        "kind": "css",
        "status": "processing",
        "content_type": "text/css",
        "size": 0,
    }
    asset_cache[source_url] = asset_info

    try:
        prefetched = consume_prefetched_payload(state, source_url)
        if prefetched:
            final_url = prefetched.get("final_url") or source_url
            content_type = prefetched.get("content_type") or "text/css"
            css_bytes = prefetched.get("content") or b""
            css_text = css_bytes.decode("utf-8", errors="replace")
        else:
            response = session.get(source_url, timeout=ASSET_REQUEST_TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            final_url = normalize_source_url(response.url)
            content_type = response.headers.get("content-type") or "text/css"
            css_text = decode_response_body(response)
        rewritten_css = rewrite_css_text(css_text, final_url, local_path, state)
        digest = hashlib.sha1(rewritten_css.encode("utf-8")).hexdigest()
        existing_path = state["asset_hash_index"].get(digest)
        if existing_path and existing_path != local_path:
            asset_info.update(
                {
                    "source_url": final_url,
                    "local_path": existing_path,
                    "status": "deduplicated",
                    "content_type": content_type,
                    "size": os.path.getsize(os.path.join(bundle_root, *existing_path.split("/"))),
                    "hash": digest,
                }
            )
            increment_diag(diagnostics, "assets", "deduplicated_count")
            append_diag(
                diagnostics,
                "assets",
                "deduplicated",
                {"source_url": final_url, "kind": "css", "existing_local_path": existing_path, "hash": digest},
            )
            asset_cache[final_url] = asset_info
            progress_state = state.get("progress")
            if progress_state is not None:
                progress_state["assets_deduplicated"] += 1
                emit_state_progress(
                    state,
                    "rewrite",
                    current_url=final_url,
                    pages_crawled=progress_state.get("pages_total", 0),
                )
            return asset_info
        with open(file_path, "w", encoding="utf-8") as output_file:
            output_file.write(rewritten_css)
        state["asset_hash_index"][digest] = local_path
        asset_info.update(
            {
                "source_url": final_url,
                "status": "downloaded",
                "content_type": content_type,
                "size": os.path.getsize(file_path),
                "hash": digest,
            }
        )
        increment_diag(diagnostics, "assets", "downloaded_count")
        append_diag(
            diagnostics,
            "assets",
            "downloaded",
            {"source_url": final_url, "local_path": local_path, "kind": "css", "content_type": asset_info["content_type"]},
        )
        asset_cache[final_url] = asset_info
    except Exception as exc:
        increment_diag(diagnostics, "assets", "failed_count")
        append_diag(diagnostics, "assets", "failed", {"source_url": source_url, "kind": "css", "error": str(exc)})
        asset_info.update(
            {
                "local_path": source_url,
                "status": "external_reference",
                "content_type": "",
                "size": 0,
            }
        )

    progress_state = state.get("progress")
    if progress_state is not None:
        status = asset_info.get("status")
        if status == "downloaded":
            progress_state["assets_downloaded"] += 1
        elif status == "deduplicated":
            progress_state["assets_deduplicated"] += 1
        elif status == "external_reference":
            progress_state["assets_external"] += 1
        else:
            progress_state["assets_failed"] += 1
        emit_state_progress(
            state,
            "rewrite",
            current_url=asset_info.get("source_url", source_url),
            pages_crawled=progress_state.get("pages_total", 0),
        )

    return asset_info


def clone_asset(source_url, state, preferred_kind=""):
    if not source_url:
        return {"source_url": "", "local_path": "", "kind": preferred_kind or "file", "status": "skipped"}

    normalized = normalize_source_url(source_url)
    if not normalized:
        return {"source_url": source_url, "local_path": source_url, "kind": preferred_kind or "file", "status": "external_reference"}

    asset_cache = state["asset_cache"]
    if normalized in asset_cache:
        return asset_cache[normalized]

    asset_kind = preferred_kind or detect_asset_kind(normalized)
    if asset_kind == "css":
        return clone_stylesheet_asset(normalized, state)
    return clone_binary_asset(normalized, asset_kind, state)


def iter_asset_attributes(tag):
    seen = set()
    attrs = []
    for attribute in tag.attrs.keys():
        attr_name = str(attribute).lower()
        if attr_name in LINK_ATTRS:
            continue
        if attr_name in SRCSET_ATTRS or "srcset" in attr_name or attr_name.endswith("bgset"):
            if attr_name not in seen:
                seen.add(attr_name)
                attrs.append((attr_name, "srcset"))
            continue
        if attr_name in ASSET_ATTRS:
            if attr_name not in seen:
                seen.add(attr_name)
                attrs.append((attr_name, "asset"))
            continue
        if any(hint in attr_name for hint in LAZY_ASSET_HINTS):
            if attr_name not in seen:
                seen.add(attr_name)
                attrs.append((attr_name, "asset"))
    return attrs


def iter_srcset_candidates(value):
    for item in str(value or "").split(","):
        token = item.strip()
        if not token:
            continue
        parts = token.split()
        if parts:
            yield parts[0]


def iter_css_asset_candidates(css_text):
    rewritten = str(css_text or "")
    for match in CSS_IMPORT_PATTERN.finditer(rewritten):
        candidate = match.group(2).strip()
        if candidate:
            yield candidate, "css"
    for match in CSS_URL_PATTERN.finditer(rewritten):
        candidate = match.group(1).strip().strip("\"'")
        if candidate:
            yield candidate, ""


def collect_page_asset_requests_from_soup(soup, source_url):
    document_base = extract_document_base(source_url, soup)
    requests_map = {}

    def record(candidate, preferred_kind="", tag_name="", rel_values=None, as_attr=""):
        resolved = normalize_source_url(candidate, document_base)
        if not resolved:
            return
        preferred = preferred_kind or detect_asset_kind(resolved, tag_name=tag_name, rel_values=rel_values, as_attr=as_attr)
        requests_map[resolved] = preferred or requests_map.get(resolved, "")

    for tag in soup.find_all("link", href=True):
        rel_values = [str(item).lower() for item in (tag.get("rel") or [])]
        href = tag.get("href", "").strip()
        if not href:
            continue
        preferred = detect_asset_kind(href, tag_name="link", rel_values=rel_values, as_attr=tag.get("as"))
        if "stylesheet" in rel_values or preferred != "file":
            record(href, preferred_kind=preferred, tag_name="link", rel_values=rel_values, as_attr=tag.get("as"))

    for tag in soup.find_all(True):
        for attribute, attr_kind in iter_asset_attributes(tag):
            value = tag.get(attribute)
            if not value:
                continue
            if attr_kind == "srcset":
                for candidate in iter_srcset_candidates(value):
                    record(candidate, tag_name=tag.name)
                continue
            if tag.name == "iframe":
                resolved_iframe = normalize_source_url(value, document_base)
                if resolved_iframe and looks_like_html_page(resolved_iframe) and is_internal_url(resolved_iframe, source_url):
                    continue
            record(value, tag_name=tag.name)

        if tag.get("style"):
            for candidate, preferred_kind in iter_css_asset_candidates(tag.get("style")):
                record(candidate, preferred_kind=preferred_kind)

    for style_tag in soup.find_all("style"):
        for candidate, preferred_kind in iter_css_asset_candidates(style_tag.get_text()):
            record(candidate, preferred_kind=preferred_kind)

    return requests_map


def collect_page_asset_requests(raw_html, source_url):
    soup = BeautifulSoup(raw_html, "html.parser")
    return collect_page_asset_requests_from_soup(soup, source_url)


def fetch_prefetch_payload(source_url, preferred_kind, headers):
    response = requests.get(source_url, headers=headers, timeout=ASSET_REQUEST_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    final_url = normalize_source_url(response.url)
    content_type = response.headers.get("content-type") or ""
    return {
        "source_url": source_url,
        "final_url": final_url,
        "preferred_kind": preferred_kind or detect_asset_kind(final_url, content_type=content_type),
        "content_type": content_type,
        "content": response.content,
    }


_CRITICAL_ASSET_KINDS = {"css", "js", "font", "icon"}


def prefetch_assets(asset_requests, state):
    if not asset_requests:
        return

    headers = dict(state["session"].headers)
    progress_state = state.get("progress") or {}
    progress_state["assets_target"] = len(asset_requests)
    state["progress"] = progress_state
    total = len(asset_requests)
    emit_state_progress(state, "prefetch", current_url=state.get("root_url", ""), prefetched=0, total=total)

    # Split into critical (CSS/JS/font/icon) and non-critical for ordered prefetching.
    # Critical assets are downloaded first to ensure visual fidelity even if the
    # process is interrupted or the site has many images.
    critical = {}
    non_critical = {}
    for source_url, preferred_kind in asset_requests.items():
        kind = preferred_kind or detect_asset_kind(source_url)
        if kind in _CRITICAL_ASSET_KINDS:
            critical[source_url] = preferred_kind
        else:
            non_critical[source_url] = preferred_kind

    results = {}
    completed = 0

    for batch in (critical, non_critical):
        if not batch:
            continue
        with ThreadPoolExecutor(max_workers=ASSET_PREFETCH_WORKERS) as executor:
            futures = {
                executor.submit(fetch_prefetch_payload, source_url, preferred_kind, headers): (source_url, preferred_kind)
                for source_url, preferred_kind in batch.items()
            }
            for future in as_completed(futures):
                source_url, preferred_kind = futures[future]
                completed += 1
                try:
                    payload = future.result()
                    results[source_url] = payload
                    if payload["final_url"] and payload["final_url"] != source_url:
                        results[payload["final_url"]] = payload
                except Exception as exc:
                    append_diag(state.get("diagnostics"), "assets", "failed", {"source_url": source_url, "kind": preferred_kind or "file", "error": str(exc), "phase": "prefetch"})
                    increment_diag(state.get("diagnostics"), "assets", "failed_count")
                emit_state_progress(
                    state,
                    "prefetch",
                    current_url=source_url,
                    prefetched=completed,
                    total=total,
                )

    state["prefetched_payloads"] = results


def consume_prefetched_payload(state, source_url):
    prefetched_payloads = state.get("prefetched_payloads") or {}
    payload = prefetched_payloads.pop(source_url, None)
    if payload and payload.get("final_url") and payload["final_url"] != source_url:
        prefetched_payloads.pop(payload["final_url"], None)
    return payload


def rewrite_script_text(script_text, page_local_path, document_base, state):
    if not script_text:
        return script_text
    rewritten = str(script_text)
    for original_candidate, resolved in extract_navigation_script_targets(rewritten, document_base):
        replacement = rewrite_navigation_target(original_candidate, page_local_path, document_base, state)
        if replacement != original_candidate:
            rewritten = rewritten.replace(original_candidate, replacement)
    return rewritten


def ensure_internal_page_target(resolved_url, page_local_path, state, reason):
    page_map = state["page_map"]
    if resolved_url in page_map:
        return relative_url(page_local_path, page_map[resolved_url]["local_path"])

    placeholder_path = build_page_output_path(resolved_url, state["used_paths"])
    page_info = {"source_url": resolved_url, "local_path": placeholder_path, "placeholder": True}
    page_map[resolved_url] = page_info
    register_page_aliases(state.setdefault("page_aliases", {}), resolved_url, page_info)
    state["placeholder_pages"][resolved_url] = {"source_url": resolved_url, "local_path": placeholder_path, "reason": reason}
    append_diag(
        state.get("diagnostics"),
        "links",
        "fallback_pages",
        {"source_url": resolved_url, "local_path": placeholder_path, "reason": reason},
    )
    return relative_url(page_local_path, placeholder_path)


def rewrite_srcset(value, page_local_path, document_base, state):
    rebuilt = []
    for item in str(value or "").split(","):
        token = item.strip()
        if not token:
            continue
        parts = token.split()
        source_candidate = parts[0]
        resolved = normalize_source_url(source_candidate, document_base)
        if resolved:
            asset = clone_asset(resolved, state)
            if asset.get("status") == "downloaded":
                parts[0] = relative_url(page_local_path, asset["local_path"])
        rebuilt.append(" ".join(parts))
    return ", ".join(rebuilt)


def rewrite_inline_style(value, page_local_path, document_base, state):
    def replace_url(match):
        raw_value = match.group(1).strip().strip("\"'")
        if not raw_value or raw_value.startswith(("data:", "#", "javascript:")):
            return match.group(0)
        resolved = normalize_source_url(raw_value, document_base)
        if not resolved:
            return match.group(0)
        asset = clone_asset(resolved, state)
        if asset.get("status") != "downloaded":
            return match.group(0)
        replacement = relative_url(page_local_path, asset["local_path"])
        return f'url("{replacement}")'

    return CSS_URL_PATTERN.sub(replace_url, value)


def rewrite_navigation_target(value, page_local_path, document_base, state):
    diagnostics = state.get("diagnostics")
    if not value:
        return value
    raw = str(value).strip()
    if not raw or raw.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return value
    if raw.startswith("#"):
        return raw
    if not looks_like_navigation_candidate(raw):
        return value

    resolved, fragment = split_fragment(raw, document_base)
    if not resolved:
        return value

    page_map = state["page_map"]
    mapped_page = page_map.get(resolved) or (state.get("page_aliases") or {}).get(resolved)
    if mapped_page:
        rewritten = relative_url(page_local_path, mapped_page["local_path"])
        increment_diag(diagnostics, "links", "internal_links_seen")
        increment_diag(diagnostics, "links", "rewritten_count")
        append_diag(
            diagnostics,
            "links",
            "rewritten",
            {"page": state.get("current_page_source_url", ""), "from": resolved, "to": rewritten, "raw": raw},
        )
        return f"{rewritten}#{fragment}" if fragment else rewritten

    if is_internal_url(resolved, state["root_url"]) and should_clone_as_page(resolved, raw):
        rewritten = ensure_internal_page_target(resolved, page_local_path, state, reason="unreachable_or_outside_crawl")
        increment_diag(diagnostics, "links", "internal_links_seen")
        increment_diag(diagnostics, "links", "rewritten_count")
        append_diag(
            diagnostics,
            "links",
            "rewritten",
            {"page": state.get("current_page_source_url", ""), "from": resolved, "to": rewritten, "raw": raw, "fallback": True},
        )
        return f"{rewritten}#{fragment}" if fragment else rewritten

    if is_internal_url(resolved, state["root_url"]):
        resolved_ext = extension_from_url(resolved)
        asset_kind = detect_asset_kind(resolved)
        if asset_kind != "file" or resolved_ext in ASSET_EXTENSIONS:
            asset = clone_asset(resolved, state, preferred_kind=asset_kind)
            if asset.get("status") == "downloaded":
                rewritten = relative_url(page_local_path, asset["local_path"])
                increment_diag(diagnostics, "links", "internal_links_seen")
                increment_diag(diagnostics, "links", "rewritten_count")
                append_diag(
                    diagnostics,
                    "links",
                    "rewritten",
                    {
                        "page": state.get("current_page_source_url", ""),
                        "from": resolved,
                        "to": rewritten,
                        "raw": raw,
                        "asset": True,
                    },
                )
                return f"{rewritten}#{fragment}" if fragment else rewritten
        # Internal URL that could not be mapped to a downloaded asset or known page.
        # Create a placeholder page so the link stays inside the clone instead of
        # routing back to the original website.
        rewritten = ensure_internal_page_target(resolved, page_local_path, state, reason="internal_unresolved_link")
        increment_diag(diagnostics, "links", "internal_links_seen")
        increment_diag(diagnostics, "links", "rewritten_count")
        append_diag(
            diagnostics,
            "links",
            "rewritten",
            {"page": state.get("current_page_source_url", ""), "from": resolved, "to": rewritten, "raw": raw, "fallback_internal": True},
        )
        return f"{rewritten}#{fragment}" if fragment else rewritten

    increment_diag(diagnostics, "links", "external_links_seen")
    return resolved + (f"#{fragment}" if fragment else "")


def rewrite_event_handler(value, page_local_path, document_base, state):
    if not value:
        return value

    rewritten = value
    replacements = []
    for original_candidate, _ in extract_quoted_urls(value, document_base):
        replacement = rewrite_navigation_target(original_candidate, page_local_path, document_base, state)
        if replacement != original_candidate:
            replacements.append((original_candidate, replacement))

    for original_candidate, replacement in replacements:
        rewritten = rewritten.replace(original_candidate, replacement)
    return rewritten


def inject_navigation_bridge(soup):
    for existing in soup.find_all("script", attrs={"data-clone-nav-bridge": "true"}):
        existing.decompose()

    bridge_script = """
    (function () {
      function toggleDropdown(target) {
        const holder = target.closest('.dropdown, .menu-item-has-children, .has-submenu, .nav-item');
        const menu = holder && holder.querySelector('.dropdown-menu, .sub-menu, .children, .submenu');
        if (!holder || !menu) return false;
        const isOpen = holder.classList.contains('show') || holder.classList.contains('open');
        holder.classList.toggle('show', !isOpen);
        holder.classList.toggle('open', !isOpen);
        menu.classList.toggle('show', !isOpen);
        menu.classList.toggle('open', !isOpen);
        target.setAttribute('aria-expanded', String(!isOpen));
        return true;
      }

      function hrefForTarget(target) {
        if (!target) return '';
        return (
          target.getAttribute('data-href') ||
          target.getAttribute('data-url') ||
          target.getAttribute('formaction') ||
          target.getAttribute('action') ||
          ''
        ).trim();
      }

      function navigateTarget(target) {
        const href = hrefForTarget(target);
        if (!href || href.startsWith('javascript:') || href.startsWith('#')) return false;
        window.location.href = href;
        return true;
      }

      function anchorActsAsToggle(anchor) {
        if (!anchor) return false;
        const href = (anchor.getAttribute('href') || '').trim().toLowerCase();
        return !href || href === '#' || href === 'javascript:void(0)' || href === 'javascript:;';
      }

      document.addEventListener('click', function (event) {
        const dropdownToggle = event.target.closest('[data-bs-toggle=\"dropdown\"], [data-toggle=\"dropdown\"], .dropdown-toggle, [aria-haspopup=\"true\"]');
        const anchorToggle = dropdownToggle && dropdownToggle.closest('a[href]');
        if (dropdownToggle && (!anchorToggle || anchorActsAsToggle(anchorToggle))) {
          event.preventDefault();
          if (toggleDropdown(dropdownToggle)) return;
        }

        const target = event.target.closest('[data-clone-clickable=\"true\"], [data-href], [data-url], [formaction], form[action]');
        if (!target) return;
        if (target.closest('a[href]')) return;
        if (target.tagName === 'BUTTON' && target.type && target.type !== 'button') return;
        if (!hrefForTarget(target)) return;
        event.preventDefault();
        navigateTarget(target);
      });

      document.addEventListener('submit', function (event) {
        const form = event.target.closest('form[action]');
        if (!form) return;
        if (!hrefForTarget(form)) return;
        event.preventDefault();
        navigateTarget(form);
      });

      document.addEventListener('keydown', function (event) {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        const target = event.target.closest('[data-clone-clickable=\"true\"]');
        if (!target) return;
        event.preventDefault();
        navigateTarget(target);
      });

      /* Handle Bootstrap 5 tabs and pill toggles */
      document.addEventListener('click', function (event) {
        var tabToggle = event.target.closest('[data-bs-toggle="tab"], [data-bs-toggle="pill"]');
        if (tabToggle) {
          event.preventDefault();
          var targetSelector = tabToggle.getAttribute('data-bs-target') || tabToggle.getAttribute('href');
          if (targetSelector && targetSelector.startsWith('#')) {
            var nav = tabToggle.closest('.nav, [role="tablist"]');
            if (nav) nav.querySelectorAll('.active, .show').forEach(function(el) { el.classList.remove('active', 'show'); });
            tabToggle.classList.add('active');
            var li = tabToggle.closest('.nav-item');
            if (li) li.classList.add('active');
            var tabContent = document.querySelector(targetSelector);
            if (tabContent) {
              var container = tabContent.parentElement;
              if (container) container.querySelectorAll('.tab-pane.active, .tab-pane.show').forEach(function(el) { el.classList.remove('active', 'show'); });
              tabContent.classList.add('active', 'show');
            }
          }
          return;
        }
        var collapseToggle = event.target.closest('[data-bs-toggle="collapse"], [data-toggle="collapse"]');
        if (collapseToggle) {
          event.preventDefault();
          var collapseTarget = collapseToggle.getAttribute('data-bs-target') || collapseToggle.getAttribute('href');
          if (collapseTarget && collapseTarget.startsWith('#')) {
            var collapseEl = document.querySelector(collapseTarget);
            if (collapseEl) {
              var isShown = collapseEl.classList.contains('show');
              collapseEl.classList.toggle('show', !isShown);
              collapseEl.classList.toggle('collapse', isShown);
              collapseToggle.classList.toggle('collapsed', isShown);
              collapseToggle.setAttribute('aria-expanded', String(!isShown));
            }
          }
        }
      });
    }());
    """

    script_tag = soup.new_tag("script")
    script_tag["data-clone-nav-bridge"] = "true"
    script_tag.string = bridge_script
    if soup.body:
        soup.body.append(script_tag)
    elif soup.html:
        soup.html.append(script_tag)
    else:
        soup.append(script_tag)


def rewrite_page_html(source_url, raw_html, page_local_path, state):
    soup = BeautifulSoup(raw_html, "html.parser")
    document_base = extract_document_base(source_url, soup)
    state["current_page_source_url"] = source_url

    for tag in soup.find_all("base"):
        tag.decompose()
    for tag in soup.find_all("meta", attrs={"http-equiv": re.compile(r"content-security-policy", re.I)}):
        tag.decompose()
    for tag in soup.find_all(attrs={"integrity": True}):
        del tag["integrity"]

    for tag in soup.find_all(True):
        if tag.name == "link":
            rel_values = [str(item).lower() for item in (tag.get("rel") or [])]
            link_type = (tag.get("type") or "").lower()
            href = tag.get("href", "").strip()
            if href:
                resolved = normalize_source_url(href, document_base)
                if resolved and ("stylesheet" in rel_values or detect_asset_kind(resolved, tag_name="link", rel_values=rel_values, as_attr=tag.get("as")) != "file"):
                    asset = clone_asset(
                        resolved,
                        state,
                        preferred_kind=detect_asset_kind(resolved, tag_name="link", rel_values=rel_values, as_attr=tag.get("as")),
                    )
                    tag["href"] = relative_url(page_local_path, asset["local_path"]) if asset.get("status") == "downloaded" else resolved
                elif any(token in link_type for token in {"rss", "xml", "json"}):
                    tag["href"] = resolved or href
                else:
                    tag["href"] = rewrite_navigation_target(href, page_local_path, document_base, state)

        if tag.name in {"a", "area"} and tag.get("href"):
            tag["href"] = rewrite_navigation_target(tag.get("href"), page_local_path, document_base, state)

        for attribute in LINK_ATTRS:
            if tag.name in {"a", "area", "link"} and attribute == "href":
                continue
            if tag.get(attribute):
                tag[attribute] = rewrite_navigation_target(tag.get(attribute), page_local_path, document_base, state)

        if tag.name == "iframe" and tag.get("src"):
            iframe_src = tag.get("src")
            resolved_iframe = normalize_source_url(iframe_src, document_base)
            if resolved_iframe and is_internal_url(resolved_iframe, state["root_url"]) and looks_like_html_page(resolved_iframe):
                tag["src"] = rewrite_navigation_target(iframe_src, page_local_path, document_base, state)

        for attribute, attr_kind in iter_asset_attributes(tag):
            if not tag.get(attribute):
                continue
            if attr_kind == "srcset":
                tag[attribute] = rewrite_srcset(tag.get(attribute), page_local_path, document_base, state)
                continue
            resolved = normalize_source_url(tag.get(attribute), document_base)
            if not resolved:
                continue
            if tag.name == "iframe" and is_internal_url(resolved, state["root_url"]) and looks_like_html_page(resolved):
                tag[attribute] = rewrite_navigation_target(tag.get(attribute), page_local_path, document_base, state)
                continue
            preferred_kind = detect_asset_kind(resolved, tag_name=tag.name)
            asset = clone_asset(resolved, state, preferred_kind=preferred_kind)
            if asset.get("status") == "downloaded":
                replacement = relative_url(page_local_path, asset["local_path"])
                tag[attribute] = replacement
                append_diag(
                    state.get("diagnostics"),
                    "assets",
                    "rewritten_references",
                    {"owner": source_url, "attribute": attribute, "from": resolved, "to": replacement},
                )
            else:
                tag[attribute] = resolved

        event_navigation_target = ""
        for attribute in EVENT_HANDLER_ATTRS:
            if tag.get(attribute):
                original_handler = tag.get(attribute)
                if not event_navigation_target:
                    script_targets = extract_navigation_script_targets(original_handler, document_base)
                    if script_targets:
                        event_navigation_target = rewrite_navigation_target(
                            script_targets[0][0],
                            page_local_path,
                            document_base,
                            state,
                        )
                rewritten_handler = rewrite_event_handler(original_handler, page_local_path, document_base, state)
                tag[attribute] = rewritten_handler

        if event_navigation_target and not any(tag.get(link_attr) for link_attr in ["href", "data-href", "data-url", "formaction", "action"]):
            if tag.name in {"a", "area"}:
                tag["href"] = event_navigation_target
            else:
                tag["data-href"] = event_navigation_target

        if any(tag.get(link_attr) for link_attr in ["data-href", "data-url", "formaction"]):
            tag["data-clone-clickable"] = "true"
            tag["tabindex"] = tag.get("tabindex") or "0"
            tag["role"] = tag.get("role") or "link"

        if tag.get("style"):
            tag["style"] = rewrite_inline_style(tag.get("style"), page_local_path, document_base, state)

        if tag.name not in {"a", "area"} and any(tag.get(link_attr) for link_attr in ["data-href", "data-url", "formaction"]):
            tag["data-clone-clickable"] = "true"
            tag["tabindex"] = tag.get("tabindex") or "0"
            tag["role"] = tag.get("role") or "link"

        if tag.name == "script" and not tag.get("src") and re.search(r"(?:window|document|top)?\.?location|open\s*\(", tag.get_text() or "", flags=re.I):
            tag.string = rewrite_script_text(tag.get_text(), page_local_path, document_base, state)

    for style_tag in soup.find_all("style"):
        style_tag.string = rewrite_inline_style(style_tag.get_text(), page_local_path, document_base, state)

    for meta_tag in soup.find_all("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)}):
        refresh_target = extract_meta_refresh_url(meta_tag.get("content", ""), document_base)
        if refresh_target and is_internal_url(refresh_target, state["root_url"]) and looks_like_html_page(refresh_target):
            content = meta_tag.get("content", "")
            rewritten_target = rewrite_navigation_target(refresh_target, page_local_path, document_base, state)
            meta_tag["content"] = re.sub(r"url\s*=\s*([^;]+)", f"url={rewritten_target}", content, flags=re.I)

    # Ensure responsive viewport meta is present for proper mobile rendering.
    head = soup.find("head")
    if head:
        if not soup.find("meta", attrs={"name": "viewport"}):
            viewport_tag = soup.new_tag("meta", attrs={"name": "viewport", "content": "width=device-width, initial-scale=1"})
            head.insert(0, viewport_tag)
        if not soup.find("meta", attrs={"charset": True}):
            charset_tag = soup.new_tag("meta", charset="utf-8")
            head.insert(0, charset_tag)

    inject_navigation_bridge(soup)
    return str(soup)


def write_bundle_manifest(bundle_root, manifest):
    manifest_path = os.path.join(bundle_root, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as output_file:
        json.dump(manifest, output_file, indent=2)
    return manifest_path


_ALREADY_COMPRESSED_EXTS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".ico",
    ".mp4", ".webm", ".mov", ".m4v", ".mp3", ".wav", ".ogg",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".zip", ".rar", ".gz", ".br",
}


def create_bundle_archive(bundle_root, archive_path=None):
    archive_path = archive_path or os.path.join(bundle_root, "clone-export.zip")
    with zipfile.ZipFile(archive_path, "w") as archive:
        for root, _, files in os.walk(bundle_root):
            for filename in files:
                full_path = os.path.join(root, filename)
                if os.path.abspath(full_path) == os.path.abspath(archive_path):
                    continue
                relative_path = os.path.relpath(full_path, bundle_root)
                ext = os.path.splitext(filename)[1].lower()
                compression = zipfile.ZIP_STORED if ext in _ALREADY_COMPRESSED_EXTS else zipfile.ZIP_DEFLATED
                archive.write(full_path, relative_path, compress_type=compression)
    return archive_path


def write_placeholder_pages(bundle_site_root, placeholder_pages):
    for info in placeholder_pages.values():
        file_path = os.path.join(bundle_site_root, *info["local_path"].split("/"))
        ensure_directory(os.path.dirname(file_path))
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Cloned Page Placeholder</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 48px; }}
    .panel {{ max-width: 760px; margin: 0 auto; background: #111827; border: 1px solid #334155; border-radius: 18px; padding: 32px; }}
    code {{ color: #7dd3fc; word-break: break-all; }}
  </style>
</head>
<body>
  <div class="panel">
    <h1>Cloned route placeholder</h1>
    <p>This internal route stayed inside the clone, but the page could not be fetched during crawling.</p>
    <p>Original URL: <code>{info['source_url']}</code></p>
    <p>Reason: <code>{info['reason']}</code></p>
  </div>
</body>
</html>"""
        with open(file_path, "w", encoding="utf-8") as output_file:
            output_file.write(html)


def default_workspace_roots(base_dir=None):
    base_dir = base_dir or os.getcwd()
    staging_root = os.path.join(base_dir, "project_assets", "staged_clones")
    saved_root = os.path.join(base_dir, "project_assets", "clone_packages")
    ensure_directory(staging_root)
    ensure_directory(saved_root)
    return staging_root, saved_root


def create_stage_directory(staging_root, stage_name):
    candidate = os.path.join(staging_root, stage_name)
    suffix = 0
    while True:
        try:
            os.makedirs(candidate)
            return candidate
        except FileExistsError:
            suffix += 1
            candidate = os.path.join(staging_root, f"{stage_name}-{suffix:02d}")


def clone_site_bundle(root_url, base_dir=None, max_pages=DEFAULT_MAX_PAGES, max_depth=DEFAULT_MAX_DEPTH, progress_callback=None):
    staging_root, _ = default_workspace_roots(base_dir)
    normalized_root = normalize_source_url(root_url)
    if not normalized_root:
        raise ValueError("Invalid URL supplied for cloning.")
    diagnostics = build_diagnostics(normalized_root, max_pages, max_depth)

    stage_name = (
        f"{slugify(urlparse(normalized_root).netloc)[:18]}-"
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}-"
        f"{hashlib.sha1(normalized_root.encode('utf-8')).hexdigest()[:8]}"
    )
    stage_dir = create_stage_directory(staging_root, stage_name)

    session = requests.Session()
    session.trust_env = False
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    adapter = HTTPAdapter(pool_connections=ASSET_PREFETCH_WORKERS * 2, pool_maxsize=ASSET_PREFETCH_WORKERS * 2, max_retries=1)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    emit_progress(
        progress_callback,
        phase="start",
        root_url=normalized_root,
        current_url=normalized_root,
        max_pages=max_pages,
        max_depth=max_depth,
    )

    pages, crawl_order = crawl_site_pages(
        normalized_root,
        session,
        max_pages=max_pages,
        max_depth=max_depth,
        diagnostics=diagnostics,
        progress_callback=progress_callback,
    )
    if not pages:
        shutil.rmtree(stage_dir, ignore_errors=True)
        raise ValueError("Unable to fetch any HTML pages from the target website.")

    if normalized_root not in pages:
        normalized_root = crawl_order[0]

    used_paths = set()
    page_map = {}
    page_aliases = {}
    for source_url in crawl_order:
        page_info = {"source_url": source_url, "local_path": build_page_output_path(source_url, used_paths)}
        page_map[source_url] = page_info
        register_page_aliases(page_aliases, source_url, page_info)

    bundle_site_root = os.path.join(stage_dir, "site")
    ensure_directory(bundle_site_root)
    state = {
        "root_url": normalized_root,
        "session": session,
        "bundle_root": bundle_site_root,
        "page_map": page_map,
        "page_aliases": page_aliases,
        "asset_cache": {},
        "asset_hash_index": {},
        "placeholder_pages": {},
        "diagnostics": diagnostics,
        "used_paths": used_paths,
        "progress": {
            "callback": progress_callback,
            "pages_total": len(crawl_order),
            "pages_rewritten": 0,
            "assets_downloaded": 0,
            "assets_deduplicated": 0,
            "assets_failed": 0,
            "assets_external": 0,
        },
        "prefetched_payloads": {},
    }

    asset_requests = {}
    for source_url in crawl_order:
        asset_requests.update(pages[source_url].get("asset_requests") or collect_page_asset_requests(pages[source_url]["html"], source_url))
    prefetch_assets(asset_requests, state)

    emit_state_progress(
        state,
        "rewrite",
        current_url=normalized_root,
        pages_crawled=len(crawl_order),
        queue_size=0,
        backlog_size=0,
    )

    page_records = []
    for source_url in crawl_order:
        page = pages[source_url]
        raw_html = page["html"]
        if not raw_html or not raw_html.strip():
            continue
        local_path = page_map[source_url]["local_path"]
        rewritten_html = rewrite_page_html(source_url, raw_html, local_path, state)
        if not rewritten_html or not rewritten_html.strip():
            continue
        file_path = os.path.join(bundle_site_root, *local_path.split("/"))
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, "w", encoding="utf-8") as output_file:
            output_file.write(rewritten_html)
        page_records.append({"source_url": source_url, "local_path": local_path, "title": page.get("title", urlparse(source_url).path or "/")})
        state["progress"]["pages_rewritten"] += 1
        emit_state_progress(
            state,
            "rewrite",
            current_url=source_url,
            pages_crawled=len(crawl_order),
        )

    if state["placeholder_pages"]:
        write_placeholder_pages(bundle_site_root, state["placeholder_pages"])
        for source_url, info in state["placeholder_pages"].items():
            page_records.append({"source_url": source_url, "local_path": info["local_path"], "title": "Placeholder route"})

    unique_assets = {
        item["local_path"]: item
        for item in state["asset_cache"].values()
        if item.get("local_path")
    }
    manifest = {
        "source_url": normalized_root,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "page_count": len(page_records),
        "asset_count": len(unique_assets),
        "pages": page_records,
        "assets": [
            {
                "source_url": asset["source_url"],
                "local_path": asset["local_path"],
                "kind": asset["kind"],
                "status": asset["status"],
                "content_type": asset.get("content_type", ""),
                "size": asset.get("size", 0),
                "hash": asset.get("hash", ""),
            }
            for asset in unique_assets.values()
        ],
        "route_map": {source_url: info["local_path"] for source_url, info in page_map.items()},
        "diagnostics": diagnostics,
        "settings": {"max_pages": max_pages, "max_depth": max_depth, "domain": normalized_host(normalized_root)},
    }
    manifest_path = write_bundle_manifest(stage_dir, manifest)
    emit_state_progress(state, "archive", current_url=normalized_root)
    archive_path = create_bundle_archive(stage_dir)

    entry_local_path = page_map[normalized_root]["local_path"]
    entry_html_path = os.path.join(bundle_site_root, *entry_local_path.split("/"))
    with open(entry_html_path, "r", encoding="utf-8") as input_file:
        entry_html = input_file.read()

    result = {
        "bundle_dir": stage_dir,
        "site_dir": bundle_site_root,
        "archive_path": archive_path,
        "manifest_path": manifest_path,
        "entry_html": entry_html,
        "source_entry_html": pages[normalized_root]["html"],
        "entry_local_path": entry_local_path,
        "page_count": len(page_records),
        "asset_count": len(manifest["assets"]),
        "pages": page_records,
        "assets": manifest["assets"],
        "route_map": manifest["route_map"],
    }
    emit_progress(
        progress_callback,
        phase="complete",
        root_url=normalized_root,
        current_url=normalized_root,
        pages_total=len(crawl_order),
        pages_rewritten=state["progress"]["pages_rewritten"],
        assets_downloaded=state["progress"]["assets_downloaded"],
        assets_deduplicated=state["progress"]["assets_deduplicated"],
        assets_failed=state["progress"]["assets_failed"],
        assets_external=state["progress"]["assets_external"],
        page_count=result["page_count"],
        asset_count=result["asset_count"],
    )
    return result


def get_saved_bundle_dir(site_id, base_dir=None):
    _, saved_root = default_workspace_roots(base_dir)
    return os.path.join(saved_root, f"site_{int(site_id)}")


def get_saved_bundle_site_dir(site_id, base_dir=None):
    return os.path.join(get_saved_bundle_dir(site_id, base_dir), "site")


def get_saved_bundle_archive(site_id, base_dir=None):
    return os.path.join(get_saved_bundle_dir(site_id, base_dir), "clone-export.zip")


def get_saved_bundle_manifest(site_id, base_dir=None):
    return os.path.join(get_saved_bundle_dir(site_id, base_dir), "manifest.json")


def persist_bundle_for_site(site_id, staged_bundle_dir, base_dir=None):
    destination_dir = get_saved_bundle_dir(site_id, base_dir)
    if os.path.isdir(destination_dir):
        shutil.rmtree(destination_dir)
    shutil.copytree(staged_bundle_dir, destination_dir)
    return destination_dir


def load_bundle_manifest(site_id, base_dir=None):
    manifest_path = get_saved_bundle_manifest(site_id, base_dir)
    if not os.path.exists(manifest_path):
        return {}
    with open(manifest_path, "r", encoding="utf-8") as input_file:
        return json.load(input_file)


def prefix_preview_paths(html, site_id):
    prefix = f"/clone/{int(site_id)}/"
    soup = BeautifulSoup(html, "html.parser")

    def prefix_value(value):
        raw = str(value or "").strip()
        if not raw or raw.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "data:", "#", "//", "/clone/", "/staged-clone/")):
            return raw
        # Handle root-relative paths (e.g., /assets/style.css)
        if raw.startswith("/"):
            return prefix + raw.lstrip("/")
        normalized = raw.lstrip("./")
        return prefix + normalized

    def prefix_srcset(value):
        rebuilt = []
        for item in str(value or "").split(","):
            token = item.strip()
            if not token:
                continue
            parts = token.split()
            parts[0] = prefix_value(parts[0])
            rebuilt.append(" ".join(parts))
        return ", ".join(rebuilt)

    def prefix_css_urls(css_text):
        def replace_url(match):
            raw_value = match.group(1).strip().strip("\"'")
            if raw_value.startswith(("http://", "https://", "data:", "#", "/clone/")):
                return match.group(0)
            return f'url("{prefix_value(raw_value)}")'

        return CSS_URL_PATTERN.sub(replace_url, css_text)

    for tag in soup.find_all(True):
        for attribute in ASSET_ATTRS + LINK_ATTRS:
            if tag.get(attribute):
                tag[attribute] = prefix_value(tag.get(attribute))
        for attribute in SRCSET_ATTRS:
            if tag.get(attribute):
                tag[attribute] = prefix_srcset(tag.get(attribute))
        for attribute in EVENT_HANDLER_ATTRS:
            if tag.get(attribute):
                rewritten = tag.get(attribute)
                for original_candidate, _ in extract_navigation_script_targets(rewritten, "http://preview.local/"):
                    rewritten = rewritten.replace(original_candidate, prefix_value(original_candidate))
                tag[attribute] = rewritten
        if tag.get("style"):
            tag["style"] = prefix_css_urls(tag.get("style"))

    for style_tag in soup.find_all("style"):
        style_tag.string = prefix_css_urls(style_tag.get_text())

    return str(soup)


def strip_preview_paths(html, site_id):
    prefix = f"/clone/{int(site_id)}/"
    soup = BeautifulSoup(html, "html.parser")

    def strip_value(value):
        raw = str(value or "")
        return raw[len(prefix):] if raw.startswith(prefix) else raw

    def strip_srcset(value):
        rebuilt = []
        for item in str(value or "").split(","):
            token = item.strip()
            if not token:
                continue
            parts = token.split()
            parts[0] = strip_value(parts[0])
            rebuilt.append(" ".join(parts))
        return ", ".join(rebuilt)

    def strip_css_urls(css_text):
        def replace_url(match):
            raw_value = match.group(1).strip().strip("\"'")
            stripped = strip_value(raw_value)
            return f'url("{stripped}")' if stripped != raw_value else match.group(0)

        return CSS_URL_PATTERN.sub(replace_url, css_text)

    for tag in soup.find_all(True):
        for attribute in ASSET_ATTRS + LINK_ATTRS:
            if tag.get(attribute):
                tag[attribute] = strip_value(tag.get(attribute))
        for attribute in SRCSET_ATTRS:
            if tag.get(attribute):
                tag[attribute] = strip_srcset(tag.get(attribute))
        for attribute in EVENT_HANDLER_ATTRS:
            if tag.get(attribute):
                tag[attribute] = tag.get(attribute).replace(prefix, "")
        if tag.get("style"):
            tag["style"] = strip_css_urls(tag.get("style"))

    for style_tag in soup.find_all("style"):
        style_tag.string = strip_css_urls(style_tag.get_text())

    return str(soup)


def update_saved_bundle_entry(site_id, html, base_dir=None):
    manifest = load_bundle_manifest(site_id, base_dir)
    entry_path = (manifest.get("route_map") or {}).get(manifest.get("source_url"), "index.html")
    site_dir = get_saved_bundle_site_dir(site_id, base_dir)
    file_path = os.path.join(site_dir, *entry_path.split("/"))
    if not os.path.exists(file_path):
        return False
    ensure_directory(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as output_file:
        output_file.write(strip_preview_paths(html, site_id))
    create_bundle_archive(get_saved_bundle_dir(site_id, base_dir), get_saved_bundle_archive(site_id, base_dir))
    return True


def _is_garbled_html(text):
    if not text or len(text) < 20:
        return False
    replacements = text.count("\ufffd")
    if replacements / max(len(text), 1) > 0.03:
        return True
    # Check for extremely low ratio of recognizable HTML characters
    printable = sum(1 for ch in text[:500] if ch.isprintable() or ch in "\n\r\t")
    if printable / min(len(text), 500) < 0.5:
        return True
    return False


def load_saved_bundle_entry(site_id, base_dir=None, preview=False):
    manifest = load_bundle_manifest(site_id, base_dir)
    entry_path = (manifest.get("route_map") or {}).get(manifest.get("source_url"), "index.html")
    file_path = os.path.join(get_saved_bundle_site_dir(site_id, base_dir), *entry_path.split("/"))
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as input_file:
            html = input_file.read()
    except (UnicodeDecodeError, ValueError):
        return ""
    if _is_garbled_html(html):
        return ""
    return prefix_preview_paths(html, site_id) if preview else html
