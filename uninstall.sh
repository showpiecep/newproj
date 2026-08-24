#!/bin/sh

set -eu

if ! command -v uv >/dev/null 2>&1; then
  printf '%s\n' 'newproj uninstaller: uv is required: https://docs.astral.sh/uv/' >&2
  exit 1
fi

uv tool uninstall newproj
