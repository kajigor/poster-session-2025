---
id: poster-gallery
type: goal-and-requirements
title: Poster Showcase — Static One-Page Gallery
status: draft
---

# Poster Showcase — Static One-Page Gallery

A static, single-page website that showcases one-page scientific poster PDFs to a
public audience, grouped by team, with image previews and a "show me a random
poster" feature. No database, CMS, framework, or backend — plain HTML/CSS/JS plus a
small Python generation script.

## Overview

Presenters bring one-page poster PDFs. The site displays every poster as an image
card on one page, organized into labeled team/topic sections, and lets visitors open
or download the original PDF. A build script converts each PDF's first page into WebP
previews and regenerates the gallery HTML from a metadata file. The output is a
folder of static files suitable for GitHub Pages, Netlify, or an institutional web
server.

## Problem

Poster PDFs are heavy, awkward to browse in bulk, and normally require opening each
file individually or embedding many PDF viewers. There is no lightweight way to
present a whole event's posters on one page that loads fast, works on phones, and
stays usable without JavaScript.

## Target Users

- **Visitors (public):** browse posters by team, preview at a glance, open/download
  the source PDF, and jump to a random poster for serendipity.
- **Maintainer (non-developer):** adds/updates poster PDFs and edits a single
  metadata file, then reruns one script to regenerate the site.

## V1 Scope

In v1:

- One HTML page with an event title, short intro, and a prominent **"Show me a
  random poster"** button near the top.
- Posters grouped into clearly labeled sections by team/topic (derived from the
  `[TEAM][subteam] Title.pdf` filename convention, overridable in metadata).
- Responsive poster cards: preview image, title, authors (if known), optional
  description; image and title open the original PDF in a new tab; explicit
  "View / Download PDF" link.
- Build script (`scripts/build-gallery.py`) that: renders each PDF's first page to a
  gallery thumbnail (~600px) and a larger preview (~1800px) as WebP, preserving
  aspect ratio without cropping; merges/creates rows in a CSV metadata file; and
  regenerates `index.html`. Repeatable and idempotent.
- Metadata in `data/posters.csv` (one row per poster) plus `data/teams.csv` (team
  display labels + order) and `data/site.json` (title/intro/footer) — all editable
  by a non-developer. Derived placeholders only; no fabricated scientific content.
- Random-poster interaction: uniform choice, never the same twice in a row, smooth
  scroll into view, keyboard focus, temporary highlight, honoring
  `prefers-reduced-motion`, working after content changes with no hard-coded list.
- Performance/a11y: lazy-loaded below-the-fold images, image dimensions to limit
  layout shift, meaningful alt text from known metadata only, keyboard nav with
  visible focus, no full-resolution PDFs on initial load.
- Lightweight validation (in the build script) for duplicate IDs, missing PDFs,
  missing required metadata, and failed image generation.

Out of v1: multi-page PDF handling beyond page 1, search/filtering, tags/facets,
per-poster pages, comments/analytics, any server-side component.

## Done Conditions

- Every source PDF appears exactly once, under the correct team/topic heading, and
  its preview links to the correct PDF.
- No poster content is cropped in generated previews.
- The random button selects, scrolls to, focuses, and highlights a poster; not the
  same one twice consecutively.
- Layout is usable at narrow mobile and wide desktop sizes; keyboard navigable.
- No broken local links, missing images, or browser-console errors.
- Basic gallery browsing works with JavaScript disabled.
- Generated files (`index.html`, `previews/`) are clearly distinguished from source
  (`data/`, `scripts/`, `styles.css`, `script.js`).
- Rerunning the script after adding/removing a PDF or editing metadata updates the
  site without manual HTML edits.

## Technology

| Aspect | Choice | Rationale |
| --- | --- | --- |
| Page | Static HTML/CSS/JS | No backend/framework per constraints; hostable anywhere |
| PDF → image | PyMuPDF (pip) + Pillow → WebP | Self-contained, no system deps; portable across machines/CI |
| Metadata | CSV + small JSON | Non-developer editable; diff-friendly; no DB/CMS |
| Build | `scripts/build-gallery.py` | One repeatable, idempotent command |

## Notes

- Team codes in filenames (e.g. `AR`, `ML`) are kept as placeholder section labels;
  their human-readable expansions are *unconfirmed* — the maintainer edits
  `data/teams.csv` to rename and reorder sections. _(inferred — not confirmed)_
- Authors are unknown from filenames and left blank until the maintainer fills them
  in; alt text and cards never invent authors or findings. _(inferred)_
- Event title uses a generic placeholder ("Poster Showcase") pending real branding.
