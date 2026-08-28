# Poster Showcase

A static, single-page website that showcases one-page poster PDFs to a public
audience. Posters are grouped into labeled team/topic sections, shown as image
previews (so no PDF viewers are embedded), and every card links to the original
PDF. A prominent **"Show me a random poster"** button jumps to a random poster.

No database, CMS, framework, or backend — just HTML, CSS, JS, and one Python
build script. The output is a folder of static files you can host on GitHub
Pages, Netlify, or an institutional web server.

## What's here

| Path | Kind | Purpose |
| --- | --- | --- |
| `posters/*.pdf` | **source** | Your one-page poster PDFs. |
| `data/posters.csv` | **source** | One row per poster: title, authors, team, description. |
| `data/teams.csv` | **source** | Section display names and their order. |
| `data/site.json` | **source** | Page title, subtitle, intro, footer. |
| `scripts/build-gallery.py` | **source** | Regenerates previews + `index.html`. |
| `scripts/template.html` | **source** | HTML shell the page is built from. |
| `styles.css`, `script.js` | **source** | Styling and the random-poster button. |
| `index.html` | *generated* | The gallery page. **Do not edit by hand.** |
| `previews/thumbnails/`, `previews/large/` | *generated* | WebP previews. |

Generated files are recreated by the build script; source files are what you edit.

## Required local tools

- **Python 3.9+**
- Python packages: **PyMuPDF** and **Pillow**

```bash
pip install -r requirements.txt
```

PyMuPDF renders the PDFs to images with no system-level dependencies (no
Homebrew, poppler, or ImageMagick needed), so the build runs the same on a
laptop or in CI.

## Add or update a poster

1. Drop the one-page PDF into `posters/`. Any filename works, but the build
   reads a convention to pre-fill the section and title:

   ```
   [TEAM][subteam] My Poster Title.pdf     ->  team=TEAM, subteam=subteam, title="My Poster Title"
   [TEAM] My Poster Title.pdf              ->  team=TEAM, title="My Poster Title"
   [TEAM].pdf                              ->  team=TEAM, title="TEAM"
   ```

2. Run the build (see below). A new row appears in `data/posters.csv` with
   placeholder values derived from the filename.

3. Open `data/posters.csv` in a spreadsheet or text editor and fill in the real
   **title**, **authors**, and (optional) **description**. Leave `id`,
   `thumbnail`, and `preview` alone — the build manages those. Your edits are
   preserved on every subsequent build.

To **replace** a poster, overwrite the PDF in `posters/` and run the build (use
`--force` if the filename didn't change, so the preview is re-rendered). To
**remove** one, delete its PDF *and* its row from `data/posters.csv`.

## Assign a poster to a team/topic

- The **section** a poster appears in is its `team` value in `data/posters.csv`.
  Change that value to move a poster; posters sharing a `team` value are grouped
  together.
- To rename a section heading or reorder sections, edit `data/teams.csv`:
  - `team` — the code used in `posters.csv` (e.g. `AR`).
  - `label` — the heading shown on the page (e.g. `Applied Research`).
  - `order` — lower numbers appear first.
- The `subteam` value is shown as a small badge on each card.

> The team codes and titles pre-filled from filenames are **placeholders**.
> Rename them to human-readable labels; nothing is invented on your behalf.

## Change the page title / intro

Edit `data/site.json` (`title`, `subtitle`, `intro`, `footer`) and rebuild.

## Regenerate the site

```bash
python3 scripts/build-gallery.py           # incremental: only new/changed PDFs re-render
python3 scripts/build-gallery.py --force    # re-render every preview image
python3 scripts/build-gallery.py --check    # validate only; render/write nothing
```

`--check` validates the metadata and PDFs and exits non-zero on any problem
(missing PDF, duplicate id, empty title, unreadable PDF). Use it in CI.

## Preview locally

Open with a local web server (needed so relative links resolve correctly):

```bash
python3 -m http.server 8000
# then visit http://localhost:8000/
```

## Publish as a static site

Everything needed is in this folder: `index.html`, `styles.css`, `script.js`,
`posters/`, and `previews/`. (`data/` and `scripts/` are harmless to publish but
not required by visitors.)

- **GitHub Pages:** commit the repo and enable Pages for the branch, serving
  from the repository root.
- **Netlify:** drag-and-drop the folder, or connect the repo with build command
  `python3 scripts/build-gallery.py` and publish directory `.`.
- **Institutional web server:** copy the folder to the served directory.

## Notes on design choices

- **No JavaScript required** to browse: the gallery is plain HTML. JS only adds
  the random-poster button, which hides itself when JS is disabled.
- Previews are **WebP**, sized ~600px (thumbnail) and ~1800px (large), aspect
  ratio preserved with no cropping. Images lazy-load below the fold and carry
  width/height to avoid layout shift.
- The random button never picks the same poster twice in a row, scrolls it into
  view, moves focus to it, briefly highlights it, and respects
  `prefers-reduced-motion`.
