"""AI Creator — Holographic Matrix Sandbox.

A lightweight, pure Python 3.10 sandbox where a local LLM serves as the
autonomous creator of an infinite 3D Matrix reality.
"""

from __future__ import annotations

from typing import Any

from aicreator.app import AICreatorApp, main
from aicreator.commands import (
    Command,
    Delete,
    Idle,
    Modify,
    SpawnCreature,
    SpawnPrimitive,
    parse_commands_json,
)
from aicreator.grammar import build_grammar
from aicreator.llm import CreatorLLM
from aicreator.world import World


def run_gui_server(*args: Any, **kwargs: Any) -> Any:
    """Lazy launcher for Holographic Matrix Web GUI Studio."""
    from aicreator.gui_server import run_gui_server as _runner

    return _runner(*args, **kwargs)


def run_pyside_app(*args: Any, **kwargs: Any) -> Any:
    """Lazy launcher for native PySide6 / PyQt Desktop application."""
    from aicreator.gui_pyside import run_pyside_app as _runner

    return _runner(*args, **kwargs)


__version__ = "0.1.0"
__all__ = [
    "AICreatorApp",
    "main",
    "run_gui_server",
    "run_pyside_app",
    "World",
    "CreatorLLM",
    "build_grammar",
    "Command",
    "SpawnPrimitive",
    "SpawnCreature",
    "Modify",
    "Delete",
    "Idle",
    "parse_commands_json",
]
