"""Procedural 3D wireframe mesh primitives."""

from __future__ import annotations

import math
from typing import Sequence, Tuple, Union

from matrixholo.scene import Entity, Mesh
from matrixholo.shaders import COLOR_MATRIX_PRIMARY, parse_color
from matrixholo.vec import Vec3


def cube(
    pos: Sequence[float] | Vec3 = (0.0, 0.0, 0.0),
    size: float = 1.0,
    color: Union[str, Sequence[int]] = COLOR_MATRIX_PRIMARY,
    name: str = "cube",
) -> Entity:
    """Generate a wireframe cube centered at origin."""
    h = size * 0.5
    vertices = [
        Vec3(-h, -h, -h),  # 0: left bottom back
        Vec3(h, -h, -h),   # 1: right bottom back
        Vec3(h, h, -h),    # 2: right top back
        Vec3(-h, h, -h),   # 3: left top back
        Vec3(-h, -h, h),   # 4: left bottom front
        Vec3(h, -h, h),    # 5: right bottom front
        Vec3(h, h, h),     # 6: right top front
        Vec3(-h, h, h),    # 7: left top front
    ]
    edges = [
        # Back face
        (0, 1), (1, 2), (2, 3), (3, 0),
        # Front face
        (4, 5), (5, 6), (6, 7), (7, 4),
        # Connecting struts
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    mesh = Mesh(vertices=vertices, edges=edges, color=color, name=name)
    return Entity(mesh=mesh, position=pos, name=name)


def sphere(
    pos: Sequence[float] | Vec3 = (0.0, 0.0, 0.0),
    radius: float = 1.0,
    rings: int = 8,
    sectors: int = 12,
    color: Union[str, Sequence[int]] = COLOR_MATRIX_PRIMARY,
    name: str = "sphere",
) -> Entity:
    """Generate a UV sphere wireframe."""
    vertices: list[Vec3] = []
    edges: list[Tuple[int, int]] = []

    # Generate vertices
    for r in range(rings + 1):
        v = r / rings
        phi = v * math.pi  # 0 to pi
        sp = math.sin(phi)
        cp = math.cos(phi)

        for s in range(sectors):
            u = s / sectors
            theta = u * 2.0 * math.pi  # 0 to 2pi
            st = math.sin(theta)
            ct = math.cos(theta)

            x = radius * sp * ct
            y = radius * cp
            z = radius * sp * st
            vertices.append(Vec3(x, y, z))

    # Connect rings (horizontal circles)
    for r in range(rings + 1):
        row_start = r * sectors
        for s in range(sectors):
            curr = row_start + s
            nxt = row_start + ((s + 1) % sectors)
            edges.append((curr, nxt))

    # Connect sectors (meridians)
    for r in range(rings):
        row_curr = r * sectors
        row_next = (r + 1) * sectors
        for s in range(sectors):
            edges.append((row_curr + s, row_next + s))

    mesh = Mesh(vertices=vertices, edges=edges, color=color, name=name)
    return Entity(mesh=mesh, position=pos, name=name)


def cylinder(
    pos: Sequence[float] | Vec3 = (0.0, 0.0, 0.0),
    radius: float = 1.0,
    height: float = 2.0,
    segments: int = 12,
    color: Union[str, Sequence[int]] = COLOR_MATRIX_PRIMARY,
    name: str = "cylinder",
) -> Entity:
    """Generate a wireframe cylinder centered on the Y axis."""
    vertices: list[Vec3] = []
    edges: list[Tuple[int, int]] = []
    hy = height * 0.5

    # Bottom ring vertices [0 .. segments-1]
    # Top ring vertices [segments .. 2*segments-1]
    for i in range(segments):
        angle = (i / segments) * 2.0 * math.pi
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        vertices.append(Vec3(x, -hy, z))

    for i in range(segments):
        angle = (i / segments) * 2.0 * math.pi
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        vertices.append(Vec3(x, hy, z))

    # Ring edges and vertical connecting edges
    for i in range(segments):
        nxt = (i + 1) % segments
        # Bottom circle
        edges.append((i, nxt))
        # Top circle
        edges.append((segments + i, segments + nxt))
        # Vertical wall line
        edges.append((i, segments + i))

    mesh = Mesh(vertices=vertices, edges=edges, color=color, name=name)
    return Entity(mesh=mesh, position=pos, name=name)


def cone(
    pos: Sequence[float] | Vec3 = (0.0, 0.0, 0.0),
    radius: float = 1.0,
    height: float = 2.0,
    segments: int = 12,
    color: Union[str, Sequence[int]] = COLOR_MATRIX_PRIMARY,
    name: str = "cone",
) -> Entity:
    """Generate a wireframe cone with apex at top (+Y)."""
    vertices: list[Vec3] = []
    edges: list[Tuple[int, int]] = []
    hy = height * 0.5

    # Apex is vertex 0
    vertices.append(Vec3(0.0, hy, 0.0))

    # Base circle vertices [1 .. segments]
    for i in range(segments):
        angle = (i / segments) * 2.0 * math.pi
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        vertices.append(Vec3(x, -hy, z))

    for i in range(segments):
        curr = 1 + i
        nxt = 1 + ((i + 1) % segments)
        # Base circle edge
        edges.append((curr, nxt))
        # Edge to apex
        edges.append((0, curr))

    mesh = Mesh(vertices=vertices, edges=edges, color=color, name=name)
    return Entity(mesh=mesh, position=pos, name=name)


def torus(
    pos: Sequence[float] | Vec3 = (0.0, 0.0, 0.0),
    r_major: float = 1.5,
    r_minor: float = 0.5,
    seg_major: int = 12,
    seg_minor: int = 8,
    color: Union[str, Sequence[int]] = COLOR_MATRIX_PRIMARY,
    name: str = "torus",
) -> Entity:
    """Generate a wireframe torus (doughnut)."""
    vertices: list[Vec3] = []
    edges: list[Tuple[int, int]] = []

    for i in range(seg_major):
        theta = (i / seg_major) * 2.0 * math.pi
        ct = math.cos(theta)
        st = math.sin(theta)

        for j in range(seg_minor):
            phi = (j / seg_minor) * 2.0 * math.pi
            cp = math.cos(phi)
            sp = math.sin(phi)

            x = (r_major + r_minor * cp) * ct
            y = r_minor * sp
            z = (r_major + r_minor * cp) * st
            vertices.append(Vec3(x, y, z))

    # Connect edges
    for i in range(seg_major):
        i_nxt = (i + 1) % seg_major
        for j in range(seg_minor):
            j_nxt = (j + 1) % seg_minor
            curr = i * seg_minor + j
            # Minor ring edge
            edges.append((curr, i * seg_minor + j_nxt))
            # Major ring edge
            edges.append((curr, i_nxt * seg_minor + j))

    mesh = Mesh(vertices=vertices, edges=edges, color=color, name=name)
    return Entity(mesh=mesh, position=pos, name=name)


def line(
    p1: Sequence[float] | Vec3 = (0.0, 0.0, 0.0),
    p2: Sequence[float] | Vec3 = (1.0, 1.0, 1.0),
    color: Union[str, Sequence[int]] = COLOR_MATRIX_PRIMARY,
    name: str = "line",
) -> Entity:
    """Generate a single wireframe line segment."""
    v1 = p1 if isinstance(p1, Vec3) else Vec3.from_seq(p1)
    v2 = p2 if isinstance(p2, Vec3) else Vec3.from_seq(p2)
    mesh = Mesh(vertices=[v1, v2], edges=[(0, 1)], color=color, name=name)
    return Entity(mesh=mesh, position=(0.0, 0.0, 0.0), name=name)


def grid(
    size: int = 20,
    step: float = 2.0,
    y: float = 0.0,
    color: Union[str, Sequence[int]] = (0, 143, 17),
    name: str = "grid",
) -> Entity:
    """Generate an infinite-feel ground plane wireframe grid."""
    vertices: list[Vec3] = []
    edges: list[Tuple[int, int]] = []
    half = (size * step) * 0.5

    idx = 0
    for i in range(size + 1):
        c = -half + i * step
        # Line parallel to Z
        vertices.append(Vec3(c, y, -half))
        vertices.append(Vec3(c, y, half))
        edges.append((idx, idx + 1))
        idx += 2

        # Line parallel to X
        vertices.append(Vec3(-half, y, c))
        vertices.append(Vec3(half, y, c))
        edges.append((idx, idx + 1))
        idx += 2

    mesh = Mesh(vertices=vertices, edges=edges, color=color, name=name)
    return Entity(mesh=mesh, position=(0.0, 0.0, 0.0), name=name)
