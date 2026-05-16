# LaTeX → Medium publishing toolchain

A small, reusable pipeline that converts a LaTeX article into a
Medium-friendly Markdown document plus a folder of JPEG assets (figures and
tables rendered as isolated images), then publishes the result on this GitHub
repository so Medium can fetch the images via `raw.githubusercontent.com`.

Three scripts:

| Script | Purpose |
|--------|---------|
| [`latex_to_medium.py`](latex_to_medium.py) | Convert a `.tex` file to `medium.md` + `assets/`. Each figure/table is rendered as an isolated `standalone` LaTeX document → clean JPEG (no page-context bleed). |
| [`run_export.sh`](run_export.sh) | Convenience wrapper that invokes the Python converter with the project's virtualenv. |
| [`publish_github.sh`](publish_github.sh) | Regenerates the export with absolute image URLs, copies the output into this repo under `Medium/<YYYYMMDD>_<Title>/`, commits and pushes. |

## Prerequisites

- **TeX Live** (or any pdfLaTeX distribution) with the `standalone`, `tikz`,
  `pgfplots`, `tabularx`, `booktabs`, `ragged2e` packages.
- **Python 3.10+** in a virtualenv with:
  ```bash
  pip install pymupdf pillow
  ```
- **git**, with push access to this repo (or another repo where you want to
  host the assets).

The scripts assume the following layout in the *source project* (the one that
holds the LaTeX article):

```
<project root>/
├── .venv/                       # Python venv with pymupdf, pillow
└── article/
    ├── main.tex                 # your article
    └── medium_export/           # checked-out copy of the scripts here
        ├── latex_to_medium.py
        ├── run_export.sh
        └── publish_github.sh
```

The Python venv path the wrappers look for is `<project root>/.venv/bin/python`.

## 1. Convert LaTeX → Markdown + JPEG (local only)

```bash
cd article
./medium_export/run_export.sh                       # uses main.tex
./medium_export/run_export.sh path/to/other.tex     # any other article
KEEP_BUILD=1 ./medium_export/run_export.sh          # keep per-float .tex/.pdf
```

Output appears under `article/medium_export/output/<tex-stem>/`:

```
medium.md             # Markdown with relative links: assets/fig_001.jpg
assets/               # fig_NNN.jpg, tab_NNN.jpg
float_map.csv         # idx,kind,caption,image,rendered_ok,error
```

To preview locally, open `medium.md` in VS Code (`Cmd+Shift+V`) or any
Markdown viewer.

## 2. Publish to GitHub (so Medium can fetch images)

The `publish_github.sh` script:

1. Re-runs the converter with `--image-base-url` set to the raw URL of the
   article's `assets/` directory on GitHub.
2. Copies `medium.md` (with absolute image URLs) + `assets/` + `float_map.csv`
   into `<repo>/Medium/<YYYYMMDD>_<TitleWithoutSpaces>/`.
3. Commits and pushes.

### One-time setup

```bash
# Clone the publishing repo somewhere local:
git clone https://github.com/<user>/<repo>.git ~/code/articles
```

### Each publish

```bash
cd <project root>/article
GH_REPO_DIR=~/code/articles ./medium_export/publish_github.sh
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `GH_REPO_DIR` | *(required)* | Path to the local clone of the publishing repo. Must have an `origin` remote pointing to GitHub. |
| `GH_BRANCH` | `main` | Branch to push to. |
| `GH_SUBDIR` | `Medium` | Top-level folder inside the repo. |
| `SLUG` | `<YYYYMMDD>_<TitleWithoutSpaces>` | Override the auto-generated slug. The title is parsed from `\title{}` in the `.tex`; non-alphanumeric chars are stripped except hyphens. |
| `PUBLISH_DATE` | `$(date +%Y%m%d)` | Override the date prefix (useful for backdating). |
| `INPUT_TEX` | `main.tex` | Source `.tex` (relative to `article/`). Can also be passed positionally. |
| `GH_NO_PUSH` | `0` | If `1`, commit but don't push. |
| `GH_DRY_RUN` | `0` | If `1`, only print the plan, don't touch git. |

### Examples

```bash
# Publish main.tex with auto-derived slug (today's date + title)
GH_REPO_DIR=~/code/articles ./medium_export/publish_github.sh

# Publish a different article, backdated, with a custom slug
GH_REPO_DIR=~/code/articles \
PUBLISH_DATE=20260401 \
SLUG=20260401_MyCustomSlug \
./medium_export/publish_github.sh paper2.tex

# Stage only (no push), then inspect
GH_NO_PUSH=1 GH_REPO_DIR=~/code/articles ./medium_export/publish_github.sh
```

## 3. Import into Medium

After publishing, the script prints a URL like:

```
https://github.com/<user>/<repo>/blob/main/Medium/20260516_.../medium.md
```

**Option A — Medium native import** (try first):

1. Open Medium → your profile → **Stories** → **Import a story**
2. Paste the GitHub blob URL above
3. Medium fetches the file, parses headings/quotes/images, and creates a draft

**Option B — copy/paste fallback** (always works):

1. Open the local file:
   `~/code/articles/Medium/<YYYYMMDD>_<Title>/medium.md`
2. Render in VS Code (`Cmd+Shift+V`) or any Markdown previewer
3. Select all rendered output, copy, paste into Medium's editor
4. Medium fetches each image from `raw.githubusercontent.com` and re-hosts it
   on its CDN automatically

## How figure/table rendering works (in short)

The biggest pitfall when converting LaTeX articles is that ripping the
compiled PDF page-by-page bleeds running headers, neighboring paragraphs and
adjacent floats into the cropped image. This pipeline avoids that completely:

For each `figure`/`table` environment found in the `.tex`, the converter:

1. Strips the float wrapper, `\caption{...}` and `\label{...}`.
2. Wraps the remaining inner content in a minimal `\documentclass[border=10pt,varwidth=18cm]{standalone}` document with TikZ, pgfplots, tabularx and booktabs preloaded.
3. Compiles it with `pdflatex` (two passes for pgfplots).
4. Renders the resulting single-page PDF at 2.5× scale via PyMuPDF → JPEG.

The caption is preserved in the Markdown as italicized text below the image,
e.g.:

```markdown
![Stylized context-rot curves ...](.../assets/fig_001.jpg)

*Stylized context-rot curves reconstructed from the Chroma (2025) study.*
```

## Troubleshooting

- **Empty image / `[FAIL]` in the run output** — check
  `medium_export/output/<slug>/_build/float_NNN/` (run with `KEEP_BUILD=1`)
  for the per-float `.log`. Usually a missing `\usepackage` or a custom macro
  the standalone preamble doesn't know about; add it to `STANDALONE_PREAMBLE`
  in `latex_to_medium.py`.
- **Medium import shows broken images** — verify the raw URL is reachable:
  `curl -I https://raw.githubusercontent.com/<user>/<repo>/main/Medium/<slug>/assets/fig_001.jpg`
  should return `200`. If `404`, the push didn't complete or the repo is
  private (Medium needs public URLs).
- **`failed to compile regex` in zsh** — make sure you're on a recent zsh
  (5.x). Older versions reject some PCRE-style patterns.

## License

The scripts are MIT-licensed. The articles themselves carry their own
copyright notice in `medium.md`.
