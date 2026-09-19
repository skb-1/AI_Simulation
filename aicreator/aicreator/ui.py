"""Rich-based terminal UI layout for chat history, streaming tokens, and sandbox telemetry."""

from __future__ import annotations

import io
from typing import Sequence

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    from aicreator._rich_compat import Console, Panel, Table, Text  # type: ignore


class ChatUI:
    """Rich terminal user interface managing split-screen dashboard."""

    def __init__(self, width: int = 44) -> None:
        self.width = width
        self.console = Console(file=io.StringIO(), force_terminal=True, color_system="truecolor")
        self.history: list[tuple[str, str]] = []  # (role, text)
        self.status = "READY"

    def add_user_message(self, text: str) -> None:
        """Add prompt to conversation history."""
        self.history.append(("USER", text))

    def add_ai_message(self, text: str) -> None:
        """Add completed AI response to conversation history."""
        self.history.append(("AI", text))

    def render_panel_lines(
        self,
        streaming_text: str = "",
        stats: dict[str, object] | None = None,
        height: int = 36,
    ) -> list[str]:
        """Render UI panel to a list of formatted ANSI string rows."""
        s = stats or {}
        # Header Table
        table = Table.grid(padding=(0, 1))
        table.add_column("Key", style="dim green")
        table.add_column("Val", style="bold green")

        table.add_row("ENTITIES:", str(s.get("entities", 0)))
        table.add_row("CHUNKS:", str(s.get("chunks", 0)))
        table.add_row("CREATURES:", str(s.get("creatures", 0)))
        table.add_row("FPS:", f"{s.get('fps', 30.0):.1f}")
        table.add_row("CAM:", str(s.get("cam", "(0, 0, 0)")))
        table.add_row("STATUS:", f"[blink]{self.status}[/blink]" if self.status == "GENERATING" else self.status)

        # Recent chat history
        chat_text = Text()
        for role, msg in self.history[-3:]:
            if role == "USER":
                chat_text.append(f"\n> {msg}\n", style="bold green")
            else:
                summary = f"[{len(msg)} chars JSON materialized]"
                chat_text.append(f"{summary}\n", style="dim green")

        if streaming_text:
            chat_text.append("\nAI CREATOR STREAM:\n", style="bold #00FF41")
            # Show last few lines of streaming JSON
            last_lines = streaming_text.splitlines()[-6:]
            chat_text.append("\n".join(last_lines) + " █\n", style="green")

        controls = (
            "\n[dim green]CONTROLS:[/dim green]\n"
            "[green]WASD[/green]: Move   [green]ARROWS[/green]: Orbit\n"
            "[green]+ / -[/green]: Zoom   [green]:[/green]: Idea prompt\n"
            "[green]Q[/green]: Quit"
        )

        content = Table.grid()
        content.add_row(table)
        content.add_row(chat_text)
        content.add_row(Text.from_markup(controls))

        panel = Panel(
            content,
            title="[bold #00FF41]AI CREATOR :: MATRIX[/bold #00FF41]",
            border_style="#008F11",
            width=self.width,
        )

        string_io = io.StringIO()
        out_console = Console(file=string_io, width=self.width, color_system="truecolor")
        out_console.print(panel)
        rendered_str = string_io.getvalue()
        lines = rendered_str.splitlines()

        # Pad or trim to height
        if len(lines) < height:
            lines.extend([" " * self.width] * (height - len(lines)))
        return lines[:height]
