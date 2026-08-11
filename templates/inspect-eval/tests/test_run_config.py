"""Контракт YAML прогона: ошибка конфигурации должна падать до запуска."""

from pathlib import Path

import pytest
import yaml

from {{ project_slug }}.evaluation.configuration import RunConfig

BASE = {
    "dataset": "data/questions.jsonl",
    "judge": {"model": "openai/gpt-4o-mini"},
    "criteria": [{"name": "relevance", "description": "по делу"}],
}


def _write(tmp_path: Path, config: dict) -> Path:
    path = tmp_path / "run.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    return path


def test_loads_valid_config(tmp_path: Path) -> None:
    config = RunConfig.load(_write(tmp_path, BASE))

    assert [criterion.name for criterion in config.criteria] == ["relevance"]


def test_rejects_duplicate_criteria(tmp_path: Path) -> None:
    duplicated = BASE | {"criteria": BASE["criteria"] * 2}

    with pytest.raises(ValueError, match="уникальны"):
        RunConfig.load(_write(tmp_path, duplicated))


def test_rejects_unknown_prompt_version(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="версия промпта"):
        RunConfig.load(_write(tmp_path, BASE | {"prompt_version": "v99"}))


def test_rejects_unknown_field(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        RunConfig.load(_write(tmp_path, BASE | {"datasett": "typo.jsonl"}))
