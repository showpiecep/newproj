#!/bin/sh

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPOSITORY_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
REPOSITORY_PARENT="$(dirname "$REPOSITORY_ROOT")"
REPOSITORY_NAME="$(basename "$REPOSITORY_ROOT")"

TEMPLATE_NAME="fastapi-yaml"
ARCHIVE_VERSION="v9.9.9"

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/newproj-installer-test.XXXXXX")"
TEST_HOME="$TEMP_ROOT/home"
ARCHIVE_PATH="$TEMP_ROOT/newproj-templates.tar.gz"
RAW_ARCHIVE_PATH="$TEMP_ROOT/newproj-templates-unversioned.tar.gz"
STAGE_DIR="$TEMP_ROOT/stage"

checksum_of() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

# Число резервных копий rc-файла: обновление не должно плодить их на каждый
# запуск установщика.
count_rc_backups() {
  set -- "$1".newproj-backup.*
  if [ -e "$1" ]; then
    printf '%s\n' "$#"
  else
    printf '0\n'
  fi
}

cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$TEST_HOME"
printf '# Existing user configuration\n' >"$TEST_HOME/.zshrc"

COPYFILE_DISABLE=1 tar -czf "$RAW_ARCHIVE_PATH" \
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

# Релизный архив распаковывается в newproj-templates-<версия>; установщик берёт
# версию оттуда, поэтому тестовый архив собирается с тем же префиксом.
mkdir -p "$STAGE_DIR"
tar -xzf "$RAW_ARCHIVE_PATH" -C "$STAGE_DIR"
mv "$STAGE_DIR/$REPOSITORY_NAME" "$STAGE_DIR/newproj-templates-$ARCHIVE_VERSION"
COPYFILE_DISABLE=1 tar -czf "$ARCHIVE_PATH" \
  -C "$STAGE_DIR" \
  "newproj-templates-$ARCHIVE_VERSION"

tar -tzf "$ARCHIVE_PATH" | grep -q "/templates/$TEMPLATE_NAME/copier.yml$"
if tar -tzf "$ARCHIVE_PATH" | grep -qE '(^|/)(\.git|config\.yaml)(/|$)'; then
  echo "test archive contains files that must never be released" >&2
  exit 1
fi

CHECKSUM="$(checksum_of "$ARCHIVE_PATH")"
RAW_CHECKSUM="$(checksum_of "$RAW_ARCHIVE_PATH")"

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
test -f "$TEST_HOME/.local/share/newproj/install.sh"

# Версия разрешается из имени корня архива, а не из NEWPROJ_VERSION.
grep -q "^version=$ARCHIVE_VERSION$" \
  "$TEST_HOME/templates/$TEMPLATE_NAME/.newproj-managed"
grep -q "^version=$ARCHIVE_VERSION$" "$TEST_HOME/.local/share/newproj/state"
grep -q "^templates_dir=$TEST_HOME/templates$" \
  "$TEST_HOME/.local/share/newproj/state"
test ! -e "$TEST_HOME/templates/$TEMPLATE_NAME/install.sh"
test "$(grep -c '^# >>> newproj >>>$' "$TEST_HOME/.zshrc")" -eq 1
test "$(grep -c '^# <<< newproj <<<$' "$TEST_HOME/.zshrc")" -eq 1
zsh -n "$TEST_HOME/.zshrc"

HOME="$TEST_HOME" zsh -dfc \
  'source "$HOME/.zshrc"; whence -w newproj' |
  grep -q '^newproj: function$'

RC_BACKUPS_BEFORE="$(count_rc_backups "$TEST_HOME/.zshrc")"

run_installer

test "$(grep -c '^# >>> newproj >>>$' "$TEST_HOME/.zshrc")" -eq 1
test "$(grep -c '^# <<< newproj <<<$' "$TEST_HOME/.zshrc")" -eq 1
test "$(count_rc_backups "$TEST_HOME/.zshrc")" -eq "$RC_BACKUPS_BEFORE"

NO_RC_HOME="$TEMP_ROOT/no-rc-home"
mkdir -p "$NO_RC_HOME"
env \
  HOME="$NO_RC_HOME" \
  NEWPROJ_VERSION="test" \
  NEWPROJ_ARCHIVE_URL="file://$RAW_ARCHIVE_PATH" \
  NEWPROJ_CHECKSUM="$RAW_CHECKSUM" \
  NEWPROJ_TEMPLATES_DIR="$NO_RC_HOME/templates" \
  NEWPROJ_INSTALL_DIR="$NO_RC_HOME/.local/share/newproj" \
  NEWPROJ_RC_FILE="$NO_RC_HOME/.zshrc" \
  NEWPROJ_NO_MODIFY_RC=1 \
  sh "$REPOSITORY_ROOT/install.sh" >/dev/null
test ! -e "$NO_RC_HOME/.zshrc"
test -f "$NO_RC_HOME/.local/share/newproj/newproj.zsh"
test -f "$NO_RC_HOME/templates/$TEMPLATE_NAME/.newproj-managed"

# Архив без релизного префикса: версия берётся из NEWPROJ_VERSION.
grep -q '^version=test$' "$NO_RC_HOME/.local/share/newproj/state"

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

test -f "$TEST_HOME/.local/share/newproj/uninstall.sh"

# Баннер строится из кеша проверки и не ходит в сеть.
printf 'checked_at=%s\nlatest=v9.9.10\n' "$(date +%s)" \
  >"$TEST_HOME/.local/share/newproj/update-check"

HOME="$TEST_HOME" zsh -dfc 'source "$HOME/.zshrc"; newproj list' |
  grep -q 'newproj update'

if HOME="$TEST_HOME" NEWPROJ_UPDATE_CHECK_DAYS=0 zsh -dfc \
  'source "$HOME/.zshrc"; newproj list' |
  grep -q 'доступна версия'; then
  echo "banner shown while update checks are disabled" >&2
  exit 1
fi

# newproj update запускает сохранённую копию установщика с настройками из
# состояния; --force не ходит в сеть за версией.
env \
  HOME="$TEST_HOME" \
  NEWPROJ_ARCHIVE_URL="file://$ARCHIVE_PATH" \
  NEWPROJ_CHECKSUM="$CHECKSUM" \
  zsh -dfc 'source "$HOME/.zshrc"; newproj update --force' >/dev/null

test -f "$TEST_HOME/templates/$TEMPLATE_NAME/copier.yml"
grep -q "^version=$ARCHIVE_VERSION$" "$TEST_HOME/.local/share/newproj/state"
test ! -e "$TEST_HOME/.local/share/newproj/update-check"
test "$(grep -c '^# >>> newproj >>>$' "$TEST_HOME/.zshrc")" -eq 1
test "$(count_rc_backups "$TEST_HOME/.zshrc")" -eq "$RC_BACKUPS_BEFORE"

if HOME="$TEST_HOME" zsh -dfc \
  'source "$HOME/.zshrc"; newproj update --unknown' >/dev/null 2>&1; then
  echo "newproj update accepted an unknown argument" >&2
  exit 1
fi

# Обновление обязано читать настройки из состояния: переменные rc-блока не
# экспортируются, поэтому при потере состояния установщик разложил бы шаблоны
# по путям по умолчанию.
UPDATE_HOME="$TEMP_ROOT/update-home"
mkdir -p "$UPDATE_HOME"
env \
  HOME="$UPDATE_HOME" \
  NEWPROJ_ARCHIVE_URL="file://$ARCHIVE_PATH" \
  NEWPROJ_CHECKSUM="$CHECKSUM" \
  NEWPROJ_TEMPLATES="$TEMPLATE_NAME" \
  NEWPROJ_TEMPLATES_DIR="$UPDATE_HOME/custom-templates" \
  NEWPROJ_INSTALL_DIR="$UPDATE_HOME/opt/newproj" \
  NEWPROJ_RC_FILE="$UPDATE_HOME/.zshrc" \
  sh "$REPOSITORY_ROOT/install.sh" >/dev/null

grep -q "^requested_templates=$TEMPLATE_NAME$" "$UPDATE_HOME/opt/newproj/state"
grep -q "^installed_templates=$TEMPLATE_NAME$" "$UPDATE_HOME/opt/newproj/state"

touch "$UPDATE_HOME/custom-templates/$TEMPLATE_NAME/stale-marker"

env \
  HOME="$UPDATE_HOME" \
  NEWPROJ_ARCHIVE_URL="file://$ARCHIVE_PATH" \
  NEWPROJ_CHECKSUM="$CHECKSUM" \
  zsh -dfc 'source "$HOME/.zshrc"; newproj update --force' >/dev/null

test ! -e "$UPDATE_HOME/custom-templates/$TEMPLATE_NAME/stale-marker"
test -f "$UPDATE_HOME/custom-templates/$TEMPLATE_NAME/copier.yml"
test ! -e "$UPDATE_HOME/custom-templates/inspect-eval"
test ! -e "$UPDATE_HOME/templates"
test ! -e "$UPDATE_HOME/.local/share/newproj"

# Чужой шаблон рядом обязан пережить удаление.
mkdir -p "$TEST_HOME/templates/own-template"
printf 'project_name:\n  type: str\n' >"$TEST_HOME/templates/own-template/copier.yml"

env \
  HOME="$TEST_HOME" \
  NEWPROJ_TEMPLATES_DIR="$TEST_HOME/templates" \
  NEWPROJ_INSTALL_DIR="$TEST_HOME/.local/share/newproj" \
  NEWPROJ_RC_FILE="$TEST_HOME/.zshrc" \
  sh "$TEST_HOME/.local/share/newproj/uninstall.sh" >/dev/null

test ! -e "$TEST_HOME/templates/$TEMPLATE_NAME"
test ! -e "$TEST_HOME/.local/share/newproj"
test -f "$TEST_HOME/templates/own-template/copier.yml"
test "$(grep -c 'newproj' "$TEST_HOME/.zshrc")" -eq 0
grep -q '^# Existing user configuration$' "$TEST_HOME/.zshrc"
zsh -n "$TEST_HOME/.zshrc"

# Повторное удаление не должно падать.
env \
  HOME="$TEST_HOME" \
  NEWPROJ_TEMPLATES_DIR="$TEST_HOME/templates" \
  NEWPROJ_INSTALL_DIR="$TEST_HOME/.local/share/newproj" \
  NEWPROJ_RC_FILE="$TEST_HOME/.zshrc" \
  sh "$REPOSITORY_ROOT/uninstall.sh" >/dev/null

test -f "$TEST_HOME/templates/own-template/copier.yml"

echo "newproj installer smoke-test passed"
