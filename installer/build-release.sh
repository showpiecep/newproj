#!/bin/sh

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPOSITORY_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

git -C "$REPOSITORY_ROOT" diff --quiet
git -C "$REPOSITORY_ROOT" diff --cached --quiet

OUTPUT_DIR="$REPOSITORY_ROOT/dist/$VERSION"
ARCHIVE_PATH="$OUTPUT_DIR/newproj-templates.tar.gz"
CHECKSUM_PATH="$ARCHIVE_PATH.sha256"

mkdir -p "$OUTPUT_DIR"
git -C "$REPOSITORY_ROOT" archive \
  --format=tar.gz \
  --prefix="newproj-templates-$VERSION/" \
  --output="$ARCHIVE_PATH" \
  HEAD

if command -v shasum >/dev/null 2>&1; then
  CHECKSUM="$(shasum -a 256 "$ARCHIVE_PATH" | awk '{print $1}')"
else
  CHECKSUM="$(sha256sum "$ARCHIVE_PATH" | awk '{print $1}')"
fi

printf '%s  %s\n' "$CHECKSUM" "$(basename "$ARCHIVE_PATH")" >"$CHECKSUM_PATH"

echo "Release artifacts:"
echo "  $ARCHIVE_PATH"
echo "  $CHECKSUM_PATH"
