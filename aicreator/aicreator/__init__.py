"""AI Creator — Holographic Matrix Sandbox.

A lightweight, pure Python 3.10 sandbox where a local LLM serves as the
autonomous creator of an infinite 3D Matrix reality.
"""

from __future__ import annotations

from aicreator.app import AICreatorApp, main
from aicreator.gui_pyside import run_pyside_app
from aicreator.gui_server import run_gui_server
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
