from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from newproj import cli


def test_bundled_templates_are_discoverable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("NEWPROJ_TEMPLATES_DIR", str(tmp_path / "custom"))

    templates = cli.discover_templates()

    assert [template.name for template in templates] == ["fastapi-yaml", "inspect-eval"]
    assert all(template.built_in for template in templates)


def test_custom_template_is_added(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    custom = tmp_path / "custom" / "mine"
    custom.mkdir(parents=True)
    (custom / "copier.yml").write_text("project_name:\n  type: str\n", encoding="utf-8")
    monkeypatch.setenv("NEWPROJ_TEMPLATES_DIR", str(tmp_path / "custom"))

    templates = cli.discover_templates()

    assert [template.name for template in templates] == ["fastapi-yaml", "inspect-eval", "mine"]
    assert not templates[-1].built_in


def test_legacy_managed_template_does_not_shadow_bundled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    legacy = tmp_path / "custom" / "fastapi-yaml"
    legacy.mkdir(parents=True)
    (legacy / "copier.yml").write_text("old: true\n", encoding="utf-8")
    (legacy / cli.MANAGED_MARKER).touch()
    monkeypatch.setenv("NEWPROJ_TEMPLATES_DIR", str(tmp_path / "custom"))

    template = next(item for item in cli.discover_templates() if item.name == "fastapi-yaml")

    assert template.built_in
    assert template.path != legacy


@pytest.mark.parametrize("name", ["", ".", "..", "a/b", "a\\b"])
def test_invalid_project_names_are_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        cli._validate_project_name(name)


def test_non_interactive_creation_calls_copier(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_run_copy(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))

    monkeypatch.setattr(cli, "run_copy", fake_run_copy)
    monkeypatch.setenv("NEWPROJ_TEMPLATES_DIR", str(tmp_path / "custom"))
    args = SimpleNamespace(
        parent=str(tmp_path),
        name="Smoke Project",
        template="fastapi-yaml",
        defaults=True,
        non_interactive=True,
    )

    result = cli.create_project(args)

    assert result == 0
    assert calls[0][0][1] == tmp_path / "Smoke Project"
    assert calls[0][1]["data"] == {"project_name": "Smoke Project"}
    assert calls[0][1]["defaults"] is True
    assert calls[0][1]["unsafe"] is True


def test_cli_lists_templates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("NEWPROJ_TEMPLATES_DIR", str(tmp_path / "custom"))

    result = cli.main(["list"])

    assert result == 0
    output = capsys.readouterr().out
    assert "fastapi-yaml" in output
    assert "inspect-eval" in output


def test_update_uses_uv_tool_upgrade(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[list[str]] = []
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/bin/uv" if name == "uv" else None)

    def fake_run(command: list[str], *, check: bool) -> SimpleNamespace:
        assert check is False
        commands.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = cli.update_tool(SimpleNamespace(check=False, force=True))

    assert result == 0
    assert commands == [["/bin/uv", "tool", "upgrade", "newproj", "--reinstall"]]


def test_cli_uses_utf8_when_parent_shell_has_legacy_encoding() -> None:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "cp1252"

    result = subprocess.run(
        [sys.executable, "-m", "newproj", "list"],
        check=False,
        capture_output=True,
        env=environment,
    )

    assert result.returncode == 0
    assert "Доступные шаблоны" in result.stdout.decode("utf-8")
