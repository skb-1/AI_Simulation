"""High-performance 30 FPS terminal renderer with ANSI delta updates and Z-buffer."""

from __future__ import annotations

import os
import select
import shutil
import sys
import termios
import time
import tty
from typing import Any, Tuple

from matrixholo.camera import Camera
from matrixholo.rain import DigitalRain
from matrixholo.raster import draw_point, render_projected_line
from matrixholo.scene import Scene
from matrixholo.shaders import COLOR_MATRIX_BG, COLOR_MATRIX_PRIMARY
from matrixholo.vec import Vec3
from matrixholo.zbuffer import ZBuffer


class TerminalRenderer:
    """Matrix holographic terminal renderer with manual slots."""

    __slots__ = (
        "width",
        "height",
        "zbuf",
        "prev_cells",
        "rain",
        "target_fps",
        "frame_delay",
        "last_frame_time",
        "running",
        "alt_screen",
        "_old_term_settings",
        "_enable_input",
    )

    def __init__(
        self,
        width: int | None = None,
        height: int | None = None,
        target_fps: int = 30,
        enable_rain: bool = True,
        enable_input: bool = False,
    ) -> None:
        term_size = shutil.get_terminal_size((120, 36))
        self.width = width or term_size.columns
        self.height = height or term_size.lines

        self.zbuf = ZBuffer(self.width, self.height)
        self.prev_cells: list[tuple[str, Tuple[int, int, int]]] = [
            (" ", (0, 0, 0))
        ] * (self.width * self.height)

        self.rain = DigitalRain(
            self.width, self.height, density=0.35, enabled=enable_rain
        )
        self.target_fps = target_fps
        self.frame_delay = 1.0 / max(1, target_fps)
        self.last_frame_time = time.perf_counter()
        self.running = True
        self.alt_screen = False
        self._old_term_settings: Any = None
        self._enable_input = enable_input

    def enter_screen(self) -> None:
        """Switch terminal to alternate screen buffer and hide cursor."""
        if sys.stdout.isatty():
            # \033[?1049h: switch to alt buffer
            # \033[?25l: hide cursor
            # \033[2J: clear screen
            sys.stdout.write("\033[?1049h\033[?25l\033[2J\033[H")
            sys.stdout.flush()
            self.alt_screen = True
            if self._enable_input:
                try:
                    self._old_term_settings = termios.tcgetattr(sys.stdin)
                    tty.setcbreak(sys.stdin.fileno())
                except Exception:
                    pass

    def exit_screen(self) -> None:
        """Restore standard terminal buffer and reveal cursor."""
        if self._old_term_settings is not None:
            try:
                termios.tcsetattr(
                    sys.stdin, termios.TCSADRAIN, self._old_term_settings
                )
            except Exception:
                pass
        if self.alt_screen and sys.stdout.isatty():
            # \033[?25h: show cursor
            # \033[?1049l: restore normal screen
            sys.stdout.write("\033[?25h\033[?1049l\033[0m\n")
            sys.stdout.flush()
            self.alt_screen = False

    def check_resize(self) -> None:
        """Detect and adapt to terminal window dimension changes."""
        term_size = shutil.get_terminal_size()
        if term_size.columns != self.width or term_size.lines != self.height:
            self.width = term_size.columns
            self.height = term_size.lines
            self.zbuf.resize(self.width, self.height)
            self.rain.resize(self.width, self.height)
            self.prev_cells = [(" ", (0, 0, 0))] * (self.width * self.height)
            sys.stdout.write("\033[2J")
            sys.stdout.flush()

    def read_input(self, cam: Camera | None = None) -> str | None:
        """Read non-blocking keyboard input for camera control and commands."""
        if not sys.stdin.isatty():
            return None

        # Check if stdin has data ready without blocking
        r, _, _ = select.select([sys.stdin], [], [], 0.0)
        if not r:
            return None

        ch = sys.stdin.read(1)
        if ch == "\033":
            # Check for escape sequence (arrow keys)
            seq = sys.stdin.read(2) if select.select([sys.stdin], [], [], 0.05)[0] else ""
            if seq == "[A":  # Up arrow
                if cam:
                    cam.rotate(0.0, 0.08)
                return "UP"
            elif seq == "[B":  # Down arrow
                if cam:
                    cam.rotate(0.0, -0.08)
                return "DOWN"
            elif seq == "[C":  # Right arrow
                if cam:
                    cam.rotate(0.08, 0.0)
                return "RIGHT"
            elif seq == "[D":  # Left arrow
                if cam:
                    cam.rotate(-0.08, 0.0)
                return "LEFT"
            return "ESC"

        if cam:
            if ch in ("w", "W"):
                cam.move(forward=1.0, right=0.0)
            elif ch in ("s", "S"):
                cam.move(forward=-1.0, right=0.0)
            elif ch in ("a", "A"):
                cam.move(forward=0.0, right=-1.0)
            elif ch in ("d", "D"):
                cam.move(forward=0.0, right=1.0)
            elif ch in ("e", "E", " "):
                cam.move(forward=0.0, right=0.0, up=1.0)
            elif ch in ("c", "C"):
                cam.move(forward=0.0, right=0.0, up=-1.0)
            elif ch in ("+", "="):
                cam.zoom(-1.5)
            elif ch in ("-", "_"):
                cam.zoom(1.5)

        return ch

    def render(self, scene: Scene, camera: Camera) -> None:
        """Render complete scene and digital rain at 30 FPS target."""
        now = time.perf_counter()
        dt = max(0.001, min(0.1, now - self.last_frame_time))
        self.last_frame_time = now

        # Handle input if enabled
        if self._enable_input:
            key = self.read_input(camera)
            if key in ("q", "Q"):
                self.running = False
                return

        # Clear z-buffer
        self.zbuf.clear(bg_char=" ", bg_color=(0, 0, 0))

        # 1. Update and render digital rain into background depth (z=200.0)
        self.rain.update(dt)
        self.rain.render(self.zbuf)

        # 2. Aspect ratio correction (terminal cell is ~2x taller than wide)
        aspect = (self.width / max(1, self.height)) * 0.5
        vp = camera.get_view_projection(aspect)

        # 3. Frustum culling and rendering of scene entities
        for entity in scene.all_entities():
            if not entity.visible:
                continue

            model_matrix = entity.get_model_matrix()
            mvp = vp.multiply(model_matrix)

            # LOD threshold check: distant objects render as single points
            dist = (entity.position - camera.pos).length()
            if dist > entity.lod_threshold:
                # Render single representative point
                center_clip = mvp.transform_point(Vec3(0, 0, 0))
                if center_clip.z > 0.1:
                    from matrixholo.raster import ndc_to_screen

                    sc = ndc_to_screen(center_clip, self.width, self.height)
                    if sc:
                        draw_point(
                            self.zbuf,
                            sc[0],
                            sc[1],
                            sc[2],
                            entity.mesh.color,
                            char="*",
                        )
                continue

            # Transform mesh vertices to clip space
            verts = entity.mesh.vertices
            clip_pts = [mvp.transform_point(v) for v in verts]

            # Render wireframe edges
            color = entity.mesh.color
            for e0, e1 in entity.mesh.edges:
                if 0 <= e0 < len(clip_pts) and 0 <= e1 < len(clip_pts):
                    render_projected_line(
                        self.zbuf,
                        clip_pts[e0],
                        clip_pts[e1],
                        color,
                        char_mode="matrix",
                    )

        # 4. Flush delta updates to terminal
        self._flush_delta()

        # 5. Frame pacing to maintain target FPS
        elapsed = time.perf_counter() - now
        sleep_dur = self.frame_delay - elapsed
        if sleep_dur > 0.001:
            time.sleep(sleep_dur)

    def _flush_delta(self) -> None:
        """Emit ANSI cursor movements only for changed cells (ANSI delta update)."""
        out: list[str] = []
        w = self.width
        h = self.height
        curr_chars = self.zbuf.char
        curr_colors = self.zbuf.color
        prev = self.prev_cells

        cur_color: Tuple[int, int, int] | None = None
        idx = 0

        for y in range(h):
            row_y = y + 1
            consecutive_changed = False
            for x in range(w):
                ch = curr_chars[idx]
                col = curr_colors[idx]
                p_ch, p_col = prev[idx]

                if ch != p_ch or col != p_col:
                    prev[idx] = (ch, col)
                    if not consecutive_changed:
                        # Reposition cursor: \033[{row};{col}H
                        out.append(f"\033[{row_y};{x + 1}H")
                        consecutive_changed = True

                    # Update ANSI truecolor if changed
                    if col != cur_color:
                        cur_color = col
                        out.append(f"\033[38;2;{col[0]};{col[1]};{col[2]}m")

                    out.append(ch)
                else:
                    consecutive_changed = False
                idx += 1

        if out:
            # Append reset code at end
            out.append("\033[0m")
            sys.stdout.write("".join(out))
            sys.stdout.flush()
