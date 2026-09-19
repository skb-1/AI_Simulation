"""High-performance 3D vector and matrix math in pure Python 3.10.

No external dependencies (no numpy, no scipy).
"""

from __future__ import annotations

import math
from typing import Iterator, Sequence, Union


class Vec3:
    """3D Vector with manual slots for high CPU performance."""

    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self) -> str:
        return f"Vec3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vec3):
            return False
        return (
            math.isclose(self.x, other.x, rel_tol=1e-5, abs_tol=1e-5)
            and math.isclose(self.y, other.y, rel_tol=1e-5, abs_tol=1e-5)
            and math.isclose(self.z, other.z, rel_tol=1e-5, abs_tol=1e-5)
        )

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        if index == 2:
            return self.z
        raise IndexError(f"Vec3 index out of range: {index}")

    def __add__(self, other: Union[Vec3, float, int]) -> Vec3:
        if isinstance(other, Vec3):
            return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
        val = float(other)
        return Vec3(self.x + val, self.y + val, self.z + val)

    def __radd__(self, other: Union[Vec3, float, int]) -> Vec3:
        return self.__add__(other)

    def __sub__(self, other: Union[Vec3, float, int]) -> Vec3:
        if isinstance(other, Vec3):
            return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
        val = float(other)
        return Vec3(self.x - val, self.y - val, self.z - val)

    def __rsub__(self, other: Union[Vec3, float, int]) -> Vec3:
        if isinstance(other, Vec3):
            return Vec3(other.x - self.x, other.y - self.y, other.z - self.z)
        val = float(other)
        return Vec3(val - self.x, val - self.y, val - self.z)

    def __mul__(self, other: Union[Vec3, float, int]) -> Vec3:
        if isinstance(other, Vec3):
            return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)
        val = float(other)
        return Vec3(self.x * val, self.y * val, self.z * val)

    def __rmul__(self, other: Union[Vec3, float, int]) -> Vec3:
        return self.__mul__(other)

    def __truediv__(self, other: Union[Vec3, float, int]) -> Vec3:
        if isinstance(other, Vec3):
            return Vec3(
                self.x / other.x if other.x != 0.0 else 0.0,
                self.y / other.y if other.y != 0.0 else 0.0,
                self.z / other.z if other.z != 0.0 else 0.0,
            )
        val = float(other)
        if val == 0.0:
            return Vec3(0.0, 0.0, 0.0)
        inv = 1.0 / val
        return Vec3(self.x * inv, self.y * inv, self.z * inv)

    def __neg__(self) -> Vec3:
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other: Vec3) -> float:
        """Dot product with another vector."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vec3) -> Vec3:
        """Cross product with another vector."""
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length_sq(self) -> float:
        """Squared Euclidean length."""
        return self.x * self.x + self.y * self.y + self.z * self.z

    def length(self) -> float:
        """Euclidean length."""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self) -> Vec3:
        """Return a unit vector in the same direction, or zero vector if length is 0."""
        len_sq = self.x * self.x + self.y * self.y + self.z * self.z
        if len_sq < 1e-12:
            return Vec3(0.0, 0.0, 0.0)
        inv = 1.0 / math.sqrt(len_sq)
        return Vec3(self.x * inv, self.y * inv, self.z * inv)

    def lerp(self, other: Vec3, t: float) -> Vec3:
        """Linear interpolation between self and other."""
        return Vec3(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t,
        )

    def distance_to(self, other: Vec3) -> float:
        """Euclidean distance to another vector."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert to (x, y, z) tuple."""
        return (self.x, self.y, self.z)

    @classmethod
    def from_seq(cls, seq: Sequence[float]) -> Vec3:
        """Construct from sequence of 3 floats."""
        return cls(seq[0], seq[1], seq[2])


class Vec4:
    """4D Vector with manual slots for homogeneous coordinate transforms."""

    __slots__ = ("x", "y", "z", "w")

    def __init__(
        self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 1.0
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)

    def __repr__(self) -> str:
        return f"Vec4({self.x:.3f}, {self.y:.3f}, {self.z:.3f}, {self.w:.3f})"

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z
        yield self.w

    def to_vec3(self) -> Vec3:
        """Perspective divide: converts homogeneous coordinates (x, y, z, w) to 3D Vec3."""
        if abs(self.w) > 1e-9:
            inv = 1.0 / self.w
            return Vec3(self.x * inv, self.y * inv, self.z * inv)
        return Vec3(self.x, self.y, self.z)

    def to_tuple(self) -> tuple[float, float, float, float]:
        """Convert to (x, y, z, w) tuple."""
        return (self.x, self.y, self.z, self.w)


class Mat4:
    """4x4 row-major transformation matrix with manual slots."""

    __slots__ = ("m",)

    def __init__(self, data: Sequence[float] | None = None) -> None:
        if data is None:
            # Identity matrix
            self.m: tuple[float, ...] = (
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            )
        else:
            if len(data) != 16:
                raise ValueError(f"Mat4 requires 16 elements, got {len(data)}")
            self.m = tuple(float(x) for x in data)

    def __repr__(self) -> str:
        rows = [
            f"[{self.m[i]:.2f}, {self.m[i+1]:.2f}, {self.m[i+2]:.2f}, {self.m[i+3]:.2f}]"
            for i in range(0, 16, 4)
        ]
        return "Mat4(\n  " + "\n  ".join(rows) + "\n)"

    def __getitem__(self, index: int) -> float:
        return self.m[index]

    @classmethod
    def identity(cls) -> Mat4:
        """Return a 4x4 identity matrix."""
        return cls()

    @classmethod
    def translation(cls, x: float, y: float, z: float) -> Mat4:
        """Translation matrix."""
        return cls((
            1.0, 0.0, 0.0, float(x),
            0.0, 1.0, 0.0, float(y),
            0.0, 0.0, 1.0, float(z),
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def scaling(cls, sx: float, sy: float, sz: float) -> Mat4:
        """Scaling matrix."""
        return cls((
            float(sx), 0.0, 0.0, 0.0,
            0.0, float(sy), 0.0, 0.0,
            0.0, 0.0, float(sz), 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def rotation_x(cls, rad: float) -> Mat4:
        """Rotation around X axis."""
        c = math.cos(rad)
        s = math.sin(rad)
        return cls((
            1.0, 0.0, 0.0, 0.0,
            0.0, c, -s, 0.0,
            0.0, s, c, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def rotation_y(cls, rad: float) -> Mat4:
        """Rotation around Y axis."""
        c = math.cos(rad)
        s = math.sin(rad)
        return cls((
            c, 0.0, s, 0.0,
            0.0, 1.0, 0.0, 0.0,
            -s, 0.0, c, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def rotation_z(cls, rad: float) -> Mat4:
        """Rotation around Z axis."""
        c = math.cos(rad)
        s = math.sin(rad)
        return cls((
            c, -s, 0.0, 0.0,
            s, c, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def euler(cls, rx: float, ry: float, rz: float) -> Mat4:
        """Rotation from Euler angles in radians (Y * X * Z order)."""
        my = cls.rotation_y(ry)
        mx = cls.rotation_x(rx)
        mz = cls.rotation_z(rz)
        return my.multiply(mx).multiply(mz)

    @classmethod
    def look_at(cls, eye: Vec3, target: Vec3, up: Vec3) -> Mat4:
        """View matrix looking from `eye` towards `target` with `up` reference vector."""
        f = (target - eye).normalized()
        r = f.cross(up).normalized()
        u = r.cross(f)

        return cls((
            r.x, r.y, r.z, -r.dot(eye),
            u.x, u.y, u.z, -u.dot(eye),
            -f.x, -f.y, -f.z, f.dot(eye),
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def perspective(
        cls, fov_deg: float, aspect: float, near: float, far: float
    ) -> Mat4:
        """Perspective projection matrix."""
        fov_rad = math.radians(fov_deg)
        tan_half = math.tan(fov_rad * 0.5)
        f = 1.0 / tan_half if tan_half != 0.0 else 1.0
        depth = near - far
        if abs(depth) < 1e-9:
            depth = -1e-9

        return cls((
            f / aspect if aspect != 0.0 else f, 0.0, 0.0, 0.0,
            0.0, f, 0.0, 0.0,
            0.0, 0.0, (far + near) / depth, (2.0 * far * near) / depth,
            0.0, 0.0, -1.0, 0.0,
        ))

    def multiply(self, other: Mat4) -> Mat4:
        """Multiply two 4x4 matrices (self @ other)."""
        a = self.m
        b = other.m
        out = [0.0] * 16
        for r in range(4):
            r_idx = r * 4
            for c in range(4):
                out[r_idx + c] = (
                    a[r_idx] * b[c]
                    + a[r_idx + 1] * b[4 + c]
                    + a[r_idx + 2] * b[8 + c]
                    + a[r_idx + 3] * b[12 + c]
                )
        return Mat4(out)

    def __matmul__(self, other: Mat4) -> Mat4:
        return self.multiply(other)

    def transform_vec3(self, v: Vec3) -> Vec3:
        """Transform 3D direction vector (w=0, ignores translation)."""
        m = self.m
        return Vec3(
            m[0] * v.x + m[1] * v.y + m[2] * v.z,
            m[4] * v.x + m[5] * v.y + m[6] * v.z,
            m[8] * v.x + m[9] * v.y + m[10] * v.z,
        )

    def transform_vec4(self, v: Vec4) -> Vec4:
        """Transform 4D vector."""
        m = self.m
        return Vec4(
            m[0] * v.x + m[1] * v.y + m[2] * v.z + m[3] * v.w,
            m[4] * v.x + m[5] * v.y + m[6] * v.z + m[7] * v.w,
            m[8] * v.x + m[9] * v.y + m[10] * v.z + m[11] * v.w,
            m[12] * v.x + m[13] * v.y + m[14] * v.z + m[15] * v.w,
        )

    def transform_point(self, v: Vec3) -> Vec3:
        """Transform 3D point (w=1) with perspective division."""
        m = self.m
        x = m[0] * v.x + m[1] * v.y + m[2] * v.z + m[3]
        y = m[4] * v.x + m[5] * v.y + m[6] * v.z + m[7]
        z = m[8] * v.x + m[9] * v.y + m[10] * v.z + m[11]
        w = m[12] * v.x + m[13] * v.y + m[14] * v.z + m[15]

        if abs(w) > 1e-9:
            inv = 1.0 / w
            return Vec3(x * inv, y * inv, z * inv)
        return Vec3(x, y, z)
