#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
pandoc article.tex --from=latex --to=gfm --wrap=none --standalone \
  --template=tools/medium.md.template --lua-filter=tools/medium.lua --output=article.md
builddir=$(mktemp -d)
trap 'rm -rf "$builddir"' EXIT
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$builddir" article.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$builddir" article.tex
cp "$builddir/article.pdf" article.pdf
