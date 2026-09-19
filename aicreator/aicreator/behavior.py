"""Autonomous Finite State Machine (FSM) driving creature behaviors."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Sequence

from matrixholo.creatures import animate_creature
from matrixholo.vec import Vec3

if TYPE_CHECKING:
    from aicreator.entities import WorldCreature, WorldEntity
    from aicreator.world import World

PREDATORS = {
    "wolf", "tiger", "lion", "dragon", "shark", "bear", "t-rex", "dino", "raptor", "fox"
}
HERBIVORES = {
    "deer", "cow", "sheep", "horse", "rabbit", "elephant", "unicorn"
}
BIRDS = {
    "bird", "eagle", "crow", "hawk", "seagull", "owl", "bat"
}
AQUATIC = {
    "fish", "shark", "whale", "dolphin", "salmon", "eel"
}


def update_creature_fsm(
    creature: WorldCreature,
    dt: float,
    world: World,
    neighbors: Sequence[WorldEntity],
) -> None:
    """Update decision state and physics for an autonomous creature."""
    creature.age += dt
    creature.decision_timer -= dt
    creature.anim_time += dt

    # 1. State Decision Cycle
    if creature.decision_timer <= 0.0:
        creature.decision_timer = random.uniform(1.2, 2.8)
        _make_decision(creature, neighbors)

    # 2. State Physics & Steering
    move_speed = creature.speed
    target = creature.target_pos

    match creature.state:
        case "IDLE":
            creature.velocity = Vec3(0, 0, 0)

        case "SLEEP":
            creature.velocity = Vec3(0, 0, 0)

        case "WANDER":
            if target:
                diff = target - creature.position
                dist = diff.length()
                if dist < 0.8:
                    creature.state = "IDLE"
                    creature.target_pos = None
                    creature.velocity = Vec3(0, 0, 0)
                else:
                    dir_norm = diff.normalized()
                    creature.velocity = dir_norm * move_speed
            else:
                creature.velocity = Vec3(0, 0, 0)

        case "HUNT":
            # Chase target entity
            target_ent = (
                world.get_entity(creature.target_entity_id)
                if creature.target_entity_id
                else None
            )
            if target_ent:
                diff = target_ent.position - creature.position
                dist = diff.length()
                if dist < 1.2:
                    # Caught prey
                    creature.state = "EAT"
                    creature.decision_timer = 2.0
                    creature.velocity = Vec3(0, 0, 0)
                else:
                    creature.velocity = diff.normalized() * (move_speed * 1.4)
            else:
                creature.state = "WANDER"

        case "FLEE":
            # Run directly away from threat
            threat = (
                world.get_entity(creature.target_entity_id)
                if creature.target_entity_id
                else None
            )
            if threat:
                away = (creature.position - threat.position).normalized()
                creature.velocity = away * (move_speed * 1.5)
            else:
                creature.state = "WANDER"

        case "SOCIALIZE":
            target_ent = (
                world.get_entity(creature.target_entity_id)
                if creature.target_entity_id
                else None
            )
            if target_ent:
                diff = target_ent.position - creature.position
                if diff.length() < 2.0:
                    creature.state = "IDLE"
                    creature.velocity = Vec3(0, 0, 0)
                else:
                    creature.velocity = diff.normalized() * (move_speed * 0.8)
            else:
                creature.state = "WANDER"

        case "EAT":
            creature.velocity = Vec3(0, 0, 0)

    # 3. Apply Velocity to Position
    new_pos = creature.position + (creature.velocity * dt)

    # Elevation logic
    if creature.species in BIRDS:
        # Soar with sine oscillation
        new_pos = Vec3(
            new_pos.x,
            3.0 + math.sin(creature.anim_time * 1.2) * 1.5,
            new_pos.z,
        )
    elif creature.species in AQUATIC:
        # Swim submerged
        new_pos = Vec3(new_pos.x, -0.5 + math.sin(creature.anim_time * 2.0) * 0.2, new_pos.z)
    else:
        # Ground creature: follow terrain elevation
        ground_y = world.get_terrain_height(new_pos.x, new_pos.z)
        new_pos = Vec3(new_pos.x, ground_y, new_pos.z)

    creature.position = new_pos

    # 4. Heading / Yaw Rotation
    vel_len = creature.velocity.length()
    if vel_len > 0.1:
        # Align yaw with velocity
        yaw = math.atan2(creature.velocity.x, creature.velocity.z)
        creature.rotation = Vec3(0.0, yaw, 0.0)

    # 5. Limb animation
    creature.sync_to_mesh()
    animate_creature(creature.mesh_entity, creature.anim_time, speed=vel_len)


def _make_decision(
    creature: WorldCreature, neighbors: Sequence[WorldEntity]
) -> None:
    """FSM transition rules evaluating environment and nearby agents."""
    spec = creature.species

    # 1. Predators hunt nearby herbivores / humans
    if spec in PREDATORS or creature.aggression > 0.5:
        closest_prey = None
        closest_dist = 20.0
        for n in neighbors:
            if n.id == creature.id:
                continue
            from aicreator.entities import WorldCreature as WC

            if isinstance(n, WC) and n.species not in PREDATORS:
                d = (n.position - creature.position).length()
                if d < closest_dist:
                    closest_dist = d
                    closest_prey = n

        if closest_prey:
            creature.state = "HUNT"
            creature.target_entity_id = closest_prey.id
            return

    # 2. Herbivores / Peaceful creatures flee if predator is close
    if spec in HERBIVORES or creature.kind == "human":
        for n in neighbors:
            if n.id == creature.id:
                continue
            from aicreator.entities import WorldCreature as WC

            if isinstance(n, WC) and n.species in PREDATORS:
                d = (n.position - creature.position).length()
                if d < 12.0:
                    creature.state = "FLEE"
                    creature.target_entity_id = n.id
                    return

    # 3. Socialize with peers of same species
    if random.random() < creature.curiosity:
        for n in neighbors:
            if n.id == creature.id:
                continue
            from aicreator.entities import WorldCreature as WC

            if isinstance(n, WC) and n.species == spec:
                d = (n.position - creature.position).length()
                if 2.0 < d < 15.0:
                    creature.state = "SOCIALIZE"
                    creature.target_entity_id = n.id
                    return

    # 4. Default: Wander or Idle
    roll = random.random()
    if roll < 0.6:
        creature.state = "WANDER"
        # Pick random target within 10 units
        angle = random.uniform(0.0, 2.0 * math.pi)
        dist = random.uniform(3.0, 10.0)
        creature.target_pos = Vec3(
            creature.position.x + math.cos(angle) * dist,
            creature.position.y,
            creature.position.z + math.sin(angle) * dist,
        )
    else:
        creature.state = "IDLE"
        creature.target_pos = None
