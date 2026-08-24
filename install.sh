#!/bin/sh

set -eu

DEFAULT_SOURCE="https://github.com/showpiecep/newproj/releases/latest/download/newproj-templates.tar.gz"
SOURCE="${NEWPROJ_SOURCE:-$DEFAULT_SOURCE}"

if ! command -v uv >/dev/null 2>&1; then
  printf '%s\n' 'newproj installer: uv is required: https://docs.astral.sh/uv/' >&2
  exit 1
fi

uv tool install --force "$SOURCE"

printf '\n%s\n' 'newproj installed successfully.'
printf '%s\n' 'If the command is not in PATH yet, run: uv tool update-shell'
printf '%s\n' 'Then open a new terminal and run: newproj'

if [ -f "${HOME}/.local/share/newproj/newproj.zsh" ]; then
  printf '\n%s\n' 'A legacy Zsh installation was found.'
  printf '%s\n' 'Remove its managed block with the old uninstaller, then restart Zsh.'
fi
