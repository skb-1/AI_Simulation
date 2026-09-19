"""Unit tests for procedural creature generation and limb animation."""

from matrixholo.creatures import animate_creature, spawn_creature


def test_spawn_creatures():
    species_list = [
        ("human", "human"),
        ("wolf", "animal"),
        ("bird", "animal"),
        ("dragon", "animal"),
        ("fish", "animal"),
        ("spider", "animal"),
        ("snake", "animal"),
        ("robot", "animal"),
        ("elephant", "animal"),
        ("unicorn", "animal"),
        ("mysterious_beast", "animal"),  # triggers procedural fallback
    ]

    for spec, kind in species_list:
        creature = spawn_creature(spec, pos=(0, 0, 0), kind=kind)
        assert len(creature.mesh.vertices) > 0
        assert len(creature.mesh.edges) > 0
        assert "groups" in creature.metadata


def test_creature_animation():
    wolf = spawn_creature("wolf", pos=(0, 0, 0))
    initial_v0 = wolf.mesh.vertices[9]  # Leg vertex
    # Animate at time t=1.0 with movement speed=1.0
    animate_creature(wolf, time_sec=1.0, speed=1.0)
    # Leg should have moved from sinusoidal offset
    assert wolf.mesh.vertices[9] != initial_v0
