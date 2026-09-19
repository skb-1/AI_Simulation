"""Infinite 3D reality composed of 16x16x16 chunks, value-noise terrain, and spatial hash."""

from __future__ import annotations

import gzip
import math
import pickle
from typing import TYPE_CHECKING, Sequence

from aicreator.behavior import update_creature_fsm
from aicreator.commands import (
    Command,
    Delete,
    Idle,
    Modify,
    SpawnCreature,
    SpawnPrimitive,
)
from aicreator.entities import WorldCreature, WorldEntity, WorldPrimitive
from matrixholo.scene import Entity as HoloEntity
from matrixholo.scene import Mesh, Scene
from matrixholo.vec import Vec3

CHUNK_SIZE = 16


def _hash2d(x: int, z: int) -> float:
    """Deterministic pseudo-random hash for 2D grid coordinates (pure Python)."""
    n = (x * 374761393 + z * 668265263) ^ 0x5BF03635
    n = (n ^ (n >> 13)) * 1274126177
    return float((n ^ (n >> 16)) & 0x7FFFFFFF) / float(0x7FFFFFFF)


def _smooth_noise(x: float, z: float) -> float:
    """Smooth bicubic value-noise generator for infinite terrain."""
    x0 = int(math.floor(x))
    z0 = int(math.floor(z))
    x1 = x0 + 1
    z1 = z0 + 1

    fx = x - x0
    fz = z - z0

    # Smoothstep interpolation: 3t^2 - 2t^3
    sx = fx * fx * (3.0 - 2.0 * fx)
    sz = fz * fz * (3.0 - 2.0 * fz)

    v00 = _hash2d(x0, z0)
    v10 = _hash2d(x1, z0)
    v01 = _hash2d(x0, z1)
    v11 = _hash2d(x1, z1)

    top = v00 * (1.0 - sx) + v10 * sx
    bot = v01 * (1.0 - sx) + v11 * sx
    return top * (1.0 - sz) + bot * sz


class Chunk:
    """16x16x16 World chunk containing wireframe terrain and entity identifiers."""

    __slots__ = ("coord", "entities", "terrain_entity")

    def __init__(self, coord: tuple[int, int, int]) -> None:
        self.coord = coord
        self.entities: set[int] = set()
        self.terrain_entity: HoloEntity | None = None

    def generate_terrain(self, world: World) -> HoloEntity:
        """Generate wireframe terrain mesh for this chunk."""
        cx, cy, cz = self.coord
        start_x = cx * CHUNK_SIZE
        start_z = cz * CHUNK_SIZE
        step = 4.0  # 4x4 sub-grid per chunk for crisp wireframes
        cols = int(CHUNK_SIZE / step)

        vertices: list[Vec3] = []
        edges: list[tuple[int, int]] = []

        for ix in range(cols + 1):
            for iz in range(cols + 1):
                wx = start_x + ix * step
                wz = start_z + iz * step
                wy = world.get_terrain_height(wx, wz)
                vertices.append(Vec3(wx, wy, wz))

        # Generate wireframe grid edges
        for ix in range(cols + 1):
            for iz in range(cols + 1):
                curr = ix * (cols + 1) + iz
                if iz < cols:
                    edges.append((curr, curr + 1))
                if ix < cols:
                    edges.append((curr, (ix + 1) * (cols + 1) + iz))

        mesh = Mesh(
            vertices=vertices,
            edges=edges,
            color=(0, 75, 10),
            name=f"terrain_{cx}_{cz}",
        )
        self.terrain_entity = HoloEntity(
            mesh=mesh, position=(0, 0, 0), name=f"chunk_{cx}_{cz}"
        )
        return self.terrain_entity


class World:
    """Infinite sandbox world with dynamic chunk streaming and spatial hash."""

    __slots__ = (
        "chunks",
        "entities",
        "holo_scene",
        "spatial_hash",
        "load_radius",
        "unload_radius",
        "_id_counter",
        "last_cam_chunk",
    )

    def __init__(self, holo_scene: Scene) -> None:
        self.chunks: dict[tuple[int, int, int], Chunk] = {}
        self.entities: dict[int, WorldEntity] = {}
        self.holo_scene = holo_scene
        self.spatial_hash: dict[tuple[int, int, int], list[int]] = {}
        self.load_radius = 3
        self.unload_radius = 4
        self._id_counter = 100
        self.last_cam_chunk = (0, 0, 0)

    def get_terrain_height(self, x: float, z: float) -> float:
        """Calculate terrain elevation using multi-octave value noise."""
        h1 = _smooth_noise(x * 0.03, z * 0.03) * 3.5
        h2 = _smooth_noise(x * 0.09, z * 0.09) * 1.0
        return (h1 + h2) - 3.0

    def get_chunk_coord(self, pos: Vec3) -> tuple[int, int, int]:
        """Convert world coordinates to chunk coordinates."""
        return (
            int(math.floor(pos.x / CHUNK_SIZE)),
            int(math.floor(pos.y / CHUNK_SIZE)),
            int(math.floor(pos.z / CHUNK_SIZE)),
        )

    def get_spatial_cell(self, pos: Vec3) -> tuple[int, int, int]:
        """Convert position to spatial hash cell (cell size = 8)."""
        return (
            int(math.floor(pos.x / 8.0)),
            int(math.floor(pos.y / 8.0)),
            int(math.floor(pos.z / 8.0)),
        )

    def _rebuild_spatial_hash(self) -> None:
        """Rebuild spatial hash grid for O(1) proximity queries."""
        self.spatial_hash.clear()
        for ent in self.entities.values():
            cell = self.get_spatial_cell(ent.position)
            if cell not in self.spatial_hash:
                self.spatial_hash[cell] = []
            self.spatial_hash[cell].append(ent.id)

    def get_neighbors(
        self, pos: Vec3, radius: float = 16.0
    ) -> list[WorldEntity]:
        """Query nearby entities using spatial hash."""
        cell_radius = int(math.ceil(radius / 8.0))
        cx, cy, cz = self.get_spatial_cell(pos)
        rad_sq = radius * radius
        results: list[WorldEntity] = []

        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                for dz in range(-cell_radius, cell_radius + 1):
                    cell = (cx + dx, cy + dy, cz + dz)
                    ids = self.spatial_hash.get(cell)
                    if ids:
                        for eid in ids:
                            ent = self.entities.get(eid)
                            if (
                                ent
                                and (ent.position - pos).length_sq() <= rad_sq
                            ):
                                results.append(ent)
        return results

    def add_entity(self, entity: WorldEntity) -> int:
        """Add an entity to world, assign chunk, and register in holographic scene."""
        if entity.id <= 0:
            entity.id = self._id_counter
            self._id_counter += 1

        self.entities[entity.id] = entity
        self.holo_scene.add(entity.mesh_entity)

        # Register in spatial hash
        cell = self.get_spatial_cell(entity.position)
        if cell not in self.spatial_hash:
            self.spatial_hash[cell] = []
        if entity.id not in self.spatial_hash[cell]:
            self.spatial_hash[cell].append(entity.id)

        # Place inside appropriate chunk
        c_coord = self.get_chunk_coord(entity.position)
        if c_coord not in self.chunks:
            self._load_chunk(c_coord)
        self.chunks[c_coord].entities.add(entity.id)
        entity.chunk_coord = c_coord
        return entity.id

    def remove_entity(self, entity_id: int) -> bool:
        """Remove entity from world and holographic scene."""
        if entity_id in self.entities:
            ent = self.entities.pop(entity_id)
            self.holo_scene.remove(ent.mesh_entity.id)
            cell = self.get_spatial_cell(ent.position)
            if cell in self.spatial_hash and entity_id in self.spatial_hash[cell]:
                self.spatial_hash[cell].remove(entity_id)
            if ent.chunk_coord in self.chunks:
                self.chunks[ent.chunk_coord].entities.discard(entity_id)
            return True
        return False

    def get_entity(self, entity_id: int) -> WorldEntity | None:
        """Retrieve entity by ID."""
        return self.entities.get(entity_id)

    def _load_chunk(self, coord: tuple[int, int, int]) -> Chunk:
        """Create chunk, build terrain mesh, and add to holographic scene."""
        chunk = Chunk(coord)
        terrain_ent = chunk.generate_terrain(self)
        self.holo_scene.add(terrain_ent)
        self.chunks[coord] = chunk
        return chunk

    def _unload_chunk(self, coord: tuple[int, int, int]) -> None:
        """Unload chunk and remove terrain mesh from scene."""
        chunk = self.chunks.pop(coord, None)
        if chunk and chunk.terrain_entity:
            self.holo_scene.remove(chunk.terrain_entity.id)

    def update_chunks_around(self, camera_pos: Vec3) -> None:
        """Stream chunks in radius 3 around camera and unload distant chunks."""
        cam_c = self.get_chunk_coord(camera_pos)
        self.last_cam_chunk = cam_c

        # 1. Load active chunks in radius
        cx, _, cz = cam_c
        needed_coords: set[tuple[int, int, int]] = set()
        r = self.load_radius
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r:
                    coord = (cx + dx, 0, cz + dz)
                    needed_coords.add(coord)
                    if coord not in self.chunks:
                        self._load_chunk(coord)

        # 2. Unload chunks beyond unload radius
        ur = self.unload_radius
        ur_sq = ur * ur
        for coord in list(self.chunks.keys()):
            dx = coord[0] - cx
            dz = coord[2] - cz
            if dx * dx + dz * dz > ur_sq:
                self._unload_chunk(coord)

    def apply_commands(self, commands: Sequence[Command]) -> list[int]:
        """Apply a sequence of validated Pydantic commands to the world."""
        created_ids: list[int] = []

        for cmd in commands:
            match cmd:
                case SpawnPrimitive():
                    eid = self._id_counter
                    self._id_counter += 1
                    prim = WorldPrimitive(
                        entity_id=eid,
                        primitive_type=cmd.type,
                        position=cmd.position,
                        scale=cmd.scale,
                        rotation=cmd.rotation,
                        color=cmd.color,
                    )
                    self.add_entity(prim)
                    created_ids.append(eid)

                case SpawnCreature():
                    eid = self._id_counter
                    self._id_counter += 1
                    creature = WorldCreature(
                        entity_id=eid,
                        kind=cmd.kind,
                        species=cmd.species,
                        position=cmd.position,
                        name=cmd.name,
                        personality=cmd.personality,
                        traits=cmd.traits,
                    )
                    self.add_entity(creature)
                    created_ids.append(eid)

                case Modify():
                    ent = self.get_entity(cmd.target)
                    if ent:
                        match cmd.property:
                            case "position":
                                if len(cmd.value) >= 3:
                                    ent.position = Vec3(
                                        cmd.value[0], cmd.value[1], cmd.value[2]
                                    )
                            case "rotation":
                                if len(cmd.value) >= 3:
                                    ent.rotation = Vec3(
                                        cmd.value[0], cmd.value[1], cmd.value[2]
                                    )
                            case "scale":
                                if len(cmd.value) >= 3:
                                    ent.scale = Vec3(
                                        cmd.value[0], cmd.value[1], cmd.value[2]
                                    )
                            case "color":
                                if len(cmd.value) >= 3:
                                    ent.color = (
                                        int(cmd.value[0]),
                                        int(cmd.value[1]),
                                        int(cmd.value[2]),
                                    )
                                    ent.mesh_entity.mesh.color = ent.color
                        ent.sync_to_mesh()

                case Delete():
                    self.remove_entity(cmd.target)

                case Idle():
                    pass

        return created_ids

    def update(self, dt: float, camera_pos: Vec3) -> None:
        """Frame update: dynamic chunk streaming, spatial hash, and creature FSMs."""
        # 1. Update streaming chunks
        self.update_chunks_around(camera_pos)

        # 2. Rebuild spatial hash
        self._rebuild_spatial_hash()

        # 3. Update creatures
        for ent in list(self.entities.values()):
            if isinstance(ent, WorldCreature):
                neighbors = self.get_neighbors(ent.position, radius=18.0)
                update_creature_fsm(ent, dt, self, neighbors)

                # Update chunk membership if entity crossed chunk boundary
                new_c = self.get_chunk_coord(ent.position)
                if new_c != ent.chunk_coord:
                    if ent.chunk_coord in self.chunks:
                        self.chunks[ent.chunk_coord].entities.discard(ent.id)
                    if new_c not in self.chunks:
                        self._load_chunk(new_c)
                    self.chunks[new_c].entities.add(ent.id)
                    ent.chunk_coord = new_c

    def save_to_file(self, path: str) -> None:
        """Serialize world entities and state to a gzip-compressed pickle file."""
        state = {
            "id_counter": self._id_counter,
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "pos": e.position.to_tuple(),
                    "rot": e.rotation.to_tuple(),
                    "scale": e.scale.to_tuple(),
                    "color": e.color,
                    "is_creature": isinstance(e, WorldCreature),
                    "kind": getattr(e, "kind", ""),
                    "species": getattr(e, "species", ""),
                    "traits": getattr(e, "traits", {}),
                    "prim_type": getattr(e, "primitive_type", ""),
                }
                for e in self.entities.values()
            ],
        }
        with gzip.open(path, "wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load_from_file(self, path: str) -> None:
        """Load entities and state from a gzip-compressed pickle file."""
        with gzip.open(path, "rb") as f:
            state = pickle.load(f)

        # Clear existing entities
        for eid in list(self.entities.keys()):
            self.remove_entity(eid)

        self._id_counter = state.get("id_counter", 100)
        for data in state.get("entities", []):
            if data["is_creature"]:
                c = WorldCreature(
                    entity_id=data["id"],
                    kind=data["kind"],
                    species=data["species"],
                    position=data["pos"],
                    name=data["name"],
                    traits=data["traits"],
                    color=data["color"],
                )
                self.add_entity(c)
            else:
                p = WorldPrimitive(
                    entity_id=data["id"],
                    primitive_type=data.get("prim_type", "cube"),
                    position=data["pos"],
                    scale=data["scale"],
                    rotation=data["rot"],
                    color=data["color"],
                    name=data["name"],
                )
                self.add_entity(p)
