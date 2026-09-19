"""Digital Rain effect in classic Matrix visual style."""

from __future__ import annotations

import random
from typing import Sequence

from matrixholo.glyphs import MATRIX_CHARS, get_random_matrix_char
from matrixholo.shaders import (
    COLOR_MATRIX_BG,
    COLOR_MATRIX_DARK,
    COLOR_MATRIX_PRIMARY,
    COLOR_MATRIX_WHITE,
)
from matrixholo.zbuffer import ZBuffer


class RainDrop:
    """Individual vertical stream of digital Matrix characters with manual slots."""

    __slots__ = (
        "col",
        "y",
        "speed",
        "length",
        "chars",
        "mutate_timer",
        "active",
    )

    def __init__(self, col: int, max_height: int, rng: random.Random | None = None) -> None:
        self.col = col
        self.chars: list[str] = []
        self.mutate_timer = 0.0
        self.reset(max_height, rng, initial=True)

    def reset(
        self,
        max_height: int,
        rng: random.Random | None = None,
        initial: bool = False,
    ) -> None:
        """Reset column position, speed, and length."""
        r = rng or random
        self.speed = r.uniform(10.0, 30.0)
        self.length = r.randint(6, 24)
        if initial:
            self.y = r.uniform(-max_height, max_height)
        else:
            self.y = r.uniform(-self.length, -1.0)

        self.chars = [get_random_matrix_char(r) for _ in range(self.length)]
        self.active = True

    def update(
        self, dt: float, max_height: int, rng: random.Random | None = None
    ) -> None:
        """Update stream position and mutate characters in trail."""
        r = rng or random
        self.y += self.speed * dt

        # Randomly mutate 1 character along the stream
        self.mutate_timer += dt
        if self.mutate_timer > 0.1:
            self.mutate_timer = 0.0
            if self.chars and r.random() < 0.4:
                idx = r.randint(0, len(self.chars) - 1)
                self.chars[idx] = get_random_matrix_char(r)

        # Wrap around when trail falls below bottom
        if (self.y - self.length) > max_height:
            self.reset(max_height, rng, initial=False)


class DigitalRain:
    """Digital rain simulation spanning the terminal buffer with manual slots."""

    __slots__ = ("width", "height", "drops", "density", "depth", "enabled")

    def __init__(
        self,
        width: int,
        height: int,
        density: float = 0.4,
        depth: float = 200.0,
        enabled: bool = True,
    ) -> None:
        self.width = width
        self.height = height
        self.density = max(0.05, min(1.0, density))
        self.depth = depth
        self.enabled = enabled
        self.drops: list[RainDrop] = []
        self._init_drops()

    def _init_drops(self) -> None:
        """Initialize columns based on density."""
        self.drops.clear()
        for x in range(self.width):
            if random.random() < self.density:
                self.drops.append(RainDrop(x, self.height))

    def resize(self, width: int, height: int) -> None:
        """Handle terminal buffer resize."""
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            self._init_drops()

    def update(self, dt: float) -> None:
        """Update all active rain drops."""
        if not self.enabled:
            return
        for drop in self.drops:
            drop.update(dt, self.height)

    def render(self, zbuf: ZBuffer) -> None:
        """Render digital rain into the ZBuffer at background depth.

        Closer wireframe objects will naturally occlude the falling rain.
        """
        if not self.enabled:
            return

        for drop in self.drops:
            head_y = int(drop.y)
            length = drop.length
            x = drop.col

            if not (0 <= x < zbuf.width):
                continue

            for i in range(length):
                py = head_y - i
                if 0 <= py < zbuf.height:
                    char = drop.chars[i % len(drop.chars)]
                    # Head character is bright white-green
                    if i == 0:
                        color = COLOR_MATRIX_WHITE
                        alpha = 1.0
                    # Near head: bright neon green
                    elif i < 3:
                        color = COLOR_MATRIX_PRIMARY
                        alpha = 0.95
                    # Mid trail: medium dark green
                    elif i < length - 3:
                        color = COLOR_MATRIX_DARK
                        alpha = 0.8
                    # Tail end: deep dark green fading into void
                    else:
                        color = COLOR_MATRIX_BG
                        alpha = 0.5

                    # Digital rain renders at self.depth
                    zbuf.test_and_set(x, py, self.depth, char, color, alpha=alpha)
