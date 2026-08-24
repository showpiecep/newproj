# Установка и выпуск newproj

`newproj` распространяется как Python wheel с консольной командой и встроенными
Copier-шаблонами. Изолированным окружением и размещением executable в `PATH`
управляет uv, одинаково на macOS, Linux и Windows.

## Установка

```text
uv tool install https://github.com/showpiecep/newproj/releases/latest/download/newproj-templates.tar.gz
```

POSIX-загрузчик `install.sh` и PowerShell-загрузчик `install.ps1` выполняют эту
же команду. Для локальной проверки источник можно переопределить:

```text
NEWPROJ_SOURCE=/path/to/newproj-0.3.0-py3-none-any.whl sh install.sh
```

```powershell
$env:NEWPROJ_SOURCE = "C:\path\to\newproj-0.3.0-py3-none-any.whl"
.\install.ps1
```

Загрузчики не редактируют rc-файлы. Если каталог команд uv ещё не в `PATH`, uv
показывает предупреждение; исправление выполняет `uv tool update-shell`.

## Обновление и удаление

```text
newproj update
uv tool uninstall newproj
```

Встроенная команда обновления вызывает `uv tool upgrade newproj`. Обновление
wheel одновременно заменяет код CLI и встроенные шаблоны.

## Проверка

```text
sh installer/test-install.sh
```

Smoke-тест запускает pytest и Ruff, собирает sdist и wheel, устанавливает wheel
в отдельный каталог и создаёт проект `fastapi-yaml`. CI повторяет проверки на
Ubuntu, macOS и Windows; Windows job использует и Git Bash, и PowerShell.

## Сборка релиза

Версия тега `vX.Y.Z` обязана совпадать с `project.version` в `pyproject.toml`:

```text
sh installer/build-release.sh v0.3.0
```

Результат:

```text
dist/v0.3.0/newproj-templates.tar.gz
dist/v0.3.0/newproj-templates.tar.gz.sha256
dist/v0.3.0/newproj-0.3.0-py3-none-any.whl
```

Архив имеет постоянное имя и служит URL установки `releases/latest/download`.
Wheel прикладывается отдельно для диагностики и прямой установки конкретной
версии. Workflow `release-newproj.yml` публикует все три файла.
