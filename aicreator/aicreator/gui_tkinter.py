"""Native Tkinter Holographic Matrix Desktop GUI (Standard Library Zero-Dependency).

Provides a native OS desktop window on Windows 11 / Linux / macOS without
requiring PySide6 or any pip package installation:
- Cyberpunk dark green & neon Matrix styling
- 3D Holographic Canvas with digital rain and wireframe entities
- Full working mouse controls: Left Drag = Orbit, Right Drag = Pan, Wheel = Zoom
- GGUF Model Selector dialog with file browser and hot-reloading
- Prompt terminal with quick presets and live streaming GBNF JSON
- World entities inspector & live creature FSM state monitor
"""

from __future__ import annotations

import math
import os
import sys
import threading
import time
from typing import Any

TK_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

from aicreator.commands import parse_commands_json
from aicreator.entities import WorldCreature, WorldPrimitive
from aicreator.llm import CreatorLLM, find_gguf_models
from aicreator.world import World
from matrixholo.camera import Camera
from matrixholo.glyphs import RAIN_CHARS
from matrixholo.rain import DigitalRain
from matrixholo.scene import Scene
from matrixholo.vec import Vec3


if TK_AVAILABLE:

    class TkModelDialog(tk.Toplevel):
        """Native Tkinter Dialog to browse, inspect, and select GGUF model files."""

        def __init__(self, parent: tk.Tk, llm: CreatorLLM) -> None:
            super().__init__(parent)
            self.llm = llm
            self.title("Выбор GGUF Модели — AI Creator")
            self.geometry("540x480")
            self.configure(bg="#031206")
            self.resizable(False, False)

            header = tk.Label(
                self,
                text="📁 ВЫБОР И ЗАГРУЗКА GGUF МОДЕЛИ",
                font=("Consolas", 12, "bold"),
                fg="#00ff41",
                bg="#031206",
            )
            header.pack(pady=10)

            # Engine mode
            self.var_engine = tk.StringVar(value="builtin" if self.llm.is_simulated and not self.llm.model_path else "gguf")
            frm_mode = tk.LabelFrame(self, text="Режим движка ИИ", fg="#00ff41", bg="#051a08", font=("Consolas", 10, "bold"))
            frm_mode.pack(fill="x", padx=15, pady=5)

            rb1 = tk.Radiobutton(frm_mode, text="Локальная GGUF модель (llama-cpp-python)", variable=self.var_engine, value="gguf", fg="#00ff41", bg="#051a08", selectcolor="#010602", activebackground="#051a08", activeforeground="#00ff41")
            rb2 = tk.Radiobutton(frm_mode, text="Встроенный процедурный Creator (Offline)", variable=self.var_engine, value="builtin", fg="#00ff41", bg="#051a08", selectcolor="#010602", activebackground="#051a08", activeforeground="#00ff41")
            rb1.pack(anchor="w", padx=10, pady=2)
            rb2.pack(anchor="w", padx=10, pady=2)

            # Models list
            frm_files = tk.LabelFrame(self, text="Файл модели .gguf", fg="#00ff41", bg="#051a08", font=("Consolas", 10, "bold"))
            frm_files.pack(fill="x", padx=15, pady=5)

            frm_browse = tk.Frame(frm_files, bg="#051a08")
            frm_browse.pack(fill="x", padx=8, pady=6)

            self.entry_path = tk.Entry(frm_browse, bg="#010803", fg="#00ff41", insertbackground="#00ff41", font=("Consolas", 10))
            self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 5))
            if self.llm.model_path:
                self.entry_path.insert(0, self.llm.model_path)

            btn_browse = tk.Button(frm_browse, text="Обзор...", command=self.browse_file, bg="#003b00", fg="#00ff41", font=("Consolas", 9, "bold"), activebackground="#00ff41", activeforeground="#000")
            btn_browse.pack(side="right")

            # Parameters
            frm_params = tk.LabelFrame(self, text="Параметры инференса", fg="#00ff41", bg="#051a08", font=("Consolas", 10, "bold"))
            frm_params.pack(fill="x", padx=15, pady=5)

            # Context
            p1 = tk.Frame(frm_params, bg="#051a08")
            p1.pack(fill="x", padx=10, pady=3)
            tk.Label(p1, text="Контекст (n_ctx):", fg="#00ff41", bg="#051a08", width=18, anchor="w").pack(side="left")
            self.spin_ctx = tk.Spinbox(p1, from_=512, to=32768, increment=512, bg="#010803", fg="#00ff41", insertbackground="#00ff41", width=10)
            self.spin_ctx.delete(0, "end")
            self.spin_ctx.insert(0, str(self.llm.n_ctx))
            self.spin_ctx.pack(side="left")

            # Threads
            p2 = tk.Frame(frm_params, bg="#051a08")
            p2.pack(fill="x", padx=10, pady=3)
            tk.Label(p2, text="Потоки CPU:", fg="#00ff41", bg="#051a08", width=18, anchor="w").pack(side="left")
            self.spin_threads = tk.Spinbox(p2, from_=1, to=32, bg="#010803", fg="#00ff41", insertbackground="#00ff41", width=10)
            self.spin_threads.delete(0, "end")
            self.spin_threads.insert(0, str(self.llm.threads))
            self.spin_threads.pack(side="left")

            # GPU Layers
            p3 = tk.Frame(frm_params, bg="#051a08")
            p3.pack(fill="x", padx=10, pady=3)
            tk.Label(p3, text="Слои GPU (0=CPU):", fg="#00ff41", bg="#051a08", width=18, anchor="w").pack(side="left")
            self.spin_gpu = tk.Spinbox(p3, from_=0, to=99, bg="#010803", fg="#00ff41", insertbackground="#00ff41", width=10)
            self.spin_gpu.delete(0, "end")
            self.spin_gpu.insert(0, "0")
            self.spin_gpu.pack(side="left")

            # Status label
            self.lbl_status = tk.Label(self, text="", fg="#20ff70", bg="#031206", font=("Consolas", 10, "bold"))
            self.lbl_status.pack(pady=5)
            self.update_status_label()

            # Action buttons
            frm_act = tk.Frame(self, bg="#031206")
            frm_act.pack(side="bottom", fill="x", padx=15, pady=12)

            self.btn_apply = tk.Button(frm_act, text="⚡ ЗАГРУЗИТЬ МОДЕЛЬ", command=self.apply_model, bg="#004d0b", fg="#ffffff", font=("Consolas", 10, "bold"), activebackground="#00ff41", activeforeground="#000")
            self.btn_apply.pack(side="left", padx=5)

            btn_close = tk.Button(frm_act, text="Закрыть", command=self.destroy, bg="#002200", fg="#00ff41", font=("Consolas", 10), activebackground="#00ff41", activeforeground="#000")
            btn_close.pack(side="right", padx=5)

        def browse_file(self) -> None:
            fn = filedialog.askopenfilename(
                title="Выберите файл GGUF модели",
                filetypes=[("GGUF Models", "*.gguf"), ("All files", "*.*")],
            )
            if fn:
                self.entry_path.delete(0, "end")
                self.entry_path.insert(0, fn)
                self.var_engine.set("gguf")

        def update_status_label(self) -> None:
            info = self.llm.get_model_info()
            if info["is_simulated"]:
                self.lbl_status.config(text="Текущий статус: [Встроенный процедурный Creator]")
            else:
                self.lbl_status.config(text=f"Текущий статус: [GGUF: {info['model_name']}]")

        def apply_model(self) -> None:
            if self.var_engine.get() == "builtin":
                ok, msg = self.llm.load_model(None)
                self.update_status_label()
                messagebox.showinfo("AI Engine", msg)
                self.destroy()
                return

            path = self.entry_path.get().strip()
            if not path or not os.path.isfile(path):
                messagebox.showerror("Ошибка", f"Файл модели не найден:\n{path}")
                return

            try:
                ctx = int(self.spin_ctx.get())
                thr = int(self.spin_threads.get())
                gpu = int(self.spin_gpu.get())
            except ValueError:
                ctx, thr, gpu = 4096, 4, 0

            self.btn_apply.config(text="Загрузка...", state="disabled")
            self.update()

            ok, msg = self.llm.load_model(
                model_path=path,
                n_ctx=ctx,
                n_threads=thr,
                n_gpu_layers=gpu,
            )
            self.btn_apply.config(text="⚡ ЗАГРУЗИТЬ МОДЕЛЬ", state="normal")
            self.update_status_label()

            if ok:
                messagebox.showinfo("Успех", msg)
                self.destroy()
            else:
                messagebox.showerror("Ошибка загрузки", msg)

    class TkHolographicApp:
        """Main Native Tkinter Desktop Application with Holographic Viewport and Controls."""

        def __init__(self, root: tk.Tk, model_path: str | None = None) -> None:
            self.root = root
            self.root.title("AI CREATOR — HOLOGRAPHIC MATRIX STUDIO (Tk Desktop)")
            self.root.geometry("1200x750")
            self.root.configure(bg="#020904")

            self.llm = CreatorLLM(model_path)
            self.scene = Scene()
            self.camera = Camera(pos=(0.0, 6.0, 18.0), target=(0.0, 1.0, 0.0))
            self.world = World(self.scene)
            self.world.update_chunks_around(self.camera.pos)
            self.rain = DigitalRain(width=100, height=50)

            self.fps = 30.0
            self.last_time = time.time()
            self.show_rain = True
            self.show_wireframe = True

            self.last_mouse_x = 0
            self.last_mouse_y = 0

            self.build_ui()
            self.animate()

        def build_ui(self) -> None:
            # Menu bar
            menubar = tk.Menu(self.root, bg="#051408", fg="#00ff41", activebackground="#00ff41", activeforeground="#000")
            
            m_file = tk.Menu(menubar, tearoff=0, bg="#051408", fg="#00ff41", activebackground="#00ff41", activeforeground="#000")
            m_file.add_command(label="Очистить мир", command=self.clear_world)
            m_file.add_separator()
            m_file.add_command(label="Выход", command=self.root.quit)
            menubar.add_cascade(label="Файл", menu=m_file)

            m_model = tk.Menu(menubar, tearoff=0, bg="#051408", fg="#00ff41", activebackground="#00ff41", activeforeground="#000")
            m_model.add_command(label="Выбрать / Загрузить GGUF модель...", command=self.open_model_dialog)
            menubar.add_cascade(label="Модели GGUF", menu=m_model)

            m_view = tk.Menu(menubar, tearoff=0, bg="#051408", fg="#00ff41", activebackground="#00ff41", activeforeground="#000")
            m_view.add_command(label="Сброс камеры", command=self.reset_camera)
            m_view.add_command(label="Переключить матричный дождь", command=self.toggle_rain)
            menubar.add_cascade(label="Вид", menu=m_view)

            self.root.config(menu=menubar)

            # Top Toolbar
            toolbar = tk.Frame(self.root, bg="#051408", bd=1, relief="solid")
            toolbar.pack(side="top", fill="x")

            btn_m = tk.Button(toolbar, text="📁 ВЫБРАТЬ GGUF МОДЕЛЬ", command=self.open_model_dialog, bg="#004d0b", fg="#fff", font=("Consolas", 10, "bold"), activebackground="#00ff41", activeforeground="#000")
            btn_m.pack(side="left", padx=6, pady=4)

            btn_res = tk.Button(toolbar, text="🔄 Сброс камеры", command=self.reset_camera, bg="#002b06", fg="#00ff41", font=("Consolas", 9, "bold"), activebackground="#00ff41", activeforeground="#000")
            btn_res.pack(side="left", padx=4, pady=4)

            btn_cl = tk.Button(toolbar, text="🧹 Очистить мир", command=self.clear_world, bg="#002b06", fg="#00ff41", font=("Consolas", 9, "bold"), activebackground="#00ff41", activeforeground="#000")
            btn_cl.pack(side="left", padx=4, pady=4)

            self.lbl_active_model = tk.Label(toolbar, text="", bg="#051408", fg="#20ff70", font=("Consolas", 10, "bold"))
            self.lbl_active_model.pack(side="right", padx=10)
            self.update_model_badge()

            # Main container
            main_frm = tk.Frame(self.root, bg="#020904")
            main_frm.pack(fill="both", expand=True)

            # Left Dock: AI Prompt Terminal
            dock_left = tk.Frame(main_frm, bg="#031206", width=310, bd=1, relief="solid")
            dock_left.pack(side="left", fill="y", padx=2, pady=2)
            dock_left.pack_propagate(False)

            tk.Label(dock_left, text="AI CREATOR — МАТЕРИАЛИЗАЦИЯ", bg="#051a08", fg="#00ff41", font=("Consolas", 10, "bold"), pady=4).pack(fill="x")

            p_box = tk.Frame(dock_left, bg="#031206")
            p_box.pack(fill="x", padx=8, pady=6)

            tk.Label(p_box, text="Идея создания мира:", bg="#031206", fg="#00ff41", font=("Consolas", 9, "bold"), anchor="w").pack(fill="x")
            self.entry_prompt = tk.Entry(p_box, bg="#010803", fg="#00ff41", insertbackground="#00ff41", font=("Consolas", 10))
            self.entry_prompt.pack(fill="x", pady=4)
            self.entry_prompt.bind("<Return>", lambda e: self.send_prompt())

            self.btn_send = tk.Button(p_box, text="⚡ МАТЕРИАЛИЗОВАТЬ (Enter)", command=self.send_prompt, bg="#004d0b", fg="#fff", font=("Consolas", 10, "bold"), activebackground="#00ff41", activeforeground="#000")
            self.btn_send.pack(fill="x", pady=2)

            # Quick Presets
            prs_frm = tk.LabelFrame(dock_left, text="Быстрые пресеты", bg="#031206", fg="#00ff41", font=("Consolas", 9, "bold"))
            prs_frm.pack(fill="x", padx=8, pady=6)

            presets = [
                ("🌲 Лес и олени", "Создай лес и оленей"),
                ("🏰 Замок из кубов", "Замок из кубов"),
                ("🐺 Стая волков", "Стая волков и оленей"),
                ("🐉 Дракон", "Дракон и единорог"),
                ("🤖 Боевые роботы", "Боевые роботы"),
                ("👥 Больше жизни", "Наполни мир жизнью"),
            ]
            for title, p_text in presets:
                b = tk.Button(prs_frm, text=title, command=lambda t=p_text: self.run_preset(t), bg="#002b06", fg="#00ff41", font=("Consolas", 8), activebackground="#00ff41", activeforeground="#000")
                b.pack(fill="x", pady=1)

            # Token stream
            tk.Label(dock_left, text="Поток генерации ИИ (GBNF JSON):", bg="#031206", fg="#00ff41", font=("Consolas", 9, "bold"), anchor="w").pack(fill="x", padx=8, pady=(6, 2))
            self.txt_stream = tk.Text(dock_left, bg="#010602", fg="#00ff41", font=("Consolas", 8), height=10, insertbackground="#00ff41", bd=1, relief="solid")
            self.txt_stream.pack(fill="x", padx=8, pady=2)

            # Right Dock: Inspector
            dock_right = tk.Frame(main_frm, bg="#031206", width=280, bd=1, relief="solid")
            dock_right.pack(side="right", fill="y", padx=2, pady=2)
            dock_right.pack_propagate(False)

            tk.Label(dock_right, text="ИНСПЕКТОР СУЩНОСТЕЙ И ИИ", bg="#051a08", fg="#00ff41", font=("Consolas", 10, "bold"), pady=4).pack(fill="x")

            self.lbl_telemetry = tk.Label(dock_right, text="", bg="#031206", fg="#00ff41", font=("Consolas", 9), justify="left")
            self.lbl_telemetry.pack(anchor="w", padx=8, pady=4)

            tk.Label(dock_right, text="Существа и поведение (FSM):", bg="#031206", fg="#00ff41", font=("Consolas", 9, "bold"), anchor="w").pack(fill="x", padx=8, pady=(6, 2))
            self.txt_creatures = tk.Text(dock_right, bg="#010602", fg="#20ff70", font=("Consolas", 8), height=16, bd=1, relief="solid")
            self.txt_creatures.pack(fill="both", expand=True, padx=8, pady=4)

            # Center 3D Viewport
            vp_frm = tk.Frame(main_frm, bg="#010602")
            vp_frm.pack(side="left", fill="both", expand=True)

            self.canvas = tk.Canvas(vp_frm, bg="#010602", highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)

            # Mouse bindings on 3D Viewport
            self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
            self.canvas.bind("<B1-Motion>", self.on_left_drag)
            self.canvas.bind("<ButtonPress-3>", self.on_mouse_down)
            self.canvas.bind("<B3-Motion>", self.on_right_drag)
            self.canvas.bind("<MouseWheel>", self.on_wheel)  # Windows
            self.canvas.bind("<Button-4>", lambda e: self.camera.zoom(-2.0))  # Linux
            self.canvas.bind("<Button-5>", lambda e: self.camera.zoom(2.0))   # Linux

            # Global keyboard bindings
            self.root.bind("<Key>", self.on_key_press)

            # Status bar
            self.statusbar = tk.Label(self.root, text="● ГОТОВ :: Нажмите ЛКМ и тяните для вращения, колесико для Zoom", bg="#051408", fg="#00ff41", font=("Consolas", 9), anchor="w", padx=8)
            self.statusbar.pack(side="bottom", fill="x")

        def update_model_badge(self) -> None:
            info = self.llm.get_model_info()
            if info["is_simulated"]:
                self.lbl_active_model.config(text="🤖 ДВИЖОК: Встроенный процедурный (Offline)")
            else:
                self.lbl_active_model.config(text=f"🧠 ДВИЖОК: {info['model_name']} (CPU)")

        def open_model_dialog(self) -> None:
            dlg = TkModelDialog(self.root, self.llm)
            self.root.wait_window(dlg)
            self.update_model_badge()

        def reset_camera(self) -> None:
            self.camera.pos = Vec3(0.0, 6.0, 18.0)
            self.camera.target = Vec3(0.0, 1.0, 0.0)
            self.camera.distance = 18.0
            self.camera.yaw = 0.0
            self.camera.pitch = 0.25

        def toggle_rain(self) -> None:
            self.show_rain = not self.show_rain

        def clear_world(self) -> None:
            for eid in list(self.world.entities.keys()):
                self.world.remove_entity(eid)
            self.txt_stream.delete("1.0", "end")
            self.statusbar.config(text="Мир очищен.")

        def run_preset(self, text: str) -> None:
            self.entry_prompt.delete(0, "end")
            self.entry_prompt.insert(0, text)
            self.send_prompt()

        def send_prompt(self) -> None:
            text = self.entry_prompt.get().strip()
            if not text:
                return

            self.btn_send.config(text="ГЕНЕРАЦИЯ...", state="disabled")
            self.statusbar.config(text=f"ИИ Создатель материализует: «{text}»...")
            self.txt_stream.delete("1.0", "end")

            def worker():
                accumulated = []
                for chunk in self.llm.stream_generate(text):
                    accumulated.append(chunk)
                    self.root.after(0, self.append_stream, chunk)

                full_json = "".join(accumulated)
                try:
                    cmds = parse_commands_json(full_json)
                    self.world.apply_commands(cmds)
                except Exception:
                    pass

                self.root.after(0, self.finish_prompt)

            threading.Thread(target=worker, daemon=True).start()

        def append_stream(self, chunk: str) -> None:
            self.txt_stream.insert("end", chunk)
            self.txt_stream.see("end")

        def finish_prompt(self) -> None:
            self.btn_send.config(text="⚡ МАТЕРИАЛИЗОВАТЬ (Enter)", state="normal")
            self.statusbar.config(text=f"Материализация завершена. Объектов в мире: {len(self.world.entities)}")

        # Mouse Handlers
        def on_mouse_down(self, event: tk.Event) -> None:
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y

        def on_left_drag(self, event: tk.Event) -> None:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.camera.orbit(dx * 0.008, -dy * 0.008)

        def on_right_drag(self, event: tk.Event) -> None:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.camera.move(0.0, -dx * 0.05, dy * 0.05)

        def on_wheel(self, event: tk.Event) -> None:
            if event.delta > 0:
                self.camera.zoom(-2.0)
            else:
                self.camera.zoom(2.0)

        def on_key_press(self, event: tk.Event) -> None:
            # If focus is in text entry, don't move camera
            if self.root.focus_get() == self.entry_prompt:
                return
            k = event.keysym.lower()
            if k == "w": self.camera.move(1.5, 0.0)
            elif k == "s": self.camera.move(-1.5, 0.0)
            elif k == "a": self.camera.move(0.0, -1.5)
            elif k == "d": self.camera.move(0.0, 1.5)
            elif k == "e": self.camera.move(0.0, 0.0, 1.5)
            elif k == "c": self.camera.move(0.0, 0.0, -1.5)
            elif k == "left": self.camera.orbit(-0.15, 0.0)
            elif k == "right": self.camera.orbit(0.15, 0.0)
            elif k == "up": self.camera.orbit(0.0, 0.15)
            elif k == "down": self.camera.orbit(0.0, -0.15)

        def animate(self) -> None:
            now = time.time()
            dt = max(0.001, min(0.1, now - self.last_time))
            self.last_time = now
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)

            # Update world
            self.world.update(dt, self.camera.pos)
            if self.show_rain:
                self.rain.update(dt)

            # Render frame to canvas
            self.render_frame()

            # Update telemetry and inspector
            c_creatures = sum(1 for e in self.world.entities.values() if isinstance(e, WorldCreature))
            self.lbl_telemetry.config(
                text=f"FPS: {self.fps:.1f}\n"
                     f"Сущностей: {len(self.world.entities)}\n"
                     f"Существ: {c_creatures}\n"
                     f"Чанков: {len(self.world.chunks)}\n"
                     f"CAM: ({self.camera.pos.x:.1f}, {self.camera.pos.y:.1f}, {self.camera.pos.z:.1f})"
            )

            # Update creatures text
            lines = []
            for e in self.world.entities.values():
                if isinstance(e, WorldCreature):
                    lines.append(f"• {e.name} ({e.species})\n  [{getattr(e, 'state', 'IDLE')}] pos=({e.position.x:.1f},{e.position.z:.1f})")
            self.txt_creatures.delete("1.0", "end")
            self.txt_creatures.insert("1.0", "\n".join(lines) if lines else "Нет активных существ.")

            self.root.after(33, self.animate)

        def render_frame(self) -> None:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w <= 10 or h <= 10:
                return

            self.canvas.delete("all")

            # 1. Digital Rain
            if self.show_rain:
                for drop in self.rain.drops[:30]:
                    col_x = int((drop.col / 100.0) * w)
                    for i in range(drop.length):
                        row_y = int(((drop.y - i) / 50.0) * h)
                        if 0 <= row_y < h:
                            col = "#003b00" if i > 3 else ("#00ff41" if i > 0 else "#dcffdc")
                            ch = RAIN_CHARS[(drop.col + i * 3) % len(RAIN_CHARS)]
                            self.canvas.create_text(col_x, row_y, text=ch, fill=col, font=("Consolas", 8))

            # 2. 3D Wireframe projection
            aspect = float(w) / max(1.0, float(h))
            vp_mat = self.camera.get_view_projection(aspect)

            def project_pt(p: Vec3) -> tuple[int, int] | None:
                m = vp_mat.m
                x, y, z = p.x, p.y, p.z
                clip_x = m[0] * x + m[4] * y + m[8] * z + m[12]
                clip_y = m[1] * x + m[5] * y + m[9] * z + m[13]
                clip_z = m[2] * x + m[6] * y + m[10] * z + m[14]
                clip_w = m[3] * x + m[7] * y + m[11] * z + m[15]
                if clip_w <= 0.05:
                    return None
                ndc_x = clip_x / clip_w
                ndc_y = clip_y / clip_w
                if abs(ndc_x) > 1.8 or abs(ndc_y) > 1.8:
                    return None
                return int((ndc_x * 0.5 + 0.5) * w), int((-ndc_y * 0.5 + 0.5) * h)

            for entity in self.world.holo_scene.entities.values():
                if not entity.visible:
                    continue
                mesh = entity.mesh
                tf = entity.get_model_matrix()
                pts = [tf.transform_point(v) for v in mesh.vertices]
                proj = [project_pt(p) for p in pts]
                c_hex = f"#{mesh.color[0]:02x}{mesh.color[1]:02x}{mesh.color[2]:02x}"

                for e0, e1 in mesh.edges:
                    if e0 < len(proj) and e1 < len(proj):
                        p0 = proj[e0]
                        p1 = proj[e1]
                        if p0 and p1:
                            self.canvas.create_line(p0[0], p0[1], p1[0], p1[1], fill=c_hex, width=1)


def run_tkinter_app(model_path: str | None = None) -> int:
    """Launch the zero-dependency Tkinter desktop window."""
    if not TK_AVAILABLE:
        print("[!] Tkinter is not available in this environment.")
        return 1

    root = tk.Tk()
    app = TkHolographicApp(root, model_path=model_path)
    root.mainloop()
    return 0
