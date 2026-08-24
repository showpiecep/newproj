#!/bin/sh

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPOSITORY_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/newproj-test.XXXXXX")"
TEST_HOME="$TEST_ROOT/home"

cleanup() {
  rm -rf "$TEST_ROOT"
}
trap cleanup EXIT HUP INT TERM

cd "$REPOSITORY_ROOT"
mkdir -p "$TEST_HOME"
uv run --locked pytest
uv run --locked ruff check src tests
uv build --out-dir "$TEST_ROOT/dist"

WHEEL="$(find "$TEST_ROOT/dist" -name '*.whl' -type f -print -quit)"
[ -n "$WHEEL" ] || {
  echo "newproj test: wheel was not built" >&2
  exit 1
}

HOME="$TEST_HOME" \
  NEWPROJ_SOURCE="$WHEEL" \
  UV_TOOL_DIR="$TEST_ROOT/tools" \
  UV_TOOL_BIN_DIR="$TEST_ROOT/bin" \
  sh "$REPOSITORY_ROOT/install.sh"
"$TEST_ROOT/bin/newproj" --version
"$TEST_ROOT/bin/newproj" list
"$TEST_ROOT/bin/newproj" create \
  --parent "$TEST_ROOT/projects" \
  --name smoke_project \
  --template fastapi-yaml \
  --defaults \
  --non-interactive

test -f "$TEST_ROOT/projects/smoke_project/pyproject.toml"
test -f "$TEST_ROOT/projects/smoke_project/src/smoke_project/main.py"

echo "newproj cross-platform smoke-test passed"
