# shellcheck shell=zsh

# Корень с шаблонами. Отдельная функция, чтобы подкоманды и подсказки читали
# одно и то же значение.
_newproj_templates_root() {
  print -r -- "${NEWPROJ_TEMPLATES_DIR:-$HOME/templates}"
}

# Пути шаблонов в корне, по одному на строку. Шаблон — каталог с copier.yml.
_newproj_find_templates() {
  emulate -L zsh
  setopt local_options no_nomatch

  local root="$1" candidate
  for candidate in "$root"/*(/N); do
    if [[ -f "$candidate/copier.yml" || -f "$candidate/copier.yaml" ]]; then
      print -r -- "$candidate"
    fi
  done
}

# Заполняет переданный массив шаблонами и печатает ошибку, если их нет.
_newproj_load_templates() {
  emulate -L zsh

  local root="$1" candidate
  local -a found

  if [[ ! -d "$root" ]]; then
    echo "Ошибка: директория шаблонов не найдена: $root" >&2
    return 1
  fi

  for candidate in ${(f)"$(_newproj_find_templates "$root")"}; do
    [[ -n "$candidate" ]] && found+=("$candidate")
  done

  if (( ${#found[@]} == 0 )); then
    echo "Ошибка: в $root нет Copier-шаблонов." >&2
    return 1
  fi

  # Массив возвращается через глобальную переменную: zsh не поддерживает
  # nameref, а печатать пути построчно во второй раз было бы лишним разбором.
  _newproj_found_templates=("${found[@]}")
}

# Однострочное описание шаблона: первый абзац его README после заголовка.
_newproj_summary() {
  emulate -L zsh
  # Описания на русском: без multibyte длина считается в байтах, и обрезка
  # срубает строку вдвое раньше нужного.
  setopt local_options multibyte

  local readme="$1/README.md" line summary=""
  local -i width=96
  [[ -f "$readme" ]] || return 0

  while IFS= read -r line; do
    # Заголовок и пустые строки до абзаца пропускаем.
    if [[ -z "$summary" ]]; then
      [[ -z "$line" || "$line" == '#'* ]] && continue
    else
      # Абзац кончился — дальше уже другой раздел README.
      [[ -z "$line" ]] && break
    fi
    summary="${summary:+$summary }$line"
  done <"$readme"

  [[ -n "$summary" ]] || return 0

  # Markdown-ссылки в списке читаются как шум: [текст](url) -> текст.
  summary="$(printf '%s' "$summary" | sed -E 's/\[([^]]*)\]\([^)]*\)/\1/g')"

  # Абзац написан для README и в строку списка не помещается. Первое
  # предложение — естественная граница и не зависит от локали, в отличие от
  # счёта символов: без UTF-8 в локали ${#...} считает байты.
  if [[ "$summary" == *". "* ]]; then
    summary="${summary%%. *}."
  elif (( ${#summary} > width )); then
    summary="${summary[1,$width]}"
    summary="${summary% *}…"
  fi

  print -r -- "$summary"
}

# Каталог shell-интеграции: рядом с этим файлом лежат состояние установки и
# кеш проверки обновлений. Установщик прописывает переменную в rc-файл, значение
# по умолчанию нужно при ручном source.
_newproj_install_dir() {
  print -r -- "${NEWPROJ_INSTALL_DIR:-$HOME/.local/share/newproj}"
}

_newproj_state_file() {
  print -r -- "$(_newproj_install_dir)/state"
}

# Значение ключа из файла вида key=value. Значением считается весь остаток
# строки, поэтому пути с пробелами читаются как есть.
_newproj_state_value() {
  emulate -L zsh

  local file="$1" key="$2" line
  [[ -f "$file" ]] || return 1

  while IFS= read -r line; do
    if [[ "$line" == "$key="* ]]; then
      print -r -- "${line#"$key="}"
      return 0
    fi
  done <"$file"

  return 1
}

_newproj_installed_version() {
  _newproj_state_value "$(_newproj_state_file)" version
}

_newproj_repository_url() {
  local repository
  repository="$(_newproj_state_value "$(_newproj_state_file)" repository)"
  [[ -n "$repository" ]] ||
    repository="${NEWPROJ_REPOSITORY_URL:-https://github.com/showpiecep/newproj}"
  print -r -- "$repository"
}

# Тег последнего релиза берётся из редиректа /releases/latest: GitHub API,
# токен и его лимиты для этого не нужны.
_newproj_fetch_latest() {
  emulate -L zsh

  local repository url tag
  command -v curl >/dev/null 2>&1 || return 1
  repository="$(_newproj_repository_url)"
  [[ -n "$repository" ]] || return 1

  url="$(curl --proto '=https' --tlsv1.2 -fsSLI \
    -o /dev/null -w '%{url_effective}' \
    --max-time "${NEWPROJ_UPDATE_CHECK_TIMEOUT:-10}" \
    "$repository/releases/latest" 2>/dev/null)" || return 1

  # Без релизов редирект не происходит, и в url_effective остаётся сам запрос.
  [[ "$url" == */releases/tag/* ]] || return 1
  tag="${url##*/}"
  [[ -n "$tag" ]] || return 1

  print -r -- "$tag"
}

_newproj_write_update_cache() {
  emulate -L zsh

  local dir="$(_newproj_install_dir)" latest="$1" tmp
  [[ -n "$latest" && -d "$dir" ]] || return 1

  tmp="$dir/.update-check.new.$$"
  {
    print -r -- "checked_at=$(date +%s)"
    print -r -- "latest=$latest"
  } >"$tmp" 2>/dev/null || return 1

  mv -f "$tmp" "$dir/update-check" 2>/dev/null
}

_newproj_check_updates() {
  emulate -L zsh

  local latest
  latest="$(_newproj_fetch_latest)" || return 1
  _newproj_write_update_cache "$latest" || return 1
  print -r -- "$latest"
}

# Проверять не чаще раза в NEWPROJ_UPDATE_CHECK_DAYS суток; 0 выключает
# проверку совсем.
_newproj_update_check_due() {
  emulate -L zsh

  local days="${NEWPROJ_UPDATE_CHECK_DAYS:-7}" checked
  [[ "$days" == <-> ]] || return 1
  (( days == 0 )) && return 1

  checked="$(_newproj_state_value "$(_newproj_install_dir)/update-check" checked_at)" ||
    return 0
  [[ "$checked" == <-> ]] || return 0

  (( $(date +%s) - checked >= days * 86400 ))
}

# Проверка уходит в отсоединённый фон: приглашение оболочки не ждёт сети, а
# результат читается из кеша при следующем запуске.
_newproj_update_check_async() {
  emulate -L zsh
  { _newproj_check_updates } >/dev/null 2>&1 &!
}

# Печатает подсказку, если в кеше лежит версия, отличная от установленной.
# NEWPROJ_UPDATE_CHECK_DAYS=0 выключает не только проверки, но и подсказку:
# иначе отказавшийся от проверок видел бы баннер из старого кеша.
_newproj_update_banner() {
  emulate -L zsh

  local installed latest
  [[ "${NEWPROJ_UPDATE_CHECK_DAYS:-7}" != "0" ]] || return 1
  installed="$(_newproj_installed_version)" || return 1
  latest="$(_newproj_state_value "$(_newproj_install_dir)/update-check" latest)" ||
    return 1
  [[ -n "$installed" && -n "$latest" && "$installed" != "$latest" ]] || return 1

  print -r -- "newproj: доступна версия $latest, установлена $installed."
  print -r -- "Обновить: newproj update"
}

# Баннер при старте оболочки: один раз за сессию и повторно только тогда, когда
# выйдет ещё более новая версия. Хук снимается после первого приглашения.
_newproj_update_precmd() {
  emulate -L zsh

  local dir latest notified
  dir="$(_newproj_install_dir)"
  latest="$(_newproj_state_value "$dir/update-check" latest)"

  if [[ -n "$latest" ]]; then
    notified="$(_newproj_state_value "$dir/update-notified" version)"
    if [[ "$notified" != "$latest" ]] && _newproj_update_banner; then
      print -r -- "version=$latest" >"$dir/update-notified" 2>/dev/null
    fi
  fi

  _newproj_update_check_due && _newproj_update_check_async

  precmd_functions=("${(@)precmd_functions:#_newproj_update_precmd}")
}

_newproj_update_usage() {
  cat <<USAGE
newproj update — обновление шаблонов и команды newproj.

Использование:
  newproj update           обновить, если вышла новая версия
  newproj update --check   только проверить, ничего не устанавливая
  newproj update --force   переустановить текущий релиз без проверки

Установщик берётся из копии рядом с shell-интеграцией и запускается с теми же
настройками, что и при установке. Проверка версии при старте оболочки
настраивается переменной NEWPROJ_UPDATE_CHECK_DAYS (по умолчанию 7, 0 —
выключить).
USAGE
}

# Обновление — это повторный запуск установщика с сохранёнными настройками.
# Свежий install.sh приезжает внутри архива и заменяет копию, поэтому правки
# самого установщика тоже доходят до пользователя.
_newproj_update() {
  emulate -L zsh

  local dir state installed latest arg pair value
  local -i force=0 check_only=0
  local -a installer_env

  for arg in "$@"; do
    case "$arg" in
      -f|--force) force=1 ;;
      -n|--check|--dry-run) check_only=1 ;;
      -h|--help)
        _newproj_update_usage
        return 0
        ;;
      *)
        echo "newproj update: неизвестный аргумент: $arg" >&2
        echo >&2
        _newproj_update_usage >&2
        return 2
        ;;
    esac
  done

  dir="$(_newproj_install_dir)"
  state="$(_newproj_state_file)"
  installed="$(_newproj_installed_version)"

  if (( ! check_only )) && [[ ! -f "$dir/install.sh" ]]; then
    echo "Ошибка: не найден установщик $dir/install.sh." >&2
    echo "Он появляется при установке; переустановите newproj по инструкции из README." >&2
    return 1
  fi

  if (( check_only || ! force )); then
    echo "Проверяю последнюю версию..."
    latest="$(_newproj_check_updates)"

    if [[ -z "$latest" ]]; then
      echo "Не удалось узнать последнюю версию." >&2
      (( check_only )) && return 1
      echo "Устанавливаю последний релиз без сравнения версий." >&2
    else
      rm -f "$dir/update-notified"
      echo "Установлено: ${installed:-неизвестно}. Последняя: $latest."

      if [[ -n "$installed" && "$installed" == "$latest" ]]; then
        (( check_only )) && return 0
        echo "Обновление не требуется."
        echo "Переустановить принудительно: newproj update --force"
        return 0
      fi
    fi

    (( check_only )) && return 0
  fi

  # Настройки прошлой установки: без них обновление разложило бы шаблоны по
  # путям по умолчанию, а не туда, куда они установлены.
  for pair in templates_dir:NEWPROJ_TEMPLATES_DIR install_dir:NEWPROJ_INSTALL_DIR \
    rc_file:NEWPROJ_RC_FILE no_modify_rc:NEWPROJ_NO_MODIFY_RC \
    requested_templates:NEWPROJ_TEMPLATES repository:NEWPROJ_REPOSITORY_URL; do
    value="$(_newproj_state_value "$state" "${pair%%:*}")"
    [[ -n "$value" ]] && installer_env+=("${pair##*:}=$value")
  done

  # Установщик заменяет собственную копию через mv: переименование не трогает
  # inode, который читает запущенный sh, поэтому обновление на себе безопасно.
  env "${(@)installer_env}" sh "$dir/install.sh" || return $?

  # Функции в текущей оболочке остались от прежней версии.
  if [[ -f "$dir/newproj.zsh" ]]; then
    source "$dir/newproj.zsh"
    echo
    echo "Команда newproj перезагружена в этой оболочке."
    echo "Остальным открытым оболочкам нужен перезапуск."
  fi
}

_newproj_usage() {
  local root
  root="$(_newproj_templates_root)"

  cat <<USAGE
newproj — создание проекта из Copier-шаблона.

Использование:
  newproj              интерактивное создание проекта
  newproj list         показать доступные шаблоны
  newproj update       обновить шаблоны и саму команду
  newproj --help       эта справка

Шаблоны берутся из $root; каталог с copier.yml считается шаблоном.
Путь переопределяется переменной NEWPROJ_TEMPLATES_DIR.

Интерактивный режим спрашивает каталог, название проекта и шаблон, затем
запускает copier и переходит в созданный проект.

Оболочка не чаще раза в NEWPROJ_UPDATE_CHECK_DAYS суток (по умолчанию 7, 0 —
выключить) проверяет в фоне, вышел ли новый релиз, и сообщает об этом.
USAGE
}

_newproj_list() {
  emulate -L zsh

  local root template summary banner
  local -a _newproj_found_templates
  root="$(_newproj_templates_root)"

  _newproj_load_templates "$root" || return 1

  echo "Шаблоны в $root:"
  echo
  for template in "${_newproj_found_templates[@]}"; do
    printf "  %s\n" "${template:t}"
    summary="$(_newproj_summary "$template")"
    [[ -n "$summary" ]] && printf "    %s\n" "$summary"
  done
  echo
  echo "Создать проект: newproj"

  banner="$(_newproj_update_banner)"
  if [[ -n "$banner" ]]; then
    echo
    print -r -- "$banner"
  fi
}

# Интерактивное создание проекта из Copier-шаблонов.
newproj() {
  emulate -L zsh
  setopt local_options no_nomatch

  local templates_root parent_input project_parent project_name target_path
  local selected_template template_summary selection confirmation create_parent
  local -a _newproj_found_templates templates copier_command
  local index copier_status

  case "${1:-}" in
    -h|--help|help)
      _newproj_usage
      return 0
      ;;
    -l|--list|list)
      _newproj_list
      return $?
      ;;
    -u|--update|update)
      shift
      _newproj_update "$@"
      return $?
      ;;
    "")
      ;;
    *)
      echo "newproj: неизвестный аргумент: $1" >&2
      echo >&2
      _newproj_usage >&2
      return 2
      ;;
  esac

  templates_root="$(_newproj_templates_root)"

  if _newproj_update_banner; then
    echo
  fi

  if command -v copier >/dev/null 2>&1; then
    copier_command=("$(command -v copier)")
  elif command -v uvx >/dev/null 2>&1; then
    copier_command=("$(command -v uvx)" --from copier copier)
  else
    echo "Ошибка: не найдены copier или uvx." >&2
    echo "Установите uv: https://docs.astral.sh/uv/getting-started/installation/" >&2
    return 1
  fi

  _newproj_load_templates "$templates_root" || return 1
  templates=("${_newproj_found_templates[@]}")

  echo "Где создать проект?"
  printf "[%s]: " "$PWD"
  read -r parent_input

  if [[ -z "$parent_input" ]]; then
    project_parent="$PWD"
  elif [[ "$parent_input" == "~" ]]; then
    project_parent="$HOME"
  elif [[ "$parent_input" == "~/"* ]]; then
    project_parent="$HOME/${parent_input#\~/}"
  elif [[ "$parent_input" == /* ]]; then
    project_parent="$parent_input"
  else
    project_parent="$PWD/$parent_input"
  fi
  project_parent="${project_parent:A}"

  if [[ ! -d "$project_parent" ]]; then
    printf "Директория %s не существует. Создать? [y/N]: " "$project_parent"
    read -r create_parent
    if [[ "${create_parent:l}" != "y" && "${create_parent:l}" != "yes" ]]; then
      echo "Создание проекта отменено."
      return 0
    fi
  fi

  while true; do
    printf "Название проекта: "
    read -r project_name

    if [[ -z "$project_name" ]]; then
      echo "Название проекта не может быть пустым." >&2
      continue
    fi

    if [[ "$project_name" == "." || "$project_name" == ".." || "$project_name" == */* ]]; then
      echo "Название должно быть именем директории без символа /." >&2
      continue
    fi

    target_path="$project_parent/$project_name"
    if [[ -e "$target_path" ]]; then
      echo "Путь уже существует: $target_path" >&2
      continue
    fi

    break
  done

  echo
  echo "Выберите шаблон из $templates_root:"
  for (( index = 1; index <= ${#templates[@]}; index++ )); do
    printf "%d) %s\n" "$index" "${templates[$index]:t}"
    template_summary="$(_newproj_summary "${templates[$index]}")"
    [[ -n "$template_summary" ]] && printf "   %s\n" "$template_summary"
  done

  while true; do
    printf "Номер шаблона: "
    read -r selection

    if [[ "$selection" == <-> ]] &&
       (( selection >= 1 && selection <= ${#templates[@]} )); then
      selected_template="${templates[$selection]}"
      break
    fi

    echo "Введите номер от 1 до ${#templates[@]}." >&2
  done

  echo
  echo "Проект:  $target_path"
  echo "Шаблон:  $selected_template"
  printf "Продолжить? [Y/n]: "
  read -r confirmation

  if [[ -n "$confirmation" &&
        "${confirmation:l}" != "y" &&
        "${confirmation:l}" != "yes" ]]; then
    echo "Создание проекта отменено."
    return 0
  fi

  if [[ ! -d "$project_parent" ]]; then
    mkdir -p -- "$project_parent" || {
      echo "Ошибка: не удалось создать директорию $project_parent" >&2
      return 1
    }
  fi

  "${copier_command[@]}" copy \
    "$selected_template" \
    "$target_path" \
    --trust \
    --data project_name="$project_name"
  copier_status=$?

  if (( copier_status != 0 )); then
    echo "Ошибка: Copier завершился с кодом $copier_status." >&2
    return "$copier_status"
  fi

  cd -- "$target_path" || return 1

  echo
  echo "Проект создан: $target_path"
  echo "Текущая директория: $PWD"
}

# Хук ставится только в интерактивной оболочке: в скриптах и `zsh -c`
# приглашения нет, а баннер там был бы шумом в чужом выводе.
if [[ -o interactive ]]; then
  autoload -Uz add-zsh-hook
  add-zsh-hook precmd _newproj_update_precmd
fi
