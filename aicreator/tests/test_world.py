"""Unit tests for infinite world, chunks, terrain, and save/load."""

import os
import tempfile
from aicreator.commands import SpawnCreature, SpawnPrimitive
from aicreator.world import World
from matrixholo.scene import Scene
from matrixholo.vec import Vec3


def test_world_chunks_and_terrain():
    scene = Scene()
    world = World(scene)

    # Elevation generator produces consistent finite numbers
    h1 = world.get_terrain_height(0.0, 0.0)
    h2 = world.get_terrain_height(0.0, 0.0)
    assert h1 == h2
    assert -50.0 < h1 < 50.0

    # Updating chunks around origin loads radius chunks
    world.update_chunks_around(Vec3(0, 0, 0))
    assert len(world.chunks) > 0


def test_world_apply_commands():
    scene = Scene()
    world = World(scene)

    cmds = [
        SpawnPrimitive(
            action="spawn",
            type="cube",
            position=(0.0, 0.0, 0.0),
        ),
        SpawnCreature(
            action="spawn_creature",
            kind="animal",
            species="wolf",
            position=(2.0, 0.0, 2.0),
            name="Ghost",
        ),
    ]

    created = world.apply_commands(cmds)
    assert len(created) == 2
    assert len(world.entities) == 2

    # Spatial hash neighbor test
    neighbors = world.get_neighbors(Vec3(0, 0, 0), radius=5.0)
    assert len(neighbors) == 2


def test_world_save_load():
    scene = Scene()
    world = World(scene)
    world.apply_commands([
        SpawnPrimitive(action="spawn", type="cube", position=(5.0, 1.0, 2.0)),
        SpawnCreature(action="spawn_creature", kind="animal", species="cat", position=(0.0, 0.0, 0.0), name="Luna"),
    ])

    with tempfile.NamedTemporaryFile(suffix=".save.gz", delete=False) as tf:
        temp_path = tf.name

    try:
        world.save_to_file(temp_path)
        assert os.path.getsize(temp_path) > 0

        # Load into new world
        scene2 = Scene()
        world2 = World(scene2)
        world2.load_from_file(temp_path)
        assert len(world2.entities) == 2
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
