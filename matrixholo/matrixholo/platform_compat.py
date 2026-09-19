"""Cross-platform terminal handling for Windows 11, Linux, and macOS.

Supports Windows 11 Virtual Terminal Sequences, UTF-8 code pages,
and non-blocking keyboard input via msvcrt on Windows and termios/select on Unix.
"""

from __future__ import annotations

import os
import sys
from typing import Any

IS_WINDOWS = sys.platform == "win32"


def setup_terminal() -> None:
    """Configure terminal for ANSI escape codes and UTF-8 output on Windows 11 and Unix."""
    if IS_WINDOWS:
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # STD_OUTPUT_HANDLE = -11
            handle_out = kernel32.GetStdHandle(-11)
            mode_out = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle_out, ctypes.byref(mode_out)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(handle_out, mode_out.value | 0x0004)

            # STD_INPUT_HANDLE = -10
            handle_in = kernel32.GetStdHandle(-10)
            mode_in = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle_in, ctypes.byref(mode_in)):
                # ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200, ENABLE_EXTENDED_FLAGS = 0x0080
                kernel32.SetConsoleMode(handle_in, mode_in.value | 0x0200 | 0x0080)

            # Set console output and input codepage to UTF-8 (CP 65001)
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass

    # Ensure stdout and stdin use UTF-8 encoding
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8")
        except Exception:
            pass


def read_key_nonblocking() -> str | None:
    """Read a single keypress non-blockingly across Windows 11 and Unix.

    Returns:
        Key string (e.g. 'w', 's', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ESC', 'ENTER', 'BACKSPACE')
        or None if no key was pressed.
    """
    if IS_WINDOWS:
        try:
            import msvcrt

            if not msvcrt.kbhit():
                return None

            ch = msvcrt.getch()
            # Windows extended key codes (arrows, home, end, etc.)
            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                match ch2:
                    case b"H":
                        return "UP"
                    case b"P":
                        return "DOWN"
                    case b"M":
                        return "RIGHT"
                    case b"K":
                        return "LEFT"
                    case _:
                        return None

            if ch == b"\r":
                return "ENTER"
            if ch == b"\x08":
                return "BACKSPACE"
            if ch == b"\x1b":
                return "ESC"

            return ch.decode("utf-8", errors="replace")
        except Exception:
            return None
    else:
        # Unix / macOS
        import select

        if not sys.stdin.isatty():
            return None

        r, _, _ = select.select([sys.stdin], [], [], 0.0)
        if not r:
            return None

        ch = sys.stdin.read(1)
        if ch == "\033":
            # Check for escape sequences
            if select.select([sys.stdin], [], [], 0.05)[0]:
                seq = sys.stdin.read(2)
                match seq:
                    case "[A":
                        return "UP"
                    case "[B":
                        return "DOWN"
                    case "[C":
                        return "RIGHT"
                    case "[D":
                        return "LEFT"
            return "ESC"

        if ch in ("\r", "\n"):
            return "ENTER"
        if ch in ("\x7f", "\x08"):
            return "BACKSPACE"

        return ch


class TerminalContext:
    """Context manager for terminal screen mode (cbreak mode & alternate buffer)."""

    def __init__(self, enable_input: bool = True) -> None:
        self.enable_input = enable_input
        self._old_settings: Any = None
        self.alt_screen_active = False

    def __enter__(self) -> TerminalContext:
        setup_terminal()
        if sys.stdout.isatty():
            # \033[?1049h: Alt screen buffer, \033[?25l: Hide cursor, \033[2J: Clear, \033[H: Home
            sys.stdout.write("\033[?1049h\033[?25l\033[2J\033[H")
            sys.stdout.flush()
            self.alt_screen_active = True

        if not IS_WINDOWS and self.enable_input and sys.stdin.isatty():
            try:
                import termios
                import tty

                self._old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except Exception:
                pass
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not IS_WINDOWS and self._old_settings is not None:
            try:
                import termios

                termios.tcsetattr(
                    sys.stdin, termios.TCSADRAIN, self._old_settings
                )
            except Exception:
                pass

        if self.alt_screen_active and sys.stdout.isatty():
            # \033[?25h: Show cursor, \033[?1049l: Restore main screen, \033[0m: Reset styles
            sys.stdout.write("\033[?25h\033[?1049l\033[0m\n")
            sys.stdout.flush()
            self.alt_screen_active = False
