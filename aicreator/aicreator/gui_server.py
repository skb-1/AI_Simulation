"""Holographic Matrix Desktop GUI Server (Zero-Dependency Python http.server).

Provides a full PySide6-styled holographic cyberpunk web GUI with:
- Desktop window styling (titlebar, menus, dock panels, status bar)
- Interactive 3D viewport with working mouse drag orbit/pan and scroll zoom
- On-screen touch/click navigation gizmo
- Model Selection Dialog for GGUF model files (scan, upload, manual path, hot-reload)
- AI Creator prompt terminal with quick presets and live streaming tokens
- World entities inspector & live creature FSM state tracker
"""

from __future__ import annotations

import cgi
import glob
import json
import math
import os
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from aicreator.commands import parse_commands_json
from aicreator.entities import WorldCreature, WorldPrimitive
from aicreator.llm import CreatorLLM, find_gguf_models
from aicreator.world import World
from matrixholo.camera import Camera
from matrixholo.glyphs import RAIN_CHARS
from matrixholo.rain import DigitalRain
from matrixholo.scene import Scene
from matrixholo.vec import Vec3


class AppState:
    """Shared application state between simulation loop and HTTP server."""

    def __init__(self, model_path: str | None = None) -> None:
        self.lock = threading.Lock()
        self.llm = CreatorLLM(model_path)
        self.scene = Scene()
        self.camera = Camera(pos=(0.0, 6.0, 18.0), target=(0.0, 1.0, 0.0))
        self.world = World(self.scene)
        self.world.update_chunks_around(self.camera.pos)
        self.rain = DigitalRain(width=120, height=60)

        self.fps = 30.0
        self.last_time = time.time()
        self.is_paused = False

        self.stream_buffer: list[str] = []
        self.is_generating = False
        self.current_prompt = ""
        self.last_error = ""

        # Pre-populate some initial terrain / scene items
        self.world.update(0.016, self.camera.pos)

    def update_sim(self) -> None:
        """Simulate world frame at ~30 FPS."""
        now = time.time()
        dt = max(0.001, min(0.1, now - self.last_time))
        self.last_time = now
        self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)

        if not self.is_paused:
            with self.lock:
                self.world.update(dt, self.camera.pos)
                self.rain.update(dt)

    def run_prompt_thread(self, prompt: str) -> None:
        """Execute LLM stream in worker thread and apply commands."""
        with self.lock:
            self.is_generating = True
            self.stream_buffer.clear()
            self.current_prompt = prompt
            self.last_error = ""

        def worker():
            accumulated = []
            try:
                for chunk in self.llm.stream_generate(prompt):
                    with self.lock:
                        self.stream_buffer.append(chunk)
                    accumulated.append(chunk)

                full_json = "".join(accumulated)
                cmds = parse_commands_json(full_json)
                with self.lock:
                    self.world.apply_commands(cmds)
            except Exception as e:
                with self.lock:
                    self.last_error = str(e)
            finally:
                with self.lock:
                    self.is_generating = False

        threading.Thread(target=worker, daemon=True).start()

    def get_serialized_state(self) -> dict[str, Any]:
        """Serialize current world and UI state for frontend renderer."""
        with self.lock:
            entities_data = []
            for ent in self.world.entities.values():
                m = ent.mesh_entity.mesh
                model_mat = ent.mesh_entity.get_model_matrix()
                pts = [model_mat.transform_point(v).to_tuple() for v in m.vertices]
                entities_data.append({
                    "id": ent.id,
                    "name": ent.name,
                    "type": getattr(ent, "species", getattr(ent, "primitive_type", "mesh")),
                    "color": m.color,
                    "pos": ent.position.to_tuple(),
                    "vertices": pts,
                    "edges": m.edges,
                })

            # Also serialize terrain meshes from chunks
            for chunk in self.world.chunks.values():
                if chunk.terrain_entity and chunk.terrain_entity.visible:
                    tm = chunk.terrain_entity.mesh
                    model_mat = chunk.terrain_entity.get_model_matrix()
                    pts = [model_mat.transform_point(v).to_tuple() for v in tm.vertices]
                    entities_data.append({
                        "id": chunk.terrain_entity.id,
                        "name": chunk.terrain_entity.name,
                        "type": "terrain",
                        "color": tm.color,
                        "pos": (0, 0, 0),
                        "vertices": pts,
                        "edges": tm.edges,
                    })

            creatures_data = []
            for ent in self.world.entities.values():
                if isinstance(ent, WorldCreature):
                    target_name = (
                        self.world.entities[ent.target_entity_id].name
                        if ent.target_entity_id and ent.target_entity_id in self.world.entities
                        else "None"
                    )
                    creatures_data.append({
                        "id": ent.id,
                        "name": ent.name,
                        "species": ent.species,
                        "fsm": getattr(ent, "state", "IDLE"),
                        "pos": [round(ent.position.x, 1), round(ent.position.y, 1), round(ent.position.z, 1)],
                        "target": target_name,
                    })

            rain_data = [
                {"x": d.col, "y": d.y, "len": d.length, "speed": d.speed}
                for d in self.rain.drops[:40]
            ]

            return {
                "camera": {
                    "pos": self.camera.pos.to_tuple(),
                    "target": self.camera.target.to_tuple(),
                    "yaw": self.camera.yaw,
                    "pitch": self.camera.pitch,
                    "distance": self.camera.distance,
                    "fov": self.camera.fov,
                },
                "stats": {
                    "entities": len(self.world.entities),
                    "creatures": len(creatures_data),
                    "chunks": len(self.world.chunks),
                    "fps": round(self.fps, 1),
                },
                "model": self.llm.get_model_info(),
                "is_generating": self.is_generating,
                "stream_text": "".join(self.stream_buffer),
                "entities": entities_data,
                "creatures": creatures_data,
                "rain": rain_data,
            }


HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>AI Creator v2.0 :: PySide6 Holographic Matrix Studio</title>
<style>
:root {
  --neon-green: #00ff41;
  --dark-green: #008f11;
  --dim-green: #003b00;
  --bg-deep: #020904;
  --bg-panel: rgba(3, 16, 7, 0.92);
  --bg-darker: #010602;
  --border-neon: 1px solid #00ff41;
  --border-dim: 1px solid #008f11;
  --glow-shadow: 0 0 10px rgba(0, 255, 65, 0.4);
}
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: 'Consolas', 'Courier New', monospace;
  user-select: none;
}
body, html {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-deep);
  color: var(--neon-green);
  font-size: 13px;
}
/* Cyberpunk CRT Scanline overlay */
body::after {
  content: " ";
  display: block;
  position: absolute;
  top: 0; left: 0; bottom: 0; right: 0;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
  background-size: 100% 3px;
  z-index: 999;
  pointer-events: none;
  opacity: 0.6;
}

/* Master App Container */
#app {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
}

/* PySide6 Title Bar */
.titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #051408;
  border-bottom: var(--border-neon);
  padding: 4px 10px;
  height: 32px;
  flex-shrink: 0;
}
.titlebar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  letter-spacing: 1px;
}
.titlebar-icon {
  width: 14px;
  height: 14px;
  background: var(--neon-green);
  box-shadow: 0 0 6px var(--neon-green);
  display: inline-block;
}
.titlebar-buttons {
  display: flex;
  gap: 6px;
}
.title-btn {
  background: var(--dim-green);
  color: var(--neon-green);
  border: var(--border-dim);
  padding: 2px 7px;
  cursor: pointer;
  font-size: 11px;
}
.title-btn:hover {
  background: var(--neon-green);
  color: #000;
}

/* Menu Bar */
.menubar {
  display: flex;
  background: #030d05;
  border-bottom: var(--border-dim);
  padding: 3px 8px;
  gap: 15px;
  font-size: 12px;
  flex-shrink: 0;
}
.menu-item {
  cursor: pointer;
  padding: 2px 6px;
}
.menu-item:hover {
  background: var(--dim-green);
  color: #fff;
}

/* Top Quick Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #020a04;
  border-bottom: var(--border-dim);
  padding: 5px 10px;
  flex-shrink: 0;
  overflow-x: auto;
}
.btn {
  background: #002b06;
  color: var(--neon-green);
  border: var(--border-neon);
  padding: 4px 10px;
  cursor: pointer;
  font-size: 12px;
  font-weight: bold;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s;
}
.btn:hover {
  background: var(--neon-green);
  color: #000;
  box-shadow: 0 0 8px var(--neon-green);
}
.btn:active {
  background: var(--dark-green);
  color: #fff;
}
.btn-highlight {
  background: #004d0b;
  border-color: #20ff70;
  color: #ffffff;
  box-shadow: 0 0 6px rgba(0, 255, 65, 0.4);
}

/* Main Workspace with Docks */
.workspace {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* Docks */
.dock {
  background: var(--bg-panel);
  border: var(--border-dim);
  display: flex;
  flex-direction: column;
  z-index: 10;
  backdrop-filter: blur(4px);
}
.dock-left {
  width: 320px;
  border-right: var(--border-neon);
}
.dock-right {
  width: 310px;
  border-left: var(--border-neon);
}
.dock-header {
  background: #051408;
  border-bottom: var(--border-neon);
  padding: 6px 10px;
  font-weight: bold;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  letter-spacing: 0.5px;
}
.dock-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Center Viewport */
.viewport-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #010602;
  cursor: grab;
}
.viewport-container:active {
  cursor: grabbing;
}
canvas#viewport {
  width: 100%;
  height: 100%;
  display: block;
}

/* HUD Overlay inside Viewport */
.viewport-hud {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(2, 10, 4, 0.85);
  border: var(--border-dim);
  padding: 8px 12px;
  font-size: 11px;
  pointer-events: none;
  line-height: 1.5;
}
.viewport-hud b {
  color: #ffffff;
}

/* On-Screen Touch / Click Controls Gizmo */
.controls-gizmo {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(3, 16, 7, 0.9);
  border: var(--border-neon);
  box-shadow: var(--glow-shadow);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  z-index: 20;
}
.gizmo-title {
  font-size: 10px;
  text-align: center;
  font-weight: bold;
  border-bottom: 1px solid var(--dim-green);
  padding-bottom: 3px;
}
.gizmo-grid {
  display: grid;
  grid-template-columns: repeat(3, 36px);
  grid-template-rows: repeat(3, 32px);
  gap: 4px;
}
.g-btn {
  background: #032007;
  border: var(--border-dim);
  color: var(--neon-green);
  font-size: 13px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.g-btn:hover {
  background: var(--neon-green);
  color: #000;
}
.gizmo-row {
  display: flex;
  gap: 4px;
}
.gizmo-row .g-btn {
  flex: 1;
  height: 28px;
  font-size: 11px;
}

/* Prompt Input and Quick Presets */
.prompt-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.input-text {
  background: var(--bg-darker);
  border: var(--border-dim);
  color: var(--neon-green);
  padding: 8px;
  font-size: 13px;
  outline: none;
  width: 100%;
}
.input-text:focus {
  border-color: var(--neon-green);
  box-shadow: 0 0 6px var(--neon-green);
}
.btn-materialize {
  background: #004d0b;
  border: 1px solid #00ff41;
  color: #fff;
  padding: 8px;
  font-weight: bold;
  font-size: 13px;
  cursor: pointer;
  letter-spacing: 1px;
  text-align: center;
  box-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
}
.btn-materialize:hover {
  background: var(--neon-green);
  color: #000;
}

/* Stream Terminal Box */
.terminal-box {
  background: #010402;
  border: var(--border-dim);
  padding: 8px;
  height: 140px;
  overflow-y: auto;
  font-size: 11px;
  color: #00ff41;
  white-space: pre-wrap;
  word-break: break-all;
}
.cursor {
  display: inline-block;
  width: 6px;
  height: 12px;
  background: var(--neon-green);
  animation: blink 0.8s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Inspector list */
.inspector-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
.inspector-table th, .inspector-table td {
  border: 1px solid var(--dim-green);
  padding: 4px 6px;
  text-align: left;
}
.inspector-table th {
  background: #051408;
  color: #20ff70;
}
.badge-state {
  display: inline-block;
  padding: 2px 4px;
  font-size: 9px;
  font-weight: bold;
  border-radius: 2px;
  background: #003b00;
  color: #00ff41;
}

/* Status Bar */
.statusbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #051408;
  border-top: var(--border-dim);
  padding: 3px 12px;
  height: 24px;
  font-size: 11px;
  flex-shrink: 0;
}
.status-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--neon-green);
  box-shadow: 0 0 6px var(--neon-green);
  margin-right: 5px;
}

/* Modal Dialog: Model Selection */
.modal-overlay {
  display: none;
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(5px);
  z-index: 1000;
  align-items: center;
  justify-content: center;
}
.modal-dialog {
  background: #031206;
  border: 2px solid var(--neon-green);
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.5);
  width: 580px;
  max-width: 95vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
.modal-header {
  background: #051a08;
  border-bottom: var(--border-neon);
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.modal-body {
  padding: 15px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.modal-footer {
  background: #051408;
  border-top: var(--border-dim);
  padding: 10px 15px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.model-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.upload-dropzone {
  border: 2px dashed var(--dark-green);
  padding: 15px;
  text-align: center;
  cursor: pointer;
  background: #010602;
}
.upload-dropzone:hover {
  border-color: var(--neon-green);
  background: #021205;
}
</style>
</head>
<body>

<div id="app">
  <!-- Window Title Bar -->
  <div class="titlebar">
    <div class="titlebar-left">
      <span class="titlebar-icon"></span>
      <span>AI CREATOR v2.0 :: PySide6 Holographic Matrix Studio</span>
    </div>
    <div class="titlebar-buttons">
      <button class="title-btn" onclick="toggleFullscreen()">▢</button>
      <button class="title-btn" onclick="alert('Закрытие окна студии.')">✕</button>
    </div>
  </div>

  <!-- Menu Bar -->
  <div class="menubar">
    <div class="menu-item" onclick="openModelModal()">🧠 Модель GGUF (Выбор)</div>
    <div class="menu-item" onclick="clearWorld()">🧹 Мир: Очистить</div>
    <div class="menu-item" onclick="resetCamera()">🔄 Камера: Сброс</div>
    <div class="menu-item" onclick="toggleRain()">🌧️ Матричный дождь</div>
    <div class="menu-item" onclick="toggleWireframe()">🌐 Сетка ландшафта</div>
    <div class="menu-item" onclick="openHelpModal()">❓ Справка</div>
  </div>

  <!-- Toolbar -->
  <div class="toolbar">
    <button class="btn btn-highlight" onclick="openModelModal()">📁 ВЫБРАТЬ GGUF МОДЕЛЬ</button>
    <button class="btn" onclick="resetCamera()">🔄 Сброс камеры</button>
    <button class="btn" onclick="toggleRain()" id="btn-rain">🌧️ Дождь [ВКЛ]</button>
    <button class="btn" onclick="toggleWireframe()" id="btn-wf">🌐 Сетка [ВКЛ]</button>
    <button class="btn" onclick="clearWorld()">🧹 Очистить мир</button>
  </div>

  <!-- Main Workspace -->
  <div class="workspace">
    <!-- Left Dock: Prompt Terminal -->
    <div class="dock dock-left">
      <div class="dock-header">
        <span>AI CREATOR — МАТЕРИАЛИЗАЦИЯ</span>
        <span style="font-size: 10px; color: #20ff70;">[LIVE]</span>
      </div>
      <div class="dock-content">
        <!-- Model Badge -->
        <div id="model-badge" style="background: #051a08; border: 1px solid #008f11; padding: 6px; font-size: 11px;">
          <b>ДВИЖОК:</b> <span id="lbl-active-model">Загрузка...</span>
        </div>

        <!-- Prompt Form -->
        <div class="prompt-box">
          <label style="font-weight: bold;">Идея создания мира:</label>
          <input type="text" id="prompt-input" class="input-text" placeholder="«Создай лес и оленей» или «Замок из кубов»..." onkeydown="if(event.key==='Enter') sendPrompt();">
          <button class="btn-materialize" id="btn-send" onclick="sendPrompt()">⚡ МАТЕРИАЛИЗОВАТЬ (Enter)</button>
        </div>

        <!-- Quick Presets -->
        <div>
          <label style="font-weight: bold; font-size: 11px; margin-bottom: 4px; display: block;">Быстрые пресеты:</label>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
            <button class="btn" style="font-size: 11px;" onclick="runPreset('Создай лес и оленей')">🌲 Лес и олени</button>
            <button class="btn" style="font-size: 11px;" onclick="runPreset('Замок из кубов')">🏰 Замок из кубов</button>
            <button class="btn" style="font-size: 11px;" onclick="runPreset('Стая волков и оленей')">🐺 Волки и олени</button>
            <button class="btn" style="font-size: 11px;" onclick="runPreset('Дракон и единорог')">🐉 Дракон</button>
            <button class="btn" style="font-size: 11px;" onclick="runPreset('Боевые роботы')">🤖 Роботы</button>
            <button class="btn" style="font-size: 11px;" onclick="runPreset('Наполни мир жизнью')">👥 Больше жизни</button>
          </div>
        </div>

        <!-- Token Stream Output -->
        <div>
          <label style="font-weight: bold; font-size: 11px;">Поток генерации ИИ (GBNF JSON):</label>
          <div id="terminal-stream" class="terminal-box"><span id="stream-content">Ожидание команды Создателя...</span><span class="cursor"></span></div>
        </div>
      </div>
    </div>

    <!-- Center Viewport -->
    <div class="viewport-container" id="viewport-container">
      <canvas id="viewport"></canvas>

      <!-- Viewport HUD -->
      <div class="viewport-hud">
        <div><b>FPS:</b> <span id="hud-fps">60.0</span> | <b>CHUNKS:</b> <span id="hud-chunks">29</span></div>
        <div><b>СУЩНОСТИ:</b> <span id="hud-entities">0</span> | <b>СУЩЕСТВА:</b> <span id="hud-creatures">0</span></div>
        <div><b>CAM:</b> <span id="hud-cam">(0.0, 6.0, 18.0)</span></div>
        <div style="color: #008f11; font-size: 10px; margin-top: 3px;">Мышь: ЛКМ = Вращение, ПКМ = Перемещение, Колесико = Zoom</div>
      </div>

      <!-- Interactive Controls Gizmo -->
      <div class="controls-gizmo">
        <div class="gizmo-title">УПРАВЛЕНИЕ КАМЕРОЙ</div>
        <div class="gizmo-grid">
          <button class="g-btn" title="Поднять (E)" onclick="cameraMove(0, 0, 2)">↑</button>
          <button class="g-btn" title="Вперед (W)" onclick="cameraMove(2, 0, 0)">W</button>
          <button class="g-btn" title="Опустить (C)" onclick="cameraMove(0, 0, -2)">↓</button>
          
          <button class="g-btn" title="Влево (A)" onclick="cameraMove(0, -2, 0)">A</button>
          <button class="g-btn" title="Сброс камеры" onclick="resetCamera()">◉</button>
          <button class="g-btn" title="Вправо (D)" onclick="cameraMove(0, 2, 0)">D</button>
          
          <button class="g-btn" title="Вращение влево" onclick="cameraOrbit(-0.2, 0)">◄</button>
          <button class="g-btn" title="Назад (S)" onclick="cameraMove(-2, 0, 0)">S</button>
          <button class="g-btn" title="Вращение вправо" onclick="cameraOrbit(0.2, 0)">►</button>
        </div>
        <div class="gizmo-row">
          <button class="g-btn" onclick="cameraZoom(-2.5)">🔍 Zoom +</button>
          <button class="g-btn" onclick="cameraZoom(2.5)">🔎 Zoom -</button>
        </div>
        <div class="gizmo-row">
          <button class="g-btn" onclick="setCameraPreset('front')">Фронт</button>
          <button class="g-btn" onclick="setCameraPreset('top')">Сверху</button>
          <button class="g-btn" onclick="setCameraPreset('iso')">Изометрия</button>
        </div>
      </div>
    </div>

    <!-- Right Dock: World Inspector -->
    <div class="dock dock-right">
      <div class="dock-header">
        <span>ИНСПЕКТОР СУЩНОСТЕЙ И ИИ</span>
        <button class="btn" style="padding: 2px 5px; font-size: 10px;" onclick="refreshState()">🔄</button>
      </div>
      <div class="dock-content">
        <label style="font-weight: bold; font-size: 11px;">Живые существа и поведение (FSM):</label>
        <div style="flex: 1; overflow-y: auto; border: var(--border-dim);">
          <table class="inspector-table" id="table-creatures">
            <thead>
              <tr>
                <th>Имя</th>
                <th>Вид</th>
                <th>FSM Состояние</th>
                <th>Позиция</th>
              </tr>
            </thead>
            <tbody id="creatures-body">
              <tr><td colspan="4" style="text-align:center; color:#008f11;">Нет активных существ</td></tr>
            </tbody>
          </table>
        </div>

        <label style="font-weight: bold; font-size: 11px;">Список объектов мира:</label>
        <div style="height: 140px; overflow-y: auto; border: var(--border-dim); font-size: 11px;" id="entities-list">
          <div style="padding: 6px; color: #008f11;">Объекты не созданы.</div>
        </div>

        <button class="btn" style="width: 100%;" onclick="clearWorld()">🧹 Очистить все объекты</button>
      </div>
    </div>
  </div>

  <!-- Bottom Status Bar -->
  <div class="statusbar">
    <div>
      <span class="status-indicator"></span>
      <span id="status-text">СИСТЕМА ГОТОВА :: МАТРИЧНЫЙ СИНТЕЗАТОР АКТИВЕН</span>
    </div>
    <div id="status-coords">CAM: X=0.0 Y=6.0 Z=18.0</div>
  </div>
</div>

<!-- Modal: Model Selection Dialog -->
<div class="modal-overlay" id="modal-model">
  <div class="modal-dialog">
    <div class="modal-header">
      <span>📁 ОКНО ВЫБОРА И ЗАГРУЗКИ GGUF МОДЕЛИ</span>
      <button class="title-btn" onclick="closeModelModal()">✕</button>
    </div>
    <div class="modal-body">
      <div style="color: #008f11; font-size: 11px;">
        Выберите квантованную модель .gguf для локального инференса на CPU/GPU или переключитесь на встроенный процедурный ИИ Создатель.
      </div>

      <!-- Engine Mode Selection -->
      <div class="model-row" style="background: #010803; border: var(--border-dim); padding: 8px;">
        <label><b>Режим движка ИИ:</b></label>
        <div style="display: flex; gap: 15px; margin-top: 4px;">
          <label><input type="radio" name="engine_mode" value="gguf" id="mode-gguf" checked> Локальная GGUF модель</label>
          <label><input type="radio" name="engine_mode" value="builtin" id="mode-builtin"> Встроенный процедурный Creator</label>
        </div>
      </div>

      <!-- Discovered Models -->
      <div class="model-row">
        <label><b>Обнаруженные .gguf модели в ./models:</b></label>
        <div style="display: flex; gap: 6px;">
          <select id="select-models" class="input-text" style="flex: 1;">
            <option value="">Поиск моделей...</option>
          </select>
          <button class="btn" onclick="scanModels()">🔄 Обновить</button>
        </div>
      </div>

      <!-- Upload or Select from Disk -->
      <div class="model-row">
        <label><b>Загрузить файл .gguf с диска:</b></label>
        <div class="upload-dropzone" onclick="document.getElementById('file-upload').click();">
          <input type="file" id="file-upload" accept=".gguf" style="display:none;" onchange="handleFileUpload(this.files)">
          <div id="upload-status">Нажмите для выбора файла .gguf на вашем компьютере</div>
        </div>
      </div>

      <!-- Manual Path -->
      <div class="model-row">
        <label><b>Или укажите путь к файлу вручную:</b></label>
        <input type="text" id="manual-model-path" class="input-text" placeholder="например: C:/models/llama-3-8b.Q4_K_M.gguf или models/my.gguf">
      </div>

      <!-- Parameters -->
      <div class="model-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
        <div>
          <label>Контекст (n_ctx):</label>
          <select id="param-ctx" class="input-text">
            <option value="2048">2048 токенов</option>
            <option value="4096" selected>4096 токенов</option>
            <option value="8192">8192 токенов</option>
          </select>
        </div>
        <div>
          <label>Потоки CPU:</label>
          <input type="number" id="param-threads" class="input-text" value="4" min="1" max="32">
        </div>
        <div>
          <label>Слои GPU (0 = CPU):</label>
          <input type="number" id="param-gpu" class="input-text" value="0" min="0" max="99">
        </div>
        <div>
          <label>Температура:</label>
          <input type="number" id="param-temp" class="input-text" value="0.2" min="0.05" max="1.5" step="0.05">
        </div>
      </div>

      <div id="model-feedback" style="font-weight: bold; font-size: 11px; padding: 4px;"></div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-highlight" id="btn-apply-model" onclick="applyModelSelection()">⚡ ЗАГРУЗИТЬ МОДЕЛЬ</button>
      <button class="btn" onclick="closeModelModal()">Закрыть</button>
    </div>
  </div>
</div>

<!-- Modal: Help Dialog -->
<div class="modal-overlay" id="modal-help">
  <div class="modal-dialog">
    <div class="modal-header">
      <span>❓ УПРАВЛЕНИЕ И СПРАВКА</span>
      <button class="title-btn" onclick="closeHelpModal()">✕</button>
    </div>
    <div class="modal-body" style="font-size: 12px; line-height: 1.6;">
      <h4 style="color: #20ff70;">🎮 УПРАВЛЕНИЕ КАМЕРОЙ:</h4>
      <ul>
        <li><b>Мышь:</b> Зажмите ЛКМ и тяните — вращение камеры (Orbit).</li>
        <li><b>Мышь:</b> Зажмите ПКМ и тяните — перемещение камеры (Pan).</li>
        <li><b>Колесико мыши:</b> Приближение / отдаление (Zoom).</li>
        <li><b>Клавиши WASD:</b> Перемещение вперед, назад, влево, вправо.</li>
        <li><b>Клавиши Стрелки:</b> Вращение обзора.</li>
        <li><b>Клавиши E / C:</b> Подъем / спуск.</li>
        <li><b>Экранные кнопки:</b> Кнопки D-Pad в правом нижнем углу работают на любом устройстве!</li>
      </ul>
      <h4 style="color: #20ff70; margin-top: 10px;">💡 ПРИМЕРЫ ИДЕЙ ДЛЯ СОЗДАНИЯ:</h4>
      <ul>
        <li>«Создай лес и оленей»</li>
        <li>«Замок из кубов с высокими башнями»</li>
        <li>«Стая волков и стадо оленей» (волки охотятся, олени убегают!)</li>
        <li>«Дракон и единорог»</li>
        <li>«Боевые роботы»</li>
        <li>«Наполни мир жизнью»</li>
      </ul>
    </div>
    <div class="modal-footer">
      <button class="btn" onclick="closeHelpModal()">Понятно</button>
    </div>
  </div>
</div>

<script>
// Master State & Viewport Engine
const state = {
  camera: {
    pos: [0.0, 6.0, 18.0],
    target: [0.0, 1.0, 0.0],
    yaw: 0.0,
    pitch: 0.25,
    distance: 18.0,
    fov: 60.0
  },
  entities: [],
  creatures: [],
  rain: [],
  showRain: true,
  showWireframe: true,
  isMouseDown: false,
  mouseButton: 0,
  lastMouseX: 0,
  lastMouseY: 0,
  katakana: "01ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ".split("")
};

const canvas = document.getElementById("viewport");
const ctx = canvas.getContext("2d");
let animFrameId = null;

function resizeCanvas() {
  const container = document.getElementById("viewport-container");
  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
}
window.addEventListener("resize", resizeCanvas);
resizeCanvas();

// Render Loop
function render() {
  const w = canvas.width;
  const h = canvas.height;
  ctx.fillStyle = "#010703";
  ctx.fillRect(0, 0, w, h);

  // 1. Digital Rain in Background
  if (state.showRain && state.rain && state.rain.length > 0) {
    ctx.font = "12px Consolas, monospace";
    for (let drop of state.rain) {
      const colX = (drop.x / 120.0) * w;
      for (let i = 0; i < drop.len; i++) {
        const rowY = ((drop.y - i) / 60.0) * h;
        if (rowY >= 0 && rowY < h) {
          if (i === 0) {
            ctx.fillStyle = "rgba(220, 255, 220, 0.9)";
          } else if (i < 3) {
            ctx.fillStyle = "rgba(0, 255, 65, 0.7)";
          } else {
            ctx.fillStyle = "rgba(0, 80, 15, 0.3)";
          }
          const ch = state.katakana[(Math.floor(drop.x) + i * 5) % state.katakana.length];
          ctx.fillText(ch, colX, rowY);
        }
      }
      drop.y = (drop.y + drop.speed * 0.5) % 60;
    }
  }

  // 2. 3D Camera Projection Setup
  const cam = state.camera;
  const cy = Math.cos(cam.yaw);
  const sy = Math.sin(cam.yaw);
  const cp = Math.cos(cam.pitch);
  const sp = Math.sin(cam.pitch);

  const cx = cam.target[0] + cam.distance * cp * sy;
  const cyPos = cam.target[1] + cam.distance * sp;
  const cz = cam.target[2] + cam.distance * cp * cy;
  cam.pos = [cx, cyPos, cz];

  // Forward, Right, Up vectors
  let fx = cam.target[0] - cx;
  let fy = cam.target[1] - cyPos;
  let fz = cam.target[2] - cz;
  const flen = Math.hypot(fx, fy, fz) || 1.0;
  fx /= flen; fy /= flen; fz /= flen;

  let rx = fz; let ry = 0; let rz = -fx;
  const rlen = Math.hypot(rx, rz) || 1.0;
  rx /= rlen; rz /= rlen;

  const ux = ry * fz - rz * fy;
  const uy = rz * fx - rx * fz;
  const uz = rx * fy - ry * fx;

  const fovRad = (cam.fov * Math.PI) / 180.0;
  const fovScale = (h / 2.0) / Math.tan(fovRad / 2.0);

  function project(p) {
    const dx = p[0] - cx;
    const dy = p[1] - cyPos;
    const dz = p[2] - cz;

    const zCam = dx * fx + dy * fy + dz * fz;
    if (zCam <= 0.2) return null;

    const xCam = dx * rx + dy * ry + dz * rz;
    const yCam = dx * ux + dy * uy + dz * uz;

    const scrX = (w / 2.0) + (xCam / zCam) * fovScale;
    const scrY = (h / 2.0) - (yCam / zCam) * fovScale;
    return [scrX, scrY, zCam];
  }

  // 3. Render 3D Entities & Terrain Wireframes
  if (state.showWireframe && state.entities) {
    for (let ent of state.entities) {
      const col = ent.color || [0, 255, 65];
      ctx.strokeStyle = `rgba(${col[0]}, ${col[1]}, ${col[2]}, 0.85)`;
      ctx.lineWidth = ent.type === "terrain" ? 1 : 1.5;

      const projVerts = ent.vertices.map(v => project(v));

      ctx.beginPath();
      for (let e of ent.edges) {
        const p0 = projVerts[e[0]];
        const p1 = projVerts[e[1]];
        if (p0 && p1) {
          ctx.moveTo(p0[0], p0[1]);
          ctx.lineTo(p1[0], p1[1]);
        }
      }
      ctx.stroke();
    }
  }

  animFrameId = requestAnimationFrame(render);
}
animFrameId = requestAnimationFrame(render);

// Mouse Controls
const vpContainer = document.getElementById("viewport-container");
vpContainer.addEventListener("mousedown", (e) => {
  state.isMouseDown = true;
  state.mouseButton = e.button;
  state.lastMouseX = e.clientX;
  state.lastMouseY = e.clientY;
  e.preventDefault();
});
window.addEventListener("mouseup", () => {
  state.isMouseDown = false;
});
window.addEventListener("mousemove", (e) => {
  if (!state.isMouseDown) return;
  const dx = e.clientX - state.lastMouseX;
  const dy = e.clientY - state.lastMouseY;
  state.lastMouseX = e.clientX;
  state.lastMouseY = e.clientY;

  if (state.mouseButton === 0) {
    // Left drag: Orbit
    state.camera.yaw += dx * 0.008;
    state.camera.pitch = Math.max(-1.45, Math.min(1.45, state.camera.pitch - dy * 0.008));
  } else if (state.mouseButton === 2) {
    // Right drag: Pan
    const panSpeed = 0.03;
    state.camera.target[0] -= dx * panSpeed;
    state.camera.target[1] += dy * panSpeed;
  }
  updateHUD();
});
vpContainer.addEventListener("contextmenu", e => e.preventDefault());
vpContainer.addEventListener("wheel", (e) => {
  e.preventDefault();
  state.camera.distance = Math.max(2.0, Math.min(200.0, state.camera.distance + (e.deltaY > 0 ? 1.5 : -1.5)));
  updateHUD();
});

// Touch controls for mobile / tablet
let touchStartX = 0, touchStartY = 0;
vpContainer.addEventListener("touchstart", (e) => {
  if (e.touches.length === 1) {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }
});
vpContainer.addEventListener("touchmove", (e) => {
  if (e.touches.length === 1) {
    const dx = e.touches[0].clientX - touchStartX;
    const dy = e.touches[0].clientY - touchStartY;
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
    state.camera.yaw += dx * 0.01;
    state.camera.pitch = Math.max(-1.45, Math.min(1.45, state.camera.pitch - dy * 0.01));
    updateHUD();
    e.preventDefault();
  }
});

// Keyboard Controls (only when not typing in text field)
window.addEventListener("keydown", (e) => {
  if (document.activeElement && document.activeElement.tagName === "INPUT") return;
  const k = e.key.toLowerCase();
  if (k === "w") cameraMove(1.5, 0, 0);
  else if (k === "s") cameraMove(-1.5, 0, 0);
  else if (k === "a") cameraMove(0, -1.5, 0);
  else if (k === "d") cameraMove(0, 1.5, 0);
  else if (k === "e") cameraMove(0, 0, 1.5);
  else if (k === "c") cameraMove(0, 0, -1.5);
  else if (k === "arrowleft") cameraOrbit(-0.15, 0);
  else if (k === "arrowright") cameraOrbit(0.15, 0);
  else if (k === "arrowup") cameraOrbit(0, 0.15);
  else if (k === "arrowdown") cameraOrbit(0, -0.15);
  else if (k === "+" || k === "=") cameraZoom(-2.0);
  else if (k === "-" || k === "_") cameraZoom(2.0);
});

// Camera Operations
function cameraMove(f, r, u) {
  const cy = Math.cos(state.camera.yaw);
  const sy = Math.sin(state.camera.yaw);
  state.camera.target[0] += (-sy * f + cy * r);
  state.camera.target[2] += (-cy * f - sy * r);
  state.camera.target[1] += u;
  updateHUD();
  syncCameraServer();
}

function cameraOrbit(dy, dp) {
  state.camera.yaw += dy;
  state.camera.pitch = Math.max(-1.45, Math.min(1.45, state.camera.pitch + dp));
  updateHUD();
  syncCameraServer();
}

function cameraZoom(delta) {
  state.camera.distance = Math.max(2.0, Math.min(200.0, state.camera.distance + delta));
  updateHUD();
  syncCameraServer();
}

function resetCamera() {
  state.camera.pos = [0.0, 6.0, 18.0];
  state.camera.target = [0.0, 1.0, 0.0];
  state.camera.yaw = 0.0;
  state.camera.pitch = 0.25;
  state.camera.distance = 18.0;
  updateHUD();
  syncCameraServer();
}

function setCameraPreset(mode) {
  if (mode === 'top') {
    state.camera.pitch = 1.45;
    state.camera.distance = 25.0;
  } else if (mode === 'front') {
    state.camera.pitch = 0.05;
    state.camera.yaw = 0.0;
  } else if (mode === 'iso') {
    state.camera.pitch = 0.55;
    state.camera.yaw = 0.78;
  }
  updateHUD();
  syncCameraServer();
}

function toggleRain() {
  state.showRain = !state.showRain;
  document.getElementById("btn-rain").innerText = state.showRain ? "🌧️ Дождь [ВКЛ]" : "🌧️ Дождь [ВЫКЛ]";
}

function toggleWireframe() {
  state.showWireframe = !state.showWireframe;
  document.getElementById("btn-wf").innerText = state.showWireframe ? "🌐 Сетка [ВКЛ]" : "🌐 Сетка [ВЫКЛ]";
}

function updateHUD() {
  const c = state.camera;
  document.getElementById("hud-cam").innerText = `(${c.pos[0].toFixed(1)}, ${c.pos[1].toFixed(1)}, ${c.pos[2].toFixed(1)})`;
  document.getElementById("status-coords").innerText = `CAM: X=${c.pos[0].toFixed(1)} Y=${c.pos[1].toFixed(1)} Z=${c.pos[2].toFixed(1)}`;
}

function syncCameraServer() {
  fetch("/api/control", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({action: "camera", camera: state.camera})
  }).catch(()=>{});
}

// Server Communication & Sync
async function refreshState() {
  try {
    const res = await fetch("/api/state");
    const data = await res.json();
    state.entities = data.entities || [];
    state.creatures = data.creatures || [];
    state.rain = data.rain || [];

    document.getElementById("hud-fps").innerText = data.stats.fps;
    document.getElementById("hud-chunks").innerText = data.stats.chunks;
    document.getElementById("hud-entities").innerText = data.stats.entities;
    document.getElementById("hud-creatures").innerText = data.stats.creatures;

    // Active model badge
    const modelInfo = data.model;
    const badge = document.getElementById("lbl-active-model");
    if (modelInfo.is_simulated) {
      badge.innerText = "Встроенный процедурный Creator (Offline)";
      badge.style.color = "#00ff41";
    } else {
      badge.innerText = `${modelInfo.model_name} [${modelInfo.engine}]`;
      badge.style.color = "#ffffff";
    }

    // Stream text
    if (data.stream_text) {
      document.getElementById("stream-content").innerText = data.stream_text;
      const term = document.getElementById("terminal-stream");
      term.scrollTop = term.scrollHeight;
    }

    // Creatures table
    const tbody = document.getElementById("creatures-body");
    if (state.creatures.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#008f11;">Нет активных существ</td></tr>';
    } else {
      tbody.innerHTML = state.creatures.map(c => `
        <tr>
          <td><b>${c.name}</b></td>
          <td>${c.species}</td>
          <td><span class="badge-state">${c.fsm}</span></td>
          <td>(${c.pos.join(", ")})</td>
        </tr>
      `).join("");
    }

    // Entities list
    const elist = document.getElementById("entities-list");
    if (state.entities.length === 0) {
      elist.innerHTML = '<div style="padding: 6px; color: #008f11;">Объекты не созданы.</div>';
    } else {
      elist.innerHTML = state.entities.filter(e => e.type !== "terrain").slice(0, 30).map(e => `
        <div style="display:flex; justify-content:space-between; padding:3px 6px; border-bottom:1px solid #002200;">
          <span>[${e.type}] ${e.name}</span>
          <button class="btn" style="padding:1px 5px; font-size:10px;" onclick="deleteEntity(${e.id})">✕</button>
        </div>
      `).join("");
    }

  } catch(e) {
    console.warn("Sync failed:", e);
  }
}
setInterval(refreshState, 1000);
refreshState();

// Send Prompt
async function sendPrompt() {
  const input = document.getElementById("prompt-input");
  const text = input.value.trim();
  if (!text) return;

  document.getElementById("btn-send").disabled = true;
  document.getElementById("btn-send").innerText = "ГЕНЕРАЦИЯ...";
  document.getElementById("status-text").innerText = `ИИ СОЗДАТЕЛЬ МАТЕРИАЛИЗУЕТ: «${text}»...`;

  try {
    await fetch("/api/prompt", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({prompt: text})
    });
    // Poll stream
    pollStream();
  } catch(e) {
    alert("Ошибка отправки запроса: " + e);
  } finally {
    document.getElementById("btn-send").disabled = false;
    document.getElementById("btn-send").innerText = "⚡ МАТЕРИАЛИЗОВАТЬ (Enter)";
  }
}

function runPreset(promptText) {
  document.getElementById("prompt-input").value = promptText;
  sendPrompt();
}

function pollStream() {
  let count = 0;
  const timer = setInterval(async () => {
    count++;
    await refreshState();
    if (count > 25) clearInterval(timer);
  }, 300);
}

// Clear World
async function clearWorld() {
  await fetch("/api/clear", {method: "POST"});
  document.getElementById("stream-content").innerText = "Мир очищен.";
  await refreshState();
}

async function deleteEntity(id) {
  await fetch("/api/delete", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({id: id})
  });
  await refreshState();
}

// Modal Windows
function openModelModal() {
  document.getElementById("modal-model").style.display = "flex";
  scanModels();
}
function closeModelModal() {
  document.getElementById("modal-model").style.display = "none";
}
function openHelpModal() {
  document.getElementById("modal-help").style.display = "flex";
}
function closeHelpModal() {
  document.getElementById("modal-help").style.display = "none";
}
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(()=>{});
  } else {
    document.exitFullscreen().catch(()=>{});
  }
}

// Scan GGUF Models
async function scanModels() {
  const sel = document.getElementById("select-models");
  sel.innerHTML = '<option value="">Сканирование директории models...</option>';
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    if (!data.models || data.models.length === 0) {
      sel.innerHTML = '<option value="">Модели .gguf не обнаружены в папке models/</option>';
    } else {
      sel.innerHTML = data.models.map(m => `
        <option value="${m.path}">${m.name} (${m.size_mb} MB)</option>
      `).join("");
    }
  } catch(e) {
    sel.innerHTML = '<option value="">Ошибка сканирования</option>';
  }
}

// Apply Model Selection
async function applyModelSelection() {
  const isBuiltin = document.getElementById("mode-builtin").checked;
  const selectVal = document.getElementById("select-models").value;
  const manualPath = document.getElementById("manual-model-path").value.trim();
  const path = manualPath || selectVal;

  const nCtx = parseInt(document.getElementById("param-ctx").value) || 4096;
  const threads = parseInt(document.getElementById("param-threads").value) || 4;
  const gpu = parseInt(document.getElementById("param-gpu").value) || 0;
  const temp = parseFloat(document.getElementById("param-temp").value) || 0.2;

  const fb = document.getElementById("model-feedback");
  fb.innerText = "Загрузка модели...";
  fb.style.color = "#00ff41";

  try {
    const res = await fetch("/api/models/load", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        path: isBuiltin ? null : path,
        builtin: isBuiltin,
        n_ctx: nCtx,
        threads: threads,
        gpu: gpu,
        temperature: temp
      })
    });
    const data = await res.json();
    if (data.ok) {
      fb.innerText = "✓ " + data.message;
      fb.style.color = "#20ff70";
      setTimeout(closeModelModal, 1200);
      refreshState();
    } else {
      fb.innerText = "✕ " + data.message;
      fb.style.color = "#ff4141";
    }
  } catch(e) {
    fb.innerText = "✕ Ошибка сети: " + e;
    fb.style.color = "#ff4141";
  }
}

// File Upload Handler
async function handleFileUpload(files) {
  if (!files || files.length === 0) return;
  const file = files[0];
  const status = document.getElementById("upload-status");
  status.innerText = `Загрузка ${file.name} (${(file.size / (1024*1024)).toFixed(1)} MB)...`;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/models/upload", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (data.ok) {
      status.innerText = `✓ Файл ${file.name} успешно загружен в models/!`;
      document.getElementById("manual-model-path").value = data.path;
      scanModels();
    } else {
      status.innerText = "✕ Ошибка загрузки: " + data.message;
    }
  } catch(e) {
    status.innerText = "✕ Ошибка соединения: " + e;
  }
}
</script>
</body>
</html>
"""


class HolographicHTTPHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP handler for Holographic Matrix GUI and REST API."""

    app_state: AppState

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy request logs."""
        pass

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/" or url.path == "/index.html":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        if url.path == "/api/state":
            data = self.app_state.get_serialized_state()
            self._send_json(data)
            return

        if url.path == "/api/models":
            models = find_gguf_models()
            self._send_json({"models": models, "current": self.app_state.llm.get_model_info()})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Path not found")

    def do_POST(self) -> None:
        url = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))

        if url.path == "/api/prompt":
            body = self.rfile.read(content_len)
            req = json.loads(body.decode("utf-8"))
            prompt = req.get("prompt", "")
            self.app_state.run_prompt_thread(prompt)
            self._send_json({"ok": True, "prompt": prompt})
            return

        if url.path == "/api/control":
            body = self.rfile.read(content_len)
            req = json.loads(body.decode("utf-8"))
            cam_data = req.get("camera", {})
            with self.app_state.lock:
                if "yaw" in cam_data:
                    self.app_state.camera.yaw = cam_data["yaw"]
                if "pitch" in cam_data:
                    self.app_state.camera.pitch = cam_data["pitch"]
                if "distance" in cam_data:
                    self.app_state.camera.distance = cam_data["distance"]
                if "target" in cam_data and len(cam_data["target"]) >= 3:
                    t = cam_data["target"]
                    self.app_state.camera.target = Vec3(t[0], t[1], t[2])
            self._send_json({"ok": True})
            return

        if url.path == "/api/clear":
            with self.app_state.lock:
                for eid in list(self.app_state.world.entities.keys()):
                    self.app_state.world.remove_entity(eid)
                self.app_state.stream_buffer.clear()
            self._send_json({"ok": True})
            return

        if url.path == "/api/delete":
            body = self.rfile.read(content_len)
            req = json.loads(body.decode("utf-8"))
            eid = req.get("id")
            with self.app_state.lock:
                if eid:
                    self.app_state.world.remove_entity(eid)
            self._send_json({"ok": True})
            return

        if url.path == "/api/models/load":
            body = self.rfile.read(content_len)
            req = json.loads(body.decode("utf-8"))
            is_builtin = req.get("builtin", False)
            path = req.get("path")
            n_ctx = int(req.get("n_ctx", 4096))
            threads = int(req.get("threads", 4))
            gpu = int(req.get("gpu", 0))
            temp = float(req.get("temperature", 0.2))

            with self.app_state.lock:
                if is_builtin or not path:
                    ok, msg = self.app_state.llm.load_model(None)
                else:
                    ok, msg = self.app_state.llm.load_model(
                        model_path=path,
                        n_ctx=n_ctx,
                        n_threads=threads,
                        n_gpu_layers=gpu,
                        temperature=temp,
                    )
            self._send_json({"ok": ok, "message": msg, "info": self.app_state.llm.get_model_info()})
            return

        if url.path == "/api/models/upload":
            ctype = self.headers.get("Content-Type", "")
            if "multipart/form-data" in ctype:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={
                        "REQUEST_METHOD": "POST",
                        "CONTENT_TYPE": ctype,
                    },
                )
                if "file" in form and form["file"].filename:
                    item = form["file"]
                    fname = os.path.basename(item.filename)
                    os.makedirs("models", exist_ok=True)
                    out_path = os.path.join("models", fname)
                    with open(out_path, "wb") as f:
                        f.write(item.file.read())
                    self._send_json({"ok": True, "path": out_path, "name": fname})
                    return
            self._send_json({"ok": False, "message": "Файл не получен"})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Path not found")

    def _send_json(self, data: Any) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run_gui_server(host: str = "0.0.0.0", port: int = 8000, model_path: str | None = None) -> None:
    """Launch background 30 FPS world simulation and HTTP GUI server."""
    app_state = AppState(model_path=model_path)
    HolographicHTTPHandler.app_state = app_state

    # Background simulation thread
    def sim_loop():
        while True:
            app_state.update_sim()
            time.sleep(0.033)

    threading.Thread(target=sim_loop, daemon=True).start()

    server = ThreadingHTTPServer((host, port), HolographicHTTPHandler)
    print(f"\n[+] AI CREATOR — HOLOGRAPHIC MATRIX SANDBOX")
    print(f"[*] GUI Server listening at: http://{host}:{port}")
    print(f"[*] Press Ctrl+C to terminate.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down GUI server.")
        server.server_close()
