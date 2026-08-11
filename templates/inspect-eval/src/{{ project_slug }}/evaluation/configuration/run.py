"""Строгий контракт YAML-описания прогона.

Прогон описывается версионируемым файлом в `configs/runs/`, а не флагами в
терминале: конфигурация прогона — воспроизводимый артефакт, который лежит рядом
с кодом и виден в истории. `extra="forbid"` здесь принципиален: опечатка в имени
поля должна падать при загрузке, а не молча менять смысл прогона.
"""

from __future__ import annotations

from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, Field, model_validator

from ...prompts import prompt_versions
from .model import JudgeModelProfile


class CriterionSpec(BaseModel):
    """Один критерий оценки: имя-ключ и то, что судья по нему проверяет."""

    model_config = {"extra": "forbid", "frozen": True}

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    description: str
    label: str | None = None
    """Короткий заголовок колонки во вьюере. Без него берётся автосокращение."""

    @model_validator(mode="after")
    def _default_label(self) -> Self:
        return self


class RunConfig(BaseModel):
    """Всё, что задаёт один прогон."""

    model_config = {"extra": "forbid", "frozen": True}

    task_name: str = "service_eval"
    dataset: Path
    criteria: list[CriterionSpec] = Field(min_length=1)
    judge: JudgeModelProfile
    prompt_version: str = "v1"
    limit: int | None = Field(default=None, ge=1)
    epochs: int = Field(default=1, ge=1)
    epochs_reducer: str = "mean"
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> Self:
        names = [criterion.name for criterion in self.criteria]
        if len(names) != len(set(names)):
            raise ValueError("Имена критериев должны быть уникальны: они же ключи оценки")

        available = prompt_versions("judge")
        if available and self.prompt_version not in available:
            raise ValueError(
                f"Неизвестная версия промпта {self.prompt_version!r}; "
                f"доступны: {', '.join(available)}"
            )
        return self

    @classmethod
    def load(cls, path: str | Path, *, models_dir: str | Path = "configs/models") -> Self:
        """Читает YAML прогона, подставляя профиль судьи по имени.

        Профиль модели хранится отдельным файлом и переиспользуется прогонами:
        так «каким судьёй мерили» остаётся сравнимым между прогонами, а не
        копируется в каждый конфиг с расхождениями.
        """
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        judge = raw.get("judge")
        if isinstance(judge, str):
            raw["judge"] = JudgeModelProfile.load(Path(models_dir) / f"{judge}.yaml")
        return cls.model_validate(raw)
