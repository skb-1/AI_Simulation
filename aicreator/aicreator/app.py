"""Main application coordinating the 3D render loop, LLM thread, and world simulation."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time

from aicreator.commands import parse_commands_json
from aicreator.entities import WorldCreature
from aicreator.llm import CreatorLLM, find_gguf_models
from aicreator.stream import MSG_DONE, MSG_ERROR, MSG_TOKEN, GenerationWorker
from aicreator.ui import ChatUI
from aicreator.world import World
from matrixholo.camera import Camera
from matrixholo.platform_compat import (
    IS_WINDOWS,
    read_key_nonblocking,
    setup_terminal,
)
from matrixholo.primitives import torus
from matrixholo.scene import Scene
from matrixholo.terminal import TerminalRenderer
from matrixholo.vec import Vec3


class AICreatorApp:
    """Core application engine with manual slots."""

    __slots__ = (
        "model_path",
        "fps",
        "width",
        "height",
        "scene",
        "camera",
        "renderer",
        "world",
        "llm",
        "worker",
        "ui",
        "running",
        "chat_mode",
        "chat_input_buffer",
    )

    def __init__(
        self,
        model_path: str | None = None,
        fps: int = 30,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        setup_terminal()
        term_size = shutil.get_terminal_size((120, 36))
        self.width = width or term_size.columns
        self.height = height or term_size.lines
        self.fps = fps
        self.running = True
        self.chat_mode = False
        self.chat_input_buffer = ""

        # 1. Model resolution
        if not model_path:
            discovered = find_gguf_models("models")
            if discovered:
                model_path = discovered[0]

        self.model_path = model_path
        self.llm = CreatorLLM(model_path)
        self.worker = GenerationWorker(self.llm)

        # 2. 3D Engine & World setup
        self.scene = Scene()
        self.camera = Camera(
            pos=(0.0, 6.0, 18.0), target=(0.0, 1.0, 0.0), mode="orbit"
        )
        self.renderer = TerminalRenderer(
            width=self.width,
            height=self.height,
            target_fps=fps,
            enable_rain=True,
            enable_input=False,
        )
        self.world = World(self.scene)
        self.ui = ChatUI(width=42)

        # 3. Seed initial holographic welcome artifact
        self.scene.add(
            torus(pos=(0, 2.0, 0), r_major=2.5, r_minor=0.25, color="green")
        )
        # Prime chunks around camera
        self.world.update(0.01, self.camera.pos)

    def handle_input(self) -> None:
        """Handle non-blocking keyboard input across Windows 11 and Unix."""
        key = read_key_nonblocking()
        if not key:
            return

        # In Chat Typing Mode
        if self.chat_mode:
            if key == "ENTER":
                prompt = self.chat_input_buffer.strip()
                self.chat_mode = False
                self.chat_input_buffer = ""
                if prompt:
                    self.submit_prompt(prompt)
            elif key == "BACKSPACE":
                self.chat_input_buffer = self.chat_input_buffer[:-1]
            elif key == "ESC":
                self.chat_mode = False
                self.chat_input_buffer = ""
            elif len(key) == 1 and ord(key) >= 32:
                self.chat_input_buffer += key
            return

        # In Camera Navigation Mode
        match key:
            case "UP":
                self.camera.rotate(0.0, 0.08)
            case "DOWN":
                self.camera.rotate(0.0, -0.08)
            case "RIGHT":
                self.camera.rotate(0.08, 0.0)
            case "LEFT":
                self.camera.rotate(-0.08, 0.0)
            case "w" | "W":
                self.camera.move(forward=1.2, right=0.0)
            case "s" | "S":
                self.camera.move(forward=-1.2, right=0.0)
            case "a" | "A":
                self.camera.move(forward=0.0, right=-1.2)
            case "d" | "D":
                self.camera.move(forward=0.0, right=1.2)
            case "e" | "E":
                self.camera.move(forward=0.0, right=0.0, up=1.0)
            case "c" | "C":
                self.camera.move(forward=0.0, right=0.0, up=-1.0)
            case "+" | "=":
                self.camera.zoom(-2.0)
            case "-" | "_":
                self.camera.zoom(2.0)
            case ":" | "/" | "\t":
                self.chat_mode = True
                self.chat_input_buffer = ""
            case "q" | "Q":
                self.running = False

    def submit_prompt(self, prompt: str) -> None:
        """Dispatch a user creation idea to the LLM worker thread."""
        self.ui.add_user_message(prompt)
        self.ui.status = "GENERATING"
        self.worker.start(prompt)

    def process_llm_queue(self) -> None:
        """Poll and apply completed LLM token messages and command parsing."""
        messages = self.worker.poll()
        for msg_type, payload in messages:
            if msg_type == MSG_DONE:
                self.ui.status = "MATERIALIZING"
                try:
                    commands = parse_commands_json(payload)
                    created_ids = self.world.apply_commands(commands)
                    self.ui.add_ai_message(f"Created {len(created_ids)} elements.")
                    self.ui.status = "READY"
                except Exception as exc:
                    self.ui.status = f"PARSE ERROR: {exc}"

            elif msg_type == MSG_ERROR:
                self.ui.status = f"ERROR: {payload}"

    def run(self, frames: int | None = None, initial_prompt: str | None = None) -> int:
        """Execute the interactive main loop."""
        self.renderer.enter_screen()
        if initial_prompt:
            self.submit_prompt(initial_prompt)

        frame_count = 0
        last_t = time.perf_counter()
        measured_fps = 30.0

        try:
            while self.running:
                now = time.perf_counter()
                dt = max(0.001, min(0.1, now - last_t))
                last_t = now
                measured_fps = measured_fps * 0.9 + (1.0 / dt) * 0.1

                # 1. Non-blocking input (Windows 11 / Unix)
                self.handle_input()

                # 2. LLM worker queue
                self.process_llm_queue()

                # 3. World simulation (chunks, physics, creature FSMs)
                self.world.update(dt, self.camera.pos)

                # 4. Render 3D holographic matrix view
                self.renderer.render(self.scene, self.camera)

                # 5. Overlay Rich split-screen chat panel on left side
                stats = {
                    "entities": len(self.world.entities),
                    "chunks": len(self.world.chunks),
                    "creatures": sum(
                        1
                        for e in self.world.entities.values()
                        if isinstance(e, WorldCreature)
                    ),
                    "fps": measured_fps,
                    "cam": f"({self.camera.pos.x:.1f}, {self.camera.pos.y:.1f}, {self.camera.pos.z:.1f})",
                }

                stream_preview = (
                    self.worker.current_text
                    if self.worker.is_generating
                    else ""
                )
                panel_lines = self.ui.render_panel_lines(
                    streaming_text=stream_preview,
                    stats=stats,
                    height=self.renderer.height,
                )

                # Composite left UI panel onto screen
                sys.stdout.write("\033[H")
                for row_idx, line in enumerate(panel_lines):
                    sys.stdout.write(f"\033[{row_idx + 1};1H{line}")

                if self.chat_mode:
                    prompt_str = f"Prompt: {self.chat_input_buffer}█"
                    sys.stdout.write(
                        f"\033[{self.renderer.height};1H\033[38;2;0;255;65m{prompt_str}\033[0m"
                    )

                sys.stdout.flush()

                frame_count += 1
                if frames is not None and frame_count >= frames:
                    break

        except KeyboardInterrupt:
            pass
        finally:
            self.renderer.exit_screen()

        return 0


def main(argv: list[str] | None = None) -> int:
    """Application CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="aicreator",
        description="AI Creator — Holographic Matrix Sandbox powered by local LLM",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to local GGUF model file",
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
        "--prompt",
        type=str,
        default=None,
        help="Initial creation prompt to materialize immediately",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="Run for N frames and exit (useful for automated testing)",
    )

    args = parser.parse_args(argv)
    app = AICreatorApp(
        model_path=args.model,
        fps=args.fps,
        width=args.width,
        height=args.height,
    )
    return app.run(frames=args.frames, initial_prompt=args.prompt)
