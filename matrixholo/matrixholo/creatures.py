"""Procedural creature morphology generator and wireframe animation."""

from __future__ import annotations

import hashlib
import math
from typing import Any, Sequence, Tuple, Union

from matrixholo.scene import Entity, Mesh
from matrixholo.shaders import COLOR_MATRIX_PRIMARY, parse_color
from matrixholo.vec import Vec3


def _build_humanoid(color: Tuple[int, int, int]) -> tuple[Mesh, dict[str, list[int]]]:
    """Human wireframe morphology: head, torso, 2 arms, 2 legs."""
    vertices = [
        # Head (0..3)
        Vec3(-0.25, 1.9, -0.2), Vec3(0.25, 1.9, -0.2),
        Vec3(0.25, 2.2, 0.0), Vec3(-0.25, 2.2, 0.0),
        # Torso (4..7)
        Vec3(-0.4, 1.7, 0.0), Vec3(0.4, 1.7, 0.0),   # Shoulders
        Vec3(-0.3, 0.9, 0.0), Vec3(0.3, 0.9, 0.0),   # Hips
        # Left Arm (8, 9)
        Vec3(-0.7, 1.3, 0.0), Vec3(-0.8, 0.8, 0.0),  # Elbow, Hand
        # Right Arm (10, 11)
        Vec3(0.7, 1.3, 0.0), Vec3(0.8, 0.8, 0.0),    # Elbow, Hand
        # Left Leg (12, 13)
        Vec3(-0.3, 0.4, 0.0), Vec3(-0.3, 0.0, 0.1),  # Knee, Foot
        # Right Leg (14, 15)
        Vec3(0.3, 0.4, 0.0), Vec3(0.3, 0.0, 0.1),   # Knee, Foot
    ]
    edges = [
        # Head box
        (0, 1), (1, 2), (2, 3), (3, 0),
        # Neck to torso
        (0, 4), (1, 5), (4, 5),
        # Torso spine and hips
        (4, 6), (5, 7), (6, 7),
        # Left Arm
        (4, 8), (8, 9),
        # Right Arm
        (5, 10), (10, 11),
        # Left Leg
        (6, 12), (12, 13),
        # Right Leg
        (7, 14), (14, 15),
    ]
    groups = {
        "left_arm": [8, 9],
        "right_arm": [10, 11],
        "left_leg": [12, 13],
        "right_leg": [14, 15],
    }
    return Mesh(vertices=vertices, edges=edges, color=color, name="human"), groups


def _build_quadruped(
    color: Tuple[int, int, int],
    scale_y: float = 1.0,
    snout_len: float = 0.5,
    tail_len: float = 0.7,
    name: str = "quadruped",
) -> tuple[Mesh, dict[str, list[int]]]:
    """Quadruped wireframe: wolf, dog, cat, horse."""
    v: list[Vec3] = [
        # Torso spine (0..3)
        Vec3(0.0, 0.9 * scale_y, 0.7),   # 0: Front shoulders
        Vec3(0.0, 0.85 * scale_y, -0.7), # 1: Pelvis / rear
        Vec3(-0.3, 0.75 * scale_y, 0.3), # 2: Chest left
        Vec3(0.3, 0.75 * scale_y, 0.3),  # 3: Chest right
        # Neck & Head (4..7)
        Vec3(0.0, 1.2 * scale_y, 1.1),   # 4: Neck top
        Vec3(0.0, 1.3 * scale_y, 1.3),   # 5: Forehead
        Vec3(0.0, 1.15 * scale_y, 1.3 + snout_len), # 6: Snout tip
        Vec3(-0.2, 1.5 * scale_y, 1.2),  # 7: Left ear
        Vec3(0.2, 1.5 * scale_y, 1.2),   # 8: Right ear
        # Front Left Leg (9, 10)
        Vec3(-0.3, 0.45 * scale_y, 0.7), Vec3(-0.3, 0.0, 0.7),
        # Front Right Leg (11, 12)
        Vec3(0.3, 0.45 * scale_y, 0.7), Vec3(0.3, 0.0, 0.7),
        # Back Left Leg (13, 14)
        Vec3(-0.3, 0.45 * scale_y, -0.7), Vec3(-0.3, 0.0, -0.7),
        # Back Right Leg (15, 16)
        Vec3(0.3, 0.45 * scale_y, -0.7), Vec3(0.3, 0.0, -0.7),
        # Tail (17, 18)
        Vec3(0.0, 0.65 * scale_y, -0.7 - tail_len * 0.5),
        Vec3(0.0, 0.45 * scale_y, -0.7 - tail_len),
    ]
    edges = [
        # Spine & Torso
        (0, 1), (0, 2), (0, 3), (2, 3), (1, 2), (1, 3),
        # Neck & Head
        (0, 4), (4, 5), (5, 6), (4, 6),
        # Ears
        (5, 7), (5, 8),
        # Front legs
        (0, 9), (9, 10),
        (0, 11), (11, 12),
        # Back legs
        (1, 13), (13, 14),
        (1, 15), (15, 16),
        # Tail
        (1, 17), (17, 18),
    ]
    groups = {
        "leg_fl": [9, 10],
        "leg_fr": [11, 12],
        "leg_bl": [13, 14],
        "leg_br": [15, 16],
        "tail": [17, 18],
    }
    return Mesh(vertices=v, edges=edges, color=color, name=name), groups


def _build_bird(color: Tuple[int, int, int]) -> tuple[Mesh, dict[str, list[int]]]:
    """Bird wireframe: body, wings, beak, tail."""
    v = [
        # Body (0..2)
        Vec3(0.0, 1.0, 0.5),   # 0: Breast
        Vec3(0.0, 0.9, -0.5),  # 1: Tail base
        Vec3(0.0, 1.3, 0.8),   # 2: Head
        # Beak (3)
        Vec3(0.0, 1.25, 1.1),  # 3: Beak tip
        # Left Wing (4, 5)
        Vec3(-1.0, 1.1, 0.2),  # 4: Mid wing
        Vec3(-1.8, 1.2, 0.0),  # 5: Wing tip
        # Right Wing (6, 7)
        Vec3(1.0, 1.1, 0.2),   # 6: Mid wing
        Vec3(1.8, 1.2, 0.0),   # 7: Wing tip
        # Tail feathers (8, 9)
        Vec3(-0.3, 0.85, -0.9), Vec3(0.3, 0.85, -0.9),
        # Feet (10, 11)
        Vec3(-0.2, 0.5, 0.0), Vec3(0.2, 0.5, 0.0),
    ]
    edges = [
        (0, 1), (0, 2), (2, 3),
        # Left wing
        (0, 4), (4, 5), (1, 4),
        # Right wing
        (0, 6), (6, 7), (1, 6),
        # Tail
        (1, 8), (1, 9), (8, 9),
        # Feet
        (0, 10), (0, 11),
    ]
    groups = {
        "wing_l": [4, 5],
        "wing_r": [6, 7],
        "tail": [8, 9],
    }
    return Mesh(vertices=v, edges=edges, color=color, name="bird"), groups


def _build_fish(color: Tuple[int, int, int]) -> tuple[Mesh, dict[str, list[int]]]:
    """Fish wireframe: streamlined ellipsoid, dorsal fin, caudal tail fin."""
    v = [
        # Snout (0)
        Vec3(0.0, 0.5, 1.0),
        # Mid body ring (1..4)
        Vec3(-0.3, 0.5, 0.2), Vec3(0.3, 0.5, 0.2),
        Vec3(0.0, 0.8, 0.2), Vec3(0.0, 0.2, 0.2),
        # Tail base (5)
        Vec3(0.0, 0.5, -0.7),
        # Caudal fin (6..8)
        Vec3(0.0, 0.9, -1.2), Vec3(0.0, 0.5, -1.0), Vec3(0.0, 0.1, -1.2),
        # Dorsal fin (9)
        Vec3(0.0, 1.1, -0.1),
        # Pectoral fins (10, 11)
        Vec3(-0.6, 0.4, 0.1), Vec3(0.6, 0.4, 0.1),
    ]
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 3), (3, 2), (2, 4), (4, 1),
        (1, 5), (2, 5), (3, 5), (4, 5),
        # Tail
        (5, 6), (5, 7), (5, 8), (6, 7), (7, 8),
        # Fins
        (3, 9), (9, 5),
        (1, 10), (2, 11),
    ]
    groups = {
        "tail": [5, 6, 7, 8],
    }
    return Mesh(vertices=v, edges=edges, color=color, name="fish"), groups


def _build_spider(color: Tuple[int, int, int]) -> tuple[Mesh, dict[str, list[int]]]:
    """Spider wireframe: head, abdomen, 8 jointed legs."""
    v = [
        # Cephalothorax (0)
        Vec3(0.0, 0.4, 0.2),
        # Abdomen (1..4)
        Vec3(0.0, 0.5, -0.4), Vec3(-0.3, 0.4, -0.4),
        Vec3(0.3, 0.4, -0.4), Vec3(0.0, 0.3, -0.8),
    ]
    edges = [
        (0, 1), (1, 2), (1, 3), (2, 4), (3, 4), (1, 4),
    ]
    leg_groups: dict[str, list[int]] = {}

    # 8 legs: 4 left, 4 right
    idx = len(v)
    for i in range(4):
        side_z = 0.3 - i * 0.25
        # Left leg
        v.append(Vec3(-0.6, 0.7, side_z))  # knee
        v.append(Vec3(-1.0, 0.0, side_z))  # tip
        edges.append((0, idx))
        edges.append((idx, idx + 1))
        leg_groups[f"leg_l_{i}"] = [idx, idx + 1]
        idx += 2

        # Right leg
        v.append(Vec3(0.6, 0.7, side_z))   # knee
        v.append(Vec3(1.0, 0.0, side_z))   # tip
        edges.append((0, idx))
        edges.append((idx, idx + 1))
        leg_groups[f"leg_r_{i}"] = [idx, idx + 1]
        idx += 2

    return Mesh(vertices=v, edges=edges, color=color, name="spider"), leg_groups


def _build_snake(
    color: Tuple[int, int, int], segments: int = 10
) -> tuple[Mesh, dict[str, list[int]]]:
    """Snake wireframe: spine of undulating vertebrae."""
    v: list[Vec3] = []
    edges: list[Tuple[int, int]] = []
    groups: dict[str, list[int]] = {"body": []}

    for i in range(segments):
        z = (segments - i) * 0.3
        v.append(Vec3(0.0, 0.15, z))
        groups["body"].append(i)
        if i > 0:
            edges.append((i - 1, i))

    # Add head triangle
    v.append(Vec3(-0.15, 0.15, segments * 0.3 + 0.2))
    v.append(Vec3(0.15, 0.15, segments * 0.3 + 0.2))
    edges.append((0, len(v) - 2))
    edges.append((0, len(v) - 1))
    edges.append((len(v) - 2, len(v) - 1))

    return Mesh(vertices=v, edges=edges, color=color, name="snake"), groups


def _build_dragon(color: Tuple[int, int, int]) -> tuple[Mesh, dict[str, list[int]]]:
    """Dragon wireframe: quadruped body, horned head, large wings, spiky tail."""
    mesh, groups = _build_quadruped(
        color, scale_y=1.4, snout_len=0.8, tail_len=1.5, name="dragon"
    )
    v = mesh.vertices
    e = mesh.edges

    # Add horns to head (vertex 5)
    horn_l = len(v)
    v.append(Vec3(-0.3, 2.3, 1.1))
    v.append(Vec3(0.3, 2.3, 1.1))
    e.append((5, horn_l))
    e.append((5, horn_l + 1))

    # Add massive wings attached to shoulder (vertex 0)
    wing_l_mid = len(v)
    v.append(Vec3(-1.8, 2.0, 0.4))   # Wing elbow L
    v.append(Vec3(-3.0, 2.5, 0.0))   # Wing tip L
    v.append(Vec3(-2.2, 1.2, -0.4))  # Wing spar L

    e.append((0, wing_l_mid))
    e.append((wing_l_mid, wing_l_mid + 1))
    e.append((wing_l_mid + 1, wing_l_mid + 2))
    e.append((0, wing_l_mid + 2))

    wing_r_mid = len(v)
    v.append(Vec3(1.8, 2.0, 0.4))    # Wing elbow R
    v.append(Vec3(3.0, 2.5, 0.0))    # Wing tip R
    v.append(Vec3(2.2, 1.2, -0.4))   # Wing spar R

    e.append((0, wing_r_mid))
    e.append((wing_r_mid, wing_r_mid + 1))
    e.append((wing_r_mid + 1, wing_r_mid + 2))
    e.append((0, wing_r_mid + 2))

    groups["wings"] = [
        wing_l_mid, wing_l_mid + 1, wing_l_mid + 2,
        wing_r_mid, wing_r_mid + 1, wing_r_mid + 2,
    ]
    return Mesh(vertices=v, edges=e, color=color, name="dragon"), groups


def _build_robot(color: Tuple[int, int, int]) -> tuple[Mesh, dict[str, list[int]]]:
    """Robot wireframe: geometric boxy chassis, antenna, piston joints."""
    v = [
        # Box Torso (0..7)
        Vec3(-0.5, 0.6, -0.3), Vec3(0.5, 0.6, -0.3),
        Vec3(0.5, 1.5, -0.3), Vec3(-0.5, 1.5, -0.3),
        Vec3(-0.5, 0.6, 0.3), Vec3(0.5, 0.6, 0.3),
        Vec3(0.5, 1.5, 0.3), Vec3(-0.5, 1.5, 0.3),
        # Box Head (8..11)
        Vec3(-0.3, 1.7, -0.2), Vec3(0.3, 1.7, -0.2),
        Vec3(0.3, 2.2, 0.2), Vec3(-0.3, 2.2, 0.2),
        # Antenna (12)
        Vec3(0.0, 2.6, 0.0),
        # Left Leg Piston (13, 14)
        Vec3(-0.3, 0.0, 0.0), Vec3(-0.3, -0.1, 0.2),
        # Right Leg Piston (15, 16)
        Vec3(0.3, 0.0, 0.0), Vec3(0.3, -0.1, 0.2),
    ]
    edges = [
        # Torso
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
        # Neck to Head
        (2, 8), (3, 9), (8, 9), (9, 10), (10, 11), (11, 8),
        # Antenna
        ((8 + 9) // 2, 12),
        # Legs
        (0, 13), (13, 14),
        (1, 15), (15, 16),
    ]
    groups = {
        "leg_l": [13, 14],
        "leg_r": [15, 16],
    }
    return Mesh(vertices=v, edges=edges, color=color, name="robot"), groups


def _build_elephant(color: Tuple[int, int, int]) -> tuple[Mesh, dict[str, list[int]]]:
    """Elephant wireframe: massive body, 4 pillar legs, trunk."""
    mesh, groups = _build_quadruped(
        color, scale_y=1.6, snout_len=0.4, tail_len=0.5, name="elephant"
    )
    v = mesh.vertices
    e = mesh.edges
    trunk_start = len(v)
    v.append(Vec3(0.0, 1.2, 1.9))
    v.append(Vec3(0.0, 0.7, 2.2))
    v.append(Vec3(0.0, 0.3, 2.1))
    e.append((6, trunk_start))
    e.append((trunk_start, trunk_start + 1))
    e.append((trunk_start + 1, trunk_start + 2))
    groups["trunk"] = [trunk_start, trunk_start + 1, trunk_start + 2]
    return Mesh(vertices=v, edges=e, color=color, name="elephant"), groups


def _build_unicorn(color: Tuple[int, int, int]) -> tuple[Mesh, dict[str, list[int]]]:
    """Unicorn wireframe: horse with forehead horn."""
    mesh, groups = _build_quadruped(
        color, scale_y=1.2, snout_len=0.6, tail_len=0.8, name="unicorn"
    )
    v = mesh.vertices
    e = mesh.edges
    horn_tip = len(v)
    v.append(Vec3(0.0, 2.1, 1.8))
    e.append((5, horn_tip))
    return Mesh(vertices=v, edges=e, color=color, name="unicorn"), groups


def _build_fallback(
    species: str, color: Tuple[int, int, int]
) -> tuple[Mesh, dict[str, list[int]]]:
    """Procedurally synthesize creature morphology based on hash of species name."""
    h = int(hashlib.md5(species.encode("utf-8")).hexdigest(), 16)
    scale_y = 0.8 + (h % 10) * 0.1
    snout_len = 0.3 + ((h >> 4) % 8) * 0.1
    tail_len = 0.4 + ((h >> 8) % 10) * 0.1
    return _build_quadruped(
        color, scale_y=scale_y, snout_len=snout_len, tail_len=tail_len, name=species
    )


def spawn_creature(
    species: str,
    pos: Sequence[float] | Vec3 = (0.0, 0.0, 0.0),
    name: str = "",
    kind: str = "animal",
    traits: dict[str, float] | None = None,
    color: Union[str, Sequence[int]] = COLOR_MATRIX_PRIMARY,
) -> Entity:
    """Instantiate a procedural wireframe creature based on species name."""
    rgb = parse_color(color)
    spec_norm = species.lower().strip()
    creature_name = name or species

    if kind == "human" or spec_norm in ("human", "person", "man", "woman"):
        mesh, groups = _build_humanoid(rgb)
    elif spec_norm in ("wolf", "dog", "cat", "horse", "lion", "tiger", "bear", "fox"):
        mesh, groups = _build_quadruped(rgb, name=spec_norm)
    elif spec_norm in ("bird", "eagle", "crow", "hawk", "seagull", "owl", "bat"):
        mesh, groups = _build_bird(rgb)
    elif spec_norm in ("fish", "shark", "whale", "dolphin", "salmon"):
        mesh, groups = _build_fish(rgb)
    elif spec_norm in ("spider", "scorpion", "crab", "bug", "ant"):
        mesh, groups = _build_spider(rgb)
    elif spec_norm in ("snake", "worm", "serpent", "eel"):
        mesh, groups = _build_snake(rgb)
    elif spec_norm in ("dragon", "wyvern", "hydra"):
        mesh, groups = _build_dragon(rgb)
    elif spec_norm in ("robot", "cyborg", "droid", "mech", "golem"):
        mesh, groups = _build_robot(rgb)
    elif spec_norm in ("elephant", "mammoth", "rhino", "hippo"):
        mesh, groups = _build_elephant(rgb)
    elif spec_norm in ("unicorn", "pegasus"):
        mesh, groups = _build_unicorn(rgb)
    elif spec_norm in ("dino", "dinosaur", "t-rex", "raptor", "rex"):
        mesh, groups = _build_quadruped(
            rgb, scale_y=1.5, snout_len=0.9, tail_len=1.8, name="dino"
        )
    else:
        mesh, groups = _build_fallback(spec_norm, rgb)

    entity = Entity(mesh=mesh, position=pos, name=creature_name)
    entity.metadata = {
        "species": spec_norm,
        "kind": kind,
        "groups": groups,
        "traits": traits or {},
        "base_vertices": [Vec3(v.x, v.y, v.z) for v in mesh.vertices],
    }
    return entity


def animate_creature(entity: Entity, time_sec: float, speed: float = 1.0) -> None:
    """Animate limbs via sinusoidal oscillations based on movement speed."""
    base_verts: list[Vec3] = entity.metadata.get("base_vertices") # type: ignore
    if not base_verts or speed < 0.05:
        return

    groups: dict[str, list[int]] = entity.metadata.get("groups", {}) # type: ignore
    verts = entity.mesh.vertices
    freq = time_sec * 6.0 * speed

    sin_a = math.sin(freq) * 0.25
    sin_b = -sin_a

    # Animate quadruped / humanoid legs
    if "leg_fl" in groups and "leg_fr" in groups:
        for idx in groups["leg_fl"]:
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y, base_verts[idx].z + sin_a)
        for idx in groups["leg_fr"]:
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y, base_verts[idx].z + sin_b)
        for idx in groups.get("leg_bl", []):
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y, base_verts[idx].z + sin_b)
        for idx in groups.get("leg_br", []):
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y, base_verts[idx].z + sin_a)

    # Animate humanoid arms / legs
    if "left_leg" in groups and "right_leg" in groups:
        for idx in groups["left_leg"]:
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y, base_verts[idx].z + sin_a)
        for idx in groups["right_leg"]:
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y, base_verts[idx].z + sin_b)
        for idx in groups.get("left_arm", []):
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y, base_verts[idx].z + sin_b)
        for idx in groups.get("right_arm", []):
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y, base_verts[idx].z + sin_a)

    # Animate bird/dragon wings
    if "wing_l" in groups and "wing_r" in groups:
        wing_flap = math.sin(freq * 1.5) * 0.5
        for idx in groups["wing_l"]:
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y + wing_flap, base_verts[idx].z)
        for idx in groups["wing_r"]:
            verts[idx] = Vec3(base_verts[idx].x, base_verts[idx].y + wing_flap, base_verts[idx].z)

    # Animate snake undulation
    if "body" in groups and entity.metadata.get("species") == "snake":
        for i, idx in enumerate(groups["body"]):
            dx = math.sin(freq + i * 0.8) * 0.25
            verts[idx] = Vec3(base_verts[idx].x + dx, base_verts[idx].y, base_verts[idx].z)
