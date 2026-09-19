"""Unit tests for 3D procedural primitives."""

from matrixholo.primitives import cone, cube, cylinder, grid, line, sphere, torus


def test_cube_generation():
    c = cube(pos=(0, 0, 0), size=2.0)
    assert len(c.mesh.vertices) == 8
    assert len(c.mesh.edges) == 12
    assert c.name == "cube"


def test_sphere_generation():
    s = sphere(pos=(1, 2, 3), radius=1.0, rings=6, sectors=8)
    assert len(s.mesh.vertices) > 0
    assert len(s.mesh.edges) > 0


def test_cylinder_and_cone():
    cyl = cylinder(segments=8)
    assert len(cyl.mesh.vertices) == 16
    assert len(cyl.mesh.edges) == 24

    cn = cone(segments=8)
    assert len(cn.mesh.vertices) == 9
    assert len(cn.mesh.edges) == 16


def test_torus_and_line_grid():
    t = torus(seg_major=6, seg_minor=4)
    assert len(t.mesh.vertices) == 24

    l = line((0, 0, 0), (1, 1, 1))
    assert len(l.mesh.vertices) == 2
    assert len(l.mesh.edges) == 1

    g = grid(size=4, step=1.0)
    assert len(g.mesh.vertices) > 0
