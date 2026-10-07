#!/bin/bash
# Source from the extracted package root. This does NOT create runtimes or run models.
export PACKAGE="$(pwd)"
export LAB="$HOME/LocalAI/qwen-bonsai-lab"
export PY="$(brew --prefix python@3.11)/bin/python3.11"
# A sourced file is parsed non-interactively. Enable pasted comments only for
# this zsh session; never edit the user's .zshrc or system shell configuration.
if [ -n "${ZSH_VERSION:-}" ]; then
  setopt interactive_comments
fi
set -o pipefail
