import hashlib
import json
import mimetypes
import os
import re
from collections import Counter
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


SITE_PATTERNS = {
    "ecommerce": [
        "add to cart",
        "buy now",
        "shop now",
        "product",
        "checkout",
        "price",
        "sku",
        "wishlist",
        "sale",
        "category",
        "shipping",
    ],
    "restaurant": [
        "menu",
        "reservation",
        "book a table",
        "chef",
        "order online",
        "our dishes",
        "drinks",
    ],
    "portfolio": [
        "portfolio",
        "case study",
        "selected work",
        "my work",
        "projects",
        "clients",
        "creative",
    ],
    "blog": [
        "blog",
        "latest posts",
        "read more",
        "article",
        "category",
        "author",
        "news",
    ],
    "education": [
        "course",
        "curriculum",
        "enroll",
        "students",
        "syllabus",
        "class",
        "faculty",
        "admission",
        "department",
        "campus",
    ],
    "saas": [
        "pricing",
        "features",
        "dashboard",
        "free trial",
        "integrations",
        "get started",
        "platform",
    ],
    "real_estate": [
        "property",
        "listing",
        "bedroom",
        "bathroom",
        "sqft",
        "agent",
        "rent",
    ],
    "agency": [
        "services",
        "our team",
        "strategy",
        "campaign",
        "clients",
        "contact us",
        "branding",
    ],
}

MEDIA_ATTRS = [
    "src",
    "data-src",
    "data-original",
    "data-lazy-src",
    "data-srcset",
    "srcset",
    "poster",
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".avif"}
SVG_EXTENSIONS = {".svg"}
ICON_HINTS = ("logo", "icon", "favicon", "brand", "seal", "badge")
LAZY_ATTRS = [
    "data-src",
    "data-lazy-src",
    "data-original",
    "data-bg",
    "data-background-image",
    "data-image",
]


def slugify(value):
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return cleaned or "item"


def normalize_text(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def unique_preserve_order(items):
    seen = set()
    ordered = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def safe_attr_token(value):
    token = re.sub(r"[^a-zA-Z0-9_-]+", "", value or "")
    return token[:64]


def truncate(value, limit):
    value = str(value or "").strip()
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def parse_srcset(srcset_value, base_url):
    candidates = []
    if not srcset_value:
        return candidates

    for item in srcset_value.split(","):
        token = item.strip()
        if not token:
            continue
        parts = token.split()
        resolved = resolve_candidate_url(base_url, parts[0])
        if resolved:
            candidates.append(resolved)
    return unique_preserve_order(candidates)


def extract_urls_from_css(css_text, base_url):
    urls = []
    if not css_text:
        return urls

    for match in re.findall(r"url\(([^)]+)\)", css_text, flags=re.I):
        cleaned = match.strip().strip("\"'")
        resolved = resolve_candidate_url(base_url, cleaned)
        if resolved:
            urls.append(resolved)
    return unique_preserve_order(urls)


def resolve_candidate_url(base_url, candidate):
    if not candidate:
        return ""
    candidate = candidate.strip().strip("\"'")
    if not candidate or candidate.startswith(("javascript:", "mailto:", "tel:", "#")):
        return ""
    if candidate.startswith("data:"):
        return candidate
    return urljoin(base_url, candidate)


def extension_from_url(url):
    path = urlparse(url).path if url else ""
    _, ext = os.path.splitext(path)
    return ext.lower()


def guess_media_type(url="", mime_type="", tag_name="", rel_values=None, context=""):
    rel_values = rel_values or []
    mime_type = (mime_type or "").lower()
    ext = extension_from_url(url)
    context_text = f"{tag_name} {' '.join(rel_values)} {context}".lower()

    if "audio" in mime_type or tag_name == "audio" or ext in {".mp3", ".wav", ".ogg", ".m4a"}:
        return "audio"
    if "video" in mime_type or tag_name == "video" or ext in {".mp4", ".webm", ".mov", ".m3u8"}:
        return "video"
    if "svg" in mime_type or ext in SVG_EXTENSIONS or tag_name == "svg":
        return "svg"
    if "icon" in context_text or any(rel in {"icon", "shortcut icon", "apple-touch-icon", "mask-icon"} for rel in rel_values):
        return "icon"
    if ext in IMAGE_EXTENSIONS or "image" in mime_type or tag_name in {"img", "source"}:
        return "image"
    if ext in {".ico"}:
        return "icon"
    return "file"


def default_extension_for_type(media_type, mime_type):
    guessed = mimetypes.guess_extension((mime_type or "").split(";")[0].strip())
    if guessed:
        return guessed
    mapping = {
        "image": ".png",
        "icon": ".ico",
        "svg": ".svg",
        "video": ".mp4",
        "audio": ".mp3",
    }
    return mapping.get(media_type, ".bin")


def collect_visible_text(soup):
    text_chunks = []
    for node in soup.find_all(string=True):
        parent_name = getattr(node.parent, "name", "")
        if parent_name in {"script", "style", "noscript"}:
            continue
        text = re.sub(r"\s+", " ", str(node)).strip()
        if text:
            text_chunks.append(text)
    return text_chunks


def collect_text_signals(soup):
    text_chunks = [
        tag.get_text(" ", strip=True)
        for tag in soup.find_all(["title", "h1", "h2", "h3", "a", "button", "p", "span", "label", "li"])
    ]
    return " ".join(chunk for chunk in text_chunks if chunk)


def build_element_selector(element):
    parts = []
    current = element
    depth = 0

    while current and getattr(current, "name", None) and current.name != "[document]" and depth < 5:
        name = current.name
        element_id = safe_attr_token(current.get("id"))
        if element_id:
            parts.append(f"{name}#{element_id}")
            break

        classes = [safe_attr_token(cls) for cls in current.get("class", []) if safe_attr_token(cls)]
        class_suffix = "".join(f".{cls}" for cls in classes[:2])
        same_tag_siblings = [sib for sib in current.parent.find_all(current.name, recursive=False)] if current.parent else []
        position = ""
        if len(same_tag_siblings) > 1 and not class_suffix:
            try:
                position = f":nth-of-type({same_tag_siblings.index(current) + 1})"
            except ValueError:
                position = ""

        parts.append(f"{name}{class_suffix}{position}")
        current = current.parent
        depth += 1

    return " > ".join(reversed(parts))


def determine_section_type(candidate):
    signature = " ".join(
        [
            candidate.name or "",
            candidate.get("id", ""),
            " ".join(candidate.get("class", [])),
            candidate.get_text(" ", strip=True)[:180],
        ]
    ).lower()
    for label in [
        "hero",
        "banner",
        "gallery",
        "slider",
        "testimonial",
        "footer",
        "header",
        "contact",
        "about",
        "course",
        "product",
        "faq",
        "admission",
        "faculty",
    ]:
        if label in signature:
            return label
    return "content"


def build_section_key(candidate, index):
    title_tag = candidate.find(["h1", "h2", "h3"])
    base = candidate.get("id") or " ".join(candidate.get("class", [])[:2]) or (title_tag.get_text(" ", strip=True) if title_tag else "")
    return slugify(base or f"section_{index}")


def extract_sections(soup, media_assets):
    section_candidates = []
    for candidate in soup.find_all(["header", "section", "main", "article", "footer"]):
        section_candidates.append(candidate)

    for candidate in soup.find_all("div"):
        signature = " ".join([candidate.get("id", ""), " ".join(candidate.get("class", []))]).lower()
        if re.search(r"hero|banner|section|gallery|slider|testimonial|about|contact|course|product|feature|faculty|admission", signature):
            section_candidates.append(candidate)

    sections = []
    seen_selectors = set()
    for index, candidate in enumerate(section_candidates, start=1):
        selector = build_element_selector(candidate)
        if selector in seen_selectors:
            continue

        text_length = len(candidate.get_text(" ", strip=True))
        media_count = len(candidate.find_all(["img", "video", "audio", "svg"]))
        heading = candidate.find(["h1", "h2", "h3"])
        if text_length < 40 and media_count == 0 and not heading:
            continue

        seen_selectors.add(selector)
        section_key = build_section_key(candidate, index)
        paragraph = candidate.find("p")
        summary = paragraph.get_text(" ", strip=True) if paragraph else candidate.get_text(" ", strip=True)
        section_asset_urls = []
        background_url = ""
        for asset in media_assets:
            for usage in asset.get("usage", []):
                if usage.get("sectionKey") == section_key:
                    section_asset_urls.append(asset.get("file_url") or asset.get("original_url"))
                    if usage.get("kind") == "background" and not background_url:
                        background_url = asset.get("file_url") or asset.get("original_url")

        primary_media_url = next((url for url in section_asset_urls if url), "")
        sections.append(
            {
                "section_key": section_key,
                "selector": selector,
                "section_type": determine_section_type(candidate),
                "title": heading.get_text(" ", strip=True) if heading else section_key.replace("_", " ").title(),
                "summary": truncate(summary, 260),
                "primary_media_url": primary_media_url,
                "background_media_url": background_url,
                "media_urls_json": json.dumps(unique_preserve_order([url for url in section_asset_urls if url])[:10]),
                "display_order": len(sections) + 1,
                "visible": True,
            }
        )

        if len(sections) >= 24:
            break

    return sections


def closest_section_context(element):
    current = element
    depth = 0
    while current and getattr(current, "name", None) and depth < 6:
        if current.name in {"header", "section", "main", "article", "footer"}:
            return build_section_key(current, 0), build_element_selector(current)
        signature = " ".join([current.get("id", ""), " ".join(current.get("class", []))]).lower()
        if re.search(r"hero|banner|section|gallery|slider|testimonial|about|contact|feature|course|product|faculty|admission", signature):
            return build_section_key(current, 0), build_element_selector(current)
        current = current.parent
        depth += 1
    return "", ""


def fetch_stylesheet_text(url, session):
    try:
        response = session.get(url, timeout=12)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "css" not in content_type and not url.lower().endswith(".css"):
            return ""
        return response.text
    except Exception:
        return ""


def add_usage(asset, element, attribute, kind):
    selector = build_element_selector(element)
    section_key, section_selector = closest_section_context(element)
    usage = {
        "selector": selector,
        "attribute": attribute,
        "kind": kind,
        "sectionKey": section_key,
        "sectionSelector": section_selector,
        "tag": element.name,
    }
    signature = json.dumps(usage, sort_keys=True)
    existing_signatures = asset.setdefault("_usage_signatures", set())
    if signature not in existing_signatures:
        existing_signatures.add(signature)
        asset.setdefault("usage", []).append(usage)
        if not asset.get("section_key") and section_key:
            asset["section_key"] = section_key


def asset_original_name(url, media_type, index):
    if url.startswith("data:"):
        return f"embedded-{media_type}-{index}"
    path = urlparse(url).path
    basename = os.path.basename(path)
    return basename or f"{media_type}-{index}"


def extract_media_assets(base_url, html, site_id=None, media_output_dir=None):
    soup = BeautifulSoup(html, "html.parser")
    session = requests.Session()
    asset_map = {}
    stylesheet_urls = []

    def register_asset(url, element, attribute, media_type="", mime_type="", rel_values=None, context=""):
        rel_values = rel_values or []
        original_url = url or ""
        if element and attribute:
            preserved_attr = f"data-fabricator-original-{attribute.replace('_', '-')}"
            original_url = element.get(preserved_attr) or original_url

        if attribute in {"srcset", "data-srcset"}:
            candidates = parse_srcset(original_url, base_url)
        else:
            candidates = [resolve_candidate_url(base_url, original_url)]

        for candidate in candidates:
            if not candidate:
                continue

            candidate_type = media_type or guess_media_type(
                url=candidate,
                mime_type=mime_type,
                tag_name=getattr(element, "name", ""),
                rel_values=rel_values,
                context=context,
            )
            if candidate_type == "file":
                continue

            asset_key = hashlib.sha1(f"url:{candidate}".encode("utf-8")).hexdigest()
            asset = asset_map.setdefault(
                asset_key,
                {
                    "asset_key": asset_key,
                    "original_url": candidate,
                    "original_name": asset_original_name(candidate, candidate_type, len(asset_map) + 1),
                    "media_type": candidate_type,
                    "mime_type": mime_type or mimetypes.guess_type(candidate)[0] or "",
                    "alt_text": "",
                    "width": None,
                    "height": None,
                    "source_kind": "clone",
                    "usage": [],
                    "status": "ready",
                    "download_status": "pending",
                    "file_url": "",
                    "filename": "",
                    "local_path": "",
                    "metadata": {
                        "rel": rel_values,
                        "context": context,
                    },
                    "section_key": "",
                },
            )

            if element:
                if element.get("alt") and not asset.get("alt_text"):
                    asset["alt_text"] = truncate(element.get("alt"), 200)
                if element.get("width") and not asset.get("width"):
                    try:
                        asset["width"] = int(str(element.get("width")).replace("px", "").strip())
                    except ValueError:
                        pass
                if element.get("height") and not asset.get("height"):
                    try:
                        asset["height"] = int(str(element.get("height")).replace("px", "").strip())
                    except ValueError:
                        pass
                add_usage(asset, element, attribute, "background" if attribute == "style" else candidate_type)

    for tag in soup.find_all(["img", "source", "video", "audio", "link"]):
        if tag.name == "link":
            rel_values = [value.lower() for value in tag.get("rel", [])]
            href = tag.get("href") or tag.get("data-href") or ""
            if not href:
                continue
            if "stylesheet" in rel_values:
                stylesheet_url = resolve_candidate_url(base_url, href)
                if stylesheet_url:
                    stylesheet_urls.append(stylesheet_url)
                continue
            register_asset(href, tag, "href", rel_values=rel_values, context=" ".join(rel_values))
            continue

        for attribute in MEDIA_ATTRS + LAZY_ATTRS:
            if tag.get(attribute):
                register_asset(tag.get(attribute), tag, attribute)

        if tag.name == "video" and tag.get("poster"):
            register_asset(tag.get("poster"), tag, "poster", media_type="image", context="video poster")

    for element in soup.find_all(attrs={"style": True}):
        for css_url in extract_urls_from_css(element.get("style"), base_url):
            register_asset(css_url, element, "style", context="inline style background")

    for style_tag in soup.find_all("style"):
        for css_url in extract_urls_from_css(style_tag.get_text(" ", strip=True), base_url):
            css_media_type = guess_media_type(url=css_url, tag_name="style", context="stylesheet background")
            if css_media_type == "file":
                continue
            asset_key = hashlib.sha1(f"url:{css_url}".encode("utf-8")).hexdigest()
            asset = asset_map.setdefault(
                asset_key,
                {
                    "asset_key": asset_key,
                    "original_url": css_url,
                    "original_name": asset_original_name(css_url, "image", len(asset_map) + 1),
                    "media_type": css_media_type,
                    "mime_type": mimetypes.guess_type(css_url)[0] or "",
                    "alt_text": "",
                    "width": None,
                    "height": None,
                    "source_kind": "clone",
                    "usage": [],
                    "status": "ready",
                    "download_status": "pending",
                    "file_url": "",
                    "filename": "",
                    "local_path": "",
                    "metadata": {
                        "context": "inline stylesheet background",
                    },
                    "section_key": "",
                },
            )
            asset.setdefault("usage", []).append(
                {
                    "selector": "style",
                    "attribute": "stylesheet",
                    "kind": "background",
                    "sectionKey": "",
                    "sectionSelector": "",
                    "tag": "style",
                }
            )

    for stylesheet_url in unique_preserve_order(stylesheet_urls)[:18]:
        css_text = fetch_stylesheet_text(stylesheet_url, session)
        if not css_text:
            continue
        for css_url in extract_urls_from_css(css_text, stylesheet_url):
            css_media_type = guess_media_type(url=css_url, tag_name="style", context="linked stylesheet background")
            if css_media_type == "file":
                continue
            asset_key = hashlib.sha1(f"url:{css_url}".encode("utf-8")).hexdigest()
            asset = asset_map.setdefault(
                asset_key,
                {
                    "asset_key": asset_key,
                    "original_url": css_url,
                    "original_name": asset_original_name(css_url, "image", len(asset_map) + 1),
                    "media_type": css_media_type,
                    "mime_type": mimetypes.guess_type(css_url)[0] or "",
                    "alt_text": "",
                    "width": None,
                    "height": None,
                    "source_kind": "clone",
                    "usage": [],
                    "status": "ready",
                    "download_status": "pending",
                    "file_url": "",
                    "filename": "",
                    "local_path": "",
                    "metadata": {
                        "context": "linked stylesheet background",
                        "stylesheetUrl": stylesheet_url,
                    },
                    "section_key": "",
                },
            )
            asset.setdefault("usage", []).append(
                {
                    "selector": "style",
                    "attribute": "stylesheet",
                    "kind": "background",
                    "sectionKey": "",
                    "sectionSelector": "",
                    "tag": "style",
                }
            )

    for index, svg in enumerate(soup.find_all("svg"), start=1):
        svg_markup = str(svg)
        asset_key = hashlib.sha1(f"inline-svg:{svg_markup}".encode("utf-8")).hexdigest()
        asset = asset_map.setdefault(
            asset_key,
            {
                "asset_key": asset_key,
                "original_url": f"inline-svg://{asset_key}",
                "original_name": f"inline-svg-{index}.svg",
                "media_type": "svg",
                "mime_type": "image/svg+xml",
                "alt_text": "",
                "width": None,
                "height": None,
                "source_kind": "clone",
                "usage": [],
                "status": "ready",
                "download_status": "pending",
                "file_url": "",
                "filename": "",
                "local_path": "",
                "metadata": {
                    "inlineSvg": svg_markup,
                },
                "section_key": "",
            },
        )
        add_usage(asset, svg, "inline_svg", "svg")

    media_assets = list(asset_map.values())
    for asset in media_assets:
        asset.pop("_usage_signatures", None)
        materialize_media_asset(asset, site_id, media_output_dir, session)

    media_assets.sort(key=lambda item: (item.get("media_type", ""), item.get("original_name", "")))
    return media_assets


def materialize_media_asset(asset, site_id, media_output_dir, session):
    original_url = asset.get("original_url", "")
    media_type = asset.get("media_type", "image")
    mime_type = asset.get("mime_type", "")
    downloaded_bytes = None

    if asset.get("metadata", {}).get("inlineSvg"):
        downloaded_bytes = asset["metadata"]["inlineSvg"].encode("utf-8")
        mime_type = "image/svg+xml"
    elif not site_id or not media_output_dir:
        asset["file_url"] = original_url
        asset["download_status"] = "external_reference"
        return
    elif original_url.startswith("data:"):
        asset["file_url"] = original_url
        asset["download_status"] = "embedded_reference"
        return
    else:
        try:
            response = session.get(original_url, timeout=15, stream=True)
            response.raise_for_status()
            mime_type = response.headers.get("content-type", mime_type or "")
            total_size = 0
            chunks = []
            for chunk in response.iter_content(16384):
                if not chunk:
                    continue
                total_size += len(chunk)
                if total_size > 12 * 1024 * 1024:
                    chunks = []
                    break
                chunks.append(chunk)
            if chunks:
                downloaded_bytes = b"".join(chunks)
        except Exception:
            downloaded_bytes = None

    if downloaded_bytes is None:
        asset["file_url"] = original_url
        asset["download_status"] = "external_reference"
        asset["mime_type"] = mime_type
        asset["hash"] = hashlib.sha1(original_url.encode("utf-8")).hexdigest()
        return

    os.makedirs(media_output_dir, exist_ok=True)
    extension = extension_from_url(original_url)
    if not extension or extension == ".php":
        extension = default_extension_for_type(media_type, mime_type)
    content_hash = hashlib.sha1(downloaded_bytes).hexdigest()
    filename = f"{content_hash[:20]}{extension}"
    local_path = os.path.join(media_output_dir, filename)

    if not os.path.exists(local_path):
        with open(local_path, "wb") as output_file:
            output_file.write(downloaded_bytes)

    asset["filename"] = filename
    asset["local_path"] = local_path
    asset["file_url"] = f"/media/{site_id}/{filename}"
    asset["download_status"] = "downloaded"
    asset["mime_type"] = mime_type
    asset["hash"] = content_hash


def localize_clone_html(html, media_assets):
    soup = BeautifulSoup(html, "html.parser")
    replacements = {
        asset["original_url"]: asset.get("file_url") or asset["original_url"]
        for asset in media_assets
        if asset.get("file_url")
    }

    def replace_attr_value(tag, attribute):
        value = tag.get(attribute)
        if not value:
            return
        preserved_attr = f"data-fabricator-original-{attribute.replace('_', '-')}"
        original_value = tag.get(preserved_attr) or value
        if attribute in {"srcset", "data-srcset"}:
            rebuilt = []
            for item in original_value.split(","):
                token = item.strip()
                if not token:
                    continue
                pieces = token.split()
                source_url = pieces[0]
                replacement = replacements.get(source_url) or replacements.get(resolve_candidate_url("", source_url)) or source_url
                rebuilt.append(" ".join([replacement] + pieces[1:]))
            tag[attribute] = ", ".join(rebuilt)
        else:
            resolved_original = resolve_candidate_url("", original_value) or original_value
            replacement = replacements.get(resolved_original) or replacements.get(original_value) or resolved_original
            tag[attribute] = replacement
        tag[preserved_attr] = original_value

    for tag in soup.find_all(["img", "source", "video", "audio", "link"]):
        for attribute in ["src", "href", "poster", "data-src", "data-original", "data-lazy-src", "srcset", "data-srcset"]:
            if tag.get(attribute):
                replace_attr_value(tag, attribute)

    for tag in soup.find_all(attrs={"style": True}):
        original_style = tag.get("data-fabricator-original-style") or tag["style"]
        localized_style = original_style
        for original_url, replacement in replacements.items():
            localized_style = localized_style.replace(original_url, replacement)
        tag["style"] = localized_style
        tag["data-fabricator-original-style"] = original_style

    return str(soup)


def inject_clone_bridge(html, site_id, api_base_url=None):
    soup = BeautifulSoup(html, "html.parser")
    for existing in soup.find_all("script", attrs={"data-fabricator-bridge": "true"}):
        existing.decompose()

    api_base_value = json.dumps((api_base_url or "").rstrip("/"))

    bridge_script = f"""
    (function() {{
      const siteId = {int(site_id)};
      const configuredApiBase = {api_base_value};
      const THEME_STYLE_SELECTOR = 'style[data-fabricator-theme="true"]';
      const resolveApiBase = () => {{
        if (configuredApiBase) {{
          return configuredApiBase;
        }}
        if (window.location.origin && window.location.origin !== 'null') {{
          return window.location.origin;
        }}
        return 'http://127.0.0.1:5001';
      }};
      const apiBase = resolveApiBase();
      const cloneBase = (() => {{
        const path = window.location.pathname || '/';
        const clonePrefix = `/clone/${{siteId}}/`;
        if (path.startsWith(clonePrefix)) {{
          return clonePrefix;
        }}
        if (path.startsWith('/site/')) {{
          return '/site/';
        }}
        return '/';
      }})();
      const resolveCloneUrl = (value) => {{
        const raw = `${{value || ''}}`.trim();
        if (!raw) {{
          return '';
        }}
        if (/^(?:https?:|mailto:|tel:|javascript:|data:|#)/i.test(raw)) {{
          return raw;
        }}
        const clonePrefix = `/clone/${{siteId}}/`;
        if (raw.startsWith(clonePrefix) || raw.startsWith('/site/')) {{
          return raw;
        }}
        return `${{cloneBase}}${{raw.replace(/^\\/+/, '')}}`;
      }};
      const currentClonePath = (() => {{
        const path = window.location.pathname || '/';
        const clonePrefix = `/clone/${{siteId}}/`;
        if (path.startsWith(clonePrefix)) {{
          return '/' + path.slice(clonePrefix.length).replace(/^\\/+/, '');
        }}
        if (path.startsWith('/site/')) {{
          return '/' + path.slice('/site/'.length).replace(/^\\/+/, '');
        }}
        return path || '/';
      }})();
      const parseResponse = async (path) => {{
        try {{
          const response = await fetch(`${{apiBase}}${{path}}`);
          if (!response.ok) {{
            return [];
          }}
          return await response.json();
        }} catch (error) {{
          return [];
        }}
      }};

      const setMediaSource = (element, value) => {{
        if (!element || !value) {{
          return;
        }}
        ['src', 'data-src', 'data-lazy-src', 'data-lazyload', 'data-original'].forEach((attribute) => {{
          if (element.hasAttribute(attribute) || attribute === 'src') {{
            element.setAttribute(attribute, value);
          }}
        }});
        ['srcset', 'data-srcset', 'data-lazy-srcset'].forEach((attribute) => {{
          if (element.hasAttribute(attribute)) {{
            element.setAttribute(attribute, value);
          }}
        }});
        if (element.tagName === 'VIDEO') {{
          element.setAttribute('poster', value);
        }}
      }};

      const applyBackgroundMedia = (element, value) => {{
        if (!element || !value) {{
          return;
        }}
        element.style.backgroundImage = `url("${{value}}")`;
      }};

      const resolveSectionMediaTarget = (root) => {{
        if (!root) {{
          return null;
        }}
        if (root.matches('img, video, source')) {{
          return root;
        }}
        return root.querySelector('img, video, source');
      }};

      const updateHeadLink = (selector, relValue, href) => {{
        if (!href) {{
          return;
        }}
        let link = document.head.querySelector(selector);
        if (!link) {{
          link = document.createElement('link');
          link.setAttribute('rel', relValue);
          document.head.appendChild(link);
        }}
        link.setAttribute('href', href);
      }};

      const updateLogoImages = (logoUrl) => {{
        if (!logoUrl) {{
          return;
        }}
        const selectors = [
          '.custom-logo-link img',
          '.site-logo img',
          '.navbar-brand img',
          'img[class*="logo"]',
          'img[id*="logo"]',
          'img[alt*="logo" i]',
          'img[class*="brand"]',
          'img[id*="brand"]'
        ];
        const seen = new Set();
        document.querySelectorAll(selectors.join(',')).forEach((image) => {{
          if (seen.has(image)) {{
            return;
          }}
          seen.add(image);
          setMediaSource(image, logoUrl);
        }});
      }};

      const applySectionData = async () => {{
        const sections = await parseResponse(`/api/public/${{siteId}}/site_sections`);
        sections.forEach((record) => {{
          const data = record.data || {{}};
          if (!data.selector) {{
            return;
          }}
          const root = document.querySelector(data.selector);
          if (!root) {{
            return;
          }}
          root.hidden = data.visible === false;
          const heading = root.querySelector('h1, h2, h3');
          const body = root.querySelector('p');
          const media = resolveSectionMediaTarget(root);
          if (heading && data.title) {{
            heading.textContent = data.title;
          }}
          if (body && data.summary) {{
            body.textContent = data.summary;
          }}
          if (media && data.primary_media_url) {{
            setMediaSource(media, data.primary_media_url);
          }} else if (data.primary_media_url) {{
            applyBackgroundMedia(root, data.primary_media_url);
          }}
          if (data.background_media_url) {{
            applyBackgroundMedia(root, data.background_media_url);
          }}
        }});
      }};

      const applyNavigationData = async () => {{
        const items = await parseResponse(`/api/public/${{siteId}}/navigation_items`);
        items.forEach((record) => {{
          const data = record.data || {{}};
          const cloneHref = resolveCloneUrl(data.clone_path || data.clonePath || '');
          let anchor = null;
          if (data.selector) {{
            anchor = document.querySelector(data.selector);
          }}
          if (!anchor && cloneHref) {{
            anchor = document.querySelector(`a[href="${{cloneHref}}"]`);
          }}
          if (!anchor && data.href) {{
            anchor = document.querySelector(`a[href="${{data.href}}"]`);
          }}
          if (!anchor) {{
            return;
          }}
          if (data.label) {{
            anchor.textContent = data.label;
          }}
          if (cloneHref) {{
            anchor.href = cloneHref;
          }} else if (data.href) {{
            anchor.href = data.href;
          }}
        }});
      }};

      const applyPageData = async () => {{
        const pages = await parseResponse(`/api/public/${{siteId}}/site_pages`);
        if (!pages.length) {{
          return;
        }}
        const pageRecord = pages.find((record) => {{
          const data = record.data || {{}};
          const candidate = (data.clone_path || data.clonePath || data.path || '').toString();
          if (!candidate) {{
            return false;
          }}
          try {{
            const normalized = new URL(resolveCloneUrl(candidate), window.location.origin);
            return normalized.pathname === window.location.pathname || normalized.pathname === currentClonePath;
          }} catch (error) {{
            return candidate === currentClonePath;
          }}
        }}) || pages[0];
        const page = (pageRecord && pageRecord.data) || {{}};
        if (page.meta_title) {{
          document.title = page.meta_title;
        }}
      }};

      const applyThemeData = async () => {{
        const themes = await parseResponse(`/api/public/${{siteId}}/theme_styles`);
        if (!themes.length) {{
          return;
        }}
        const theme = themes[0].data || {{}};
        document.querySelectorAll(THEME_STYLE_SELECTOR).forEach((existing) => existing.remove());
        const styleTag = document.createElement('style');
        styleTag.setAttribute('data-fabricator-theme', 'true');
        styleTag.textContent = `
          :root {{
            --fabricator-primary: ${{theme.primary_color || '#0f172a'}};
            --fabricator-secondary: ${{theme.secondary_color || '#1e293b'}};
            --fabricator-accent: ${{theme.accent_color || '#38bdf8'}};
            --fabricator-font: ${{theme.font_family || 'inherit'}};
          }}
        `;
        document.head.appendChild(styleTag);
        if (theme.font_family) {{
          document.body.style.fontFamily = theme.font_family;
        }}
        updateLogoImages(theme.logo_url || '');
        updateHeadLink('link[rel="shortcut icon"]', 'shortcut icon', theme.favicon_url || '');
        updateHeadLink('link[rel="icon"]', 'icon', theme.favicon_url || '');
        updateHeadLink('link[rel="apple-touch-icon"]', 'apple-touch-icon', theme.favicon_url || '');
      }};

      document.addEventListener('DOMContentLoaded', () => {{
        applySectionData();
        applyNavigationData();
        applyPageData();
        applyThemeData();
      }});
    }})();
    """

    script_tag = soup.new_tag("script")
    script_tag["data-fabricator-bridge"] = "true"
    script_tag.string = bridge_script
    if soup.body:
        soup.body.append(script_tag)
    elif soup.html:
        soup.html.append(script_tag)
    else:
        soup.append(script_tag)
    return str(soup)


def detect_site_type(url, soup):
    signal_text = normalize_text(collect_text_signals(soup))
    scores = Counter()

    for site_type, patterns in SITE_PATTERNS.items():
        for pattern in patterns:
            if pattern in signal_text:
                scores[site_type] += 2

    if soup.find_all("form"):
        scores["lead_generation"] += 2
    if soup.find_all(attrs={"type": "email"}):
        scores["lead_generation"] += 2
    if soup.find_all(string=re.compile(r"subscribe|newsletter", re.I)):
        scores["blog"] += 1
    if soup.find_all(string=re.compile(r"book|appointment|schedule", re.I)):
        scores["service_business"] += 2

    hostname = urlparse(url).netloc.lower()
    if "shop" in hostname or "store" in hostname or "daraz" in hostname:
        scores["ecommerce"] += 3
    if "blog" in hostname:
        scores["blog"] += 2
    if any(term in hostname for term in ["edu", "university", "college", "school"]):
        scores["education"] += 3

    site_type, score = ("general_business", 1)
    if scores:
        site_type, score = scores.most_common(1)[0]

    total = sum(scores.values()) or score
    confidence = min(0.96, max(0.4, score / max(total, 1)))
    return site_type, round(confidence, 2), dict(scores)


def extract_navigation(soup):
    links = []
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        href = anchor["href"].strip()
        if label and href and not href.startswith("#"):
            links.append(
                {
                    "label": truncate(label, 80),
                    "href": href[:240],
                    "selector": build_element_selector(anchor),
                    "section_key": closest_section_context(anchor)[0],
                }
            )
        if len(links) >= 30:
            break
    return links


def extract_forms(soup):
    forms = []
    for index, form in enumerate(soup.find_all("form"), start=1):
        fields = []
        for field in form.find_all(["input", "textarea", "select"]):
            field_name = field.get("name") or field.get("id") or field.get("placeholder") or field.get("type") or f"field_{len(fields) + 1}"
            field_type = field.get("type") or field.name
            fields.append(
                {
                    "name": slugify(field_name),
                    "type": field_type.lower(),
                }
            )
        forms.append(
            {
                "name": f"form_{index}",
                "selector": build_element_selector(form),
                "fields": fields or [{"name": "message", "type": "textarea"}],
            }
        )
    return forms


def extract_text_blocks(soup, tags, min_length=3, max_length=180):
    items = []
    seen = set()
    for tag in soup.find_all(tags):
        text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
        if min_length <= len(text) <= max_length and text.lower() not in seen:
            seen.add(text.lower())
            items.append(text)
    return items


def extract_price_tokens(text_items):
    prices = []
    pattern = re.compile(r"(?:rs\.?|pkr|\$)\s*\d[\d,]*(?:\.\d+)?", re.I)
    for item in text_items:
        prices.extend(pattern.findall(item))
    return prices


def is_noise_heading(text):
    lowered = text.lower()
    if len(text) <= 2:
        return True
    if re.fullmatch(r"[\d\W]+", text):
        return True
    return lowered in {"home", "about", "contact", "read more", "learn more", "apply now", "portal"}


def select_titles_for_model(model_name, headings, paragraphs, navigation):
    clean_headings = [heading for heading in headings if not is_noise_heading(heading)]

    if model_name == "courses":
        keywords = ("bachelor", "bachelors", "master", "associate", "degree", "program", "science", "engineering")
        matches = [heading for heading in clean_headings if any(keyword in heading.lower() for keyword in keywords)]
        return matches[:10]
    if model_name in {"products", "services", "features", "projects", "posts", "menu_items", "properties", "case_studies"}:
        return clean_headings[:10]
    if model_name == "categories":
        return [item["label"] for item in navigation[:10]]
    if model_name in {"plans", "pages"}:
        return clean_headings[:6] or [item["label"] for item in navigation[:6]]
    if model_name == "testimonials":
        return [paragraph[:90] for paragraph in paragraphs[:6]]
    if model_name in {"instructors", "agents", "authors", "team_members"}:
        candidates = []
        for heading in clean_headings:
            words = heading.split()
            if 2 <= len(words) <= 5 and all(word[:1].isupper() for word in words if word):
                candidates.append(heading)
        return candidates[:8]
    return clean_headings[:6]


def normalize_numeric(value):
    match = re.search(r"\d+(?:\.\d+)?", value or "")
    if not match:
        return 0
    number = match.group(0)
    return float(number) if "." in number else int(number)


def pick_media_url(media_assets, index=0, preferred_types=None):
    preferred_types = preferred_types or {"image", "svg", "icon"}
    candidates = [
        asset
        for asset in media_assets
        if asset.get("media_type") in preferred_types and (asset.get("file_url") or asset.get("original_url"))
    ]
    if not candidates:
        return ""
    asset = candidates[index % len(candidates)]
    return asset.get("file_url") or asset.get("original_url") or ""


def build_record_from_source(model_name, fields, title, summary, price_hint, site_type, media_url="", section_selector=""):
    record = {}
    for field in fields:
        field_name = field["name"]
        field_type = field["type"]

        if field_name in {"title", "name", "full_name", "customer_name", "student_name", "label"}:
            value = title
        elif field_name == "slug":
            value = slugify(title).replace("_", "-")
        elif field_name in {"summary", "description", "excerpt", "body", "quote", "bio", "notes", "result", "meta_description"}:
            value = summary
        elif field_name in {"price", "total_amount"}:
            value = normalize_numeric(price_hint)
        elif field_name == "status":
            value = "published"
        elif field_name == "billing_cycle":
            value = "monthly"
        elif field_name == "category":
            value = site_type.replace("_", " ")
        elif field_name in {"role", "title"} and model_name in {"instructors", "authors", "agents", "team_members"}:
            value = "Team Member"
        elif field_name == "duration":
            value = "Flexible"
        elif field_name in {"email", "phone", "reservation_date", "published_at", "date", "appointment_at", "created_at"}:
            value = ""
        elif field_name in {
            "image_url",
            "photo_url",
            "project_url",
            "icon",
            "location",
            "hero_media_url",
            "primary_media_url",
            "background_media_url",
            "logo_url",
            "favicon_url",
            "media_url",
        }:
            value = media_url
        elif field_name == "selector":
            value = section_selector
        elif field_name == "seo_title":
            value = title
        elif field_type == "number":
            value = 0
        elif field_type == "boolean":
            value = True
        else:
            value = summary if len(summary) < 160 else summary[:160]

        record[field_name] = value
    return record


def infer_fields_for_model(model_name, headings):
    defaults = {
        "products": [("title", "text"), ("price", "number"), ("description", "textarea"), ("image_url", "image"), ("status", "text")],
        "categories": [("name", "text"), ("slug", "text"), ("description", "textarea")],
        "orders": [("customer_name", "text"), ("email", "email"), ("status", "text"), ("total_amount", "number")],
        "customers": [("full_name", "text"), ("email", "email"), ("phone", "text")],
        "menu_items": [("name", "text"), ("price", "number"), ("description", "textarea"), ("category", "text"), ("image_url", "image")],
        "reservations": [("guest_name", "text"), ("email", "email"), ("reservation_date", "date"), ("party_size", "number")],
        "projects": [("title", "text"), ("summary", "textarea"), ("image_url", "image"), ("project_url", "url")],
        "posts": [("title", "text"), ("slug", "text"), ("excerpt", "textarea"), ("body", "textarea"), ("published_at", "date"), ("image_url", "image")],
        "authors": [("name", "text"), ("role", "text"), ("bio", "textarea"), ("photo_url", "image")],
        "subscribers": [("email", "email"), ("created_at", "datetime")],
        "courses": [("title", "text"), ("duration", "text"), ("description", "textarea"), ("price", "number"), ("image_url", "image")],
        "instructors": [("name", "text"), ("title", "text"), ("bio", "textarea"), ("photo_url", "image")],
        "enrollments": [("student_name", "text"), ("email", "email"), ("course_id", "number"), ("status", "text")],
        "plans": [("name", "text"), ("price", "number"), ("billing_cycle", "text"), ("description", "textarea")],
        "features": [("title", "text"), ("description", "textarea"), ("icon", "image")],
        "leads": [("name", "text"), ("email", "email"), ("phone", "text"), ("message", "textarea"), ("status", "text")],
        "properties": [("title", "text"), ("price", "number"), ("location", "text"), ("bedrooms", "number"), ("bathrooms", "number"), ("image_url", "image")],
        "agents": [("name", "text"), ("email", "email"), ("phone", "text"), ("photo_url", "image")],
        "services": [("title", "text"), ("description", "textarea"), ("icon", "image")],
        "case_studies": [("title", "text"), ("client_name", "text"), ("summary", "textarea"), ("result", "textarea"), ("image_url", "image")],
        "appointments": [("customer_name", "text"), ("email", "email"), ("appointment_at", "datetime"), ("notes", "textarea")],
        "pages": [("title", "text"), ("slug", "text"), ("body", "textarea"), ("status", "text")],
        "testimonials": [("name", "text"), ("quote", "textarea"), ("role", "text"), ("photo_url", "image")],
        "navigation_items": [("label", "text"), ("href", "url"), ("clone_path", "url"), ("source_url", "url"), ("selector", "text"), ("section_key", "text"), ("display_order", "number")],
        "site_sections": [("section_key", "text"), ("selector", "text"), ("section_type", "text"), ("title", "text"), ("summary", "textarea"), ("primary_media_url", "image"), ("background_media_url", "image"), ("media_urls_json", "textarea"), ("display_order", "number"), ("visible", "boolean")],
        "site_pages": [("title", "text"), ("slug", "text"), ("path", "url"), ("clone_path", "url"), ("source_url", "url"), ("meta_title", "text"), ("meta_description", "textarea"), ("hero_media_url", "image")],
        "theme_styles": [("label", "text"), ("primary_color", "color"), ("secondary_color", "color"), ("accent_color", "color"), ("font_family", "text"), ("logo_url", "image"), ("favicon_url", "image")],
    }

    fields = defaults.get(model_name, [("title", "text"), ("description", "textarea")])
    enriched = [{"name": name, "type": field_type} for name, field_type in fields]
    if headings and "seo_title" not in {field["name"] for field in enriched} and model_name not in {"navigation_items", "site_sections", "site_pages", "theme_styles"}:
        enriched.append({"name": "seo_title", "type": "text"})
    return enriched


def extract_navigation_records(navigation):
    records = []
    for index, item in enumerate(navigation, start=1):
        records.append(
            {
                "label": item["label"],
                "href": item["href"],
                "clone_path": item.get("clone_path", ""),
                "source_url": item.get("source_url", item["href"]),
                "selector": item["selector"],
                "section_key": item.get("section_key", ""),
                "display_order": index,
            }
        )
    return records[:18]


def extract_site_page_records(soup, url, sections):
    title = soup.title.get_text(" ", strip=True) if soup.title else urlparse(url).netloc
    description = ""
    meta_description = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta_description and meta_description.get("content"):
        description = meta_description["content"]
    hero_media_url = next((section.get("primary_media_url", "") for section in sections if section.get("section_type") in {"hero", "banner"}), "")
    return [
        {
            "title": title,
            "slug": "home",
            "path": "/",
            "clone_path": "/",
            "source_url": url,
            "meta_title": title,
            "meta_description": truncate(description or title, 220),
            "hero_media_url": hero_media_url,
        }
    ]


def extract_style_colors(style_text):
    colors = re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}\b|rgba?\([^)]+\)|hsla?\([^)]+\)", style_text or "")
    filtered = [color for color in colors if color.lower() not in {"#fff", "#ffffff", "#000", "#000000"}]
    return [item for item, _ in Counter(filtered).most_common(6)]


def extract_font_families(style_text):
    fonts = re.findall(r"font-family\s*:\s*([^;]+)", style_text or "", flags=re.I)
    cleaned = []
    for font_entry in fonts:
        family = font_entry.split(",")[0].strip().strip("\"'")
        if family and family.lower() != "inherit":
            cleaned.append(family)
    return [item for item, _ in Counter(cleaned).most_common(4)]


def extract_theme_style_records(soup, media_assets):
    style_text = " ".join(
        [tag.get_text(" ", strip=True) for tag in soup.find_all("style")]
        + [tag.get("style", "") for tag in soup.find_all(attrs={"style": True})]
    )
    colors = extract_style_colors(style_text)
    fonts = extract_font_families(style_text)
    logo_url = ""
    favicon_url = ""

    for asset in media_assets:
        asset_url = asset.get("file_url") or asset.get("original_url") or ""
        if not asset_url:
            continue
        name = f"{asset.get('original_name', '')} {asset.get('alt_text', '')}".lower()
        if not logo_url and any(token in name for token in ICON_HINTS):
            logo_url = asset_url
        if not favicon_url and asset.get("media_type") == "icon":
            favicon_url = asset_url

    return [
        {
            "label": "Primary Theme",
            "primary_color": colors[0] if colors else "#0f172a",
            "secondary_color": colors[1] if len(colors) > 1 else "#1e293b",
            "accent_color": colors[2] if len(colors) > 2 else "#38bdf8",
            "font_family": fonts[0] if fonts else "inherit",
            "logo_url": logo_url,
            "favicon_url": favicon_url,
        }
    ]


def extract_content_models(soup, site_type):
    headings = [tag.get_text(" ", strip=True) for tag in soup.find_all(["h1", "h2", "h3"])]
    models = []
    seen = set()

    base_models = {
        "ecommerce": ["products", "categories", "orders", "customers"],
        "restaurant": ["menu_items", "reservations", "testimonials"],
        "portfolio": ["projects", "testimonials", "inquiries"],
        "blog": ["posts", "categories", "authors", "subscribers"],
        "education": ["courses", "instructors", "enrollments"],
        "saas": ["plans", "features", "leads"],
        "real_estate": ["properties", "agents", "inquiries"],
        "agency": ["services", "case_studies", "leads"],
        "lead_generation": ["leads", "services", "testimonials"],
        "service_business": ["services", "appointments", "leads"],
        "general_business": ["pages", "services", "leads"],
    }

    for model_name in base_models.get(site_type, ["pages", "leads"]):
        if model_name in seen:
            continue
        seen.add(model_name)
        models.append({"name": model_name, "fields": infer_fields_for_model(model_name, headings)})

    for system_model in ["site_pages", "site_sections", "navigation_items", "theme_styles"]:
        if system_model in seen:
            continue
        seen.add(system_model)
        models.append({"name": system_model, "fields": infer_fields_for_model(system_model, headings)})

    for form in extract_forms(soup):
        form_model = f"{form['name']}_submissions"
        if form_model not in seen:
            seen.add(form_model)
            models.append({"name": form_model, "fields": form["fields"] + [{"name": "created_at", "type": "datetime"}]})

    return models


def extract_seed_records(soup, url, site_type, models, navigation, sections, media_assets):
    headings = extract_text_blocks(soup, ["h1", "h2", "h3", "h4"])
    paragraphs = extract_text_blocks(soup, ["p", "li"], min_length=20, max_length=260)
    text_items = headings + paragraphs
    price_tokens = extract_price_tokens(text_items)
    seed_records = {}

    for model in models:
        model_name = model["name"]
        fields = model["fields"]
        records = []

        if model_name == "navigation_items":
            seed_records[model_name] = extract_navigation_records(navigation)
            continue

        if model_name == "site_sections":
            seed_records[model_name] = sections
            continue

        if model_name == "site_pages":
            seed_records[model_name] = extract_site_page_records(soup, url, sections)
            continue

        if model_name == "theme_styles":
            seed_records[model_name] = extract_theme_style_records(soup, media_assets)
            continue

        if model_name in {"orders", "customers", "reservations", "enrollments", "leads", "appointments", "inquiries"}:
            seed_records[model_name] = records
            continue

        titles = select_titles_for_model(model_name, headings, paragraphs, navigation)
        for index, title in enumerate(titles):
            summary = paragraphs[index % len(paragraphs)] if paragraphs else f"Auto-extracted content for {title}"
            price_hint = price_tokens[index % len(price_tokens)] if price_tokens else ""
            media_url = pick_media_url(media_assets, index)
            section_selector = sections[index % len(sections)]["selector"] if sections else ""
            records.append(build_record_from_source(model_name, fields, title, summary, price_hint, site_type, media_url, section_selector))

        if not records and model_name == "pages":
            site_title = soup.title.get_text(strip=True) if soup.title else "Home"
            summary = paragraphs[0] if paragraphs else "Imported from cloned website."
            records.append(build_record_from_source(model_name, fields, site_title, summary, "", site_type, pick_media_url(media_assets)))

        seed_records[model_name] = records[:16]

    return seed_records


def build_backend_routes(models):
    routes = []
    for model in models:
        name = model["name"]
        singular = name[:-1] if name.endswith("s") else name
        routes.append({"method": "GET", "path": f"/api/{name}", "purpose": f"List {name}"})
        routes.append({"method": "POST", "path": f"/api/{name}", "purpose": f"Create {singular}"})
        routes.append({"method": "PUT", "path": f"/api/{name}/<id>", "purpose": f"Update {singular}"})
        routes.append({"method": "DELETE", "path": f"/api/{name}/<id>", "purpose": f"Delete {singular}"})
    return routes


def build_frontend_bindings(site_type, models):
    primary_model = models[0]["name"] if models else "pages"
    bindings = [
        {"component": "site sections", "data_source": "/api/site_sections", "strategy": "Map extracted section selectors to editable titles, summaries, and media."},
        {"component": "navigation", "data_source": "/api/navigation_items", "strategy": "Keep menu labels and links editable without changing the original layout structure."},
        {"component": "theme styles", "data_source": "/api/theme_styles", "strategy": "Expose colors, logo, favicon, and typography tokens to the admin panel bridge."},
    ]

    if site_type == "ecommerce":
        bindings.append(
            {"component": "product grid", "data_source": "/api/products", "strategy": "Replace static product cards with dynamic product records while preserving markup."}
        )
    else:
        bindings.append(
            {"component": "content collections", "data_source": f"/api/{primary_model}", "strategy": "Bind repeatable sections and cards to extracted content records."}
        )
    return bindings


def build_admin_sections(models):
    sections = []
    for model in models:
        columns = [field["name"] for field in model["fields"][:6]]
        if model["name"] == "site_sections":
            columns = ["section_key", "title", "primary_media_url", "background_media_url", "display_order"]
        sections.append({"title": model["name"].replace("_", " ").title(), "columns": columns, "actions": ["create", "edit", "delete", "publish"]})
    sections.append({"title": "Media Library", "columns": ["original_name", "media_type", "file_url", "original_url"], "actions": ["view", "replace", "delete"]})
    return sections


def map_field_type(field_type):
    mapping = {
        "text": "string",
        "email": "string",
        "date": "string",
        "datetime": "string",
        "textarea": "text",
        "number": "number",
        "boolean": "boolean",
        "image": "media",
        "url": "string",
        "color": "string",
    }
    return mapping.get(field_type, "string")


def count_dom_nodes(soup):
    return len(soup.find_all(True))


def calculate_confidence_breakdown(url, soup, site_type_confidence, site_type_scores, navigation, sections, media_assets, forms):
    dom_nodes = count_dom_nodes(soup)
    semantic_hits = sum(1 for tag in ["head", "body", "header", "nav", "main", "footer"] if soup.find(tag))
    visible_text = " ".join(collect_visible_text(soup))
    headings = extract_text_blocks(soup, ["h1", "h2", "h3", "h4"], min_length=2, max_length=220)
    paragraphs = extract_text_blocks(soup, ["p", "li"], min_length=20, max_length=260)
    text_coverage = min(1.0, (sum(len(item) for item in headings + paragraphs) / max(len(visible_text), 1)) * 1.7)
    section_score = min(1.0, len(sections) / max(4, min(16, dom_nodes // 40 or 1)))
    stylesheet_count = len(soup.find_all("link", rel=lambda value: value and "stylesheet" in " ".join(value).lower()))
    style_tag_count = len(soup.find_all("style"))
    style_attr_count = len(soup.find_all(attrs={"style": True}))
    class_density = min(1.0, sum(1 for tag in soup.find_all(True) if tag.get("class")) / max(dom_nodes, 1) * 2.2)
    style_score = min(1.0, ((stylesheet_count > 0) * 0.4) + min(style_tag_count / 8, 0.3) + min(style_attr_count / 40, 0.2) + class_density * 0.1)
    images = len(soup.find_all("img"))
    sections_with_media = sum(1 for section in sections if section.get("primary_media_url") or section.get("background_media_url"))
    layout_score = min(1.0, ((images > 0) * 0.25) + min(len(sections) / 12, 0.4) + min(sections_with_media / max(len(sections), 1), 1.0) * 0.35)
    recovered_media = sum(1 for asset in media_assets if asset.get("file_url") or asset.get("original_url"))
    downloaded_media = sum(1 for asset in media_assets if asset.get("download_status") == "downloaded")
    media_score = 1.0 if not media_assets else min(1.0, ((downloaded_media * 1.0) + ((recovered_media - downloaded_media) * 0.72)) / len(media_assets))
    total_links = len(soup.find_all("a", href=True))
    link_score = min(1.0, ((len(navigation) / max(total_links, 1)) * 1.5) if total_links else 0.7)
    interactivity_count = len(forms) + len(soup.find_all("button")) + len(soup.find_all(["input", "select", "textarea"])) + len(soup.find_all(attrs={"role": re.compile(r"button|tab|dialog|menu", re.I)}))
    interactive_score = min(1.0, interactivity_count / max(4, min(18, dom_nodes // 50 or 1)))
    structure_score = min(1.0, semantic_hits / 6 + min(dom_nodes / 240, 0.25))

    components = [
        {"key": "dom_structure_match", "label": "DOM structure match", "score": round(structure_score, 2), "weight": 0.14, "details": f"Found {semantic_hits}/6 core semantic regions across {dom_nodes} DOM nodes."},
        {"key": "text_extraction_completeness", "label": "Text extraction completeness", "score": round(text_coverage, 2), "weight": 0.14, "details": f"Recovered {len(headings)} headings and {len(paragraphs)} paragraph blocks from visible text."},
        {"key": "section_detection_accuracy", "label": "Section detection accuracy", "score": round(section_score, 2), "weight": 0.14, "details": f"Mapped {len(sections)} editable sections with selectors and summaries."},
        {"key": "style_match", "label": "Style match", "score": round(style_score, 2), "weight": 0.12, "details": f"Detected {stylesheet_count} stylesheets, {style_tag_count} style tags, and {style_attr_count} inline style nodes."},
        {"key": "layout_match", "label": "Layout match", "score": round(layout_score, 2), "weight": 0.12, "details": f"Observed {images} image tags and {sections_with_media} section-to-media mappings."},
        {"key": "media_recovery_completeness", "label": "Media recovery completeness", "score": round(media_score, 2), "weight": 0.17, "details": f"Recovered {recovered_media} media assets with {downloaded_media} localized into project storage."},
        {"key": "link_extraction_completeness", "label": "Link extraction completeness", "score": round(link_score, 2), "weight": 0.08, "details": f"Captured {len(navigation)} navigation links out of {total_links} anchors."},
        {"key": "interactive_component_detection", "label": "Interactive component detection", "score": round(interactive_score, 2), "weight": 0.07, "details": f"Detected {interactivity_count} interactive nodes including forms, buttons, and inputs."},
        {"key": "website_type_confidence", "label": "Website type confidence", "score": round(site_type_confidence, 2), "weight": 0.02, "details": f"Top classification signals: {', '.join(f'{key}:{value}' for key, value in sorted(site_type_scores.items(), key=lambda item: item[1], reverse=True)[:3]) or 'general business fallback'}."},
    ]

    overall = round(sum(component["score"] * component["weight"] for component in components), 2)
    overall = min(0.97, max(0.38, overall))
    return {
        "overall": overall,
        "components": components,
        "rawSignals": {
            "domNodes": dom_nodes,
            "semanticHits": semantic_hits,
            "visibleTextCharacters": len(visible_text),
            "headings": len(headings),
            "paragraphs": len(paragraphs),
            "sections": len(sections),
            "mediaAssets": len(media_assets),
            "downloadedMedia": downloaded_media,
            "navigationLinks": len(navigation),
            "interactiveNodes": interactivity_count,
        },
    }


def build_media_summary(media_assets):
    counts_by_type = Counter(asset.get("media_type", "file") for asset in media_assets)
    downloaded = sum(1 for asset in media_assets if asset.get("download_status") == "downloaded")
    fallback = sum(1 for asset in media_assets if asset.get("download_status") not in {"downloaded", "embedded_reference"})
    return {"total": len(media_assets), "downloaded": downloaded, "fallbackReferences": fallback, "countsByType": dict(counts_by_type)}


def build_site_spec(site_id, url, blueprint):
    site_name = urlparse(url).netloc.replace("www.", "") or f"site-{site_id}"
    resources = []
    for model in blueprint["database_models"]:
        fields = []
        for field in model["fields"]:
            fields.append({"key": field["name"], "label": field["name"].replace("_", " ").title(), "type": map_field_type(field["type"]), "required": False})
        resources.append({"key": model["name"], "label": model["name"].replace("_", " ").title(), "type": blueprint["site_type"], "fields": fields, "listDisplay": [field["key"] for field in fields[:5]], "publishable": True})

    return {
        "projectId": site_id,
        "siteName": site_name,
        "sourceUrl": url,
        "siteType": blueprint["site_type"],
        "confidence": blueprint["confidence"],
        "confidenceBreakdown": blueprint.get("confidence_breakdown", {}),
        "adminTheme": blueprint.get("admin_theme", {}),
        "mediaSummary": blueprint.get("media_summary", {}),
        "resources": resources,
        "bindings": blueprint["frontend_bindings"],
        "pipeline": blueprint.get("pipeline", []),
        "diagnostics": blueprint.get("clone_diagnostics", {}),
    }


def build_conversion_blueprint(url, html, site_id=None, media_output_dir=None):
    soup = BeautifulSoup(html, "html.parser")
    site_type, site_type_confidence, site_type_scores = detect_site_type(url, soup)
    media_assets = extract_media_assets(url, html, site_id=site_id, media_output_dir=media_output_dir)
    localized_html = localize_clone_html(html, media_assets) if media_assets else html
    if site_id:
        localized_html = inject_clone_bridge(localized_html, site_id)
    localized_soup = BeautifulSoup(localized_html, "html.parser")
    navigation = extract_navigation(localized_soup)
    forms = extract_forms(localized_soup)
    sections = extract_sections(localized_soup, media_assets)
    models = extract_content_models(localized_soup, site_type)
    seed_records = extract_seed_records(localized_soup, url, site_type, models, navigation, sections, media_assets)
    confidence_breakdown = calculate_confidence_breakdown(url, localized_soup, site_type_confidence, site_type_scores, navigation, sections, media_assets, forms)

    return {
        "source_url": url,
        "site_type": site_type,
        "confidence": confidence_breakdown["overall"],
        "confidence_breakdown": confidence_breakdown,
        "pipeline": [
            "URL Input",
            "Website Cloner",
            "DOM Analyzer + Structure Detection",
            "Website Type Detection",
            "Entity & Resource Extraction",
            "SiteSpec Generator (Schema)",
            "Database + Records Creation",
            "API Generation",
            "Admin Panel Auto Creation",
            "Data Migration (HTML -> DB)",
            "Frontend <-> Backend Connection",
            "Dynamic Website + Admin Panel",
        ],
        "navigation": navigation,
        "forms": forms,
        "sections": sections,
        "database_models": models,
        "seed_records": seed_records,
        "backend_routes": build_backend_routes(models),
        "admin_sections": build_admin_sections(models),
        "frontend_bindings": build_frontend_bindings(site_type, models),
        "media_assets": media_assets,
        "media_summary": build_media_summary(media_assets),
        "localized_html": localized_html,
        "clone_diagnostics": {
            "siteTypeSignals": site_type_scores,
            "formsDetected": len(forms),
            "sectionsDetected": len(sections),
            "mediaDetected": len(media_assets),
            "downloadedMedia": sum(1 for asset in media_assets if asset.get("download_status") == "downloaded"),
            "navigationLinks": len(navigation),
            "warnings": [
                "Some media remain as external references when download size or source availability blocked localization."
                if any(asset.get("download_status") == "external_reference" for asset in media_assets)
                else "All detected media were localized or embedded successfully."
            ],
        },
        "automation_notes": [
            "Map static repeated sections to the closest extracted collection or site section selector.",
            "Preserve original frontend layout while replacing cards, navigation, and media through the public bridge.",
            "Treat localized media URLs as the editable source of truth so replacements reflect on the cloned output.",
        ],
    }


def create_scaffold_files(output_dir, site_id, blueprint):
    os.makedirs(output_dir, exist_ok=True)
    backend_path = os.path.join(output_dir, "generated_backend.py")
    schema_path = os.path.join(output_dir, "schema.json")
    admin_path = os.path.join(output_dir, "admin_sections.json")
    site_spec_path = os.path.join(output_dir, "site_spec.json")
    media_manifest_path = os.path.join(output_dir, "media_manifest.json")
    diagnostics_path = os.path.join(output_dir, "diagnostics.json")
    notes_path = os.path.join(output_dir, "integration_notes.md")

    backend_source = render_backend_source(site_id, blueprint)
    notes = render_notes(site_id, blueprint)
    site_spec = build_site_spec(site_id, blueprint["source_url"], blueprint)

    with open(backend_path, "w", encoding="utf-8") as file:
        file.write(backend_source)
    with open(schema_path, "w", encoding="utf-8") as file:
        json.dump(blueprint["database_models"], file, indent=2)
    with open(admin_path, "w", encoding="utf-8") as file:
        json.dump(blueprint["admin_sections"], file, indent=2)
    with open(site_spec_path, "w", encoding="utf-8") as file:
        json.dump(site_spec, file, indent=2)
    with open(media_manifest_path, "w", encoding="utf-8") as file:
        json.dump(blueprint.get("media_assets", []), file, indent=2)
    with open(diagnostics_path, "w", encoding="utf-8") as file:
        json.dump(blueprint.get("clone_diagnostics", {}), file, indent=2)
    with open(notes_path, "w", encoding="utf-8") as file:
        file.write(notes)

    return {
        "backend_path": backend_path,
        "schema_path": schema_path,
        "admin_path": admin_path,
        "site_spec_path": site_spec_path,
        "media_manifest_path": media_manifest_path,
        "diagnostics_path": diagnostics_path,
        "notes_path": notes_path,
    }


def render_backend_source(site_id, blueprint):
    models_json = json.dumps(blueprint["database_models"], indent=4)
    admin_sections_json = json.dumps(blueprint["admin_sections"], indent=4)
    return f"""import sqlite3
from flask import Flask, jsonify

app = Flask(__name__)
DB_NAME = "dynamic_site_{site_id}.db"
MODELS = {models_json}
ADMIN_SECTIONS = {admin_sections_json}


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, payload_json TEXT)")
    conn.commit()
    conn.close()


@app.route("/api/meta")
def meta():
    return jsonify({{"site_type": "{blueprint['site_type']}", "admin_sections": ADMIN_SECTIONS}})


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, port=5100)
"""


def render_notes(site_id, blueprint):
    lines = [
        f"# Smart Dynamic Conversion Output for Site {site_id}",
        "",
        f"- Detected site type: `{blueprint['site_type']}`",
        f"- Confidence: `{blueprint['confidence']}`",
        f"- Media assets detected: `{blueprint.get('media_summary', {}).get('total', 0)}`",
        "- This output includes section selectors, media localization, and confidence diagnostics.",
        "",
        "## Suggested rollout",
        "1. Serve the cloned HTML through the bridge-enabled preview endpoint.",
        "2. Use `site_spec.json` to power the standalone admin website.",
        "3. Use `media_manifest.json` to seed the admin media library and media-aware form fields.",
    ]
    return "\\n".join(lines) + "\\n"
