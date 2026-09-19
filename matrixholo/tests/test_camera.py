"""Unit tests for Camera navigation and matrix generation."""

import math
from matrixholo.camera import Camera
from matrixholo.vec import Vec3


def test_camera_init():
    cam = Camera(pos=(0.0, 5.0, 10.0), target=(0.0, 0.0, 0.0))
    assert cam.pos == Vec3(0.0, 5.0, 10.0)
    assert cam.target == Vec3(0.0, 0.0, 0.0)
    assert len(cam.get_view_matrix().m) == 16
    assert len(cam.get_projection_matrix(1.5).m) == 16
    assert len(cam.get_view_projection(1.5).m) == 16


def test_camera_orbit():
    cam = Camera(pos=(0.0, 0.0, 10.0), target=(0.0, 0.0, 0.0), mode="orbit")
    # Orbit 90 degrees horizontally
    cam.orbit(math.pi * 0.5, 0.0)
    assert math.isclose(cam.pos.x, 10.0, abs_tol=1e-4)
    assert math.isclose(cam.pos.z, 0.0, abs_tol=1e-4)


def test_camera_move():
    cam = Camera(pos=(0.0, 0.0, 10.0), target=(0.0, 0.0, 0.0))
    # Forward vector points from (0,0,10) to (0,0,0), so forward = (0,0,-1)
    cam.move(forward=2.0, right=0.0, up=1.0)
    assert math.isclose(cam.pos.z, 8.0, abs_tol=1e-4)
    assert math.isclose(cam.pos.y, 1.0, abs_tol=1e-4)
