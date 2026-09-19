"""Unit tests for terminal renderer mechanics."""

from matrixholo.camera import Camera
from matrixholo.primitives import cube
from matrixholo.scene import Scene
from matrixholo.terminal import TerminalRenderer


def test_terminal_renderer_init():
    renderer = TerminalRenderer(width=80, height=24, enable_rain=False)
    assert renderer.width == 80
    assert renderer.height == 24
    assert renderer.zbuf.size == 80 * 24


def test_terminal_render_frame():
    renderer = TerminalRenderer(width=40, height=20, enable_rain=True)
    scene = Scene()
    scene.add(cube(pos=(0, 0, 0), size=2.0))
    cam = Camera(pos=(0, 0, 5), target=(0, 0, 0))

    # Single render call (without entering alt screen to not mess up test output)
    renderer.render(scene, cam)
    # Check that Z-buffer processed some entities
    assert any(c != " " for c in renderer.zbuf.char)
