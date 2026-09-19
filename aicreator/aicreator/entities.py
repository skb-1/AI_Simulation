"""World entity wrappers with manual slots for high-frequency physics and FSM updates."""

from __future__ import annotations

import math
from typing import Any, Sequence, Union

from matrixholo.creatures import spawn_creature
from matrixholo.primitives import cone, cube, cylinder, line, sphere, torus
from matrixholo.scene import Entity as HoloEntity
from matrixholo.vec import Vec3


class WorldEntity:
    """Base world entity with manual slots for CPU performance."""

    __slots__ = (
        "id",
        "name",
        "position",
        "rotation",
        "scale",
        "velocity",
        "color",
        "mesh_entity",
        "chunk_coord",
    )

    def __init__(
        self,
        entity_id: int,
        name: str,
        position: Union[Vec3, Sequence[float]],
        mesh_entity: HoloEntity,
        rotation: Union[Vec3, Sequence[float]] = (0.0, 0.0, 0.0),
        scale: Union[Vec3, Sequence[float]] = (1.0, 1.0, 1.0),
        velocity: Union[Vec3, Sequence[float]] = (0.0, 0.0, 0.0),
        color: tuple[int, int, int] = (0, 255, 65),
    ) -> None:
        self.id = entity_id
        self.name = name
        self.position = (
            position if isinstance(position, Vec3) else Vec3.from_seq(position)
        )
        self.rotation = (
            rotation if isinstance(rotation, Vec3) else Vec3.from_seq(rotation)
        )
        self.scale = scale if isinstance(scale, Vec3) else Vec3.from_seq(scale)
        self.velocity = (
            velocity if isinstance(velocity, Vec3) else Vec3.from_seq(velocity)
        )
        self.color = color
        self.mesh_entity = mesh_entity
        self.chunk_coord = (
            int(math.floor(self.position.x / 16.0)),
            int(math.floor(self.position.y / 16.0)),
            int(math.floor(self.position.z / 16.0)),
        )

    def sync_to_mesh(self) -> None:
        """Synchronize physics position and rotation to matrixholo visual entity."""
        self.mesh_entity.position = self.position
        self.mesh_entity.rotation = self.rotation
        self.mesh_entity.scale = self.scale


class WorldPrimitive(WorldEntity):
    """Static or procedural geometric primitive placed in the world."""

    __slots__ = ("primitive_type",)

    def __init__(
        self,
        entity_id: int,
        primitive_type: str,
        position: Union[Vec3, Sequence[float]],
        scale: Union[Vec3, Sequence[float]] = (1.0, 1.0, 1.0),
        rotation: Union[Vec3, Sequence[float]] = (0.0, 0.0, 0.0),
        color: tuple[int, int, int] = (0, 255, 65),
        name: str = "",
    ) -> None:
        p_name = name or f"{primitive_type}_{entity_id}"
        pos_v = position if isinstance(position, Vec3) else Vec3.from_seq(position)

        match primitive_type:
            case "sphere":
                holo_ent = sphere(pos=pos_v, color=color, name=p_name)
            case "cylinder":
                holo_ent = cylinder(pos=pos_v, color=color, name=p_name)
            case "cone":
                holo_ent = cone(pos=pos_v, color=color, name=p_name)
            case "torus":
                holo_ent = torus(pos=pos_v, color=color, name=p_name)
            case "line":
                holo_ent = line(pos_v, pos_v + Vec3(1, 1, 1), color=color, name=p_name)
            case _:  # default cube
                holo_ent = cube(pos=pos_v, color=color, name=p_name)

        holo_ent.id = entity_id
        super().__init__(
            entity_id=entity_id,
            name=p_name,
            position=pos_v,
            mesh_entity=holo_ent,
            rotation=rotation,
            scale=scale,
            color=color,
        )
        self.primitive_type = primitive_type
        self.sync_to_mesh()


class WorldCreature(WorldEntity):
    """Autonomous living entity with state machine and procedural wireframe animation."""

    __slots__ = (
        "kind",
        "species",
        "personality",
        "traits",
        "state",
        "decision_timer",
        "target_pos",
        "target_entity_id",
        "anim_time",
        "speed",
        "aggression",
        "curiosity",
        "lifespan",
        "age",
    )

    def __init__(
        self,
        entity_id: int,
        kind: str,
        species: str,
        position: Union[Vec3, Sequence[float]],
        name: str = "",
        personality: str = "",
        traits: dict[str, float] | None = None,
        color: tuple[int, int, int] = (0, 255, 65),
    ) -> None:
        c_name = name or f"{species}_{entity_id}"
        pos_v = position if isinstance(position, Vec3) else Vec3.from_seq(position)

        holo_ent = spawn_creature(
            species=species,
            pos=pos_v,
            name=c_name,
            kind=kind,
            traits=traits,
            color=color,
        )
        holo_ent.id = entity_id

        super().__init__(
            entity_id=entity_id,
            name=c_name,
            position=pos_v,
            mesh_entity=holo_ent,
            color=color,
        )

        self.kind = kind
        self.species = species.lower().strip()
        self.personality = personality
        t = traits or {}
        self.traits = t
        self.speed = float(t.get("speed", 2.0))
        self.aggression = float(t.get("aggression", 0.0))
        self.curiosity = float(t.get("curiosity", 0.5))
        self.lifespan = float(t.get("lifespan", 300.0))
        self.age = 0.0

        # FSM State
        self.state = "WANDER"
        self.decision_timer = 0.5
        self.target_pos: Vec3 | None = None
        self.target_entity_id: int | None = None
        self.anim_time = 0.0

        self.sync_to_mesh()
