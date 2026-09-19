# AI Creator — Holographic Matrix Sandbox

> **A Pure Python 3.10.0 Holographic 3D Reality Engine Powered by Local LLMs.**  
> A cyberpunk desktop & terminal sandbox where an AI Creator materializes infinite 3D worlds rendered in the iconic green phosphor Matrix aesthetic.

---

## 🌌 Project Architecture

The project is structured into modular packages with a unified root entrypoint:

1. **`aicreator`** — The sandbox application orchestrating the AI Creator.
   - **PySide6-Styled Holographic Studio (Web GUI)**: Zero-dependency browser-based desktop window system running on `http://0.0.0.0:8000` with authentic cyberpunk Matrix aesthetics, dockable panels, interactive 3D viewport, GGUF model selector dialog, and working mouse/keyboard controls.
   - **Native PySide6 Desktop Application (`gui_pyside.py`)**: Real OS window implementation for Windows 11/Linux desktops using `PySide6` / `PyQt6` with QSS styling and model loader dialog.
   - **Autonomous Creature FSM**: Real-time state machine (`IDLE`, `WANDER`, `HUNT`, `FLEE`, `SOCIALIZE`, `SLEEP`, `EAT`) with sine limb oscillations.
   - **Model Selector Dialog**: Allows selecting discovered `.gguf` files, uploading models from disk, manual path input, and inference tuning (`n_ctx`, threads, GPU layers, temperature).
   - **Threaded Streaming**: Real-time GBNF grammar constraints built from Pydantic schemas without stalling the 30 FPS simulation loop.
   - **Infinite 16×16×16 Chunks**: Streaming chunk grid with bicubic value noise terrain.

2. **`matrixholo`** — A standalone, zero-dependency 3D terminal and window rendering engine.
   - Pure Python 3.10 math (`Vec3`, `Vec4`, `Mat4` with `__slots__`). No NumPy, Pygame, or OpenGL in base requirements.
   - Real-time Z-buffer with depth testing and alpha blending.
   - Authentic Matrix digital rain (`01ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵ`) on background depth layers.
   - Ultra-fast 30 FPS terminal rendering via ANSI cursor delta updates (`\033[y;xH`).
   - Procedural wireframe morphologies for humans, wolves, cats, dogs, birds, dragons, fish, spiders, snakes, robots, dinosaurs, and unicorns.
   - Full cross-platform console compatibility (Windows 11, Linux, macOS).

3. **`main.py`** — Unified root launcher.
   - Launches the Holographic GUI Studio, native PySide6 desktop window, or terminal sandbox directly out of the box with zero external downloads.

---

## 🖥️ Graphical Interface & PySide6 Desktop Studio

### 1. PySide6-Styled Holographic Matrix Studio (Default GUI)
Launch immediately on any machine (zero pip packages required):
```bash
python main.py
# or
python main.py --gui --port 8000
```
- **Desktop Window Layout**: PySide6 title bar, menu bar (`Файл`, `Модели`, `Вид`, `Справка`), quick toolbar, dockable panels, and status bar.
- **Center 3D Holographic Viewport**:
  - Live 3D wireframe world with falling Katakana Matrix rain and depth-shading.
  - **Working Mouse Controls**:
    - **Left Click Drag:** Smooth Camera Orbit (Yaw & Pitch)
    - **Right Click Drag:** Smooth Camera Pan (Strafe & Elevation)
    - **Mouse Wheel:** Smooth Zoom In / Out
  - **On-Screen Navigation Gizmo & D-Pad:**
    - Dedicated buttons: `[W Вперед]`, `[S Назад]`, `[A Влево]`, `[D Вправо]`, `[↑ Вверх]`, `[↓ Вниз]`, `[Zoom +]`, `[Zoom -]`, `[Front]`, `[Top]`, `[Iso]`, `[Reset]`
  - **Keyboard Navigation:** WASD keys, Arrow keys, E/C for elevation, +/- for zoom.
- **Dedicated GGUF Model Selector Window (Окно выбора модели)**:
  - Accessible via top toolbar button **[📁 ВЫБРАТЬ GGUF МОДЕЛЬ]** or menu bar.
  - Scans `./models/` folder for `.gguf` weights and displays sizes and paths.
  - Drag-and-drop / file picker to upload any `.gguf` model from your computer.
  - Manual file path entry field (e.g. `C:\models\llama-3-8b.Q4_K_M.gguf`).
  - Tunable parameters: Context Window (`n_ctx`), CPU Threads, GPU Layers, Temperature.
  - One-click toggle: **Локальная GGUF модель** vs **Встроенный процедурный Creator (Offline)**.
  - Live loading feedback and active engine status badge.
- **Left Dock (AI Creator Terminal)**:
  - Natural language prompt input with suggestions.
  - Quick action presets: `🌲 Лес и олени`, `🏰 Замок из кубов`, `🐺 Волки и олени`, `🐉 Дракон`, `🤖 Роботы`, `👥 Больше жизни`.
  - Real-time token streaming box displaying generated GBNF JSON with green typing cursor.
- **Right Dock (World Inspector & Creature AI)**:
  - Telemetry: Entity count, creature count, chunk count, render FPS.
  - Real-time creature FSM monitor showing each animal's live state (`WANDER`, `HUNT`, `FLEE`, `SLEEP`) and targets.
  - World entity list with one-click deletion.

### 2. Native PySide6 Desktop Application
If you have PySide6 installed on your Windows 11 / Linux desktop:
```bash
python main.py --desktop
```
Launches a true native Qt/PySide6 window with custom cyberpunk QSS theme, `QDockWidget`, `QFileDialog`, and hardware-accelerated viewport.

---

## 🪟 Windows 11 Native Compatibility

- **Virtual Terminal (VT100) Sequences:** Automatically enabled via Win32 `kernel32.SetConsoleMode` (`ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004`, `DISABLE_NEWLINE_AUTO_RETURN = 0x0008`).
- **UTF-8 Output & Rain Characters:** Automatic code-page switching to UTF-8 (`CP_UTF8 = 65001`) via `SetConsoleCP` and `SetConsoleOutputCP`.
- **Non-Blocking Keyboard Navigation:** Windows-native non-blocking polling via `msvcrt.kbhit()` and `msvcrt.getwch()`.
- **Zero-External-Download Runtime:** Includes pure-Python compat layers (`_pydantic_compat.py` and `_rich_compat.py`) allowing instant execution on fresh Python 3.10 environments without PyPI downloads.

---

## 🚀 Quick Start & CLI Options

```bash
# 1. Launch Holographic Matrix Studio (Default GUI on port 8000)
python main.py

# 2. Launch Native PySide6 Window (if PySide6 is installed)
python main.py --desktop

# 3. Launch Interactive Terminal ANSI Sandbox
python main.py --cli

# 4. Preview 3D rotating holographic wireframe cube & digital rain
python main.py --demo

# 5. Preview a procedural creature in terminal
python main.py --creature wolf
python main.py --creature dragon
python main.py --creature robot

# 6. Run all unit tests
python main.py --test
```

---

## 💡 Example Creation Prompts

- **«Создай лес»** — Generates a grove of towering wireframe trees and wandering deer.
- **«Наполни мир жизнью»** — Materializes 5–10 diverse autonomous creatures (wolves, horses, birds, dragons, robots).
- **«Стая волков и стадо оленей»** — Wolves actively hunt deer; deer flee in panic when predators approach!
- **«Замок из кубов»** — Multi-tower stone fortress with keep and battlements.
- **«Дракон и единорог»** — Mythical beasts with flapping wings and horns.

---

## 🧪 Testing

```bash
python main.py --test
# or
make test
make test-all
```

All 33 test cases pass cleanly with high test coverage.

---

## 📄 License

MIT License © 2026 AI Creator Contributors
