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

_newproj_usage() {
  local root
  root="$(_newproj_templates_root)"

  cat <<USAGE
newproj — создание проекта из Copier-шаблона.

Использование:
  newproj              интерактивное создание проекта
  newproj list         показать доступные шаблоны
  newproj --help       эта справка

Шаблоны берутся из $root; каталог с copier.yml считается шаблоном.
Путь переопределяется переменной NEWPROJ_TEMPLATES_DIR.

Интерактивный режим спрашивает каталог, название проекта и шаблон, затем
запускает copier и переходит в созданный проект.
USAGE
}

_newproj_list() {
  emulate -L zsh

  local root template summary
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
