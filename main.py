#!/usr/bin/env python3
"""AI Creator — Holographic Matrix Sandbox: Unified Launcher for Windows 11, Linux, macOS.

Zero extra downloads required. Runs out of the box on Python 3.10.0.

Usage examples:
    python main.py                           # Launch AI Creator Sandbox
    python main.py --demo                    # Launch matrixholo 3D wireframe demo
    python main.py --creature wolf           # Preview a procedural creature
    python main.py --model models/llama.gguf # Use local GGUF model
    python main.py --prompt "Создай лес"     # Start with creation prompt
    python main.py --test                    # Run complete test suite
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure local packages are on sys.path without requiring pip install
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MATRIXHOLO_DIR = os.path.join(REPO_ROOT, "matrixholo")
AICREATOR_DIR = os.path.join(REPO_ROOT, "aicreator")

if MATRIXHOLO_DIR not in sys.path:
    sys.path.insert(0, MATRIXHOLO_DIR)
if AICREATOR_DIR not in sys.path:
    sys.path.insert(0, AICREATOR_DIR)

# Initialize Windows 11 / Unix console settings
from matrixholo.platform_compat import setup_terminal

setup_terminal()


def run_tests() -> int:
    """Run all test suites."""
    try:
        import pytest

        return pytest.main([
            os.path.join(MATRIXHOLO_DIR, "tests"),
            os.path.join(AICREATOR_DIR, "tests"),
        ])
    except Exception as exc:
        print(f"Error running pytest: {exc}")
        return 1


def main() -> int:
    """Unified command-line dispatcher."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="AI Creator — Holographic Matrix Sandbox (Unified Launcher)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run 3D rotating holographic wireframe cube & digital rain demo",
    )
    parser.add_argument(
        "--creature",
        type=str,
        default=None,
        help="Preview a procedural creature (wolf, dragon, bird, human...)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to local GGUF model weights",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Initial prompt for AI Creator",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Target frame rate (default: 30)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Terminal width columns",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Terminal height rows",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="Run for N frames and exit (useful for automated testing)",
    )
    parser.add_argument(
        "--no-rain",
        action="store_true",
        help="Disable background Matrix digital rain",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test suite and exit",
    )

    args = parser.parse_args()

    if args.test:
        return run_tests()

    if args.demo or args.creature:
        from matrixholo.cli import run_demo

        return run_demo(
            width=args.width,
            height=args.height,
            fps=args.fps,
            frames=args.frames,
            species=args.creature,
            no_rain=args.no_rain,
        )

    # Default: launch AI Creator
    from aicreator.app import AICreatorApp

    app = AICreatorApp(
        model_path=args.model,
        fps=args.fps,
        width=args.width,
        height=args.height,
    )
    return app.run(frames=args.frames, initial_prompt=args.prompt)


if __name__ == "__main__":
    sys.exit(main())
