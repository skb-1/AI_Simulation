"""Unit tests for line and point rasterization."""

from matrixholo.raster import draw_line, draw_point, ndc_to_screen
from matrixholo.vec import Vec3
from matrixholo.zbuffer import ZBuffer


def test_ndc_to_screen():
    # NDC (0, 0, 1.0) maps to center of screen
    sc = ndc_to_screen(Vec3(0.0, 0.0, 1.0), 100, 50)
    assert sc is not None
    # x ~ 49, y ~ 24, z = 1.0
    assert abs(sc[0] - 49) <= 1
    assert abs(sc[1] - 24) <= 1
    assert sc[2] == 1.0

    # Point behind camera (z <= 0) returns None
    assert ndc_to_screen(Vec3(0.0, 0.0, -1.0), 100, 50) is None


def test_draw_line_and_point():
    zbuf = ZBuffer(20, 20)
    draw_line(zbuf, 0, 0, 1.0, 10, 0, 1.0, (0, 255, 65))
    # Line along horizontal row 0
    drawn_count = sum(1 for x in range(11) if zbuf.char[x] != " ")
    assert drawn_count >= 10

    # Draw point with glow
    draw_point(zbuf, 5, 5, 2.0, (0, 255, 65), char="*", glow=True)
    assert zbuf.get_cell(5, 5)[0] == "*"
