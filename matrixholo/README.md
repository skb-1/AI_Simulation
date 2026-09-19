# matrixholo

> **Holographic Matrix-style 3D Wireframe Engine in Pure Python 3.10**

`matrixholo` is a standalone, dependency-free 3D rendering library engineered from scratch in pure Python 3.10. It renders green holographic wireframes, procedural creatures, and digital rain directly inside your terminal at 30 FPS using ANSI truecolor escape codes.

---

## ⚡ Features

- **Pure Python 3.10:** No NumPy, no SciPy, no Pygame, no OpenGL in base dependencies.
- **Matrix Aesthetic:** Cyberpunk neon green palette (`#00FF41`, `#008F11`, `#003B00`), authentic half-width Katakana digital rain (`01ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵ`), depth-shading, and flicker artifacts.
- **Z-Buffer & Occlusion:** Real-time depth buffer with alpha-blending ensures 3D wireframe models naturally occlude background digital rain.
- **Ultra-Fast Delta Updates:** Emits ANSI cursor movements (`\033[y;xH`) exclusively for changed terminal cells, eliminating screen flicker and maintaining smooth 30 FPS.
- **Procedural Morphologies:** Built-in generative 3D meshes for humans, quadrupeds (wolves, cats, dogs, horses), dragons, birds, fish, spiders, snakes, robots, dinosaurs, and unicorns.
- **Interactive Controls:** WASD for free motion, Arrow keys for orbit/rotation, `+`/`-` for zoom, and `Q` to quit.

---

## 📦 Installation

```bash
pip install matrixholo
```

Optional Pyglet window mode:
```bash
pip install matrixholo[window]
```

---

## 🚀 Quick Start

Run the interactive rotating holographic cube demo:
```bash
matrixholo --demo
```

Or view a procedural creature:
```bash
matrixholo --creature wolf
matrixholo --creature dragon
```

---

## 💻 Python API (Minimal Example)

```python
from matrixholo import Scene, Camera, TerminalRenderer
from matrixholo.primitives import cube, torus
from matrixholo.creatures import spawn_creature

scene = Scene()
cam = Camera(pos=(0, 4, 10), target=(0, 0, 0))
renderer = TerminalRenderer(width=120, height=36)

scene.add(cube(pos=(0, 0, 0), size=2.0, color="green"))
scene.add(spawn_creature("wolf", pos=(3, 0, 2), name="Fenrir"))

# Render one frame (or run inside while True loop)
renderer.render(scene, cam)
```

---

## 🎮 Interactive Navigation Controls

| Key | Action |
|-----|--------|
| `W` / `S` | Move Forward / Backward |
| `A` / `D` | Strafe Left / Right |
| `E` / `C` | Ascend / Descend |
| `Arrow Keys` | Orbit / Rotate View |
| `+` / `-` | Zoom In / Out |
| `Q` | Exit to terminal |

---

## 🧪 Testing

```bash
pytest matrixholo/tests
```

---

## 📄 License

MIT © AI Creator Contributors
