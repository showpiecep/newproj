# Правила репозитория

Репозиторий содержит кроссплатформенный Python CLI `newproj` и встроенные
Copier-шаблоны. Правила конкретного сгенерированного проекта живут внутри его
шаблона, например `templates/fastapi-yaml/AGENTS.md`.

## Границы

- В `templates/<имя>/` лежит только содержимое будущего проекта.
- Код CLI находится в `src/newproj/`; тесты репозитория — в `tests/`.
- Один каталог в `templates/` — один шаблон с собственным `copier.yml`.
- Новый шаблон не требует правок CLI: Hatch включает весь каталог `templates/`
  в wheel как `newproj/_templates`.
- Артефакты локальной работы (`config.yaml`, `.venv`, кеши) должны быть в
  `_exclude`, иначе попадут в сгенерированный проект.

Файлы шаблонов рендерятся Jinja (`_templates_suffix: ""`). Любой `{{` или
`{%` внутри шаблона обязан быть осознанным. Jinja, предназначенная для будущего
проекта, оборачивается в `{% raw %}` … `{% endraw %}`; `_copy_without_render`
в Copier 9 не существует.

## CLI и установка

- `newproj` обязан оставаться обычной консольной командой без зависимости от
  Zsh, Bash, Fish, PowerShell или другой оболочки.
- Пути обрабатываются через `pathlib`; нельзя предполагать POSIX-разделитель или
  наличие `/tmp` на Windows.
- Встроенные шаблоны читаются из пакета, пользовательские — из `~/templates`
  или `NEWPROJ_TEMPLATES_DIR`.
- `install.sh`, `uninstall.sh` и `installer/build-release.sh` — переносимый
  POSIX `sh`. `install.ps1` и `uninstall.ps1` — PowerShell.
- Загрузчики остаются тонкими и передают установку uv; они не редактируют
  rc-файлы оболочек.
- `project.version` в `pyproject.toml` совпадает с релизным тегом без `v`.

## Сайт и changelog

- `docs/` публикуется workflow `docs.yml` при push в `main` и после успешного
  релиза. Триггер по тегу не добавлять: GitHub Pages допускает деплой с `main`.
- Changelog генерируется `git-cliff` из conventional commits. Файл
  `docs/_changelog.md` генерируемый и остаётся в `.gitignore`.
- README и сайт описывают одно поведение; расхождение считается ошибкой.
- `docs/`, `cliff.toml` и `.github/` исключены из релизного архива через
  `.gitattributes`.

## Проверка изменений

- После правок CLI или упаковки запускать `sh installer/test-install.sh`.
- Проверять wheel, а не только editable-установку: встроенные шаблоны добавляет
  конфигурация сборки.
- CI обязан проходить на Ubuntu, macOS и Windows. Windows job проверяет Git Bash
  и PowerShell.
- После правок шаблона генерировать проект и запускать его быстрые проверки:
  `copier copy templates/<имя> <путь> --trust`, затем `make check` там, где
  доступен Make.
