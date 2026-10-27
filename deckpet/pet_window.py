"""Main floating pet window with drag-and-drop, Wayland hints, and event handlers."""

from PyQt6 import QtCore, QtGui, QtWidgets
from deckpet.audio import SoundEngine
from deckpet.config import ConfigManager
from deckpet.emo_face import EmoFaceWidget, Emotion
from deckpet.speech_bubble import SpeechBubbleWidget


class PetWindow(QtWidgets.QWidget):
    """Floating transparent desktop pet."""

    def __init__(self, config_mgr: ConfigManager, sound_engine: SoundEngine) -> None:
        super().__init__()
        self.config_mgr = config_mgr
        self.sound = sound_engine

        # Window Flags for floating desktop companion that stays above all apps
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)

        # Main Layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(4)

        # 1. Speech Bubble (Top)
        self.bubble = SpeechBubbleWidget(self)
        self.bubble.hide()
        self.main_layout.addWidget(self.bubble, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # 2. Emo Robotic Face (Bottom)
        self.face = EmoFaceWidget(self)
        self.main_layout.addWidget(self.face, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Dragging State
        self._dragging = False
        self._drag_pos = QtCore.QPoint()
        self._first_show = True

        # Active Watchdog: Keeps window strictly on top of other tabs/apps without stealing focus
        self._stay_on_top_timer = QtCore.QTimer(self)
        self._stay_on_top_timer.setInterval(600)
        self._stay_on_top_timer.timeout.connect(self._ensure_always_on_top)
        self._stay_on_top_timer.start()

        # Connect speech bubble signals
        self.bubble.water_logged.connect(self.on_water_logged)
        self.bubble.posture_done.connect(self.on_posture_done)
        self.bubble.snooze_requested.connect(self.on_snoozed)
        self.bubble.closed.connect(self._on_bubble_closed)

    def _ensure_always_on_top(self) -> None:
        if self.isVisible() and not self._dragging:
            self.raise_()

    def snap_to_bottom_right(self) -> None:
        """Positions EMO neatly in the bottom-right corner of the active screen."""
        screen = QtWidgets.QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        self.adjustSize()
        w = max(self.width(), 170)
        h = max(self.height(), 140)
        margin_x = 24
        margin_y = 32
        target_x = geo.x() + geo.width() - w - margin_x
        target_y = geo.y() + geo.height() - h - margin_y
        self.move(target_x, target_y)
        self._save_position()
        self.raise_()

    def showEvent(self, event: QtGui.QShowEvent | None) -> None:
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            self.snap_to_bottom_right()
        self.raise_()

    def trigger_water_alert(self, count: int, goal: int) -> None:
        self.face.set_emotion(Emotion.THIRSTY)
        self.sound.play("water")
        self.bubble.show_water_reminder(count, goal)
        self.adjustSize()

    def trigger_posture_alert(self, active_minutes: int) -> None:
        self.face.set_emotion(Emotion.POSTURE)
        self.sound.play("posture")
        self.bubble.show_posture_reminder(active_minutes)
        self.adjustSize()

    def handle_idle_change(self, is_idle: bool) -> None:
        if is_idle:
            self.face.set_emotion(Emotion.SLEEPY)
            self.sound.play("sleep")
            self.bubble.hide_bubble()
        else:
            self.face.set_emotion(Emotion.HAPPY)
            self.sound.play("wake")
            # Return to neutral after 3 seconds
            QtCore.QTimer.singleShot(3000, lambda: self.face.set_emotion(Emotion.NEUTRAL))

    def on_water_logged(self) -> None:
        count = self.config_mgr.increment_water()
        goal = self.config_mgr.get_water_goal()
        self.face.set_emotion(Emotion.HAPPY)
        self.sound.play("happy")
        # Quick feedback
        self.bubble.show_custom_message("💧 Great Job!", f"Glass #{count} logged! ({count}/{goal})")
        QtCore.QTimer.singleShot(3500, self.reset_to_default_emotion)

    def on_posture_done(self) -> None:
        self.config_mgr.increment_posture()
        self.face.set_emotion(Emotion.HAPPY)
        self.sound.play("happy")
        self.bubble.show_custom_message("✨ Well Done!", "Posture checked. Keep it up!")
        QtCore.QTimer.singleShot(3500, self.reset_to_default_emotion)

    def on_snoozed(self) -> None:
        self.sound.play("click")
        self.reset_to_default_emotion()

    def _on_bubble_closed(self) -> None:
        self.reset_to_default_emotion()
        self.adjustSize()

    def reset_to_default_emotion(self) -> None:
        if self.face.forced_emotion is not None:
            self.face.set_emotion(self.face.forced_emotion)
        else:
            self.face.set_emotion(Emotion.NEUTRAL)

    # --- Mouse Event Handling (Dragging & Interactivity) ---

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            self.face.set_emotion(Emotion.PICKED_UP)
            self.sound.play("click")
            event.accept()
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._dragging and (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._dragging:
            self._dragging = False
            self.reset_to_default_emotion()
            self._save_position()
            event.accept()

    def _save_position(self) -> None:
        self.config_mgr.config["window_x"] = self.x()
        self.config_mgr.config["window_y"] = self.y()
        self.config_mgr.save_config()

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Double click logs a glass of water quickly!
            self.on_water_logged()
            event.accept()

    def _show_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #1a1d27;
                color: #e2e8f0;
                border: 1px solid #363c4e;
                border-radius: 8px;
                padding: 6px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 18px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0088cc;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #363c4e;
                margin: 4px 0px;
            }
        """
        )

        # Quick Log Water
        count = self.config_mgr.get_water_count()
        goal = self.config_mgr.get_water_goal()
        act_drink = menu.addAction(f"💧 Log Water ({count}/{goal})")
        act_drink.triggered.connect(self.on_water_logged)

        # Quick Posture Check
        act_posture = menu.addAction("🧘 Do Posture Stretch")
        act_posture.triggered.connect(self.on_posture_done)

        menu.addSeparator()

        # Snap to Bottom-Right Corner
        act_snap = menu.addAction("📌 Snap to Bottom-Right")
        act_snap.triggered.connect(self.snap_to_bottom_right)

        menu.addSeparator()

        # Emotion Submenu
        emo_menu = menu.addMenu("🎭 Change Emotion")
        emo_menu.setStyleSheet(menu.styleSheet())
        emo_menu.addAction("✨ Auto Mode", lambda: self.face.clear_override())
        emo_menu.addAction("😊 Happy", lambda: self.face.set_emotion(Emotion.HAPPY, is_override=True))
        emo_menu.addAction("😴 Sleepy", lambda: self.face.set_emotion(Emotion.SLEEPY, is_override=True))
        emo_menu.addAction("💧 Thirsty", lambda: self.face.set_emotion(Emotion.THIRSTY, is_override=True))
        emo_menu.addAction("🧘 Posture Alert", lambda: self.face.set_emotion(Emotion.POSTURE, is_override=True))

        menu.addSeparator()

        # Mute / Unmute
        sound_status = "🔊 Sound: ON" if self.sound.enabled else "🔇 Sound: OFF"
        act_sound = menu.addAction(sound_status)

        def _toggle_sound():
            self.sound.enabled = not self.sound.enabled
            self.config_mgr.config["sound_enabled"] = self.sound.enabled
            self.config_mgr.save_config()

        act_sound.triggered.connect(_toggle_sound)

        # Hide to tray
        act_hide = menu.addAction("🙈 Hide to Tray")
        act_hide.triggered.connect(self.hide)

        menu.exec(pos)
