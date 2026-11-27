#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
pandoc article.md --standalone --embed-resources --css=article.css --metadata pagetitle='Beyond the Loop: The Three-Loop Architecture for AI Agents' -o article.html
