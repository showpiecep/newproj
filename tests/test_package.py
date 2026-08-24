from __future__ import annotations

from pathlib import Path

from newproj import cli


def test_bundled_template_files_are_present() -> None:
    root = cli._bundled_templates_root()

    assert (root / "fastapi-yaml" / "copier.yml").is_file()
    assert (root / "fastapi-yaml" / "src" / "{{ project_slug }}" / "main.py").is_file()
    assert (root / "inspect-eval" / "copier.yml").is_file()
    assert isinstance(root, Path)
