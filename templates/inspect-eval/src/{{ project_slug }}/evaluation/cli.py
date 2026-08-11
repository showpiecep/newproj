"""CLI прогонов. У тестирующего сервиса нет HTTP-ручек: наружу он смотрит сюда."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from ..settings import Config
from .launch import run as run_eval


@click.group()
def cli() -> None:
    """Прогоны оценки тестируемого сервиса."""


@cli.command("run")
@click.argument("run_config", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--config", "config_path", default="config.yaml", show_default=True,
              type=click.Path(dir_okay=False, path_type=Path),
              help="Мастер-конфиг с ключами и адресом тестируемого сервиса.")
@click.option("--log-dir", default=None, help="Куда писать .eval-логи (по умолчанию logs/).")
def run_command(run_config: Path, config_path: Path, log_dir: str | None) -> None:
    """Прогнать оценку по описанию прогона из configs/runs/."""
    config = Config.load(config_path)
    logs = asyncio.run(run_eval(run_config, config=config, log_dir=log_dir))
    for log in logs:
        click.echo(f"{log.status}: {log.location}")


@cli.command("template")
@click.option("--out", default="config.template.yaml", show_default=True,
              type=click.Path(dir_okay=False, path_type=Path))
def template_command(out: Path) -> None:
    """Пересобрать шаблон мастер-конфига по текущим настройкам."""
    from .settings_template import write_template

    write_template(out)
    click.echo(f"Шаблон конфигурации: {out}")


def main() -> None:
    cli()
