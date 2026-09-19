"""matrixholo — Holographic 3D Matrix Renderer for Python 3.10.

A lightweight, pure-Python 3D wireframe engine rendering holographic
digital rain and wireframe scenes directly inside the terminal.
"""

from __future__ import annotations

from matrixholo._compat import check_python_version
from matrixholo.camera import Camera
from matrixholo.creatures import animate_creature, spawn_creature
from matrixholo.primitives import cone, cube, cylinder, grid, line, sphere, torus
from matrixholo.rain import DigitalRain
from matrixholo.scene import Entity, Mesh, Scene
from matrixholo.terminal import TerminalRenderer
from matrixholo.vec import Mat4, Vec3, Vec4
from matrixholo.zbuffer import ZBuffer

check_python_version()

__version__ = "0.1.0"
__all__ = [
    "Scene",
    "Entity",
    "Mesh",
    "Camera",
    "TerminalRenderer",
    "Vec3",
    "Vec4",
    "Mat4",
    "ZBuffer",
    "DigitalRain",
    "cube",
    "sphere",
    "cylinder",
    "cone",
    "torus",
    "line",
    "grid",
    "spawn_creature",
    "animate_creature",
]
