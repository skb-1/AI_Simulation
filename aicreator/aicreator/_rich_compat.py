"""Pure Python 3.10 fallback implementation of Rich UI components.

Provides Console, Panel, Table, and Text when the external rich package
is not installed, ensuring complete out-of-the-box execution with zero downloads.
"""

from __future__ import annotations

import io
from typing import Any, Sequence


class Text:
    """Lightweight styled text container."""

    def __init__(self, text: str = "", style: str = "") -> None:
        self.plain = text
        self.style = style

    def append(self, text: str, style: str = "") -> None:
        self.plain += text

    @classmethod
    def from_markup(cls, markup: str) -> Text:
        # Strip simple [tags]
        import re

        clean = re.sub(r"\[/?[\w#\s=,]+\]", "", markup)
        return cls(clean)

    def __str__(self) -> str:
        return self.plain


class Table:
    """Lightweight grid table."""

    def __init__(self, padding: tuple[int, int] = (0, 1)) -> None:
        self.rows: list[list[Any]] = []
        self.columns: list[str] = []

    @classmethod
    def grid(cls, padding: tuple[int, int] = (0, 1)) -> Table:
        return cls(padding)

    def add_column(self, name: str = "", style: str = "") -> None:
        self.columns.append(name)

    def add_row(self, *items: Any) -> None:
        self.rows.append(list(items))


class Panel:
    """Bordered terminal panel."""

    def __init__(
        self,
        renderable: Any,
        title: str = "",
        border_style: str = "",
        width: int = 40,
    ) -> None:
        self.renderable = renderable
        self.title = title
        self.width = width


class Console:
    """Terminal output renderer for Panels and Tables."""

    def __init__(self, file: Any = None, width: int = 80, force_terminal: bool = True, color_system: str = "") -> None:
        self.file = file or io.StringIO()
        self.width = width

    def print(self, obj: Any) -> None:
        import re

        if isinstance(obj, Panel):
            w = obj.width or self.width
            title_clean = re.sub(r"\[/?[\w#\s=,]+\]", "", obj.title)
            header_title = f" {title_clean} "
            dash_count = max(0, w - len(header_title) - 2)
            left_d = dash_count // 2
            right_d = dash_count - left_d
            border_top = f"┌{'─'*left_d}{header_title}{'─'*right_d}┐\n"
            border_bot = f"└{'─'*(w-2)}┘\n"

            content_lines = []
            if isinstance(obj.renderable, Table):
                for row in obj.renderable.rows:
                    if len(row) == 1 and isinstance(row[0], Table):
                        # nested table
                        for sub_row in row[0].rows:
                            line_str = " ".join(str(c) for c in sub_row)
                            content_lines.append(line_str)
                    elif len(row) == 1 and isinstance(row[0], Text):
                        content_lines.extend(str(row[0]).splitlines())
                    else:
                        line_str = "  ".join(str(c) for c in row)
                        content_lines.append(line_str)
            else:
                content_lines = str(obj.renderable).splitlines()

            lines_out = [border_top]
            for cl in content_lines:
                cl_clean = re.sub(r"\[/?[\w#\s=,]+\]", "", cl)
                cl_trunc = cl_clean[: w - 4]
                padded = cl_trunc.ljust(w - 4)
                lines_out.append(f"│ {padded} │\n")
            lines_out.append(border_bot)

            out_text = "".join(lines_out)
            self.file.write(out_text)
        else:
            self.file.write(str(obj) + "\n")
