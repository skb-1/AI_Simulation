# AI Creator — Holographic Matrix Sandbox

> **A Pure Python 3.10.0 Holographic 3D Reality Engine Powered by Local LLMs.**  
> A lightweight cyberpunk terminal sandbox where an AI Creator materializes infinite 3D worlds rendered in the iconic green phosphor Matrix aesthetic.

---

## 🌌 Project Architecture

The project is structured into two modular packages with a unified root entrypoint:

1. **`matrixholo`** — A standalone, zero-dependency 3D terminal and window rendering engine.
   - Pure Python 3.10 math (custom `Vec3`, `Vec4`, `Mat4` with `__slots__`). No NumPy, Pygame, or OpenGL in base requirements.
   - Real-time Z-buffer with depth testing and alpha blending.
   - Authentic Matrix digital rain (`01ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵ`) on background depth layers.
   - Ultra-fast 30 FPS terminal rendering via ANSI cursor delta updates (`\033[y;xH`).
   - Procedural wireframe morphologies for humans, wolves, cats, dogs, birds, dragons, fish, spiders, snakes, robots, dinosaurs, and unicorns.
   - Full cross-platform console compatibility (Windows 11, Linux, macOS).

2. **`aicreator`** — The sandbox application orchestrating the AI Creator.
   - Integrates `llama-cpp-python` with custom GBNF grammar constraints built directly from Pydantic schemas.
   - Infinite voxel-like reality split into 16×16×16 streaming chunks with dynamic load/unload.
   - Smooth multi-octave value noise terrain (pure Python).
   - Autonomous Finite State Machine (FSM) for creature behaviors: `IDLE`, `WANDER`, `HUNT`, `FLEE`, `SOCIALIZE`, `SLEEP`, `EAT`.
   - Threaded streaming generation using `threading.Thread` and `queue.Queue` ensuring the 30 FPS render loop never blocks.
   - Rich split-screen chat interface on the left and 3D Matrix holographic viewport on the right.
   - Built-in zero-dependency fallbacks for Pydantic and Rich if external wheels are absent.

3. **`main.py`** — Unified root launcher.
   - Auto-configures `sys.path` to seamlessly run everything directly out of the box without prior `pip install`.

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

## 🪟 Windows 11 Native Compatibility

This project is fully engineered to run smoothly on **Windows 11** (Windows Terminal, PowerShell, CMD) out of the box without requiring third-party C-compilers or package downloads:

- **Virtual Terminal (VT100) Sequences:** Automatically enabled via Win32 `kernel32.SetConsoleMode` with `ENABLE_VIRTUAL_TERMINAL_PROCESSING` (`0x0004`) and `DISABLE_NEWLINE_AUTO_RETURN` (`0x0008`).
- **UTF-8 Output & Rain Characters:** Automatic code-page switching to UTF-8 (`CP_UTF8 = 65001`) via Win32 `kernel32.SetConsoleCP` and `kernel32.SetConsoleOutputCP` so half-width Katakana glyphs render crisply without garbled characters.
- **Non-Blocking Keyboard Navigation:** Windows-native non-blocking polling via `msvcrt.kbhit()` and `msvcrt.getwch()` (with two-stroke arrow key support), cleanly abstracting Unix `termios` / `select`.
- **Zero-External-Download Runtime:** Includes pure-Python compat layers (`_pydantic_compat.py` and `_rich_compat.py`) allowing instant execution even on fresh Python 3.10 environments where pip packages cannot be downloaded.

---

## 📂 Repository Structure

```
.
├── main.py                      # Unified root launcher (Windows / Linux / macOS)
├── Makefile                     # Build & run automation
├── README.md                    # Main project documentation
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
│   │   ├── __main__.py          # python -m matrixholo entrypoint
│   │   ├── _compat.py           # Python 3.10 version runtime verification
│   │   ├── platform_compat.py   # Windows 11 VT & msvcrt console abstraction
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
    │   ├── __main__.py          # python -m aicreator entrypoint
    │   ├── app.py               # Main 30 FPS game loop
    │   ├── llm.py               # Local LLM wrapper & fallback engine
    │   ├── prompts.py           # System instructions
    │   ├── grammar.py           # Custom Pydantic-to-GBNF converter
    │   ├── commands.py          # Command schemas (Pydantic / compat fallback)
    │   ├── world.py             # Infinite chunks, noise terrain & spatial hash
    │   ├── entities.py          # WorldEntity, WorldPrimitive, WorldCreature
    │   ├── behavior.py          # Autonomous creature FSM
    │   ├── stream.py            # Non-blocking threaded token worker
    │   ├── ui.py                # Dashboard HUD panel (Rich / compat fallback)
    │   ├── _pydantic_compat.py  # Pure Python zero-dependency schema fallback
    │   └── _rich_compat.py      # Pure Python zero-dependency HUD panel fallback
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

## 🚀 Quick Start & Usage

### Method A: Direct Execution via Root Launcher (No Install Needed!)

The root `main.py` launcher requires zero dependencies beyond standard Python 3.10 and runs seamlessly on Windows, Linux, and macOS:

```bash
# 1. Run the interactive 3D rotating holographic cube demo
python main.py --demo

# 2. View a specific procedural creature
python main.py --creature wolf
python main.py --creature dragon
python main.py --creature robot

# 3. Run the interactive AI Creator sandbox
python main.py

# 4. Run AI Creator with a pre-loaded prompt
python main.py --prompt "Создай лес и оленей"

# 5. Run AI Creator with a local GGUF model
python main.py --model path/to/model.gguf

# 6. Run all unit test suites
python main.py --test
```

---

### Method B: Package Module Execution (`python -m`)

Both packages support direct execution via Python's `-m` flag:

```bash
# Run matrixholo demo
python -m matrixholo --demo
python -m matrixholo --creature unicorn

# Run aicreator app
python -m aicreator
python -m aicreator --prompt "Замок из кубов"
```

---

### Method C: Installation via Pip / Makefile

```bash
make install
# or
pip install -e ./matrixholo
pip install -e ./aicreator
```

After installation, the console entrypoints are available anywhere:
```bash
matrixholo --demo
aicreator --model models/llama-3-8b.Q4_K_M.gguf
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

Run test suites for all packages:
```bash
# Via master launcher:
python main.py --test

# Via Makefile:
make test
make test-all

# Or via pytest directly:
pytest matrixholo/tests aicreator/tests
```

All 33 test cases pass with high code coverage.

---

## 📄 License

MIT License © 2026 AI Creator Contributors
