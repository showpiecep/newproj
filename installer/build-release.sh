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
PROJECT_VERSION="$(sed -n 's/^version = "\([^"]*\)"$/\1/p' "$REPOSITORY_ROOT/pyproject.toml")"
TAG_VERSION="${VERSION#v}"

[ -n "$PROJECT_VERSION" ] || {
  echo "Could not read project version from pyproject.toml" >&2
  exit 1
}
[ "$PROJECT_VERSION" = "$TAG_VERSION" ] || {
  echo "Tag $VERSION does not match pyproject.toml version $PROJECT_VERSION" >&2
  exit 1
}

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

# Обычный uv build сначала создаёт sdist, затем wheel из него. Это важно:
# sdist уважает VCS-ignore и не позволяет случайному config.yaml из рабочей
# копии попасть во wheel через force-include каталога templates.
uv build --out-dir "$OUTPUT_DIR" "$REPOSITORY_ROOT"

echo "Release artifacts:"
echo "  $ARCHIVE_PATH"
echo "  $CHECKSUM_PATH"
for wheel in "$OUTPUT_DIR"/*.whl; do
  echo "  $wheel"
done
