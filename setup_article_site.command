#!/bin/bash
# Run from an extracted archive or the articles repository. macOS / Bash 3.2+.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

usage() {
  echo 'Usage: bash setup_article_site.command [path-to-articles-repo] [--build-only] [--port NUMBER]'
  echo 'Without a path, detect the existing checkout or clone it beside this script.'
}
REPO=""
PORT=8000
PREVIEW=yes
while [[ $# -gt 0 ]]; do
  case "$1" in
    --build-only) PREVIEW=no; shift;;
    --port) [[ $# -ge 2 ]] || { usage; exit 2; }; PORT="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    --*) usage; exit 2;;
    *) [[ -z "$REPO" ]] || { usage; exit 2; }; REPO="$1"; shift;;
  esac
done
for tool in git python3 pandoc; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: $tool is required." >&2
    [[ "$tool" != pandoc ]] || echo 'Install it with: brew install pandoc' >&2
    exit 1
  fi
done
is_repo() {
  [[ -d "$1/Medium" ]] && git -C "$1" rev-parse --show-toplevel >/dev/null 2>&1
}
if [[ -z "$REPO" ]]; then
  for candidate in "$HERE" "$PWD" "$HERE/articles" "$HERE/../articles"; do
    if is_repo "$candidate"; then REPO="$candidate"; break; fi
  done
  if [[ -z "$REPO" ]]; then
    REPO="$HERE/articles"
    if [[ -e "$REPO" ]]; then
      echo "ERROR: $REPO exists but is not an articles checkout. Supply the path to your existing repo." >&2
      exit 1
    fi
    echo "Cloning the public articles repository into $REPO"
    git clone --depth 1 https://github.com/popoloni/articles.git "$REPO"
  fi
fi
if ! is_repo "$REPO"; then
  echo "ERROR: '$REPO' is not a Git checkout containing Medium/." >&2
  echo 'Supply the path to the articles repository, not its docs/ or scripts/ folder.' >&2
  exit 1
fi
REPO="$(cd "$REPO" && pwd -P)"
TOP="$(git -C "$REPO" rev-parse --show-toplevel)"
TOP="$(cd "$TOP" && pwd -P)"
[[ "$REPO" == "$TOP" ]] || { echo "ERROR: expected repository root: $TOP" >&2; exit 1; }
echo "Repository: $REPO"
echo "Source revision: $(git -C "$REPO" rev-parse --short HEAD)"
# A previously generated docs directory may be replaced; any other site must be reviewed first.
if [[ -d "$REPO/docs" && ! -f "$REPO/docs/.article-site-generated" ]] && [[ -n "$(ls -A "$REPO/docs")" ]]; then
  echo 'ERROR: docs/ contains files not owned by this generator. It has been left unchanged.' >&2
  exit 1
fi
# Preserve Medium and unrelated scripts. Do not pull, reset, commit or push automatically.
mkdir -p "$REPO/scripts"
if [[ "$HERE" != "$REPO" ]]; then
  for f in build_article_site.py preview_article_site.py articles.css articles.js; do
    cp "$HERE/scripts/$f" "$REPO/scripts/$f"
  done
  # Preserve an edited catalogue if one already exists.
  if [[ ! -f "$REPO/scripts/article_catalog.json" ]]; then
    cp "$HERE/scripts/article_catalog.json" "$REPO/scripts/article_catalog.json"
  fi
  cp "$HERE/INSTALL_ARTICLE_SITE.md" "$REPO/INSTALL_ARTICLE_SITE.md"
  cp "$HERE/setup_article_site.command" "$REPO/setup_article_site.command"
fi
cd "$REPO"
# The generator reads the current committed snapshot, not uncommitted Medium content.
if [[ -n "$(git status --porcelain -- Medium)" ]]; then
  echo 'NOTE: Medium/ has uncommitted changes. This build uses the committed source snapshot (HEAD).'
fi
python3 scripts/build_article_site.py
if [[ ! -f docs/index.html ]]; then
  echo "ERROR: build did not produce $REPO/docs/index.html" >&2
  exit 1
fi
echo "Build complete: $REPO/docs/index.html"
if [[ "$PREVIEW" == yes ]]; then
  exec python3 scripts/preview_article_site.py --port "$PORT"
fi
