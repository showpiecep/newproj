#!/bin/sh

set -eu

PROGRAM_NAME="newproj"
ARCHIVE_NAME="newproj-templates.tar.gz"
DEFAULT_REPOSITORY_URL="https://github.com/showpiecep/newproj"

REPOSITORY_URL="${NEWPROJ_REPOSITORY_URL:-$DEFAULT_REPOSITORY_URL}"
VERSION="${NEWPROJ_VERSION:-latest}"
TEMPLATES_DIR="${NEWPROJ_TEMPLATES_DIR:-$HOME/templates}"
INSTALL_DIR="${NEWPROJ_INSTALL_DIR:-$HOME/.local/share/newproj}"
RC_FILE="${NEWPROJ_RC_FILE:-$HOME/.zshrc}"
NO_MODIFY_RC="${NEWPROJ_NO_MODIFY_RC:-0}"
REQUESTED_TEMPLATES="${NEWPROJ_TEMPLATES:-}"

START_MARKER="# >>> newproj >>>"
END_MARKER="# <<< newproj <<<"

SELECTED_TEMPLATES=""
STAGED_TEMPLATES=""
SWAPPED_TEMPLATES=""

say() {
  printf '%s\n' "$*"
}

fail() {
  printf '%s installer: %s\n' "$PROGRAM_NAME" "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 ||
    fail "required command not found: $1"
}

checksum_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    fail "shasum or sha256sum is required"
  fi
}

download() {
  url="$1"
  destination="$2"

  case "$url" in
    file://*)
      curl -LsSf "$url" -o "$destination"
      ;;
    https://*)
      curl --proto '=https' --tlsv1.2 -LsSf "$url" -o "$destination"
      ;;
    *)
      fail "only file:// and https:// download URLs are supported"
      ;;
  esac
}

quote_zsh() {
  printf "'"
  printf '%s' "$1" | sed "s/'/'\\\\''/g"
  printf "'"
}

strip_managed_block() {
  awk -v start="$START_MARKER" -v end="$END_MARKER" '
    $0 == start {
      if (inside) {
        exit 2
      }
      inside = 1
      next
    }
    $0 == end {
      if (!inside) {
        exit 3
      }
      inside = 0
      next
    }
    !inside {
      print
    }
    END {
      if (inside) {
        exit 4
      }
    }
  ' "$1"
}

# Имена шаблонов приходят из архива и подставляются в пути, поэтому набор
# допустимых символов ограничен явно.
check_template_name() {
  case "$1" in
    "" | . | .. | *[!A-Za-z0-9._-]*)
      fail "unsupported template name: $1"
      ;;
  esac
}

list_contains() {
  for list_item in $1; do
    if [ "$list_item" = "$2" ]; then
      return 0
    fi
  done
  return 1
}

staged_path() {
  printf '%s/.%s.new.%s' "$TEMPLATES_DIR" "$1" "$$"
}

backup_path() {
  printf '%s/.%s.old.%s' "$TEMPLATES_DIR" "$1" "$$"
}

cleanup() {
  if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
  for cleanup_name in $STAGED_TEMPLATES; do
    rm -rf "$(staged_path "$cleanup_name")"
  done
}

# Откат возвращает все шаблоны, уже подменённые в этом запуске.
rollback_swapped() {
  for rollback_name in $SWAPPED_TEMPLATES; do
    rollback_target="$TEMPLATES_DIR/$rollback_name"
    rollback_backup="$(backup_path "$rollback_name")"
    if [ -d "$rollback_backup" ]; then
      rm -rf "$rollback_target"
      mv "$rollback_backup" "$rollback_target"
    fi
  done
}

trap cleanup EXIT HUP INT TERM

require_command curl
require_command tar
require_command awk
require_command sed
require_command zsh
require_command mktemp

if [ -n "${NEWPROJ_ARCHIVE_URL:-}" ]; then
  ARCHIVE_URL="$NEWPROJ_ARCHIVE_URL"
elif [ "$VERSION" = "latest" ]; then
  ARCHIVE_URL="$REPOSITORY_URL/releases/latest/download/$ARCHIVE_NAME"
else
  ARCHIVE_URL="$REPOSITORY_URL/releases/download/$VERSION/$ARCHIVE_NAME"
fi

if [ -n "${NEWPROJ_CHECKSUM_URL:-}" ]; then
  CHECKSUM_URL="$NEWPROJ_CHECKSUM_URL"
elif [ -z "${NEWPROJ_CHECKSUM:-}" ]; then
  CHECKSUM_URL="$ARCHIVE_URL.sha256"
fi

TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/newproj-install.XXXXXX")"
ARCHIVE_PATH="$TEMP_DIR/$ARCHIVE_NAME"
EXTRACT_DIR="$TEMP_DIR/extracted"
RC_CANDIDATE="$TEMP_DIR/zshrc"

mkdir -p "$EXTRACT_DIR"

say "Downloading newproj templates ($VERSION)..."
download "$ARCHIVE_URL" "$ARCHIVE_PATH"

if [ -n "${NEWPROJ_CHECKSUM:-}" ]; then
  EXPECTED_CHECKSUM="$NEWPROJ_CHECKSUM"
else
  CHECKSUM_PATH="$ARCHIVE_PATH.sha256"
  download "$CHECKSUM_URL" "$CHECKSUM_PATH"
  EXPECTED_CHECKSUM="$(awk 'NR == 1 {print $1}' "$CHECKSUM_PATH")"
fi

[ -n "$EXPECTED_CHECKSUM" ] || fail "empty archive checksum"
ACTUAL_CHECKSUM="$(checksum_file "$ARCHIVE_PATH")"
[ "$ACTUAL_CHECKSUM" = "$EXPECTED_CHECKSUM" ] ||
  fail "archive checksum mismatch"

tar -xzf "$ARCHIVE_PATH" -C "$EXTRACT_DIR"

set -- "$EXTRACT_DIR"/*
[ "$#" -eq 1 ] && [ -d "$1" ] ||
  fail "archive must contain exactly one root directory"
SOURCE_DIR="$1"

[ -d "$SOURCE_DIR/templates" ] ||
  fail "archive does not contain a templates directory"
[ -f "$SOURCE_DIR/installer/newproj.zsh" ] ||
  fail "archive does not contain installer/newproj.zsh"
[ -f "$SOURCE_DIR/uninstall.sh" ] ||
  fail "archive does not contain uninstall.sh"

AVAILABLE_TEMPLATES=""
for candidate in "$SOURCE_DIR"/templates/*; do
  [ -d "$candidate" ] || continue
  if [ ! -f "$candidate/copier.yml" ] && [ ! -f "$candidate/copier.yaml" ]; then
    continue
  fi
  candidate_name="$(basename "$candidate")"
  check_template_name "$candidate_name"
  AVAILABLE_TEMPLATES="$AVAILABLE_TEMPLATES $candidate_name"
done

[ -n "$AVAILABLE_TEMPLATES" ] ||
  fail "archive contains no Copier templates"

if [ -n "$REQUESTED_TEMPLATES" ]; then
  for requested_name in $(printf '%s' "$REQUESTED_TEMPLATES" | tr ',' ' '); do
    list_contains "$AVAILABLE_TEMPLATES" "$requested_name" ||
      fail "requested template is not in the archive: $requested_name"
    SELECTED_TEMPLATES="$SELECTED_TEMPLATES $requested_name"
  done
else
  SELECTED_TEMPLATES="$AVAILABLE_TEMPLATES"
fi

# Ни один шаблон не устанавливается, пока не проверены конфликты по всем.
for name in $SELECTED_TEMPLATES; do
  target="$TEMPLATES_DIR/$name"
  if [ -e "$target" ] && [ ! -f "$target/.newproj-managed" ]; then
    fail "refusing to overwrite unmanaged template: $target"
  fi
done

mkdir -p "$TEMPLATES_DIR"

for name in $SELECTED_TEMPLATES; do
  staged="$(staged_path "$name")"
  rm -rf "$staged"
  cp -R "$SOURCE_DIR/templates/$name" "$staged"
  printf 'version=%s\nrepository=%s\ntemplate=%s\n' \
    "$VERSION" "$REPOSITORY_URL" "$name" >"$staged/.newproj-managed"
  STAGED_TEMPLATES="$STAGED_TEMPLATES $name"
done

if [ "$NO_MODIFY_RC" != "1" ]; then
  if [ -f "$RC_FILE" ]; then
    strip_managed_block "$RC_FILE" >"$RC_CANDIDATE" ||
      fail "invalid managed block in $RC_FILE"
  else
    : >"$RC_CANDIDATE"
  fi

  {
    printf '\n%s\n' "$START_MARKER"
    printf 'NEWPROJ_TEMPLATES_DIR=%s\n' "$(quote_zsh "$TEMPLATES_DIR")"
    printf 'source %s\n' "$(quote_zsh "$INSTALL_DIR/newproj.zsh")"
    printf '%s\n' "$END_MARKER"
  } >>"$RC_CANDIDATE"

  zsh -n "$RC_CANDIDATE" ||
    fail "generated shell configuration is not valid Zsh"
fi

mkdir -p "$INSTALL_DIR"
NEW_SHELL_FILE="$INSTALL_DIR/.newproj.zsh.new.$$"
cp "$SOURCE_DIR/installer/newproj.zsh" "$NEW_SHELL_FILE"
zsh -n "$NEW_SHELL_FILE" || fail "newproj.zsh is not valid Zsh"
mv "$NEW_SHELL_FILE" "$INSTALL_DIR/newproj.zsh"

# Копия деинсталлятора рядом с интеграцией: удаление не должно зависеть от
# доступности репозитория и совпадает по версии с тем, что установлено.
NEW_UNINSTALL_FILE="$INSTALL_DIR/.uninstall.sh.new.$$"
cp "$SOURCE_DIR/uninstall.sh" "$NEW_UNINSTALL_FILE"
sh -n "$NEW_UNINSTALL_FILE" || fail "uninstall.sh is not valid POSIX sh"
chmod +x "$NEW_UNINSTALL_FILE"
mv "$NEW_UNINSTALL_FILE" "$INSTALL_DIR/uninstall.sh"

for name in $SELECTED_TEMPLATES; do
  target="$TEMPLATES_DIR/$name"

  if [ -d "$target" ]; then
    if ! mv "$target" "$(backup_path "$name")"; then
      rollback_swapped
      fail "failed to replace template: $target"
    fi
    SWAPPED_TEMPLATES="$SWAPPED_TEMPLATES $name"
  fi

  if ! mv "$(staged_path "$name")" "$target"; then
    rollback_swapped
    fail "failed to install template: $target"
  fi
done

STAGED_TEMPLATES=""

for name in $SWAPPED_TEMPLATES; do
  rm -rf "$(backup_path "$name")"
done

if [ "$NO_MODIFY_RC" != "1" ]; then
  mkdir -p "$(dirname "$RC_FILE")"
  if [ -f "$RC_FILE" ]; then
    RC_BACKUP_BASE="$RC_FILE.newproj-backup.$(date +%Y%m%d%H%M%S)"
    RC_BACKUP="$RC_BACKUP_BASE"
    RC_BACKUP_INDEX=0
    while [ -e "$RC_BACKUP" ]; do
      RC_BACKUP_INDEX=$((RC_BACKUP_INDEX + 1))
      RC_BACKUP="$RC_BACKUP_BASE.$RC_BACKUP_INDEX"
    done
    cp -p "$RC_FILE" "$RC_BACKUP"
    say "Shell configuration backup: $RC_BACKUP"
  fi
  mv "$RC_CANDIDATE" "$RC_FILE"
fi

say
say "newproj installed successfully"
say "Templates directory: $TEMPLATES_DIR"
for name in $SELECTED_TEMPLATES; do
  say "  $name"
done
say "Shell integration: $INSTALL_DIR/newproj.zsh"
if [ "$NO_MODIFY_RC" = "1" ]; then
  say
  say "Shell profile was not modified (NEWPROJ_NO_MODIFY_RC=1)."
else
  say
  say "Run:"
  say "  source \"$RC_FILE\""
  say "  newproj"
fi
say
say "To remove everything later: sh \"$INSTALL_DIR/uninstall.sh\""
