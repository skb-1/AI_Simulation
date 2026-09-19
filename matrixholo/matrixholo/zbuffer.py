"""Z-Buffer with depth testing and alpha-blending for terminal rendering."""

from __future__ import annotations

from typing import Sequence, Tuple


class ZBuffer:
    """Fast 2D buffer storing depth, character, color, and alpha with manual slots."""

    __slots__ = ("width", "height", "depth", "color", "char", "alpha", "size")

    def __init__(self, width: int, height: int) -> None:
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.size = self.width * self.height

        self.depth: list[float] = [1e9] * self.size
        self.char: list[str] = [" "] * self.size
        self.color: list[Tuple[int, int, int]] = [(0, 0, 0)] * self.size
        self.alpha: list[float] = [0.0] * self.size

    def clear(
        self, bg_char: str = " ", bg_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> None:
        """Clear all buffers to background state."""
        self.depth = [1e9] * self.size
        self.char = [bg_char] * self.size
        self.color = [bg_color] * self.size
        self.alpha = [0.0] * self.size

    def resize(self, width: int, height: int) -> None:
        """Resize buffer if terminal window changes."""
        w = max(1, int(width))
        h = max(1, int(height))
        if w != self.width or h != self.height:
            self.width = w
            self.height = h
            self.size = w * h
            self.clear()

    def test_and_set(
        self,
        x: int,
        y: int,
        z: float,
        char: str,
        color: Sequence[int],
        alpha: float = 1.0,
    ) -> bool:
        """Test depth and conditionally write pixel with alpha blending.

        Returns True if pixel was accepted into the buffer.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        idx = y * self.width + x
        current_z = self.depth[idx]

        # Incoming fragment is in front
        if z < current_z:
            rgb = (int(color[0]), int(color[1]), int(color[2]))
            if alpha >= 0.99 or current_z >= 1e8:
                self.depth[idx] = z
                self.char[idx] = char
                self.color[idx] = rgb
                self.alpha[idx] = alpha
            else:
                # Alpha blend with background
                old_rgb = self.color[idx]
                inv_a = 1.0 - alpha
                blended = (
                    int(rgb[0] * alpha + old_rgb[0] * inv_a),
                    int(rgb[1] * alpha + old_rgb[1] * inv_a),
                    int(rgb[2] * alpha + old_rgb[2] * inv_a),
                )
                self.depth[idx] = z
                self.char[idx] = char
                self.color[idx] = blended
                self.alpha[idx] = alpha
            return True

        # Incoming fragment is behind, but semi-transparent background blend
        elif alpha < 1.0 and z > current_z:
            return False

        return False

    def get_cell(self, x: int, y: int) -> tuple[str, Tuple[int, int, int]]:
        """Get character and color at (x, y)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = y * self.width + x
            return self.char[idx], self.color[idx]
        return " ", (0, 0, 0)
