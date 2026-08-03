# shellcheck shell=zsh

# Интерактивное создание проекта из Copier-шаблонов.
newproj() {
  emulate -L zsh
  setopt local_options no_nomatch

  local templates_root="${NEWPROJ_TEMPLATES_DIR:-$HOME/templates}"
  local parent_input project_parent project_name target_path
  local selected_template selection confirmation create_parent
  local -a template_directories templates copier_command
  local index copier_status

  if command -v copier >/dev/null 2>&1; then
    copier_command=("$(command -v copier)")
  elif command -v uvx >/dev/null 2>&1; then
    copier_command=("$(command -v uvx)" --from copier copier)
  else
    echo "Ошибка: не найдены copier или uvx." >&2
    echo "Установите uv: https://docs.astral.sh/uv/getting-started/installation/" >&2
    return 1
  fi

  if [[ ! -d "$templates_root" ]]; then
    echo "Ошибка: директория шаблонов не найдена: $templates_root" >&2
    return 1
  fi

  template_directories=("$templates_root"/*(/N))
  for selected_template in "${template_directories[@]}"; do
    if [[ -f "$selected_template/copier.yml" || -f "$selected_template/copier.yaml" ]]; then
      templates+=("$selected_template")
    fi
  done

  if (( ${#templates[@]} == 0 )); then
    echo "Ошибка: в $templates_root нет Copier-шаблонов." >&2
    return 1
  fi

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
