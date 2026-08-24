from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from copier import run_copy
from copier.errors import CopierError

from newproj import __version__

DEFAULT_REPOSITORY_URL = "https://github.com/showpiecep/newproj"
MANAGED_MARKER = ".newproj-managed"


@dataclass(frozen=True)
class Template:
    name: str
    path: Path
    built_in: bool


def _configure_stdio() -> None:
    """Use one predictable encoding in Windows shells and redirected CI logs."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _bundled_templates_root() -> Path:
    packaged = Path(__file__).parent / "_templates"
    if packaged.is_dir():
        return packaged

    # Source checkout fallback. Hatch force-includes templates in built wheels.
    checkout = Path(__file__).resolve().parents[2] / "templates"
    if checkout.is_dir():
        return checkout
    raise RuntimeError("В пакете newproj не найдены встроенные шаблоны.")


def _custom_templates_root() -> Path:
    configured = os.environ.get("NEWPROJ_TEMPLATES_DIR", "~/templates")
    return Path(configured).expanduser().resolve()


def _is_template(path: Path) -> bool:
    return path.is_dir() and ((path / "copier.yml").is_file() or (path / "copier.yaml").is_file())


def discover_templates() -> list[Template]:
    templates: dict[str, Template] = {}
    for candidate in sorted(_bundled_templates_root().iterdir(), key=lambda path: path.name):
        if _is_template(candidate):
            templates[candidate.name] = Template(candidate.name, candidate, built_in=True)

    custom_root = _custom_templates_root()
    if custom_root.is_dir():
        for candidate in sorted(custom_root.iterdir(), key=lambda path: path.name):
            if not _is_template(candidate):
                continue
            # Old installers copied built-ins to ~/templates. Do not let a stale
            # managed copy shadow the version bundled with the new CLI.
            if (candidate / MANAGED_MARKER).is_file() and candidate.name in templates:
                continue
            templates[candidate.name] = Template(candidate.name, candidate, built_in=False)

    return sorted(templates.values(), key=lambda template: template.name)


def template_summary(template: Template) -> str:
    readme = template.path / "README.md"
    if not readme.is_file():
        return ""

    paragraph: list[str] = []
    for raw_line in readme.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not paragraph and (not line or line.startswith("#")):
            continue
        if paragraph and not line:
            break
        paragraph.append(line)
    summary = " ".join(paragraph)
    if ". " in summary:
        summary = summary.split(". ", 1)[0] + "."
    return summary


def _select_template(name: str | None, *, interactive: bool) -> Template:
    templates = discover_templates()
    if not templates:
        raise RuntimeError("Не найдено ни одного Copier-шаблона.")

    if name:
        for template in templates:
            if template.name == name:
                return template
        available = ", ".join(template.name for template in templates)
        raise ValueError(f"Неизвестный шаблон {name!r}. Доступны: {available}")

    if not interactive:
        raise ValueError("В неинтерактивном режиме укажите --template.")

    print("Выберите шаблон:")
    for index, template in enumerate(templates, start=1):
        origin = "встроенный" if template.built_in else "пользовательский"
        print(f"{index}) {template.name} ({origin})")
        summary = template_summary(template)
        if summary:
            print(f"   {summary}")

    while True:
        answer = input("Номер шаблона: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(templates):
            return templates[int(answer) - 1]
        print(f"Введите номер от 1 до {len(templates)}.", file=sys.stderr)


def _validate_project_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Название проекта не может быть пустым.")
    if name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("Название должно быть именем директории без / и \\.")
    return name


def create_project(args: argparse.Namespace) -> int:
    interactive = not args.non_interactive
    parent_text = args.parent
    if parent_text is None:
        if not interactive:
            raise ValueError("В неинтерактивном режиме укажите --parent.")
        entered = input(f"Где создать проект? [{Path.cwd()}]: ").strip()
        parent_text = entered or str(Path.cwd())
    parent = Path(parent_text).expanduser().resolve()

    name = args.name
    if name is None:
        if not interactive:
            raise ValueError("В неинтерактивном режиме укажите --name.")
        name = input("Название проекта: ")
    name = _validate_project_name(name)

    template = _select_template(args.template, interactive=interactive)
    target = parent / name
    if target.exists():
        raise FileExistsError(f"Путь уже существует: {target}")

    if interactive:
        print(f"\nПроект:  {target}")
        print(f"Шаблон:  {template.name}")
        confirmation = input("Продолжить? [Y/n]: ").strip().lower()
        if confirmation and confirmation not in {"y", "yes"}:
            print("Создание проекта отменено.")
            return 0

    parent.mkdir(parents=True, exist_ok=True)
    run_copy(
        str(template.path),
        target,
        data={"project_name": name},
        defaults=args.defaults,
        unsafe=True,
    )
    print(f"\nПроект создан: {target}")
    print(f"Перейти в него: cd {target}")
    return 0


def list_templates() -> int:
    templates = discover_templates()
    if not templates:
        print("Не найдено ни одного Copier-шаблона.", file=sys.stderr)
        return 1

    print("Доступные шаблоны:")
    for template in templates:
        origin = "встроенный" if template.built_in else "пользовательский"
        print(f"\n  {template.name} ({origin})")
        summary = template_summary(template)
        if summary:
            print(f"    {summary}")
    return 0


def _latest_release_tag() -> str:
    repository = os.environ.get("NEWPROJ_REPOSITORY_URL", DEFAULT_REPOSITORY_URL).rstrip("/")
    request = urllib.request.Request(
        f"{repository}/releases/latest",
        headers={"User-Agent": f"newproj/{__version__}"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        final_url = response.geturl()
    marker = "/releases/tag/"
    if marker not in final_url:
        raise RuntimeError("Не удалось определить тег последнего релиза.")
    return final_url.rsplit(marker, 1)[1]


def update_tool(args: argparse.Namespace) -> int:
    if args.check:
        latest = _latest_release_tag()
        installed = f"v{__version__}"
        print(f"Установлено: {installed}. Последний релиз: {latest}.")
        if latest != installed:
            print("Для обновления выполните: newproj update")
        return 0

    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("Не найден uv. Установите его: https://docs.astral.sh/uv/")
    command = [uv, "tool", "upgrade", "newproj"]
    if args.force:
        command.append("--reinstall")
    return subprocess.run(command, check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="newproj",
        description="Создание проектов из встроенных и пользовательских Copier-шаблонов.",
    )
    parser.add_argument("--version", action="version", version=f"newproj {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    create = subparsers.add_parser("create", help="создать проект")
    create.add_argument("--parent", help="родительский каталог проекта")
    create.add_argument("--name", help="имя проекта и его каталога")
    create.add_argument("--template", help="имя шаблона")
    create.add_argument(
        "--defaults", action="store_true", help="принять ответы Copier по умолчанию"
    )
    create.add_argument(
        "--non-interactive", action="store_true", help="не задавать вопросы newproj"
    )

    subparsers.add_parser("list", help="показать доступные шаблоны")

    update = subparsers.add_parser("update", help="обновить установленную команду и шаблоны")
    update_mode = update.add_mutually_exclusive_group()
    update_mode.add_argument("--check", action="store_true", help="только проверить версию")
    update_mode.add_argument("--force", action="store_true", help="переустановить текущую версию")
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command in {None, "create"}:
            if args.command is None:
                args = parser.parse_args(["create"])
            return create_project(args)
        if args.command == "list":
            return list_templates()
        if args.command == "update":
            return update_tool(args)
    except (EOFError, KeyboardInterrupt):
        print("\nСоздание проекта отменено.", file=sys.stderr)
        return 130
    except (CopierError, OSError, RuntimeError, ValueError, urllib.error.URLError) as error:
        print(f"newproj: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
