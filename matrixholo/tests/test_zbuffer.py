"""Unit tests for ZBuffer depth testing and alpha blending."""

from matrixholo.zbuffer import ZBuffer


def test_zbuffer_depth_test():
    zbuf = ZBuffer(10, 10)
    assert zbuf.width == 10
    assert zbuf.height == 10

    # Write fragment at z=5.0
    accepted = zbuf.test_and_set(5, 5, 5.0, "#", (0, 255, 65))
    assert accepted is True
    char, color = zbuf.get_cell(5, 5)
    assert char == "#"
    assert color == (0, 255, 65)

    # Write fragment behind (z=8.0) -> should be rejected
    rejected = zbuf.test_and_set(5, 5, 8.0, ".", (0, 50, 0))
    assert rejected is False
    char, color = zbuf.get_cell(5, 5)
    assert char == "#"  # Unchanged

    # Write fragment in front (z=2.0) -> should overwrite
    closer = zbuf.test_and_set(5, 5, 2.0, "@", (255, 255, 255))
    assert closer is True
    char, color = zbuf.get_cell(5, 5)
    assert char == "@"
    assert color == (255, 255, 255)


def test_zbuffer_clear():
    zbuf = ZBuffer(4, 4)
    zbuf.test_and_set(1, 1, 1.0, "X", (10, 20, 30))
    zbuf.clear()
    char, color = zbuf.get_cell(1, 1)
    assert char == " "
    assert color == (0, 0, 0)
