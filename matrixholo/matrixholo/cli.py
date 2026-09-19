"""Command-line demo and interactive entrypoint for matrixholo."""

from __future__ import annotations

import argparse
import math
import sys
import time

from matrixholo.camera import Camera
from matrixholo.creatures import animate_creature, spawn_creature
from matrixholo.primitives import cube, grid, sphere, torus
from matrixholo.scene import Scene
from matrixholo.terminal import TerminalRenderer
from matrixholo.vec import Vec3


def run_demo(
    width: int | None = None,
    height: int | None = None,
    fps: int = 30,
    frames: int | None = None,
    species: str | None = None,
    no_rain: bool = False,
) -> int:
    """Run interactive 3D Matrix holographic demo."""
    renderer = TerminalRenderer(
        width=width,
        height=height,
        target_fps=fps,
        enable_rain=not no_rain,
        enable_input=True,
    )

    scene = Scene()
    cam = Camera(pos=(0.0, 4.0, 10.0), target=(0.0, 0.0, 0.0), mode="orbit")

    # Add ground grid
    scene.add(grid(size=14, step=2.0, y=-2.0, color="dark_green"))

    # Add centerpiece entity
    if species:
        main_entity = spawn_creature(species, pos=(0.0, -1.0, 0.0), name=species)
    else:
        # Rotating green cube + floating torus
        main_entity = cube(pos=(0.0, 0.0, 0.0), size=2.5, color="neon_green")
        scene.add(torus(pos=(0.0, 0.0, 0.0), r_major=3.2, r_minor=0.3, color="dark_green"))

    scene.add(main_entity)

    renderer.enter_screen()
    frame_count = 0
    start_time = time.perf_counter()

    try:
        while renderer.running:
            now = time.perf_counter() - start_time

            # Slowly rotate centerpiece
            main_entity.rotation = Vec3(now * 0.7, now * 1.1, now * 0.3)

            if species:
                animate_creature(main_entity, now, speed=1.0)

            renderer.render(scene, cam)
            frame_count += 1

            if frames is not None and frame_count >= frames:
                break
    except KeyboardInterrupt:
        pass
    finally:
        renderer.exit_screen()

    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI argument parsing and dispatcher."""
    parser = argparse.ArgumentParser(
        prog="matrixholo",
        description="Holographic Matrix-style 3D terminal wireframe renderer.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run rotating wireframe cube and digital rain demo",
    )
    parser.add_argument(
        "--creature",
        type=str,
        default=None,
        help="Spawn a specific procedural creature (wolf, dragon, bird, human...)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Target frames per second (default: 30)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Custom terminal width columns",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Custom terminal height rows",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="Exit after N frames (useful for tests/automation)",
    )
    parser.add_argument(
        "--no-rain",
        action="store_true",
        help="Disable Matrix digital rain background",
    )

    args = parser.parse_args(argv)
    # Default to demo if no arguments provided
    return run_demo(
        width=args.width,
        height=args.height,
        fps=args.fps,
        frames=args.frames,
        species=args.creature,
        no_rain=args.no_rain,
    )


if __name__ == "__main__":
    sys.exit(main())
