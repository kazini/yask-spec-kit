"""ws: tools that operate the workspace. See ../README.md for the contract of each command."""
from pathlib import Path

try:   # one version for the steering and its tool: _steering/VERSION
    __version__ = (Path(__file__).resolve().parents[3] / "VERSION").read_text(encoding="utf-8").strip() or "0.0.0"
except OSError:
    __version__ = "0.0.0"
