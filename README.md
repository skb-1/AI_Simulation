# AI Creator — Holographic Matrix Sandbox

> **A Pure Python 3.10.0 Holographic 3D Reality Engine Powered by Local LLMs.**  
> A lightweight cyberpunk terminal sandbox where an AI Creator materializes infinite 3D worlds rendered in the iconic green phosphor Matrix aesthetic.

---

## 🌌 Project Architecture

The project is structured into two modular packages:

1. **`matrixholo`** — A standalone, zero-dependency 3D terminal and window rendering engine.
   - Pure Python 3.10 math (custom `Vec3`, `Vec4`, `Mat4` with `__slots__`). No NumPy, Pygame, or OpenGL in base requirements.
   - Real-time Z-buffer with depth testing and alpha blending.
   - Authentic Matrix digital rain (`01ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵ`) on background depth layers.
   - Ultra-fast 30 FPS terminal rendering via ANSI cursor delta updates (`\033[y;xH`).
   - Procedural wireframe morphologies for humans, wolves, cats, dogs, birds, dragons, fish, spiders, snakes, robots, dinosaurs, and unicorns.

2. **`aicreator`** — The sandbox application orchestrating the AI Creator.
   - Integrates `llama-cpp-python` with custom GBNF grammar constraints built directly from Pydantic schemas.
   - Infinite voxel-like reality split into 16×16×16 streaming chunks with dynamic load/unload.
   - Smooth multi-octave value noise terrain (pure Python).
   - Autonomous Finite State Machine (FSM) for creature behaviors: `IDLE`, `WANDER`, `HUNT`, `FLEE`, `SOCIALIZE`, `SLEEP`, `EAT`.
   - Threaded streaming generation using `threading.Thread` and `queue.Queue` ensuring the 30 FPS render loop never blocks.
   - Rich split-screen chat interface on the left and 3D Matrix holographic viewport on the right.

---

## ⚡ Strict Version & API Constraints

- **Python Version Constraint:** `requires-python = ">=3.10.0,<3.11"`
- **Strictly targets Python 3.10.0:** Zero usage of Python 3.11+ APIs:
  - ✗ `typing.Self`
  - ✗ `typing.LiteralString`
  - ✗ `tomllib`
  - ✗ `ExceptionGroup` / `except*`
  - ✗ `asyncio.TaskGroup`
  - ✗ `enum.StrEnum`
  - ✗ `contextlib.chdir`
- **Uses Python 3.10 capabilities:**
  - ✓ PEP 604 union syntax (`X | Y`)
  - ✓ PEP 634 structural pattern matching (`match / case`)
  - ✓ PEP 585 generics (`tuple[float, float, float]`, `dict[str, float]`)
  - ✓ Manual `__slots__` for extreme CPU execution speed

---

## 📂 Repository Structure

```
.
├── Makefile
├── README.md
├── .gitignore
├── assets/
│   ├── system_prompt.txt        # AI Creator system prompt
│   └── grammar.gbnf             # Compiled GBNF grammar for llama.cpp
├── matrixholo/
│   ├── pyproject.toml           # PEP 621 package definition
│   ├── README.md
│   ├── LICENSE                  # MIT
│   ├── matrixholo/
│   │   ├── __init__.py          # Public API (Scene, Camera, TerminalRenderer...)
│   │   ├── _compat.py           # Python 3.10 version runtime verification
│   │   ├── vec.py               # Pure Python Vec3, Vec4, Mat4
│   │   ├── camera.py            # Orbit and free 3D camera
│   │   ├── raster.py            # 3D line and point rasterization
│   │   ├── zbuffer.py           # Z-Buffer and alpha blending
│   │   ├── glyphs.py            # Katakana & digital rain characters
│   │   ├── rain.py              # Digital rain simulation
│   │   ├── scene.py             # Scene, Entity, Mesh graph
│   │   ├── primitives.py        # cube, sphere, cylinder, cone, torus, line, grid
│   │   ├── creatures.py         # Procedural morphologies & limb animation
│   │   ├── shaders.py           # Matrix green color palette & depth shading
│   │   ├── terminal.py          # 30 FPS ANSI delta update terminal renderer
│   │   ├── window.py            # Optional pyglet GUI window renderer
│   │   └── cli.py               # CLI demo runner (matrixholo --demo)
│   └── tests/
│       ├── test_vec.py
│       ├── test_camera.py
│       ├── test_zbuffer.py
│       ├── test_raster.py
│       ├── test_primitives.py
│       ├── test_creatures.py
│       ├── test_rain.py
│       ├── test_shaders.py
│       └── test_terminal.py
└── aicreator/
    ├── pyproject.toml           # PEP 621 package definition
    ├── README.md
    ├── aicreator/
    │   ├── __init__.py
    │   ├── __main__.py          # python -m aicreator
    │   ├── app.py               # Main 30 FPS game loop
    │   ├── llm.py               # Local LLM wrapper & fallback engine
    │   ├── prompts.py           # System instructions
    │   ├── grammar.py           # Custom Pydantic-to-GBNF converter
    │   ├── commands.py          # Pydantic command schemas
    │   ├── world.py             # Infinite chunks, noise terrain & spatial hash
    │   ├── entities.py          # WorldEntity, WorldPrimitive, WorldCreature
    │   ├── behavior.py          # Autonomous creature FSM
    │   ├── stream.py            # Non-blocking threaded token worker
    │   └── ui.py                # Rich dashboard panel
    ├── models/
    │   └── README.md            # GGUF models instructions
    └── tests/
        ├── test_commands.py
        ├── test_grammar.py
        ├── test_world.py
        ├── test_behavior.py
        └── test_llm.py
```

---

## 🚀 Installation & Quick Start

### 1. Installation

```bash
make install
```
*(Runs `pip install -e ./matrixholo && pip install -e ./aicreator`)*

### 2. Run the 3D Holographic Matrix Demo

```bash
matrixholo --demo
```
*(Shows a spinning neon green wireframe cube with falling Katakana digital rain and ground grid)*

View a specific procedural creature:
```bash
matrixholo --creature wolf
matrixholo --creature dragon
```

### 3. Run AI Creator

```bash
# With local GGUF model:
python -m aicreator --model models/llama-3-8b.Q4_K_M.gguf

# Or without a model (activates built-in creator engine):
python -m aicreator
```

---

## 🎮 Interactive Controls

| Key | Action |
|---|---|
| `W` / `S` | Move Forward / Backward in 3D Space |
| `A` / `D` | Strafe Left / Right |
| `E` / `C` | Elevate / Descend |
| `Arrow Keys` | Orbit / Rotate Camera View |
| `+` / `-` | Zoom In / Out |
| `:` or `/` | Open AI Creator prompt input |
| `Enter` | Submit prompt to materialize |
| `ESC` | Cancel chat prompt |
| `Q` | Exit to terminal |

---

## 💡 Example Creation Prompts

- **«Создай лес»** — Generates a grove of towering wireframe trees and wandering deer.
- **«Наполни мир жизнью»** — Materializes 5–10 diverse autonomous creatures (wolves, horses, birds, dragons, robots).
- **«Стая волков и стадо оленей»** — Wolves actively hunt deer; deer flee in panic when predators approach!
- **«Замок из кубов»** — Multi-tower stone fortress with keep and battlements.
- **«Дракон и единорог»** — Mythical beasts with flapping wings and horns.

---

## 🧪 Testing

Run test suites for both packages:
```bash
make test
# or full suite:
make test-all
```

---

## 📄 License

MIT License © 2026 AI Creator Contributors
