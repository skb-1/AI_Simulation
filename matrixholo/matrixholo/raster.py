"""Rasterization of 3D lines and points into a 2D ZBuffer."""

from __future__ import annotations

import math
from typing import Sequence, Tuple, Union

from matrixholo.glyphs import WIREFRAME_GLYPHS, get_glyph_by_depth
from matrixholo.shaders import depth_shading
from matrixholo.vec import Vec3
from matrixholo.zbuffer import ZBuffer


def ndc_to_screen(
    p: Vec3, width: int, height: int
) -> tuple[int, int, float] | None:
    """Convert NDC coordinates (-1..1) to screen space (0..width-1, 0..height-1).

    Returns None if point is behind camera (z <= 0).
    """
    if p.z <= 0.05:
        return None

    # NDC x, y in [-1, 1]
    # In screen space, y=0 is top, y=height-1 is bottom
    sx = int((p.x + 1.0) * 0.5 * (width - 1))
    sy = int((1.0 - (p.y + 1.0) * 0.5) * (height - 1))
    return (sx, sy, p.z)


def draw_point(
    zbuf: ZBuffer,
    x: int,
    y: int,
    z: float,
    color: Tuple[int, int, int],
    char: str = "*",
    glow: bool = False,
) -> None:
    """Rasterize a single 3D point with optional surrounding green glow."""
    shaded_col = depth_shading(color, z)
    zbuf.test_and_set(x, y, z, char, shaded_col, alpha=1.0)

    if glow and z < 30.0:
        glow_col = (shaded_col[0] // 3, shaded_col[1] // 3, shaded_col[2] // 3)
        glow_z = z + 0.05
        # Soft cross glow
        zbuf.test_and_set(x + 1, y, glow_z, ".", glow_col, alpha=0.4)
        zbuf.test_and_set(x - 1, y, glow_z, ".", glow_col, alpha=0.4)
        zbuf.test_and_set(x, y + 1, glow_z, ".", glow_col, alpha=0.4)
        zbuf.test_and_set(x, y - 1, glow_z, ".", glow_col, alpha=0.4)


def draw_line(
    zbuf: ZBuffer,
    x0: int,
    y0: int,
    z0: float,
    x1: int,
    y1: int,
    z1: float,
    color: Tuple[int, int, int],
    char_mode: str = "matrix",
) -> None:
    """Rasterize a 3D line using Bresenham's algorithm with linear depth interpolation."""
    dx = x1 - x0
    dy = y1 - y0

    adx = abs(dx)
    ady = abs(dy)
    steps = max(adx, ady)

    if steps == 0:
        draw_point(zbuf, x0, y0, z0, color, char="+")
        return

    x_inc = dx / steps
    y_inc = dy / steps
    z_inc = (z1 - z0) / steps

    cx = float(x0)
    cy = float(y0)
    cz = float(z0)

    glyph_count = len(WIREFRAME_GLYPHS)

    for i in range(steps + 1):
        ix = int(round(cx))
        iy = int(round(cy))

        if 0 <= ix < zbuf.width and 0 <= iy < zbuf.height:
            if char_mode == "matrix":
                # Cycle through Matrix wireframe characters
                glyph = WIREFRAME_GLYPHS[(ix + iy + i) % glyph_count]
            elif char_mode == "depth":
                glyph = get_glyph_by_depth(cz)
            else:
                glyph = "+" if (i == 0 or i == steps) else "."

            col = depth_shading(color, cz)
            zbuf.test_and_set(ix, iy, cz, glyph, col, alpha=1.0)

        cx += x_inc
        cy += y_inc
        cz += z_inc


def render_projected_line(
    zbuf: ZBuffer,
    p0: Vec3,
    p1: Vec3,
    color: Tuple[int, int, int],
    char_mode: str = "matrix",
) -> None:
    """Clip and rasterize a line given two points in clip space."""
    # Near plane clipping
    near = 0.1
    if p0.z < near and p1.z < near:
        return

    # Clip against near plane if one point is behind
    if p0.z < near:
        t = (near - p0.z) / (p1.z - p0.z)
        p0 = p0.lerp(p1, t)
    elif p1.z < near:
        t = (near - p1.z) / (p0.z - p1.z)
        p1 = p1.lerp(p0, t)

    s0 = ndc_to_screen(p0, zbuf.width, zbuf.height)
    s1 = ndc_to_screen(p1, zbuf.width, zbuf.height)

    if s0 is None or s1 is None:
        return

    draw_line(zbuf, s0[0], s0[1], s0[2], s1[0], s1[1], s1[2], color, char_mode)
