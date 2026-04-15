from __future__ import annotations

import math
from pathlib import Path
from textwrap import wrap


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "AI_WEBSITE_FABRICATOR_JURY_CODE_FLOW_BRIEF.md"
OUTPUT = ROOT / "AI_WEBSITE_FABRICATOR_JURY_CODE_FLOW_BRIEF.pdf"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT = 48
TOP = 804
BOTTOM = 42


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_line(text: str, width: int) -> list[str]:
    if not text.strip():
        return [""]
    return wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
        replace_whitespace=False,
        drop_whitespace=False,
    ) or [text]


def parse_markdown(path: Path) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("### "):
            items.append(("h3", line[4:].strip()))
        elif line.startswith("## "):
            items.append(("h2", line[3:].strip()))
        elif line.startswith("# "):
            items.append(("h1", line[2:].strip()))
        elif line.startswith("- "):
            items.append(("bullet", line[2:].strip()))
        elif line.startswith("Reference:"):
            items.append(("label", line))
        elif line.startswith("References:"):
            items.append(("label", line))
        elif not line.strip():
            items.append(("blank", ""))
        else:
            items.append(("body", line))
    return items


def layout_items(items: list[tuple[str, str]]) -> list[list[tuple[int, int, str]]]:
    pages: list[list[tuple[int, int, str]]] = [[]]
    y = TOP

    style = {
        "h1": {"font": 20, "leading": 26, "width": 46},
        "h2": {"font": 16, "leading": 22, "width": 60},
        "h3": {"font": 13, "leading": 18, "width": 78},
        "label": {"font": 11, "leading": 16, "width": 92},
        "body": {"font": 10, "leading": 14, "width": 105},
        "bullet": {"font": 10, "leading": 14, "width": 100},
        "blank": {"font": 10, "leading": 10, "width": 105},
    }

    def ensure_space(lines_needed: int, leading: int) -> None:
        nonlocal y
        if y - (lines_needed * leading) < BOTTOM:
            pages.append([])
            y = TOP

    for kind, text in items:
        spec = style[kind]
        if kind == "blank":
            y -= spec["leading"]
            continue

        prefix = "- " if kind == "bullet" else ""
        wrapped = wrap_line(prefix + text, spec["width"])
        ensure_space(len(wrapped), spec["leading"])

        for segment in wrapped:
            pages[-1].append((LEFT, y, f"/F1 {spec['font']} Tf ({pdf_escape(segment)}) Tj"))
            y -= spec["leading"]

        if kind in {"h1", "h2", "h3"}:
            y -= 4

    return pages


def build_pdf(pages: list[list[tuple[int, int, str]]]) -> bytes:
    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    content_ids: list[int] = []

    for page in pages:
        stream_lines = ["BT"]
        for x, y, command in page:
            stream_lines.append(f"1 0 0 1 {x} {y} Tm {command}")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("latin-1", errors="replace")
        content_id = add_object(
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"
        )
        content_ids.append(content_id)
        page_id = add_object(b"")  # placeholder, replaced after pages root exists
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    pages_root_id = add_object(
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] >>".encode(
            "latin-1"
        )
    )

    for page_id, content_id in zip(page_ids, content_ids):
        objects[page_id - 1] = (
            f"<< /Type /Page /Parent {pages_root_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode(
                "latin-1"
            )
        )

    catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_root_id} 0 R >>".encode("latin-1"))

    parts = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    current = len(parts[0])

    for index, obj in enumerate(objects, start=1):
        offsets.append(current)
        chunk = f"{index} 0 obj\n".encode("latin-1") + obj + b"\nendobj\n"
        parts.append(chunk)
        current += len(chunk)

    xref_offset = current
    xref = [f"xref\n0 {len(objects) + 1}\n", "0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n")
    parts.append("".join(xref).encode("latin-1"))
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    )
    parts.append(trailer.encode("latin-1"))
    return b"".join(parts)


def main() -> None:
    items = parse_markdown(SOURCE)
    pages = layout_items(items)
    OUTPUT.write_bytes(build_pdf(pages))
    print(f"Wrote {OUTPUT}")
    print(f"Pages: {len(pages)}")


if __name__ == "__main__":
    main()
