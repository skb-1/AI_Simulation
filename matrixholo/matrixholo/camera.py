"""Camera system supporting view/projection matrices and interactive navigation."""

from __future__ import annotations

import math
from typing import Sequence, Union

from matrixholo.vec import Mat4, Vec3


class Camera:
    """3D Camera with manual slots for high-frequency matrix calculations."""

    __slots__ = (
        "pos",
        "target",
        "up",
        "fov",
        "near",
        "far",
        "yaw",
        "pitch",
        "distance",
        "mode",
    )

    def __init__(
        self,
        pos: Union[Vec3, Sequence[float]] = (0.0, 5.0, 15.0),
        target: Union[Vec3, Sequence[float]] = (0.0, 0.0, 0.0),
        up: Union[Vec3, Sequence[float]] = (0.0, 1.0, 0.0),
        fov: float = 60.0,
        near: float = 0.1,
        far: float = 1000.0,
        mode: str = "orbit",
    ) -> None:
        self.pos = pos if isinstance(pos, Vec3) else Vec3.from_seq(pos)
        self.target = target if isinstance(target, Vec3) else Vec3.from_seq(target)
        self.up = up if isinstance(up, Vec3) else Vec3.from_seq(up)
        self.fov = float(fov)
        self.near = float(near)
        self.far = float(far)
        self.mode = mode

        # Derive initial spherical coordinates from pos and target
        diff = self.pos - self.target
        self.distance = max(diff.length(), 0.1)
        self.yaw = math.atan2(diff.x, diff.z)
        self.pitch = math.asin(max(-1.0, min(1.0, diff.y / self.distance)))

    def get_view_matrix(self) -> Mat4:
        """Compute camera view matrix."""
        return Mat4.look_at(self.pos, self.target, self.up)

    def get_projection_matrix(self, aspect: float) -> Mat4:
        """Compute camera perspective projection matrix."""
        return Mat4.perspective(self.fov, aspect, self.near, self.far)

    def get_view_projection(self, aspect: float) -> Mat4:
        """Compute combined view-projection matrix (proj @ view)."""
        proj = self.get_projection_matrix(aspect)
        view = self.get_view_matrix()
        return proj.multiply(view)

    def move(self, forward: float, right: float, up: float = 0.0) -> None:
        """Translate camera and target in local camera space (WASD controls)."""
        f = (self.target - self.pos).normalized()
        r = f.cross(self.up).normalized()
        u = self.up.normalized()

        delta = (f * forward) + (r * right) + (u * up)
        self.pos = self.pos + delta
        self.target = self.target + delta

    def orbit(self, delta_yaw: float, delta_pitch: float) -> None:
        """Orbit camera around the target point."""
        self.yaw += delta_yaw
        # Clamp pitch to prevent gimbal flip
        max_pitch = math.radians(89.0)
        self.pitch = max(-max_pitch, min(max_pitch, self.pitch + delta_pitch))

        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)

        offset = Vec3(self.distance * cp * sy, self.distance * sp, self.distance * cp * cy)
        self.pos = self.target + offset

    def rotate(self, delta_yaw: float, delta_pitch: float) -> None:
        """Rotate camera view direction (arrow key controls)."""
        if self.mode == "orbit":
            self.orbit(delta_yaw, delta_pitch)
        else:
            self.yaw += delta_yaw
            max_pitch = math.radians(89.0)
            self.pitch = max(-max_pitch, min(max_pitch, self.pitch + delta_pitch))
            cy = math.cos(self.yaw)
            sy = math.sin(self.yaw)
            cp = math.cos(self.pitch)
            sp = math.sin(self.pitch)
            dir_vec = Vec3(cp * sy, sp, -cp * cy).normalized()
            self.target = self.pos + dir_vec

    def zoom(self, delta: float) -> None:
        """Zoom in or out by adjusting distance or FOV (+/- controls)."""
        if self.mode == "orbit":
            self.distance = max(1.0, min(500.0, self.distance + delta))
            cy = math.cos(self.yaw)
            sy = math.sin(self.yaw)
            cp = math.cos(self.pitch)
            sp = math.sin(self.pitch)
            offset = Vec3(
                self.distance * cp * sy, self.distance * sp, self.distance * cp * cy
            )
            self.pos = self.target + offset
        else:
            self.fov = max(15.0, min(120.0, self.fov + delta))
