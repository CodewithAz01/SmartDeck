import sys
import threading
from datetime import datetime

import keyboard

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush, QPen, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QFrame,
    QSizePolicy,
    QSpacerItem,
    QGraphicsDropShadowEffect,
)


# ─────────────────────────── Animated Status Dot ────────────────────────────

class PulseDot(QWidget):
    """A pulsing dot indicator for live / stopped status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._active = False
        self._opacity = 1.0

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._tick)
        self._phase = 0.0

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._pulse_timer.start(40)
        else:
            self._pulse_timer.stop()
            self._opacity = 1.0
            self.update()

    def _tick(self):
        import math
        self._phase += 0.12
        self._opacity = 0.45 + 0.55 * abs(math.sin(self._phase))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#00e676") if self._active else QColor("#ff5252")
        color.setAlphaF(self._opacity)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 12, 12)


# ─────────────────────────── Action Flash Card ──────────────────────────────

class ActionCard(QFrame):
    """Bottom strip that briefly flashes the last action."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.06);
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.10);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)

        self._icon = QLabel("—")
        self._icon.setFont(QFont("Segoe UI Emoji", 18))
        self._icon.setFixedWidth(32)

        self._label = QLabel("No action yet")
        self._label.setFont(QFont("Consolas", 12))
        self._label.setStyleSheet("color: rgba(255,255,255,0.45);")

        layout.addWidget(self._icon)
        layout.addSpacing(8)
        layout.addWidget(self._label)
        layout.addStretch()

        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._reset)

    def flash(self, icon: str, text: str, color: str):
        self._icon.setText(icon)
        self._label.setText(text)
        self._label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.10);
                border-radius: 12px;
                border: 1px solid {color};
            }}
        """)
        self._fade_timer.start(2200)

    def _reset(self):
        self._icon.setText("—")
        self._label.setText("Waiting for input…")
        self._label.setStyleSheet("color: rgba(255,255,255,0.45);")
        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.06);
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.10);
            }
        """)


# ─────────────────────────── Main Window ────────────────────────────────────

class PowerPointRemote(QWidget):

    # Signals are the correct way to update UI from non-Qt threads.
    log_signal = pyqtSignal(str, str)
    action_signal = pyqtSignal(str, str, str)   # icon, text, color

    # Key mappings: media-key name → (direction, arrow-key, log-text, icon, color)
    KEY_MAP = {
        # Next slide
        "next track":        ("next",  "right", "NEXT SLIDE",     "▶▶", "#00e676"),
        "media next":        ("next",  "right", "NEXT SLIDE",     "▶▶", "#00e676"),
        "next":              ("next",  "right", "NEXT SLIDE",     "▶▶", "#00e676"),
        # Previous slide
        "previous track":    ("prev",  "left",  "PREVIOUS SLIDE", "◀◀", "#40c4ff"),
        "media previous":    ("prev",  "left",  "PREVIOUS SLIDE", "◀◀", "#40c4ff"),
        "prev track":        ("prev",  "left",  "PREVIOUS SLIDE", "◀◀", "#40c4ff"),
        "previous":          ("prev",  "left",  "PREVIOUS SLIDE", "◀◀", "#40c4ff"),
        # Play / Pause (toggle fullscreen presentation mode F5 / Escape)
        "play/pause media":  ("pp",    None,    "PLAY / PAUSE",   "⏯",  "#ffd740"),
        "media play pause":  ("pp",    None,    "PLAY / PAUSE",   "⏯",  "#ffd740"),
        "play/pause":        ("pp",    None,    "PLAY / PAUSE",   "⏯",  "#ffd740"),
    }

    def __init__(self):
        super().__init__()
        self.running = False
        self._hook_ref = None           # store hook so we can unhook safely

        self.setWindowTitle("SmartDeck · PowerPoint Remote")
        self.setFixedSize(780, 620)

        # Connect cross-thread signals
        self.log_signal.connect(self._append_log)
        self.action_signal.connect(self._on_action)

        self._build_ui()

    # ─────────────────────────── UI Construction ────────────────────────────

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0f1117;
                color: #e8eaf0;
                font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
            }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.05);
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.20);
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(14)

        watch_icon = QLabel("⌚")
        watch_icon.setFont(QFont("Segoe UI Emoji", 28))
        watch_icon.setFixedWidth(42)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)

        app_title = QLabel("SmartDeck")
        app_title.setFont(QFont("Trebuchet MS", 22, QFont.Weight.Bold))
        app_title.setStyleSheet("color: #ffffff; letter-spacing: 1px;")

        subtitle = QLabel("PowerPoint Remote · Smartwatch Edition")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.45);")

        title_block.addWidget(app_title)
        title_block.addWidget(subtitle)

        header.addWidget(watch_icon, alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addLayout(title_block)
        header.addStretch()

        # Status pill
        status_pill = QFrame()
        status_pill.setFixedSize(140, 36)
        status_pill.setObjectName("statusPill")
        pill_layout = QHBoxLayout(status_pill)
        pill_layout.setContentsMargins(10, 0, 14, 0)
        pill_layout.setSpacing(8)

        self._dot = PulseDot()
        self._status_text = QLabel("STOPPED")
        self._status_text.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self._status_text.setStyleSheet("color: #ff5252;")

        pill_layout.addWidget(self._dot)
        pill_layout.addWidget(self._status_text)

        status_pill.setStyleSheet("""
            QFrame#statusPill {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 18px;
            }
        """)

        header.addWidget(status_pill, alignment=Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)
        root.addSpacing(22)

        # ── Slide Nav Buttons ────────────────────────────────────────────────
        nav_frame = QFrame()
        nav_frame.setFixedHeight(110)
        nav_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
            }
        """)
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(24, 12, 24, 12)
        nav_layout.setSpacing(16)

        self._btn_prev = self._make_nav_btn("◀  PREV", "#40c4ff", "left")
        self._btn_pp   = self._make_nav_btn("⏯  PLAY / PAUSE", "#ffd740", None)
        self._btn_next = self._make_nav_btn("NEXT  ▶", "#00e676", "right")

        nav_layout.addWidget(self._btn_prev)
        nav_layout.addWidget(self._btn_pp)
        nav_layout.addWidget(self._btn_next)

        root.addWidget(nav_frame)
        root.addSpacing(14)

        # ── Control Buttons ──────────────────────────────────────────────────
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(14)

        self._start_btn = self._make_ctrl_btn("▶  START LISTENING", "#00e676", "#004d28")
        self._stop_btn  = self._make_ctrl_btn("■  STOP LISTENING",  "#ff5252", "#4d0000")
        self._clear_btn = self._make_ctrl_btn("🗑  CLEAR LOG",       "#9e9e9e", "#1a1a1a")

        self._start_btn.clicked.connect(self.start_listening)
        self._stop_btn.clicked.connect(self.stop_listening)
        self._clear_btn.clicked.connect(lambda: self._log_box.clear())

        ctrl_layout.addWidget(self._start_btn)
        ctrl_layout.addWidget(self._stop_btn)
        ctrl_layout.addWidget(self._clear_btn)

        root.addLayout(ctrl_layout)
        root.addSpacing(14)

        # ── Log Box ──────────────────────────────────────────────────────────
        log_label = QLabel("  📋  EVENT LOG")
        log_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        log_label.setStyleSheet("color: rgba(255,255,255,0.35); letter-spacing: 2px;")
        root.addWidget(log_label)
        root.addSpacing(6)

        self._log_box = QTextEdit()
        self._log_box.setReadOnly(True)
        self._log_box.setFont(QFont("Consolas", 11))
        self._log_box.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,0.04);
                color: #cfd8e3;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 14px;
                padding: 12px 14px;
                selection-background-color: #37474f;
            }
        """)
        root.addWidget(self._log_box, stretch=1)
        root.addSpacing(14)

        # ── Action Card ──────────────────────────────────────────────────────
        self._action_card = ActionCard()
        root.addWidget(self._action_card)

        # ── Key-map Reference ────────────────────────────────────────────────
        root.addSpacing(10)
        hint = QLabel(
            "Mapped keys:  next track  ·  previous track  ·  play/pause media"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setFont(QFont("Segoe UI", 9))
        hint.setStyleSheet("color: rgba(255,255,255,0.22);")
        root.addWidget(hint)

    # ─────────────────────────── Widget Helpers ─────────────────────────────

    def _make_nav_btn(self, text: str, color: str, arrow_key):
        btn = QPushButton(text)
        btn.setFixedHeight(72)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFont(QFont("Trebuchet MS", 13, QFont.Weight.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.05);
                color: {color};
                border: 1.5px solid {color};
                border-radius: 12px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {color}22;
            }}
            QPushButton:pressed {{
                background: {color}44;
            }}
            QPushButton:disabled {{
                color: rgba(255,255,255,0.20);
                border-color: rgba(255,255,255,0.12);
                background: transparent;
            }}
        """)

        def _click():
            if not self.running:
                self._append_log("⚠ Start the listener first.", "#ff9800")
                return
            if arrow_key:
                keyboard.send(arrow_key)
                label = "NEXT SLIDE" if arrow_key == "right" else "PREVIOUS SLIDE"
                icon  = "▶▶" if arrow_key == "right" else "◀◀"
                clr   = "#00e676" if arrow_key == "right" else "#40c4ff"
                self.log_signal.emit(f"Manual: {label}", clr)
                self.action_signal.emit(icon, label, clr)
            else:
                self.log_signal.emit("Manual: PLAY / PAUSE", "#ffd740")
                self.action_signal.emit("⏯", "PLAY / PAUSE", "#ffd740")

        btn.clicked.connect(_click)
        return btn

    def _make_ctrl_btn(self, text: str, fg: str, bg_dark: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(42)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_dark};
                color: {fg};
                border: 1.5px solid {fg}66;
                border-radius: 10px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {fg}33;
                border-color: {fg};
            }}
            QPushButton:pressed {{
                background: {fg}55;
            }}
        """)
        return btn

    # ─────────────────────────── Listener Logic ─────────────────────────────

    def start_listening(self):
        if self.running:
            return

        self.running = True

        # Update status pill
        self._dot.set_active(True)
        self._status_text.setText("LIVE")
        self._status_text.setStyleSheet("color: #00e676;")

        # Hook keyboard in a daemon thread so it never blocks Qt's event loop.
        # keyboard.hook() is thread-safe; the callback uses signals to cross back.
        self._hook_ref = keyboard.hook(self._handle_event)

        self.log_signal.emit("✅  Listener started — watching for smartwatch keys.", "#00e676")
        self._action_card.flash("👂", "Listening…", "#00e676")

    def stop_listening(self):
        if not self.running:
            return

        self.running = False

        # Unhook only our specific hook, leaving any other hooks intact.
        if self._hook_ref is not None:
            keyboard.unhook(self._hook_ref)
            self._hook_ref = None

        self._dot.set_active(False)
        self._status_text.setText("STOPPED")
        self._status_text.setStyleSheet("color: #ff5252;")

        self.log_signal.emit("🔴  Listener stopped.", "#ff5252")
        self._action_card._reset()

    def _handle_event(self, event):
        """Called by the keyboard library (may be a background thread)."""

        if not self.running:
            return

        # Only process key-down events; ignore key-up / repeat.
        if event.event_type != keyboard.KEY_DOWN:
            return

        key = str(event.name).lower().strip()

        # Always log what we see (helps debugging unknown key names).
        self.log_signal.emit(f"🔑  Key detected: <b>{key}</b>", "rgba(255,255,255,0.55)")

        mapping = self.KEY_MAP.get(key)
        if mapping is None:
            return                          # Not a mapped key — silently skip.

        direction, arrow_key, label, icon, color = mapping

        if arrow_key:
            keyboard.send(arrow_key)        # Send the actual slide-advance key.

        self.log_signal.emit(f"⚡  Action: <b>{label}</b>", color)
        self.action_signal.emit(icon, label, color)

    # ─────────────────────────── Slot Handlers ──────────────────────────────

    def _append_log(self, message: str, color: str = "#cfd8e3"):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_box.append(
            f'<span style="color:rgba(255,255,255,0.30);">[{ts}]</span>'
            f'&nbsp;<span style="color:{color};">{message}</span>'
        )
        sb = self._log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_action(self, icon: str, text: str, color: str):
        self._action_card.flash(icon, text, color)

    # ─────────────────────────── Cleanup ────────────────────────────────────

    def closeEvent(self, event):
        """Ensure keyboard hooks are released when the window is closed."""
        if self.running:
            self.stop_listening()
        event.accept()


# ─────────────────────────── Entry Point ────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")          # Consistent cross-platform look.

    window = PowerPointRemote()
    window.show()

    sys.exit(app.exec())