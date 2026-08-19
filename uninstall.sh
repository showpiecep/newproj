#!/bin/sh

set -eu

# Скрипт запускается через `curl | sh` и из каталога установки, поэтому он
# самодостаточен: общие с install.sh помощники повторены намеренно, вынести их
# в отдельный файл нельзя без второй загрузки по сети.

PROGRAM_NAME="newproj"

TEMPLATES_DIR="${NEWPROJ_TEMPLATES_DIR:-$HOME/templates}"
INSTALL_DIR="${NEWPROJ_INSTALL_DIR:-$HOME/.local/share/newproj}"
RC_FILE="${NEWPROJ_RC_FILE:-$HOME/.zshrc}"
NO_MODIFY_RC="${NEWPROJ_NO_MODIFY_RC:-0}"
REQUESTED_TEMPLATES="${NEWPROJ_TEMPLATES:-}"

START_MARKER="# >>> newproj >>>"
END_MARKER="# <<< newproj <<<"

REMOVED_TEMPLATES=""
KEPT_TEMPLATES=""

say() {
  printf '%s\n' "$*"
}

fail() {
  printf '%s uninstaller: %s\n' "$PROGRAM_NAME" "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 ||
    fail "required command not found: $1"
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

cleanup() {
  if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}

trap cleanup EXIT HUP INT TERM

require_command awk
require_command zsh
require_command mktemp

TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/newproj-uninstall.XXXXXX")"
RC_CANDIDATE="$TEMP_DIR/zshrc"

# Удаляются только каталоги с меткой установщика: чужие шаблоны, лежащие
# рядом в том же каталоге, остаются нетронутыми.
MANAGED_TEMPLATES=""
if [ -d "$TEMPLATES_DIR" ]; then
  for candidate in "$TEMPLATES_DIR"/*; do
    [ -d "$candidate" ] || continue
    candidate_name="$(basename "$candidate")"
    if [ -f "$candidate/.newproj-managed" ]; then
      check_template_name "$candidate_name"
      MANAGED_TEMPLATES="$MANAGED_TEMPLATES $candidate_name"
    else
      KEPT_TEMPLATES="$KEPT_TEMPLATES $candidate_name"
    fi
  done
fi

if [ -n "$REQUESTED_TEMPLATES" ]; then
  SELECTED_TEMPLATES=""
  for requested_name in $(printf '%s' "$REQUESTED_TEMPLATES" | tr ',' ' '); do
    list_contains "$MANAGED_TEMPLATES" "$requested_name" ||
      fail "not an installed newproj template: $TEMPLATES_DIR/$requested_name"
    SELECTED_TEMPLATES="$SELECTED_TEMPLATES $requested_name"
  done
else
  SELECTED_TEMPLATES="$MANAGED_TEMPLATES"
fi

# Shell-интеграция снимается, только когда удаляются все шаблоны: иначе
# команда newproj ещё нужна для оставшихся.
REMOVE_SHELL_INTEGRATION=1
for name in $MANAGED_TEMPLATES; do
  list_contains "$SELECTED_TEMPLATES" "$name" || REMOVE_SHELL_INTEGRATION=0
done

if [ "$REMOVE_SHELL_INTEGRATION" = "1" ] && [ "$NO_MODIFY_RC" != "1" ] &&
  [ -f "$RC_FILE" ]; then
  if strip_managed_block "$RC_FILE" >"$RC_CANDIDATE"; then
    zsh -n "$RC_CANDIDATE" ||
      fail "cleaned shell configuration is not valid Zsh, $RC_FILE left as is"

    if ! cmp -s "$RC_CANDIDATE" "$RC_FILE"; then
      RC_BACKUP_BASE="$RC_FILE.newproj-backup.$(date +%Y%m%d%H%M%S)"
      RC_BACKUP="$RC_BACKUP_BASE"
      RC_BACKUP_INDEX=0
      while [ -e "$RC_BACKUP" ]; do
        RC_BACKUP_INDEX=$((RC_BACKUP_INDEX + 1))
        RC_BACKUP="$RC_BACKUP_BASE.$RC_BACKUP_INDEX"
      done
      cp -p "$RC_FILE" "$RC_BACKUP"
      say "Shell configuration backup: $RC_BACKUP"
      mv "$RC_CANDIDATE" "$RC_FILE"
      say "Removed managed block from $RC_FILE"
    fi
  else
    fail "invalid managed block in $RC_FILE, remove it manually"
  fi
fi

for name in $SELECTED_TEMPLATES; do
  rm -rf "$TEMPLATES_DIR/$name"
  REMOVED_TEMPLATES="$REMOVED_TEMPLATES $name"
done

if [ "$REMOVE_SHELL_INTEGRATION" = "1" ] && [ -d "$INSTALL_DIR" ]; then
  rm -f \
    "$INSTALL_DIR/newproj.zsh" \
    "$INSTALL_DIR/uninstall.sh" \
    "$INSTALL_DIR/install.sh" \
    "$INSTALL_DIR/state" \
    "$INSTALL_DIR/update-check" \
    "$INSTALL_DIR/update-notified"
  rmdir "$INSTALL_DIR" 2>/dev/null ||
    say "Kept $INSTALL_DIR: directory is not empty"
fi

say
say "newproj uninstalled"

if [ -n "$REMOVED_TEMPLATES" ]; then
  say "Removed templates:"
  for name in $REMOVED_TEMPLATES; do
    say "  $TEMPLATES_DIR/$name"
  done
else
  say "No installed templates found in $TEMPLATES_DIR"
fi

if [ -n "$KEPT_TEMPLATES" ]; then
  say "Kept, not installed by newproj:"
  for name in $KEPT_TEMPLATES; do
    say "  $TEMPLATES_DIR/$name"
  done
fi

if [ "$REMOVE_SHELL_INTEGRATION" = "1" ]; then
  say
  say "Restart the shell to drop the loaded functions, or unset them:"
  say "  add-zsh-hook -d precmd _newproj_update_precmd"
  say "  unset -f newproj \$(typeset +f | grep '^_newproj_')"
else
  say
  say "Shell integration kept: other newproj templates are still installed."
fi

set -- "$RC_FILE".newproj-backup.*
if [ -e "$1" ]; then
  say
  say "Shell configuration backups are kept on purpose:"
  for backup in "$@"; do
    say "  $backup"
  done
fi
