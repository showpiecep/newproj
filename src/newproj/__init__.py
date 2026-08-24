"""newproj command-line application."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("newproj")
except PackageNotFoundError:  # pragma: no cover - only when run outside an installation
    __version__ = "0.0.0"

__all__ = ["__version__"]
