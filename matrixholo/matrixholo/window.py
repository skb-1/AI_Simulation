"""Optional GUI window renderer using pyglet (lazy imported)."""

from __future__ import annotations

from typing import Any

from matrixholo.camera import Camera
from matrixholo.scene import Scene


class WindowRenderer:
    """Window-based wireframe renderer using pyglet.

    Requires optional dependency: pip install matrixholo[window]
    """

    def __init__(
        self,
        width: int = 1024,
        height: int = 768,
        title: str = "AI Creator — Holographic Matrix Sandbox",
    ) -> None:
        try:
            import pyglet
        except ImportError as exc:
            raise ImportError(
                "pyglet is required for WindowRenderer.\n"
                "Install it with: pip install matrixholo[window]"
            ) from exc

        self.width = width
        self.height = height
        self.title = title
        self.pyglet = pyglet
        self.window: Any = None

    def open(self) -> None:
        """Create and display GUI window."""
        self.window = self.pyglet.window.Window(
            width=self.width, height=self.height, title=self.title
        )

    def render(self, scene: Scene, camera: Camera) -> None:
        """Render frame to Pyglet window."""
        if not self.window:
            self.open()
        self.window.clear()
        # Wireframe draw loop via pyglet graphics batch if window is open
        self.window.flip()
