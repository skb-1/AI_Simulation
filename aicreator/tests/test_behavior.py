"""Unit tests for creature behavioral FSM."""

from aicreator.behavior import update_creature_fsm
from aicreator.commands import SpawnCreature
from aicreator.world import World
from matrixholo.scene import Scene
from matrixholo.vec import Vec3


def test_behavior_fsm_wander_and_flee():
    scene = Scene()
    world = World(scene)

    wolf_id = world.apply_commands([
        SpawnCreature(action="spawn_creature", kind="animal", species="wolf", position=(0.0, 0.0, 0.0), name="Alpha"),
    ])[0]
    deer_id = world.apply_commands([
        SpawnCreature(action="spawn_creature", kind="animal", species="deer", position=(3.0, 0.0, 0.0), name="Bambi"),
    ])[0]

    wolf = world.get_entity(wolf_id)
    deer = world.get_entity(deer_id)

    assert wolf is not None and deer is not None

    # Step FSM
    wolf.decision_timer = 0.0
    deer.decision_timer = 0.0

    update_creature_fsm(wolf, 0.1, world, [wolf, deer])
    update_creature_fsm(deer, 0.1, world, [wolf, deer])

    # Wolf should have triggered HUNT towards nearby deer
    assert wolf.state == "HUNT"
    # Deer should have triggered FLEE from nearby wolf
    assert deer.state == "FLEE"
