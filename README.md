# newproj

Набор [Copier](https://copier.readthedocs.io/)-шаблонов проектов и команда
`newproj`, которая создаёт новый проект из выбранного шаблона в интерактивном
режиме.

Документация и changelog: <https://showpiecep.github.io/newproj/>

## Установка

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://raw.githubusercontent.com/showpiecep/newproj/main/install.sh |
  sh
```

Установщик скачивает архив релиза, проверяет его SHA-256, раскладывает шаблоны в
`~/templates/<шаблон>` и подключает команду `newproj` через управляемый блок в
`~/.zshrc`:

```zsh
# >>> newproj >>>
NEWPROJ_TEMPLATES_DIR='/Users/you/templates'
NEWPROJ_INSTALL_DIR='/Users/you/.local/share/newproj'
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

## Обновление

```bash
newproj update           # обновить, если вышел новый релиз
newproj update --check   # только проверить, ничего не устанавливая
newproj update --force   # переустановить текущий релиз без проверки
```

Повторно запускать `curl | sh` не нужно: установщик кладёт свою копию рядом с
shell-интеграцией, и `newproj update` запускает её с настройками прошлой
установки — тем же каталогом шаблонов, тем же rc-файлом и тем же набором
шаблонов. Свежий `install.sh` приезжает внутри архива релиза и заменяет копию,
поэтому обновляется и сам установщик.

Обновление трогает только каталоги с меткой `.newproj-managed`; неудачная
подмена откатывается так же, как при установке, а `~/.zshrc` переписывается,
только если управляемый блок действительно изменился.

Установленная версия хранится в `~/.local/share/newproj/state`. Не чаще раза в
неделю оболочка проверяет в фоне, вышел ли новый релиз, и один раз за сессию
показывает подсказку:

```text
newproj: доступна версия v0.2.0, установлена v0.1.0.
Обновить: newproj update
```

Проверка идёт по редиректу `/releases/latest` — без GitHub API и без токена, —
уходит в отсоединённый фон и не задерживает запуск оболочки. Частота задаётся
переменной `NEWPROJ_UPDATE_CHECK_DAYS` (по умолчанию `7`); `0` полностью
выключает и проверки, и подсказку:

```zsh
export NEWPROJ_UPDATE_CHECK_DAYS=0
```

## Удаление

```bash
sh ~/.local/share/newproj/uninstall.sh
```

Копия деинсталлятора кладётся рядом с shell-интеграцией при установке, поэтому
сеть для удаления не нужна. Тот же скрипт доступен и по HTTPS:

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://raw.githubusercontent.com/showpiecep/newproj/main/uninstall.sh | sh
```

Удаляются только каталоги с меткой `.newproj-managed`, блок из `~/.zshrc` и сама
shell-интеграция. Ваши собственные шаблоны в `~/templates`, созданные проекты и
резервные копии `~/.zshrc` остаются на месте.

## Как работает `newproj`

```bash
newproj          # интерактивное создание проекта
newproj list     # какие шаблоны доступны, с описанием каждого
newproj update   # обновить шаблоны и саму команду
newproj --help   # справка
```

Без аргументов команда спрашивает, где создать проект, как его назвать, и
показывает список шаблонов, найденных в `$NEWPROJ_TEMPLATES_DIR`. Дальше
запускается `copier copy`, который задаёт остальные вопросы шаблона, и оболочка
переходит в созданный проект:

`каталог -> имя проекта -> выбор шаблона -> copier copy -> cd в новый проект`

Список шаблонов строится из каталогов с файлом `copier.yml`, поэтому в
`~/templates` можно положить собственный шаблон рядом с установленными — он
появится в меню без изменения кода.

## Шаблоны

| Шаблон | Назначение |
|---|---|
| [fastapi-yaml](templates/fastapi-yaml/) | FastAPI-сервис с типизированной конфигурацией из YAML вместо `.env`, Loguru, типизированным `app.state` и настроенными ruff/pytest/pre-commit |
| [inspect-eval](templates/inspect-eval/) | Тестирующий сервис на Inspect AI: прогон датасета через тестируемый сервис, оценка LLM-судьёй по критериям, версионируемые конфиги прогонов и настроенный вид логов |

Шаблоны рассчитаны на пару репозиториев: приложение из `fastapi-yaml` и
тестирующий его сервис из `inspect-eval`. У них разные зависимости, разный
жизненный цикл и разные правила разработки, поэтому это два шаблона, а не один
с флагом.

## Структура репозитория

```text
templates/<имя>/      Copier-шаблоны, по одному каталогу на шаблон
installer/newproj.zsh Функция newproj для Zsh
installer/            Сборка релиза и smoke-тест установщика
install.sh            Установщик, запускаемый через curl | sh
uninstall.sh          Деинсталлятор, копируется в каталог установки
docs/                 Сайт документации на Quarto
cliff.toml            Сборка changelog из истории коммитов
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

Тег `v*` запускает два workflow: первый собирает `newproj-templates.tar.gz` с
контрольной суммой и публикует их в GitHub Release, второй пересобирает сайт с
обновлённым changelog. Подробности установщика и переменные окружения — в
[installer/README.md](installer/README.md).

Сообщения коммитов обязаны быть conventional commits: changelog собирается из
истории, отдельного файла в репозитории нет. Собрать сайт локально:

```bash
uvx git-cliff --config cliff.toml --output docs/_changelog.md
quarto preview docs
```
