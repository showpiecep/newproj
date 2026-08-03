#!/bin/sh

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPOSITORY_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
REPOSITORY_PARENT="$(dirname "$REPOSITORY_ROOT")"
REPOSITORY_NAME="$(basename "$REPOSITORY_ROOT")"

TEMPLATE_NAME="fastapi-yaml"

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/newproj-installer-test.XXXXXX")"
TEST_HOME="$TEMP_ROOT/home"
ARCHIVE_PATH="$TEMP_ROOT/newproj-templates.tar.gz"

cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$TEST_HOME"
printf '# Existing user configuration\n' >"$TEST_HOME/.zshrc"

COPYFILE_DISABLE=1 tar -czf "$ARCHIVE_PATH" \
  --exclude='.git' \
  --exclude='*/.git' \
  --exclude='.venv' \
  --exclude='*/.venv' \
  --exclude='dist' \
  --exclude='*/dist' \
  --exclude='config.yaml' \
  --exclude='*/config.yaml' \
  -C "$REPOSITORY_PARENT" \
  "$REPOSITORY_NAME"

tar -tzf "$ARCHIVE_PATH" | grep -q "/templates/$TEMPLATE_NAME/copier.yml$"
if tar -tzf "$ARCHIVE_PATH" | grep -qE '(^|/)(\.git|config\.yaml)(/|$)'; then
  echo "test archive contains files that must never be released" >&2
  exit 1
fi

if command -v shasum >/dev/null 2>&1; then
  CHECKSUM="$(shasum -a 256 "$ARCHIVE_PATH" | awk '{print $1}')"
else
  CHECKSUM="$(sha256sum "$ARCHIVE_PATH" | awk '{print $1}')"
fi

run_installer() {
  env \
    HOME="$TEST_HOME" \
    NEWPROJ_VERSION="test" \
    NEWPROJ_ARCHIVE_URL="file://$ARCHIVE_PATH" \
    NEWPROJ_CHECKSUM="$CHECKSUM" \
    NEWPROJ_TEMPLATES_DIR="$TEST_HOME/templates" \
    NEWPROJ_INSTALL_DIR="$TEST_HOME/.local/share/newproj" \
    NEWPROJ_RC_FILE="$TEST_HOME/.zshrc" \
    sh "$REPOSITORY_ROOT/install.sh"
}

run_installer

test -f "$TEST_HOME/templates/$TEMPLATE_NAME/.newproj-managed"
test -f "$TEST_HOME/templates/$TEMPLATE_NAME/copier.yml"
test -f "$TEST_HOME/.local/share/newproj/newproj.zsh"
test ! -e "$TEST_HOME/templates/$TEMPLATE_NAME/install.sh"
test "$(grep -c '^# >>> newproj >>>$' "$TEST_HOME/.zshrc")" -eq 1
test "$(grep -c '^# <<< newproj <<<$' "$TEST_HOME/.zshrc")" -eq 1
zsh -n "$TEST_HOME/.zshrc"

HOME="$TEST_HOME" zsh -dfc \
  'source "$HOME/.zshrc"; whence -w newproj' |
  grep -q '^newproj: function$'

run_installer

test "$(grep -c '^# >>> newproj >>>$' "$TEST_HOME/.zshrc")" -eq 1
test "$(grep -c '^# <<< newproj <<<$' "$TEST_HOME/.zshrc")" -eq 1

NO_RC_HOME="$TEMP_ROOT/no-rc-home"
mkdir -p "$NO_RC_HOME"
env \
  HOME="$NO_RC_HOME" \
  NEWPROJ_VERSION="test" \
  NEWPROJ_ARCHIVE_URL="file://$ARCHIVE_PATH" \
  NEWPROJ_CHECKSUM="$CHECKSUM" \
  NEWPROJ_TEMPLATES_DIR="$NO_RC_HOME/templates" \
  NEWPROJ_INSTALL_DIR="$NO_RC_HOME/.local/share/newproj" \
  NEWPROJ_RC_FILE="$NO_RC_HOME/.zshrc" \
  NEWPROJ_NO_MODIFY_RC=1 \
  sh "$REPOSITORY_ROOT/install.sh" >/dev/null
test ! -e "$NO_RC_HOME/.zshrc"
test -f "$NO_RC_HOME/.local/share/newproj/newproj.zsh"
test -f "$NO_RC_HOME/templates/$TEMPLATE_NAME/.newproj-managed"

SUBSET_HOME="$TEMP_ROOT/subset-home"
mkdir -p "$SUBSET_HOME"
env \
  HOME="$SUBSET_HOME" \
  NEWPROJ_ARCHIVE_URL="file://$ARCHIVE_PATH" \
  NEWPROJ_CHECKSUM="$CHECKSUM" \
  NEWPROJ_TEMPLATES="$TEMPLATE_NAME" \
  NEWPROJ_TEMPLATES_DIR="$SUBSET_HOME/templates" \
  NEWPROJ_INSTALL_DIR="$SUBSET_HOME/.local/share/newproj" \
  NEWPROJ_RC_FILE="$SUBSET_HOME/.zshrc" \
  sh "$REPOSITORY_ROOT/install.sh" >/dev/null
test -f "$SUBSET_HOME/templates/$TEMPLATE_NAME/copier.yml"

if env \
  HOME="$SUBSET_HOME" \
  NEWPROJ_ARCHIVE_URL="file://$ARCHIVE_PATH" \
  NEWPROJ_CHECKSUM="$CHECKSUM" \
  NEWPROJ_TEMPLATES="missing-template" \
  NEWPROJ_TEMPLATES_DIR="$SUBSET_HOME/templates" \
  NEWPROJ_INSTALL_DIR="$SUBSET_HOME/.local/share/newproj" \
  NEWPROJ_RC_FILE="$SUBSET_HOME/.zshrc" \
  sh "$REPOSITORY_ROOT/install.sh" >/dev/null 2>&1; then
  echo "installer accepted a template name absent from the archive" >&2
  exit 1
fi

UNMANAGED_HOME="$TEMP_ROOT/unmanaged-home"
mkdir -p "$UNMANAGED_HOME/templates/$TEMPLATE_NAME"
if env \
  HOME="$UNMANAGED_HOME" \
  NEWPROJ_ARCHIVE_URL="file://$ARCHIVE_PATH" \
  NEWPROJ_CHECKSUM="$CHECKSUM" \
  NEWPROJ_TEMPLATES_DIR="$UNMANAGED_HOME/templates" \
  NEWPROJ_INSTALL_DIR="$UNMANAGED_HOME/.local/share/newproj" \
  NEWPROJ_RC_FILE="$UNMANAGED_HOME/.zshrc" \
  sh "$REPOSITORY_ROOT/install.sh" >/dev/null 2>&1; then
  echo "installer overwrote an unmanaged template" >&2
  exit 1
fi

printf '\nSmoke Project\n1\nn\n' |
  HOME="$TEST_HOME" zsh -dfc \
    'source "$HOME/.zshrc"; newproj' |
  grep -q 'Создание проекта отменено.'

echo "newproj installer smoke-test passed"
