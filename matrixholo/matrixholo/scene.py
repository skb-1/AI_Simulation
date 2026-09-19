"""Scene graph, Mesh, and Entity definitions with manual slots."""

from __future__ import annotations

import math
from typing import Iterator, Sequence, Tuple, Union

from matrixholo.shaders import COLOR_MATRIX_PRIMARY, parse_color
from matrixholo.vec import Mat4, Vec3


class Mesh:
    """3D Mesh containing wireframe vertices and edge indices."""

    __slots__ = ("vertices", "edges", "faces", "color", "name")

    def __init__(
        self,
        vertices: Sequence[Vec3] | None = None,
        edges: Sequence[Tuple[int, int]] | None = None,
        faces: Sequence[Sequence[int]] | None = None,
        color: Union[str, Sequence[int]] = COLOR_MATRIX_PRIMARY,
        name: str = "mesh",
    ) -> None:
        self.vertices: list[Vec3] = list(vertices) if vertices else []
        self.edges: list[Tuple[int, int]] = list(edges) if edges else []
        self.faces: list[tuple[int, ...]] = (
            [tuple(f) for f in faces] if faces else []
        )
        self.color: Tuple[int, int, int] = parse_color(color)
        self.name = name

    def copy(self) -> Mesh:
        """Create a deep copy of the mesh."""
        return Mesh(
            vertices=[Vec3(v.x, v.y, v.z) for v in self.vertices],
            edges=list(self.edges),
            faces=list(self.faces),
            color=self.color,
            name=self.name,
        )


class Entity:
    """Scene Entity positioned, rotated, and scaled in 3D world space."""

    __slots__ = (
        "id",
        "name",
        "mesh",
        "position",
        "rotation",
        "scale",
        "visible",
        "lod_threshold",
        "metadata",
    )

    def __init__(
        self,
        mesh: Mesh,
        position: Union[Vec3, Sequence[float]] = (0.0, 0.0, 0.0),
        rotation: Union[Vec3, Sequence[float]] = (0.0, 0.0, 0.0),
        scale: Union[Vec3, Sequence[float], float] = (1.0, 1.0, 1.0),
        name: str = "entity",
        entity_id: int = 0,
        visible: bool = True,
        lod_threshold: float = 60.0,
    ) -> None:
        self.id = int(entity_id)
        self.name = name
        self.mesh = mesh
        self.position = (
            position if isinstance(position, Vec3) else Vec3.from_seq(position)
        )
        self.rotation = (
            rotation if isinstance(rotation, Vec3) else Vec3.from_seq(rotation)
        )
        if isinstance(scale, (int, float)):
            self.scale = Vec3(float(scale), float(scale), float(scale))
        elif isinstance(scale, Vec3):
            self.scale = scale
        else:
            self.scale = Vec3.from_seq(scale)

        self.visible = visible
        self.lod_threshold = lod_threshold
        self.metadata: dict[str, object] = {}

    def get_model_matrix(self) -> Mat4:
        """Compute 4x4 model matrix: Translation * Rotation * Scale."""
        t = Mat4.translation(self.position.x, self.position.y, self.position.z)
        r = Mat4.euler(self.rotation.x, self.rotation.y, self.rotation.z)
        s = Mat4.scaling(self.scale.x, self.scale.y, self.scale.z)
        return t.multiply(r).multiply(s)


class Scene:
    """Collection of 3D entities in world space with manual slots."""

    __slots__ = ("entities", "_id_counter")

    def __init__(self) -> None:
        self.entities: dict[int, Entity] = {}
        self._id_counter = 1

    def add(self, entity: Entity) -> int:
        """Add an entity to the scene. Assigns an ID if not set."""
        if entity.id <= 0:
            entity.id = self._id_counter
            self._id_counter += 1
        self.entities[entity.id] = entity
        return entity.id

    def remove(self, entity_id: int) -> bool:
        """Remove entity by ID. Returns True if removed."""
        if entity_id in self.entities:
            del self.entities[entity_id]
            return True
        return False

    def get(self, entity_id: int) -> Entity | None:
        """Retrieve entity by ID."""
        return self.entities.get(entity_id)

    def all_entities(self) -> list[Entity]:
        """Return list of all entities in the scene."""
        return list(self.entities.values())

    def clear(self) -> None:
        """Remove all entities."""
        self.entities.clear()

    def __iter__(self) -> Iterator[Entity]:
        return iter(self.entities.values())

    def __len__(self) -> int:
        return len(self.entities)
