"""Датасет прогона: JSONL с вопросами к тестируемому сервису.

Формат одной строки:

    {"id": "q-001", "question": "...", "reference": "...", "context": {...},
     "group": "billing"}

Обязательны только `id` и `question`. `reference` — эталонный ответ, если он
есть; он попадает в промпт судьи. `group` — категория для разреза метрик
(`grouped()`) и кластерной погрешности (`stderr(cluster=...)`), поэтому кладётся
в метаданные плоским значением.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inspect_ai.dataset import Dataset, MemoryDataset, Sample

GROUP_METADATA_KEY = "group"
"""Плоский ключ категории. Плоский — потому что `grouped()` и `stderr(cluster=)`
читают метаданные сэмпла по одному ключу и во вложенный объект не заглядывают."""


def service_dataset(path: str | Path, *, limit: int | None = None) -> Dataset:
    """Читает JSONL и превращает строки в сэмплы Inspect."""
    samples: list[Sample] = []
    with Path(path).open(encoding="utf-8") as file:
        for number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            samples.append(_sample(json.loads(line), path, number))

    if not samples:
        raise ValueError(f"Датасет пуст: {path}")
    if limit is not None:
        samples = samples[:limit]
    return MemoryDataset(samples)


def _sample(row: dict[str, Any], path: str | Path, number: int) -> Sample:
    for field in ("id", "question"):
        if not row.get(field):
            raise ValueError(f"{path}:{number} — отсутствует обязательное поле {field!r}")

    return Sample(
        id=str(row["id"]),
        input=str(row["question"]),
        target=str(row.get("reference") or ""),
        metadata={
            GROUP_METADATA_KEY: str(row.get("group") or "—"),
            "context": row.get("context") or {},
        },
    )
