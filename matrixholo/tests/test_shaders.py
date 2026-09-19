"""Unit tests for shaders and color manipulation."""

from matrixholo.shaders import (
    COLOR_MATRIX_BG,
    COLOR_MATRIX_PRIMARY,
    depth_shading,
    hex_to_rgb,
    parse_color,
)


def test_color_parsing():
    assert hex_to_rgb("#00FF41") == (0, 255, 65)
    assert hex_to_rgb("00FF41") == (0, 255, 65)
    assert parse_color("green") == COLOR_MATRIX_PRIMARY
    assert parse_color((10, 20, 30)) == (10, 20, 30)


def test_depth_shading():
    # Near point retains full color
    col_near = depth_shading(COLOR_MATRIX_PRIMARY, z=1.0, near=1.0, far=40.0)
    assert col_near == COLOR_MATRIX_PRIMARY

    # Far point fades towards dark green
    col_far = depth_shading(COLOR_MATRIX_PRIMARY, z=50.0, near=1.0, far=40.0)
    assert col_far[1] < col_near[1]
