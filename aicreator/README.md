# aicreator

> **AI Creator — Holographic Matrix Sandbox**  
> Pure Python 3.10 sandbox where a local LLM serves as the AI Creator of an infinite 3D Matrix reality.

---

## ⚡ Overview

`aicreator` is an autonomous 3D world engine powered by a local quantized LLM (`llama-cpp-python` with GBNF constrained decoding). When the user inputs natural language ideas, the LLM generates structured Pydantic commands that materialize instantly in a holographic 3D Matrix wireframe universe.

All creatures live, wander, hunt, flee, socialize, and sleep autonomously via a Finite State Machine (FSM), rendered at 30 FPS directly in your terminal.

---

## ⚙️ Requirements & Constraints

- **Python:** `>= 3.10.0, < 3.11` (Strictly targets Python 3.10)
- **CPU Only:** Zero GPU required; uses CPU quantized inference (`n_gpu_layers=0`, `mmap=True`)
- **Offline:** 100% functional without an internet connection once model weights are available
- **Zero Heavy Math Dependencies:** Pure Python 3D vector and matrix math (no NumPy, no SciPy)

---

## 📦 Installation

Install both the rendering library and application in editable mode:

```bash
make install
```

Or with `pip`:
```bash
pip install -e ./matrixholo
pip install -e ./aicreator
```

---

## 🚀 Quick Start

Run the sandbox with a local GGUF model:
```bash
aicreator --model models/llama-3-8b.Q4_K_M.gguf
```

Or run without a model to explore using the built-in Creator engine:
```bash
aicreator
```

Or test a creation prompt directly:
```bash
aicreator --prompt "Создай лес и оленей" --frames 30
```

---

## 🔮 Example Creation Ideas

In the sandbox, press `:` or `/` to open the chat prompt, then type any idea:

1. **«Создай лес»**  
   Materializes cylinder trunks and cone foliage with grazing deer.
2. **«Наполни мир жизнью»**  
   Populates the infinite matrix with 5–10 diverse autonomous species (wolves, deer, eagles, dragons, humans, robots).
3. **«Стая волков и стадо оленей»**  
   Spawns predator and prey groups; wolves will actively stalk and hunt the deer, while deer flee when approached!
4. **«Замок из кубов»**  
   Constructs multi-tiered fortified towers, battlements, and keeps from geometric primitives.
5. **«Дракон и единорог»**  
   Synthesizes mythical creatures with procedural wing flaps and horns.

---

## 🎮 Controls

| Key | Function |
|---|---|
| `W` / `S` | Move Camera Forward / Backward |
| `A` / `D` | Strafe Camera Left / Right |
| `E` / `C` | Elevate / Descend Camera |
| `Arrow Keys` | Orbit / Rotate Camera View |
| `+` / `-` | Zoom In / Out |
| `:` or `/` | Open AI Creator prompt input |
| `Enter` | Submit prompt to LLM worker thread |
| `ESC` | Cancel chat input |
| `Q` | Quit sandbox |

---

## 🏗️ Architecture

- **`commands.py`**: Pydantic v2 schemas (`SpawnPrimitive`, `SpawnCreature`, `Modify`, `Delete`, `Idle`).
- **`grammar.py`**: Custom converter from Pydantic schema into GGML BNF (`GBNF`), guaranteeing 100% valid JSON output.
- **`world.py`**: Infinite 16×16×16 chunk grid, value-noise terrain, and spatial hash proximity queries.
- **`behavior.py`**: Autonomous creature FSM (`IDLE`, `WANDER`, `FLEE`, `HUNT`, `SOCIALIZE`, `SLEEP`, `EAT`) with sine limb oscillations.
- **`stream.py`**: Threaded non-blocking token stream between local LLM and UI.
- **`ui.py`**: Rich-powered split-screen terminal layout with real-time stats and streaming logs.

---

## 🧪 Testing

```bash
make test
```

---

## 📄 License

MIT © AI Creator Contributors
