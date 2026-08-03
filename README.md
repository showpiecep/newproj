# newproj

Набор [Copier](https://copier.readthedocs.io/)-шаблонов проектов и команда
`newproj`, которая создаёт новый проект из выбранного шаблона в интерактивном
режиме.

## Установка

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://raw.githubusercontent.com/showpiecep/my-project-template/main/install.sh |
  sh
```

Установщик скачивает архив релиза, проверяет его SHA-256, раскладывает шаблоны в
`~/templates/<шаблон>` и подключает команду `newproj` через управляемый блок в
`~/.zshrc`:

```zsh
# >>> newproj >>>
NEWPROJ_TEMPLATES_DIR='/Users/you/templates'
source '/Users/you/.local/share/newproj/newproj.zsh'
# <<< newproj <<<
```

После установки:

```bash
source ~/.zshrc
newproj
```

Требуется Zsh и `copier` либо `uvx` в `PATH` (`uvx` входит в
[uv](https://docs.astral.sh/uv/)).

## Как работает `newproj`

Команда спрашивает, где создать проект, как его назвать, и показывает список
шаблонов, найденных в `$NEWPROJ_TEMPLATES_DIR`. Дальше запускается
`copier copy`, который задаёт остальные вопросы шаблона, и оболочка переходит в
созданный проект:

`каталог -> имя проекта -> выбор шаблона -> copier copy -> cd в новый проект`

Список шаблонов строится из каталогов с файлом `copier.yml`, поэтому в
`~/templates` можно положить собственный шаблон рядом с установленными — он
появится в меню без изменения кода.

## Шаблоны

| Шаблон | Назначение |
|---|---|
| [fastapi-yaml](templates/fastapi-yaml/) | FastAPI-сервис с типизированной конфигурацией из YAML вместо `.env`, Loguru, типизированным `app.state` и настроенными ruff/pytest/pre-commit |

## Структура репозитория

```text
templates/<имя>/     Copier-шаблоны, по одному каталогу на шаблон
installer/newproj.zsh Функция newproj для Zsh
installer/            Сборка релиза и smoke-тест установщика
install.sh            Установщик, запускаемый через curl | sh
```

## Как добавить шаблон

1. Создать каталог `templates/<имя>` с файлом `copier.yml`.
2. Описать в нём вопросы шаблона и исключить из генерации служебные файлы через
   `_exclude` (как минимум `copier.yml` и `.newproj-managed`).
3. Проверить генерацию: `copier copy templates/<имя> /tmp/probe --trust`.
4. Добавить строку в таблицу шаблонов выше.

Отдельно править установщик не нужно: он раскладывает все каталоги из
`templates/`, а `newproj` находит их по наличию `copier.yml`.

## Выпуск версии

```bash
sh installer/test-install.sh
git tag v0.1.0 && git push origin v0.1.0
```

Тег `v*` запускает workflow, который собирает `newproj-templates.tar.gz` с
контрольной суммой и публикует их в GitHub Release. Подробности установщика и
переменные окружения — в [installer/README.md](installer/README.md).
