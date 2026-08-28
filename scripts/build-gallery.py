#!/usr/bin/env python3
"""Build the static poster gallery.

Renders the first page of every PDF in ``posters/`` into WebP previews, merges
metadata into ``data/posters.csv`` (creating placeholder rows for new PDFs while
preserving any hand-edited fields), and regenerates ``index.html`` from
``scripts/template.html``.

Usage:
    python3 scripts/build-gallery.py            # incremental build
    python3 scripts/build-gallery.py --force    # re-render every image
    python3 scripts/build-gallery.py --check    # validate only, write nothing

Requires: PyMuPDF and Pillow  (pip install -r requirements.txt)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from html import escape
from urllib.parse import quote

# --- paths -----------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTERS_DIR = os.path.join(ROOT, "posters")
PREVIEW_DIR = os.path.join(ROOT, "previews")
THUMB_DIR = os.path.join(PREVIEW_DIR, "thumbnails")
LARGE_DIR = os.path.join(PREVIEW_DIR, "large")
DATA_DIR = os.path.join(ROOT, "data")
POSTERS_CSV = os.path.join(DATA_DIR, "posters.csv")
TEAMS_CSV = os.path.join(DATA_DIR, "teams.csv")
SITE_JSON = os.path.join(DATA_DIR, "site.json")
TEMPLATE = os.path.join(ROOT, "scripts", "template.html")
INDEX_HTML = os.path.join(ROOT, "index.html")

THUMB_WIDTH = 600     # gallery card image, px
LARGE_WIDTH = 1800    # lightbox / high-res preview, px
WEBP_QUALITY = 82
EAGER_IMAGES = 4      # first N images load eagerly (above the fold)

CSV_FIELDS = ["id", "pdf", "team", "subteam", "title", "authors",
              "description", "thumbnail", "preview"]


# --- small helpers ---------------------------------------------------------
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-{2,}", "-", text).strip("-") or "poster"


def parse_filename(stem: str):
    """[TEAM][subteam] Title -> (team, subteam, title). All placeholders."""
    tags = []
    rest = stem
    while True:
        m = re.match(r"\s*\[([^\]]*)\]", rest)
        if not m:
            break
        tags.append(m.group(1).strip())
        rest = rest[m.end():]
    team = tags[0] if tags else "Uncategorized"
    subteam = tags[1] if len(tags) > 1 else ""
    title = rest.strip()
    title = re.sub(r"\s*\(\d+\)\s*$", "", title)   # drop trailing "(1)"
    title = title.replace("_", " ")
    title = re.sub(r"\s{2,}", " ", title).strip(" -_")
    if not title:
        title = team
    return team, subteam, title


def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


# --- image generation ------------------------------------------------------
def render_preview(pdf_path, out_path, target_width, force):
    """Render page 1 of the PDF to a WebP at target_width. Returns (w, h)."""
    import pymupdf
    from PIL import Image

    if (not force and os.path.exists(out_path)
            and os.path.getmtime(out_path) >= os.path.getmtime(pdf_path)):
        with Image.open(out_path) as im:
            return im.size, False   # cached

    doc = pymupdf.open(pdf_path)
    try:
        page = doc[0]                       # first (and only) page
        zoom = target_width / page.rect.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    finally:
        doc.close()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "WEBP", quality=WEBP_QUALITY, method=6)
    return img.size, True    # freshly rendered


# --- HTML rendering --------------------------------------------------------
def rel_url(path_from_root: str) -> str:
    """URL-encode a repo-relative path, keeping slashes."""
    return quote(path_from_root)


def card_html(row, thumb_dims, eager: bool) -> str:
    pdf_url = rel_url(row["pdf"])
    thumb_url = rel_url(row["thumbnail"])
    title = escape(row["title"])
    authors = escape(row.get("authors", "").strip())
    desc = escape(row.get("description", "").strip())
    subteam = escape(row.get("subteam", "").strip())
    w, h = thumb_dims

    alt = f"Poster: {row['title']}"
    if authors:
        alt += f" by {row['authors']}"
    alt = escape(alt)

    loading = "eager" if eager else "lazy"
    parts = [f'<article class="card" id="poster-{escape(row["id"])}" tabindex="-1">']
    parts.append(
        f'  <a class="card-media" href="{pdf_url}" target="_blank" rel="noopener"'
        f' aria-label="Open PDF: {title}">'
        f'<img src="{thumb_url}" width="{w}" height="{h}" loading="{loading}"'
        f' decoding="async" alt="{alt}"></a>')
    parts.append('  <div class="card-body">')
    if subteam:
        parts.append(f'    <p class="card-badge">{subteam}</p>')
    parts.append(
        f'    <h3 class="card-title"><a href="{pdf_url}" target="_blank"'
        f' rel="noopener">{title}</a></h3>')
    if authors:
        parts.append(f'    <p class="card-authors">{authors}</p>')
    if desc:
        parts.append(f'    <p class="card-desc">{desc}</p>')
    parts.append(
        f'    <a class="pdf-link" href="{pdf_url}" target="_blank" rel="noopener"'
        f' download>View / Download PDF <span aria-hidden="true">&#8599;</span></a>')
    parts.append('  </div>')
    parts.append('</article>')
    return "\n".join(parts)


def build_sections_html(rows, dims_by_id, team_order, team_labels):
    by_team = {}
    for r in rows:
        by_team.setdefault(r["team"], []).append(r)

    ordered_teams = sorted(
        by_team.keys(),
        key=lambda t: (team_order.get(t, 10_000), team_labels.get(t, t).lower()))

    img_index = 0
    out = []
    for team in ordered_teams:
        label = escape(team_labels.get(team, team))
        team_rows = sorted(by_team[team], key=lambda r: r["title"].lower())
        section_id = "team-" + slugify(team)
        out.append(f'<section class="team" aria-labelledby="{section_id}">')
        out.append(f'  <h2 class="team-heading" id="{section_id}">{label}'
                   f' <span class="team-count">{len(team_rows)}</span></h2>')
        out.append('  <div class="grid">')
        for r in team_rows:
            eager = img_index < EAGER_IMAGES
            out.append(card_html(r, dims_by_id[r["id"]], eager))
            img_index += 1
        out.append('  </div>')
        out.append('</section>')
    return "\n".join(out)


# --- main ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Build the static poster gallery.")
    ap.add_argument("--force", action="store_true",
                    help="re-render every preview image")
    ap.add_argument("--check", action="store_true",
                    help="validate metadata and PDFs only; write nothing")
    args = ap.parse_args()

    errors, warnings = [], []

    if not os.path.isdir(POSTERS_DIR):
        print(f"error: no posters/ directory at {POSTERS_DIR}", file=sys.stderr)
        return 2

    pdf_files = sorted(f for f in os.listdir(POSTERS_DIR)
                       if f.lower().endswith(".pdf"))
    if not pdf_files:
        warnings.append("no PDFs found in posters/")

    # merge existing metadata (preserve hand-edited fields), keyed by PDF basename
    existing = {os.path.basename(r["pdf"]): r
                for r in load_csv(POSTERS_CSV) if r.get("pdf")}
    for pdf, r in existing.items():
        if pdf not in pdf_files:
            errors.append(f"metadata row references missing PDF: {r['pdf']}")

    rows, seen_ids = [], {}
    for pdf in pdf_files:
        stem = os.path.splitext(pdf)[0]
        team_d, subteam_d, title_d = parse_filename(stem)
        row = dict(existing.get(pdf, {}))
        row["pdf"] = f"posters/{pdf}"
        row.setdefault("id", slugify(stem))
        # fill placeholders only where the maintainer hasn't provided a value
        row["team"] = (row.get("team") or team_d).strip()
        row["subteam"] = row.get("subteam", subteam_d).strip()
        row["title"] = (row.get("title") or title_d).strip()
        row.setdefault("authors", "")
        row.setdefault("description", "")
        row["thumbnail"] = f"previews/thumbnails/{row['id']}.webp"
        row["preview"] = f"previews/large/{row['id']}.webp"

        if row["id"] in seen_ids:
            errors.append(f"duplicate id '{row['id']}' "
                          f"({pdf} and {seen_ids[row['id']]})")
        seen_ids[row["id"]] = pdf
        if not row["title"]:
            errors.append(f"empty title for {pdf}")
        rows.append(row)

    # generate previews
    dims_by_id = {}
    rendered_count = cached_count = 0
    for row in rows:
        pdf_path = os.path.join(ROOT, row["pdf"])
        if not os.path.exists(pdf_path):
            errors.append(f"PDF not found: {row['pdf']}")
            continue
        if args.check:
            try:
                import pymupdf
                d = pymupdf.open(pdf_path)
                if d.page_count < 1:
                    errors.append(f"{row['pdf']} has no pages")
                d.close()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"cannot open {row['pdf']}: {exc}")
            continue
        try:
            dims, t_new = render_preview(
                pdf_path, os.path.join(ROOT, row["thumbnail"]),
                THUMB_WIDTH, args.force)
            dims_by_id[row["id"]] = dims
            _, l_new = render_preview(pdf_path, os.path.join(ROOT, row["preview"]),
                                      LARGE_WIDTH, args.force)
            if t_new or l_new:
                print(f"  rendered {row['id']}")
                rendered_count += 1
            else:
                cached_count += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"image generation failed for {row['pdf']}: {exc}")

    # report
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)

    if args.check:
        print(f"checked {len(rows)} poster(s): "
              f"{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1 if errors else 0

    if errors:
        print(f"\n{len(errors)} error(s) — see above. "
              "Fix the metadata/PDFs and rerun.", file=sys.stderr)
        # still write outputs for the posters that rendered, so the site works
        rows = [r for r in rows if r["id"] in dims_by_id]

    # write merged metadata back
    write_csv(POSTERS_CSV, CSV_FIELDS, rows)

    # teams: seed labels/order, preserve existing edits
    team_rows = load_csv(TEAMS_CSV)
    team_labels = {r["team"]: r.get("label") or r["team"] for r in team_rows}
    team_order = {}
    for r in team_rows:
        try:
            team_order[r["team"]] = int(r.get("order") or 0)
        except ValueError:
            team_order[r["team"]] = 0
    next_order = (max(team_order.values()) + 1) if team_order else 0
    for r in rows:
        t = r["team"]
        if t not in team_labels:
            team_labels[t] = t
            team_order[t] = next_order
            next_order += 1
    write_csv(TEAMS_CSV, ["team", "label", "order"],
              [{"team": t, "label": team_labels[t], "order": team_order[t]}
               for t in sorted(team_labels, key=lambda x: (team_order[x], x))])

    # site config
    site = {"title": "Poster Showcase", "subtitle": "", "intro": "",
            "footer": "", "lang": "en"}
    if os.path.exists(SITE_JSON):
        with open(SITE_JSON, encoding="utf-8") as f:
            site.update(json.load(f))

    sections = build_sections_html(rows, dims_by_id, team_order, team_labels)
    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()
    html = (template
            .replace("{{LANG}}", escape(site.get("lang", "en")))
            .replace("{{TITLE}}", escape(site["title"]))
            .replace("{{SUBTITLE}}", escape(site.get("subtitle", "")))
            .replace("{{INTRO}}", escape(site.get("intro", "")))
            .replace("{{FOOTER}}", escape(site.get("footer", "")))
            .replace("{{COUNT}}", str(len(rows)))
            .replace("{{SECTIONS}}", sections))
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nBuilt index.html with {len(rows)} poster(s) in "
          f"{len({r['team'] for r in rows})} section(s) "
          f"({rendered_count} rendered, {cached_count} cached).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
