"""Unit tests for Pydantic command schemas and validation."""

from aicreator.commands import (
    Delete,
    Idle,
    Modify,
    SpawnCreature,
    SpawnPrimitive,
    parse_command,
    parse_commands_json,
)


def test_spawn_primitive():
    data = {
        "action": "spawn",
        "type": "cube",
        "position": [1.0, 2.0, 3.0],
        "scale": [1.0, 1.0, 1.0],
        "rotation": [0.0, 0.0, 0.0],
        "color": [0, 255, 65],
    }
    cmd = SpawnPrimitive.model_validate(data)
    assert cmd.action == "spawn"
    assert cmd.type == "cube"
    assert cmd.position == (1.0, 2.0, 3.0)
    assert cmd.color == (0, 255, 65)


def test_spawn_creature():
    data = {
        "action": "spawn_creature",
        "kind": "animal",
        "species": "wolf",
        "position": [0.0, 0.0, 0.0],
        "name": "Fenrir",
        "traits": {"speed": 3.0, "aggression": 0.8},
    }
    cmd = SpawnCreature.model_validate(data)
    assert cmd.species == "wolf"
    assert cmd.traits["speed"] == 3.0


def test_parse_commands_json():
    json_text = """
    [
      {"action": "spawn", "type": "sphere", "position": [0.0, 1.0, 0.0]},
      {"action": "spawn_creature", "kind": "animal", "species": "deer", "position": [3.0, 0.0, 2.0], "name": "Bambi"},
      {"action": "modify", "target": 1, "property": "color", "value": [0.0, 143.0, 17.0]},
      {"action": "delete", "target": 2},
      {"action": "idle"}
    ]
    """
    cmds = parse_commands_json(json_text)
    assert len(cmds) == 5
    assert isinstance(cmds[0], SpawnPrimitive)
    assert isinstance(cmds[1], SpawnCreature)
    assert isinstance(cmds[2], Modify)
    assert isinstance(cmds[3], Delete)
    assert isinstance(cmds[4], Idle)
