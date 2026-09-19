"""Matrix color palette, depth shading, glow, and flicker effects."""

from __future__ import annotations

import random
from typing import Sequence, Tuple, Union

# Matrix Color Palette defined in specification
COLOR_MATRIX_PRIMARY: Tuple[int, int, int] = (0, 255, 65)  # #00FF41 neon green
COLOR_MATRIX_DARK: Tuple[int, int, int] = (0, 143, 17)     # #008F11 medium dark
COLOR_MATRIX_BG: Tuple[int, int, int] = (0, 59, 0)         # #003B00 deep dark background
COLOR_MATRIX_WHITE: Tuple[int, int, int] = (220, 255, 220) # Bright head / highlight
COLOR_BLACK: Tuple[int, int, int] = (0, 0, 0)

# Predefined named colors
COLOR_NAMES: dict[str, Tuple[int, int, int]] = {
    "green": COLOR_MATRIX_PRIMARY,
    "neon_green": COLOR_MATRIX_PRIMARY,
    "matrix": COLOR_MATRIX_PRIMARY,
    "dark_green": COLOR_MATRIX_DARK,
    "dim_green": COLOR_MATRIX_DARK,
    "bg_green": COLOR_MATRIX_BG,
    "white": COLOR_MATRIX_WHITE,
    "highlight": COLOR_MATRIX_WHITE,
    "black": COLOR_BLACK,
    "cyan": (0, 255, 230),
    "yellow": (220, 255, 60),
    "red": (255, 50, 50),
}


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Parse #RRGGBB or RRGGBB hex string into (r, g, b) tuple."""
    clean = hex_str.lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) != 6:
        return COLOR_MATRIX_PRIMARY
    return (
        int(clean[0:2], 16),
        int(clean[2:4], 16),
        int(clean[4:6], 16),
    )


def parse_color(val: Union[str, Sequence[int]]) -> Tuple[int, int, int]:
    """Convert string name, hex, or sequence into (r, g, b) tuple."""
    if isinstance(val, str):
        val_lower = val.lower().strip()
        if val_lower in COLOR_NAMES:
            return COLOR_NAMES[val_lower]
        if val_lower.startswith("#") or len(val_lower) == 6:
            try:
                return hex_to_rgb(val_lower)
            except ValueError:
                return COLOR_MATRIX_PRIMARY
        return COLOR_MATRIX_PRIMARY
    if isinstance(val, (tuple, list)) and len(val) >= 3:
        return (
            max(0, min(255, int(val[0]))),
            max(0, min(255, int(val[1]))),
            max(0, min(255, int(val[2]))),
        )
    return COLOR_MATRIX_PRIMARY


def depth_shading(
    base_color: Tuple[int, int, int],
    z: float,
    near: float = 1.0,
    far: float = 40.0,
) -> Tuple[int, int, int]:
    """Calculate depth-based color brightness (closer = brighter, farther = darker)."""
    if z <= near:
        return base_color
    if z >= far:
        # Interpolate down to ambient dark green
        return (
            max(0, int(base_color[0] * 0.15)),
            max(15, int(base_color[1] * 0.2)),
            max(0, int(base_color[2] * 0.15)),
        )

    t = (z - near) / (far - near)
    inv_t = 1.0 - t

    # Blend between base_color and COLOR_MATRIX_BG
    r = int(base_color[0] * inv_t + COLOR_MATRIX_BG[0] * t)
    g = int(base_color[1] * inv_t + COLOR_MATRIX_BG[1] * t)
    b = int(base_color[2] * inv_t + COLOR_MATRIX_BG[2] * t)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def apply_flicker(
    color: Tuple[int, int, int],
    probability: float = 0.03,
    rng: random.Random | None = None,
) -> Tuple[int, int, int]:
    """Periodically flicker or glitch a color for holographic Matrix artifacting."""
    roll = rng.random() if rng else random.random()
    if roll < probability:
        # Flash bright white-green
        return COLOR_MATRIX_WHITE
    if roll < probability * 1.5:
        # Dim flicker
        return (color[0] // 2, color[1] // 2, color[2] // 2)
    return color
