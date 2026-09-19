"""Unit tests for Vec3, Vec4, and Mat4 3D math."""

import math
import pytest
from matrixholo.vec import Mat4, Vec3, Vec4


def test_vec3_operations():
    v1 = Vec3(1.0, 2.0, 3.0)
    v2 = Vec3(4.0, 5.0, 6.0)

    # Addition
    v_add = v1 + v2
    assert v_add == Vec3(5.0, 7.0, 9.0)

    # Scalar addition
    assert v1 + 2.0 == Vec3(3.0, 4.0, 5.0)

    # Subtraction
    v_sub = v2 - v1
    assert v_sub == Vec3(3.0, 3.0, 3.0)

    # Scalar multiplication
    v_mul = v1 * 2.0
    assert v_mul == Vec3(2.0, 4.0, 6.0)

    # Division
    v_div = v2 / 2.0
    assert v_div == Vec3(2.0, 2.5, 3.0)

    # Dot product: 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32
    assert math.isclose(v1.dot(v2), 32.0)

    # Cross product
    # i*(2*6 - 3*5) - j*(1*6 - 3*4) + k*(1*5 - 2*4)
    # i*(-3) - j*(-6) + k*(-3) = (-3, 6, -3)
    cross = v1.cross(v2)
    assert cross == Vec3(-3.0, 6.0, -3.0)

    # Length & Normalization
    v3 = Vec3(3.0, 4.0, 0.0)
    assert math.isclose(v3.length(), 5.0)
    norm = v3.normalized()
    assert math.isclose(norm.length(), 1.0)
    assert norm == Vec3(0.6, 0.8, 0.0)

    # Distance
    assert math.isclose(Vec3(0, 0, 0).distance_to(Vec3(0, 3, 4)), 5.0)


def test_vec4():
    v4 = Vec4(2.0, 4.0, 6.0, 2.0)
    v3 = v4.to_vec3()
    assert v3 == Vec3(1.0, 2.0, 3.0)
    assert list(v4) == [2.0, 4.0, 6.0, 2.0]


def test_mat4_transformations():
    # Identity
    ident = Mat4.identity()
    pt = Vec3(1.0, 2.0, 3.0)
    assert ident.transform_point(pt) == pt

    # Translation
    trans = Mat4.translation(5.0, -2.0, 10.0)
    assert trans.transform_point(pt) == Vec3(6.0, 0.0, 13.0)

    # Scaling
    scale = Mat4.scaling(2.0, 3.0, 4.0)
    assert scale.transform_point(pt) == Vec3(2.0, 6.0, 12.0)

    # Rotation X (90 degrees = pi/2)
    rx = Mat4.rotation_x(math.pi * 0.5)
    rotated = rx.transform_point(Vec3(0.0, 1.0, 0.0))
    assert math.isclose(rotated.x, 0.0, abs_tol=1e-5)
    assert math.isclose(rotated.y, 0.0, abs_tol=1e-5)
    assert math.isclose(rotated.z, 1.0, abs_tol=1e-5)

    # Combined matrix multiplication
    m = trans.multiply(scale)
    assert m.transform_point(pt) == Vec3(7.0, 4.0, 22.0)


def test_mat4_lookat_and_perspective():
    eye = Vec3(0.0, 0.0, 5.0)
    target = Vec3(0.0, 0.0, 0.0)
    up = Vec3(0.0, 1.0, 0.0)
    view = Mat4.look_at(eye, target, up)
    transformed_target = view.transform_point(target)
    # Target in front of camera should have negative Z in standard view space
    assert math.isclose(transformed_target.z, -5.0, abs_tol=1e-4)

    proj = Mat4.perspective(60.0, 1.0, 0.1, 100.0)
    assert len(proj.m) == 16
