"""ASCII and Matrix Katakana glyph sets for holographic rendering."""

from __future__ import annotations

import random
from typing import Sequence

# Authentic Matrix half-width Katakana and digits as used in the film
MATRIX_KATAKANA = "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ"
MATRIX_DIGITS = "0123456789"
MATRIX_SYMBOLS = ":・.*=+-_¦|"
MATRIX_CHARS: tuple[str, ...] = tuple(MATRIX_KATAKANA + MATRIX_DIGITS + MATRIX_SYMBOLS)
RAIN_CHARS: tuple[str, ...] = MATRIX_CHARS

# Wireframe glyph set specified in prompt
WIREFRAME_GLYPHS: tuple[str, ...] = tuple("01ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵ")

# ASCII density ramp ordered from lightest to darkest/densest
ASCII_DENSITY = " .:-=+*#%@"

# Katakana density ramp approximate visual weight
KATAKANA_DENSITY = " .:-ｰｯｨｧｸｹﾇﾘｦｱｲｳｴｵｶｻｼﾀﾂﾃﾅﾆﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾜ"

# Wireframe edge glyphs
EDGE_HORIZONTAL = "-"
EDGE_VERTICAL = "|"
EDGE_DIAGONAL_UP = "/"
EDGE_DIAGONAL_DOWN = "\\"
EDGE_VERTEX = "+"
EDGE_POINT = "*"


def get_random_matrix_char(rng: random.Random | None = None) -> str:
    """Return a random Matrix digital rain character."""
    if rng is not None:
        return rng.choice(MATRIX_CHARS)
    return random.choice(MATRIX_CHARS)


def get_random_wireframe_char(rng: random.Random | None = None) -> str:
    """Return a random wireframe Matrix character."""
    if rng is not None:
        return rng.choice(WIREFRAME_GLYPHS)
    return random.choice(WIREFRAME_GLYPHS)


def get_glyph_by_depth(
    z: float,
    z_min: float = 1.0,
    z_max: float = 50.0,
    ramp: Sequence[str] = ASCII_DENSITY,
) -> str:
    """Return character matching perceived depth (nearer = denser glyph)."""
    if z <= z_min:
        return ramp[-1]
    if z >= z_max:
        return ramp[0]

    norm = 1.0 - (z - z_min) / (z_max - z_min)
    idx = int(norm * (len(ramp) - 1))
    idx = max(0, min(len(ramp) - 1, idx))
    return ramp[idx]


def get_edge_glyph(dx: float, dy: float, z: float) -> str:
    """Return appropriate wireframe edge character based on 2D slope and depth."""
    adx = abs(dx)
    ady = abs(dy)
    if adx > 2.5 * ady:
        return "-"
    if ady > 2.5 * adx:
        return "|"
    if (dx > 0 and dy > 0) or (dx < 0 and dy < 0):
        return "\\"
    return "/"
