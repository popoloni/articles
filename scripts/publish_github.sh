#!/usr/bin/env zsh
# Publish the converted article to a GitHub repository so Medium can
# fetch images from raw.githubusercontent.com. Produces a Medium-ready
# `medium.remote.md` with absolute image URLs.
#
# Workflow
# --------
#   1. (Re)generate the export with --image-base-url pointing at the
#      raw GitHub URL of the article's assets directory.
#   2. Copy medium.remote.md (renamed medium.md inside the repo) and
#      assets/ into <repo>/<subdir>/<slug>/.
#   3. git add + commit + push on the configured branch.
#   4. Print the URL to paste into Medium's "Import a story" feature
#      (and a fallback set of raw URLs you can use for copy/paste).
#
# Required env vars
# -----------------
#   GH_REPO_DIR   Path to a LOCAL clone of the publishing repo.
#                 Must have an `origin` remote pointing to GitHub.
#
# Optional env vars
# -----------------
#   GH_BRANCH     Branch to push to.                Default: main
#   GH_SUBDIR     Subdirectory inside the repo.     Default: Medium
#   GH_NO_PUSH    If set to 1, commit but don't push.
#   GH_DRY_RUN    If set to 1, only print the plan, don't touch git.
#   INPUT_TEX     Source .tex (relative to article/).  Default: main.tex
#   SLUG          Override the auto-generated slug. Default:
#                 <YYYYMMDD>_<TitleWithoutSpaces> derived from \title{}.
#   PUBLISH_DATE  Override publication date (YYYYMMDD). Default: today.
#
# Usage
# -----
#   GH_REPO_DIR=~/code/my-articles ./medium_export/publish_github.sh
#   GH_REPO_DIR=~/code/my-articles GH_BRANCH=main GH_SUBDIR=posts \
#     ./medium_export/publish_github.sh paper2.tex

set -euo pipefail

SCRIPT_DIR="${0:A:h}"
ARTICLE_DIR="${SCRIPT_DIR:h}"
PROJECT_ROOT="${ARTICLE_DIR:h}"
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
CONVERTER="${SCRIPT_DIR}/latex_to_medium.py"
OUTPUT_BASE="${SCRIPT_DIR}/output"

INPUT_TEX="${1:-${INPUT_TEX:-main.tex}}"
GH_BRANCH="${GH_BRANCH:-main}"
GH_SUBDIR="${GH_SUBDIR:-Medium}"

err() { print -P "%F{red}ERROR%f: $*" >&2; }
info() { print -P "%F{cyan}==>%f $*"; }

# --- Pre-flight ------------------------------------------------------------
if [[ -z "${GH_REPO_DIR:-}" ]]; then
  err "GH_REPO_DIR is not set. Point it at a local clone of your publishing GitHub repo."
  exit 2
fi
if [[ ! -d "$GH_REPO_DIR/.git" ]]; then
  err "GH_REPO_DIR ($GH_REPO_DIR) is not a git repository."
  exit 2
fi
if [[ ! -x "$PYTHON_BIN" ]]; then
  err "Python venv not found at $PYTHON_BIN"
  exit 2
fi
if [[ ! -f "$CONVERTER" ]]; then
  err "Converter not found at $CONVERTER"
  exit 2
fi

cd "$ARTICLE_DIR"
if [[ ! -f "$INPUT_TEX" ]]; then
  err "Input .tex not found: $ARTICLE_DIR/$INPUT_TEX"
  exit 2
fi

# --- Resolve repo identity (owner/name) -----------------------------------
ORIGIN_URL=$(git -C "$GH_REPO_DIR" remote get-url origin 2>/dev/null || true)
if [[ -z "$ORIGIN_URL" ]]; then
  err "Repo at $GH_REPO_DIR has no 'origin' remote."
  exit 2
fi

# Accept both git@github.com:owner/repo(.git) and https://github.com/owner/repo(.git)(/)
# Strip common suffixes, then split on the GitHub host marker.
_normalized="${ORIGIN_URL%/}"
_normalized="${_normalized%.git}"
case "$_normalized" in
  git@github.com:*)
    _path="${_normalized#git@github.com:}"
    ;;
  https://github.com/*|http://github.com/*)
    _path="${_normalized#http*://github.com/}"
    ;;
  ssh://git@github.com/*)
    _path="${_normalized#ssh://git@github.com/}"
    ;;
  *)
    err "Cannot parse GitHub owner/name from origin URL: $ORIGIN_URL"
    exit 2
    ;;
esac
OWNER="${_path%%/*}"
REPO="${_path#*/}"
if [[ -z "$OWNER" || -z "$REPO" || "$OWNER" == "$_path" ]]; then
  err "Cannot parse owner/repo from path: $_path (origin: $ORIGIN_URL)"
  exit 2
fi

SLUG="${SLUG:-}"
if [[ -z "$SLUG" ]]; then
  PUBLISH_DATE="${PUBLISH_DATE:-$(date +%Y%m%d)}"
  TITLE=$("$PYTHON_BIN" - "$INPUT_TEX" <<PY
import pathlib, sys
sys.path.insert(0, "$SCRIPT_DIR")
from latex_to_medium import extract_title, strip_latex_comments
raw = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
raw = strip_latex_comments(raw)
title, _ = extract_title(raw)
print(title)
PY
)
  if [[ -z "$TITLE" ]]; then
    err "Could not extract title from $INPUT_TEX"
    exit 2
  fi
  # Sanitize: drop everything except [A-Za-z0-9-], collapse spaces.
  SAFE_TITLE=$(print -r -- "$TITLE" | sed -E 's/[^A-Za-z0-9 -]//g; s/[[:space:]]+//g')
  SLUG="${PUBLISH_DATE}_${SAFE_TITLE}"
fi

REPO_REL_DIR="${GH_SUBDIR}/${SLUG}"
RAW_BASE="https://raw.githubusercontent.com/${OWNER}/${REPO}/${GH_BRANCH}/${REPO_REL_DIR}"
BLOB_URL="https://github.com/${OWNER}/${REPO}/blob/${GH_BRANCH}/${REPO_REL_DIR}/medium.md"

info "Article dir : $ARTICLE_DIR"
info "Input       : $INPUT_TEX"
info "Repo        : $OWNER/$REPO  (branch: $GH_BRANCH)"
info "Repo path   : $REPO_REL_DIR"
info "Raw base    : $RAW_BASE"
echo

if [[ "${GH_DRY_RUN:-0}" == "1" ]]; then
  info "DRY RUN: skipping conversion and git operations."
  exit 0
fi

# --- Regenerate export with absolute image URLs ----------------------------
info "Regenerating Markdown + assets with absolute image URLs..."
"$PYTHON_BIN" "$CONVERTER" \
  --input "$INPUT_TEX" \
  --output-dir "$OUTPUT_BASE" \
  --image-base-url "$RAW_BASE"

LOCAL_OUT="${OUTPUT_BASE}/${INPUT_TEX:t:r}"
if [[ ! -f "$LOCAL_OUT/medium.remote.md" ]]; then
  err "medium.remote.md not produced — conversion failed."
  exit 1
fi

# --- Stage into the publishing repo ----------------------------------------
TARGET_DIR="${GH_REPO_DIR}/${REPO_REL_DIR}"
info "Staging into $TARGET_DIR ..."
mkdir -p "$TARGET_DIR"
# Wipe previous assets to avoid stale files, then copy fresh ones.
rm -rf "$TARGET_DIR/assets"
mkdir -p "$TARGET_DIR/assets"
cp -R "$LOCAL_OUT/assets/." "$TARGET_DIR/assets/"
cp "$LOCAL_OUT/medium.remote.md" "$TARGET_DIR/medium.md"
cp "$LOCAL_OUT/float_map.csv"    "$TARGET_DIR/float_map.csv"

# --- Commit + push ---------------------------------------------------------
cd "$GH_REPO_DIR"
git checkout "$GH_BRANCH" 2>/dev/null || git checkout -b "$GH_BRANCH"
git add "$REPO_REL_DIR"

if git diff --cached --quiet; then
  info "No changes to commit (article already up-to-date)."
else
  COMMIT_MSG="publish: ${SLUG} ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  git commit -m "$COMMIT_MSG"
  info "Committed: $COMMIT_MSG"
fi

if [[ "${GH_NO_PUSH:-0}" == "1" ]]; then
  info "GH_NO_PUSH=1 — skipping push."
else
  info "Pushing to origin/$GH_BRANCH ..."
  git push origin "$GH_BRANCH"
fi

# --- Summary ---------------------------------------------------------------
echo
print -P "%F{green}DONE%f"
echo
echo "Medium import URL (try first):"
echo "  $BLOB_URL"
echo
echo "If Medium's importer doesn't like the GitHub blob page, fall back to:"
echo "  1. Open locally: $TARGET_DIR/medium.md"
echo "  2. Preview it in any Markdown viewer (VS Code preview is fine)."
echo "  3. Copy the rendered output and paste into Medium's editor."
echo "     Medium will fetch and re-host the images from:"
echo "     $RAW_BASE/assets/*.jpg"
echo
echo "Raw image base URL (for sanity-check):"
echo "  $RAW_BASE/assets/fig_001.jpg"
