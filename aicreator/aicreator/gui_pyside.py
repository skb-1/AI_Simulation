"""PySide6 / PyQt Holographic Matrix Desktop GUI Application.

Provides a full native desktop window with:
- Cyberpunk Matrix holographic glowing QSS theme
- Model Selection Dialog for GGUF model files (file dialog, params, hot-reload)
- Interactive 3D Holographic Viewport with working mouse controls (drag-orbit, pan, wheel-zoom)
- Left Dock: AI Creator prompt terminal with quick presets and token stream
- Right Dock: World entities inspector & live creature FSM state tracker
"""

from __future__ import annotations

import math
import os
import sys
import threading
import time
from typing import Any

# Try importing PySide6, PyQt6, or PyQt5
QT_LIB = None
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, QTimer, Signal, Slot
    from PySide6.QtGui import QColor, QFont, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QDockWidget,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QSlider,
        QSpinBox,
        QDoubleSpinBox,
        QSplitter,
        QStatusBar,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    QT_LIB = "PySide6"
except ImportError:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal, pyqtSlot as Slot
        from PyQt6.QtGui import QColor, QFont, QPainter, QPen
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QDialog,
            QDockWidget,
            QFileDialog,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QRadioButton,
            QSlider,
            QSpinBox,
            QDoubleSpinBox,
            QSplitter,
            QStatusBar,
            QTableWidget,
            QTableWidgetItem,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
        QT_LIB = "PyQt6"
    except ImportError:
        QT_LIB = None

from aicreator.commands import parse_commands_json
from aicreator.entities import WorldCreature, WorldPrimitive
from aicreator.llm import CreatorLLM, find_gguf_models
from aicreator.world import World
from matrixholo.camera import Camera
from matrixholo.glyphs import RAIN_CHARS
from matrixholo.rain import DigitalRain
from matrixholo.scene import Scene
from matrixholo.vec import Vec3

MATRIX_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #030d05;
    color: #00ff41;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
}
QMenuBar {
    background-color: #051408;
    color: #00ff41;
    border-bottom: 1px solid #00ff41;
    padding: 4px;
}
QMenuBar::item:selected {
    background-color: #003b00;
    color: #ffffff;
}
QMenu {
    background-color: #051408;
    color: #00ff41;
    border: 1px solid #00ff41;
}
QMenu::item:selected {
    background-color: #008f11;
    color: #000000;
}
QDockWidget {
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    color: #00ff41;
    font-weight: bold;
    border: 1px solid #008f11;
}
QDockWidget::title {
    background: #051408;
    border-bottom: 1px solid #00ff41;
    padding: 6px;
    text-align: left;
}
QLineEdit, QTextEdit, QTableWidget, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #020904;
    color: #00ff41;
    border: 1px solid #008f11;
    padding: 6px;
    selection-background-color: #008f11;
    selection-color: #000000;
}
QLineEdit:focus, QTextEdit:focus, QTableWidget:focus {
    border: 1px solid #00ff41;
    background-color: #031206;
}
QPushButton {
    background-color: #002b06;
    color: #00ff41;
    border: 1px solid #00ff41;
    padding: 6px 12px;
    font-weight: bold;
    border-radius: 2px;
}
QPushButton:hover {
    background-color: #00ff41;
    color: #000000;
}
QPushButton:pressed {
    background-color: #008f11;
    color: #000000;
}
QStatusBar {
    background-color: #051408;
    color: #00ff41;
    border-top: 1px solid #008f11;
}
QGroupBox {
    border: 1px solid #008f11;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #00ff41;
}
"""


if QT_LIB is not None:

    class ModelSelectionDialog(QDialog):
        """Dialog to browse, inspect, and hot-reload local GGUF models."""

        def __init__(self, llm: CreatorLLM, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.llm = llm
            self.setWindowTitle("Выбор модели GGUF — AI Creator")
            self.setMinimumWidth(560)
            self.setStyleSheet(MATRIX_QSS)

            layout = QVBoxLayout(self)

            header = QLabel("<h3>📁 ВЫБОР И ЗАГРУЗКА GGUF МОДЕЛИ</h3>")
            layout.addWidget(header)

            desc = QLabel(
                "Выберите квантованную GGUF модель для локальной генерации на CPU/GPU.\n"
                "Если файл не выбран, работает встроенный процедурный ИИ Создатель."
            )
            desc.setStyleSheet("color: #008f11;")
            layout.addWidget(desc)

            # Engine choice
            grp_engine = QGroupBox("Режим движка ИИ")
            eng_layout = QVBoxLayout(grp_engine)
            self.rad_gguf = QRadioButton("Локальная GGUF модель (llama-cpp-python)")
            self.rad_builtin = QRadioButton("Встроенный процедурный Creator (Offline Fallback)")
            if self.llm.is_simulated and not self.llm.model_path:
                self.rad_builtin.setChecked(True)
            else:
                self.rad_gguf.setChecked(True)
            eng_layout.addWidget(self.rad_gguf)
            eng_layout.addWidget(self.rad_builtin)
            layout.addWidget(grp_engine)

            # Model files dropdown
            grp_model = QGroupBox("Файл модели")
            m_layout = QVBoxLayout(grp_model)

            h_file = QHBoxLayout()
            self.combo_models = QComboBox()
            self.btn_refresh = QPushButton("🔄 Обновить")
            self.btn_refresh.clicked.connect(self.populate_models)
            h_file.addWidget(self.combo_models, stretch=1)
            h_file.addWidget(self.btn_refresh)
            m_layout.addLayout(h_file)

            h_browse = QHBoxLayout()
            self.line_custom_path = QLineEdit()
            self.line_custom_path.setPlaceholderText("Или укажите путь к файлу .gguf...")
            self.btn_browse = QPushButton("📁 Обзор...")
            self.btn_browse.clicked.connect(self.browse_model_file)
            h_browse.addWidget(self.line_custom_path, stretch=1)
            h_browse.addWidget(self.btn_browse)
            m_layout.addLayout(h_browse)

            layout.addWidget(grp_model)

            # Parameters
            grp_params = QGroupBox("Параметры инференса")
            p_layout = QFormLayout(grp_params)

            self.spin_ctx = QSpinBox()
            self.spin_ctx.setRange(512, 32768)
            self.spin_ctx.setSingleStep(512)
            self.spin_ctx.setValue(self.llm.n_ctx)
            p_layout.addRow("Контекст (n_ctx):", self.spin_ctx)

            self.spin_threads = QSpinBox()
            self.spin_threads.setRange(1, 32)
            self.spin_threads.setValue(self.llm.threads)
            p_layout.addRow("Потоки CPU:", self.spin_threads)

            self.spin_gpu = QSpinBox()
            self.spin_gpu.setRange(0, 99)
            self.spin_gpu.setValue(0)
            p_layout.addRow("Слои GPU (0 = CPU):", self.spin_gpu)

            self.spin_temp = QDoubleSpinBox()
            self.spin_temp.setRange(0.05, 2.0)
            self.spin_temp.setSingleStep(0.05)
            self.spin_temp.setValue(self.llm.temperature)
            p_layout.addRow("Температура:", self.spin_temp)

            layout.addWidget(grp_params)

            # Status label
            self.lbl_status = QLabel()
            self.update_status_label()
            layout.addWidget(self.lbl_status)

            # Buttons
            h_btns = QHBoxLayout()
            self.btn_load = QPushButton("⚡ ЗАГРУЗИТЬ МОДЕЛЬ")
            self.btn_load.clicked.connect(self.apply_model)
            self.btn_close = QPushButton("Закрыть")
            self.btn_close.clicked.connect(self.accept)
            h_btns.addWidget(self.btn_load)
            h_btns.addWidget(self.btn_close)
            layout.addLayout(h_btns)

            self.populate_models()

        def update_status_label(self) -> None:
            info = self.llm.get_model_info()
            if info["is_simulated"]:
                self.lbl_status.setText("Текущий статус: [Встроенный процедурный Creator]")
                self.lbl_status.setStyleSheet("color: #00ff41; font-weight: bold;")
            else:
                self.lbl_status.setText(f"Текущий статус: [GGUF: {info['model_name']}]")
                self.lbl_status.setStyleSheet("color: #20ff70; font-weight: bold;")

        def populate_models(self) -> None:
            self.combo_models.clear()
            models = find_gguf_models()
            if not models:
                self.combo_models.addItem("Модели .gguf не найдены в ./models", "")
            else:
                for m in models:
                    label = f"{m['name']} ({m['size_mb']} MB)"
                    self.combo_models.addItem(label, m["path"])

        def browse_model_file(self) -> None:
            fn, _ = QFileDialog.getOpenFileName(
                self, "Выберите файл GGUF модели", ".", "GGUF Models (*.gguf);;All Files (*)"
            )
            if fn:
                self.line_custom_path.setText(fn)

        def apply_model(self) -> None:
            if self.rad_builtin.isChecked():
                ok, msg = self.llm.load_model(None)
                QMessageBox.information(self, "AI Engine", msg)
                self.update_status_label()
                return

            path = self.line_custom_path.text().strip()
            if not path:
                path = self.combo_models.currentData()

            if not path or not os.path.isfile(path):
                QMessageBox.warning(
                    self, "Ошибка", "Укажите существующий путь к файлу .gguf!"
                )
                return

            self.btn_load.setEnabled(False)
            self.btn_load.setText("Загрузка...")
            QApplication.processEvents()

            ok, msg = self.llm.load_model(
                model_path=path,
                n_ctx=self.spin_ctx.value(),
                n_threads=self.spin_threads.value(),
                n_gpu_layers=self.spin_gpu.value(),
                temperature=self.spin_temp.value(),
            )
            self.btn_load.setEnabled(True)
            self.btn_load.setText("⚡ ЗАГРУЗИТЬ МОДЕЛЬ")
            self.update_status_label()

            if ok:
                QMessageBox.information(self, "Успех", msg)
            else:
                QMessageBox.critical(self, "Ошибка загрузки", msg)

    class HolographicViewport(QWidget):
        """Interactive 3D Holographic Viewport with working mouse and keyboard controls."""

        def __init__(self, world: World, camera: Camera, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.world = world
            self.camera = camera
            self.rain = DigitalRain(width=100, height=50)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setMouseTracking(True)

            self.last_mouse_pos = None
            self.mouse_pressed_button = None

            # Render loop timer (30 FPS)
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(33)

            self.last_time = time.time()
            self.fps = 30.0
            self.show_rain = True
            self.show_wireframe = True

        def update_frame(self) -> None:
            now = time.time()
            dt = max(0.001, min(0.1, now - self.last_time))
            self.last_time = now
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)

            # Update world and creatures
            self.world.update(dt, self.camera.pos)
            if self.show_rain:
                self.rain.update(dt)

            self.update()

        # Mouse controls: Left Drag = Orbit, Right Drag = Pan, Wheel = Zoom
        def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
            self.last_mouse_pos = event.position()
            self.mouse_pressed_button = event.button()
            self.setFocus()

        def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
            self.last_mouse_pos = None
            self.mouse_pressed_button = None

        def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
            if self.last_mouse_pos is None:
                return
            curr_pos = event.position()
            dx = curr_pos.x() - self.last_mouse_pos.x()
            dy = curr_pos.y() - self.last_mouse_pos.y()
            self.last_mouse_pos = curr_pos

            if self.mouse_pressed_button == Qt.MouseButton.LeftButton:
                # Orbit camera
                self.camera.orbit(dx * 0.01, -dy * 0.01)
            elif self.mouse_pressed_button == Qt.MouseButton.RightButton:
                # Pan camera
                self.camera.move(0.0, -dx * 0.05, dy * 0.05)

        def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
            delta = event.angleDelta().y()
            if delta > 0:
                self.camera.zoom(-1.5)
            else:
                self.camera.zoom(1.5)

        # Keyboard controls
        def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
            k = event.key()
            if k == Qt.Key.Key_W:
                self.camera.move(1.0, 0.0)
            elif k == Qt.Key.Key_S:
                self.camera.move(-1.0, 0.0)
            elif k == Qt.Key.Key_A:
                self.camera.move(0.0, -1.0)
            elif k == Qt.Key.Key_D:
                self.camera.move(0.0, 1.0)
            elif k == Qt.Key.Key_E:
                self.camera.move(0.0, 0.0, 1.0)
            elif k == Qt.Key.Key_C:
                self.camera.move(0.0, 0.0, -1.0)
            elif k == Qt.Key.Key_Left:
                self.camera.orbit(-0.1, 0.0)
            elif k == Qt.Key.Key_Right:
                self.camera.orbit(0.1, 0.0)
            elif k == Qt.Key.Key_Up:
                self.camera.orbit(0.0, 0.1)
            elif k == Qt.Key.Key_Down:
                self.camera.orbit(0.0, -0.1)
            elif k in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.camera.zoom(-2.0)
            elif k in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore):
                self.camera.zoom(2.0)

        def paintEvent(self, event: QtGui.QPaintEvent) -> None:
            painter = QPainter(self)
            w = self.width()
            h = self.height()

            # Background deep black/emerald
            painter.fillRect(0, 0, w, h, QColor(2, 9, 4))

            # 1. Render Matrix Digital Rain
            if self.show_rain:
                painter.setFont(QFont("Consolas", 10))
                for drop in self.rain.drops:
                    col_x = int((drop.col / 100.0) * w)
                    for i in range(drop.length):
                        row_y = int(((drop.y - i) / 50.0) * h)
                        if 0 <= row_y < h:
                            if i == 0:
                                painter.setPen(QColor(220, 255, 220, 240))
                            elif i < 3:
                                painter.setPen(QColor(0, 255, 65, 180))
                            else:
                                painter.setPen(QColor(0, 100, 15, 80))
                            ch = RAIN_CHARS[(drop.col + i * 3) % len(RAIN_CHARS)]
                            painter.drawText(col_x, row_y, ch)

            # 2. Render 3D Scene Wireframes
            aspect = float(w) / max(1.0, float(h))
            vp_mat = self.camera.get_view_projection(aspect)

            def project_point(p: Vec3) -> tuple[int, int, float] | None:
                # Manual multiply: vp_mat @ p
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
                ndc_z = clip_z / clip_w

                if abs(ndc_x) > 1.8 or abs(ndc_y) > 1.8:
                    return None

                scr_x = int((ndc_x * 0.5 + 0.5) * w)
                scr_y = int((-ndc_y * 0.5 + 0.5) * h)
                return scr_x, scr_y, ndc_z

            # Render scene entities
            if self.show_wireframe:
                for entity in self.world.holo_scene.entities.values():
                    if not entity.visible:
                        continue
                    mesh = entity.mesh
                    tf = entity.get_model_matrix()
                    pts = [tf.transform_point(v) for v in mesh.vertices]
                    proj_pts = [project_point(p) for p in pts]

                    col = mesh.color
                    pen = QPen(QColor(col[0], col[1], col[2], 220))
                    pen.setWidth(1)
                    painter.setPen(pen)

                    for e0, e1 in mesh.edges:
                        if e0 < len(proj_pts) and e1 < len(proj_pts):
                            p0 = proj_pts[e0]
                            p1 = proj_pts[e1]
                            if p0 is not None and p1 is not None:
                                painter.drawLine(p0[0], p0[1], p1[0], p1[1])

            # 3. Holographic HUD Overlays
            painter.setPen(QColor(0, 255, 65, 230))
            painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            hud_text = [
                f"FPS: {self.fps:.1f}",
                f"ENTITIES: {len(self.world.entities)}",
                f"CREATURES: {sum(1 for e in self.world.entities.values() if isinstance(e, WorldCreature))}",
                f"CHUNKS: {len(self.world.chunks)}",
                f"CAM: ({self.camera.pos.x:.1f}, {self.camera.pos.y:.1f}, {self.camera.pos.z:.1f})",
                "CONTROLS: L-Drag = Orbit, R-Drag = Pan, Wheel = Zoom, WASD = Move",
            ]
            y_offset = 20
            for line in hud_text:
                painter.drawText(15, y_offset, line)
                y_offset += 16

    class MainWindow(QMainWindow):
        """Main PySide6 Window with dockable panels, menus, and controls."""

        token_received = Signal(str)
        generation_finished = Signal()

        def __init__(self, model_path: str | None = None) -> None:
            super().__init__()
            self.setWindowTitle("AI CREATOR — HOLOGRAPHIC MATRIX SANDBOX (PySide6)")
            self.resize(1280, 800)
            self.setStyleSheet(MATRIX_QSS)

            # Engines
            self.llm = CreatorLLM(model_path)
            self.scene = Scene()
            self.camera = Camera(pos=(0.0, 6.0, 18.0), target=(0.0, 1.0, 0.0))
            self.world = World(self.scene)
            self.world.update_chunks_around(self.camera.pos)

            self.token_received.connect(self.on_token_received)
            self.generation_finished.connect(self.on_generation_finished)

            self.init_ui()

        def init_ui(self) -> None:
            # Central 3D Viewport
            self.viewport = HolographicViewport(self.world, self.camera, self)
            self.setCentralWidget(self.viewport)

            # Menus
            menubar = self.menuBar()

            m_file = menubar.addMenu("📁 Файл")
            act_clear = m_file.addAction("🧹 Очистить мир")
            act_clear.triggered.connect(self.clear_world)
            m_file.addSeparator()
            act_exit = m_file.addAction("Выход")
            act_exit.triggered.connect(self.close)

            m_models = menubar.addMenu("🧠 Модели GGUF")
            act_choose_model = m_models.addAction("📁 Выбрать / Загрузить модель...")
            act_choose_model.triggered.connect(self.open_model_dialog)

            m_view = menubar.addMenu("👁️ Вид")
            act_reset_cam = m_view.addAction("🔄 Сбросить камеру")
            act_reset_cam.triggered.connect(self.reset_camera)
            act_toggle_rain = m_view.addAction("🌧️ Матричный дождь (вкл/выкл)")
            act_toggle_rain.triggered.connect(self.toggle_rain)

            # Left Dock: AI Prompt Terminal
            dock_prompt = QDockWidget("AI CREATOR — ТЕРМИНАЛ МАТЕРИАЛИЗАЦИИ", self)
            dock_prompt.setAllowedAreas(
                Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
            )

            w_prompt = QWidget()
            l_prompt = QVBoxLayout(w_prompt)

            # Model status badge
            self.lbl_model_badge = QLabel()
            self.update_model_badge()
            l_prompt.addWidget(self.lbl_model_badge)

            btn_open_model = QPushButton("📁 Выбрать GGUF Модель")
            btn_open_model.clicked.connect(self.open_model_dialog)
            l_prompt.addWidget(btn_open_model)

            # Prompt input
            l_prompt.addWidget(QLabel("<b>Идея для создания мира:</b>"))
            self.input_prompt = QLineEdit()
            self.input_prompt.setPlaceholderText("Например: «Создай лес и оленей» или «Замок из кубов»...")
            self.input_prompt.returnPressed.connect(self.send_prompt)
            l_prompt.addWidget(self.input_prompt)

            self.btn_send = QPushButton("⚡ МАТЕРИАЛИЗОВАТЬ (Enter)")
            self.btn_send.clicked.connect(self.send_prompt)
            l_prompt.addWidget(self.btn_send)

            # Quick Presets
            grp_presets = QGroupBox("Быстрые пресеты")
            l_presets = QVBoxLayout(grp_presets)

            presets = [
                ("🌲 Лес и олени", "Создай лес и оленей"),
                ("🏰 Замок из кубов", "Замок из кубов"),
                ("🐺 Стая волков и оленей", "Стая волков и оленей"),
                ("🐉 Дракон и единорог", "Дракон и единорог"),
                ("🤖 Боевые роботы", "Боевые роботы"),
                ("👥 Наполни мир жизнью", "Наполни мир жизнью"),
            ]
            for title, p_text in presets:
                btn = QPushButton(title)
                btn.clicked.connect(lambda _, t=p_text: self.run_preset(t))
                l_presets.addWidget(btn)
            l_prompt.addWidget(grp_presets)

            # Stream output
            l_prompt.addWidget(QLabel("<b>Поток генерации ИИ (GBNF JSON):</b>"))
            self.txt_stream = QTextEdit()
            self.txt_stream.setReadOnly(True)
            self.txt_stream.setMaximumHeight(180)
            l_prompt.addWidget(self.txt_stream)

            # Navigation buttons (touch / click controls)
            grp_nav = QGroupBox("Управление камерой (Кнопки)")
            l_nav = QVBoxLayout(grp_nav)
            h_nav1 = QHBoxLayout()
            btn_fw = QPushButton("▲ Вперед (W)")
            btn_fw.clicked.connect(lambda: self.camera.move(2.0, 0.0))
            h_nav1.addWidget(btn_fw)
            l_nav.addLayout(h_nav1)

            h_nav2 = QHBoxLayout()
            btn_left = QPushButton("◄ Влево (A)")
            btn_left.clicked.connect(lambda: self.camera.move(0.0, -2.0))
            btn_bk = QPushButton("▼ Назад (S)")
            btn_bk.clicked.connect(lambda: self.camera.move(-2.0, 0.0))
            btn_rt = QPushButton("► Вправо (D)")
            btn_rt.clicked.connect(lambda: self.camera.move(0.0, 2.0))
            h_nav2.addWidget(btn_left)
            h_nav2.addWidget(btn_bk)
            h_nav2.addWidget(btn_rt)
            l_nav.addLayout(h_nav2)

            h_nav3 = QHBoxLayout()
            btn_zin = QPushButton("🔍 Zoom +")
            btn_zin.clicked.connect(lambda: self.camera.zoom(-2.5))
            btn_zout = QPushButton("🔎 Zoom -")
            btn_zout.clicked.connect(lambda: self.camera.zoom(2.5))
            btn_reset = QPushButton("🔄 Сброс")
            btn_reset.clicked.connect(self.reset_camera)
            h_nav3.addWidget(btn_zin)
            h_nav3.addWidget(btn_zout)
            h_nav3.addWidget(btn_reset)
            l_nav.addLayout(h_nav3)

            l_prompt.addWidget(grp_nav)

            dock_prompt.setWidget(w_prompt)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_prompt)

            # Right Dock: World Inspector
            dock_inspector = QDockWidget("ИНСПЕКТОР МИРА И ИИ СУЩЕСТВ", self)
            w_insp = QWidget()
            l_insp = QVBoxLayout(w_insp)

            l_insp.addWidget(QLabel("<b>Существа и поведение (FSM):</b>"))
            self.tbl_creatures = QTableWidget(0, 4)
            self.tbl_creatures.setHorizontalHeaderLabels(["Имя", "Вид", "FSM Состояние", "Позиция"])
            self.tbl_creatures.horizontalHeader().setStretchLastSection(True)
            l_insp.addWidget(self.tbl_creatures)

            btn_clear_all = QPushButton("🧹 Очистить мир")
            btn_clear_all.clicked.connect(self.clear_world)
            l_insp.addWidget(btn_clear_all)

            dock_inspector.setWidget(w_insp)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_inspector)

            # Status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("AI Creator готов. Выберите модель или введите идею.")

            # Periodic update of inspector table
            self.insp_timer = QTimer(self)
            self.insp_timer.timeout.connect(self.update_inspector)
            self.insp_timer.start(500)

        def update_model_badge(self) -> None:
            info = self.llm.get_model_info()
            if info["is_simulated"]:
                self.lbl_model_badge.setText("🤖 ДВИЖОК: Встроенный процедурный")
                self.lbl_model_badge.setStyleSheet(
                    "background: #051a08; border: 1px solid #008f11; color: #00ff41; padding: 4px; font-weight: bold;"
                )
            else:
                self.lbl_model_badge.setText(f"🧠 ДВИЖОК: {info['model_name']} (CPU)")
                self.lbl_model_badge.setStyleSheet(
                    "background: #032b0a; border: 1px solid #00ff41; color: #ffffff; padding: 4px; font-weight: bold;"
                )

        def open_model_dialog(self) -> None:
            dlg = ModelSelectionDialog(self.llm, self)
            dlg.exec()
            self.update_model_badge()

        def reset_camera(self) -> None:
            self.camera.pos = Vec3(0.0, 6.0, 18.0)
            self.camera.target = Vec3(0.0, 1.0, 0.0)
            self.camera.distance = 18.0
            self.camera.yaw = 0.0
            self.camera.pitch = 0.3

        def toggle_rain(self) -> None:
            self.viewport.show_rain = not self.viewport.show_rain

        def clear_world(self) -> None:
            for eid in list(self.world.entities.keys()):
                self.world.remove_entity(eid)
            self.txt_stream.clear()
            self.status_bar.showMessage("Мир очищен.")

        def run_preset(self, prompt: str) -> None:
            self.input_prompt.setText(prompt)
            self.send_prompt()

        def send_prompt(self) -> None:
            text = self.input_prompt.text().strip()
            if not text:
                return
            self.btn_send.setEnabled(False)
            self.txt_stream.clear()
            self.status_bar.showMessage(f"ИИ Создатель генерирует: «{text}»...")

            # Run in worker thread
            def worker():
                accumulated = []
                for chunk in self.llm.stream_generate(text):
                    accumulated.append(chunk)
                    self.token_received.emit(chunk)

                full_json = "".join(accumulated)
                try:
                    commands = parse_commands_json(full_json)
                    self.world.apply_commands(commands)
                except Exception as e:
                    pass
                self.generation_finished.emit()

            threading.Thread(target=worker, daemon=True).start()

        @Slot(str)
        def on_token_received(self, chunk: str) -> None:
            self.txt_stream.insertPlainText(chunk)
            # Auto scroll to bottom
            sb = self.txt_stream.verticalScrollBar()
            sb.setValue(sb.maximum())

        @Slot()
        def on_generation_finished(self) -> None:
            self.btn_send.setEnabled(True)
            self.status_bar.showMessage(
                f"Генерация завершена. Всего сущностей: {len(self.world.entities)}"
            )

        def update_inspector(self) -> None:
            creatures = [
                e for e in self.world.entities.values() if isinstance(e, WorldCreature)
            ]
            self.tbl_creatures.setRowCount(len(creatures))
            for row, c in enumerate(creatures):
                self.tbl_creatures.setItem(row, 0, QTableWidgetItem(c.name))
                self.tbl_creatures.setItem(row, 1, QTableWidgetItem(c.species))
                self.tbl_creatures.setItem(row, 2, QTableWidgetItem(getattr(c, "state", "IDLE")))
                pos_str = f"({c.position.x:.1f}, {c.position.y:.1f}, {c.position.z:.1f})"
                self.tbl_creatures.setItem(row, 3, QTableWidgetItem(pos_str))


def run_pyside_app(model_path: str | None = None) -> int:
    """Launch the native PySide6 / PyQt Holographic application."""
    if QT_LIB is None:
        print("[!] PySide6 or PyQt is not installed in the current environment.")
        print("    Install PySide6 with: pip install PySide6")
        return 1

    app = QApplication(sys.argv)
    window = MainWindow(model_path=model_path)
    window.show()
    return app.exec()
