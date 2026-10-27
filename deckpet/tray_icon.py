"""System tray integration for Deckpet with quick controls and emotion switcher."""

from PyQt6 import QtCore, QtGui, QtWidgets
from deckpet.config import ConfigManager
from deckpet.emo_face import Emotion


class DeckpetTrayIcon(QtWidgets.QSystemTrayIcon):
    """Ubuntu System Tray indicator."""

    toggle_visibility_requested = QtCore.pyqtSignal()
    emotion_changed = QtCore.pyqtSignal(object)  # Emotion or None
    water_log_requested = QtCore.pyqtSignal()
    quit_requested = QtCore.pyqtSignal()

    def __init__(self, config_mgr: ConfigManager, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.config_mgr = config_mgr

        self.setIcon(self._generate_tray_icon())
        self.setToolTip("EMO Desktop Companion")

        self._build_menu()
        self.activated.connect(self._on_tray_activated)

    def _generate_tray_icon(self) -> QtGui.QIcon:
        """Draws a clean glowing robot icon for the Ubuntu top bar."""
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Draw mini robot head
        painter.setPen(QtGui.QPen(QtGui.QColor("#00d2ff"), 2))
        painter.setBrush(QtGui.QColor("#181b24"))
        painter.drawRoundedRect(QtCore.QRectF(4, 4, 24, 24), 7, 7)

        # Mini glowing eyes
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor("#00f0ff"))
        painter.drawRoundedRect(QtCore.QRectF(8, 12, 5, 8), 2.5, 2.5)
        painter.drawRoundedRect(QtCore.QRectF(19, 12, 5, 8), 2.5, 2.5)
        painter.end()

        return QtGui.QIcon(pixmap)

    def _build_menu(self) -> None:
        menu = QtWidgets.QMenu()
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #1e222d;
                color: #e2e8f0;
                border: 1px solid #363c4e;
                border-radius: 8px;
                padding: 6px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
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

        # 1. Show / Hide Pet
        self.act_toggle = menu.addAction("👁 Show / Hide Pet")
        self.act_toggle.triggered.connect(self.toggle_visibility_requested.emit)

        # 2. Daily Stats entry (e.g. 💧 3 / 8 glasses)
        water_count = self.config_mgr.get_water_count()
        goal = self.config_mgr.get_water_goal()
        self.act_stats = menu.addAction(f"💧 Today: {water_count}/{goal} glasses")
        self.act_stats.setEnabled(False)

        # 3. Log a Glass of Water
        self.act_drink = menu.addAction("➕ Log Glass of Water (+1)")
        self.act_drink.triggered.connect(self.water_log_requested.emit)

        menu.addSeparator()

        # 4. Quick Emotion Switcher Submenu
        emotion_menu = menu.addMenu("🎭 Set Robot Emotion")
        emotion_menu.setStyleSheet(menu.styleSheet())

        act_auto = emotion_menu.addAction("✨ Auto (Dynamic Activity)")
        act_auto.triggered.connect(lambda: self.emotion_changed.emit(None))

        act_happy = emotion_menu.addAction("😊 Happy (^ ^)")
        act_happy.triggered.connect(lambda: self.emotion_changed.emit(Emotion.HAPPY))

        act_sleepy = emotion_menu.addAction("😴 Sleep Mode (Zzz)")
        act_sleepy.triggered.connect(lambda: self.emotion_changed.emit(Emotion.SLEEPY))

        act_thirsty = emotion_menu.addAction("💧 Thirsty Mode")
        act_thirsty.triggered.connect(lambda: self.emotion_changed.emit(Emotion.THIRSTY))

        act_posture = emotion_menu.addAction("🧘 Posture Alert Mode")
        act_posture.triggered.connect(lambda: self.emotion_changed.emit(Emotion.POSTURE))

        menu.addSeparator()

        # 5. Quit
        act_quit = menu.addAction("❌ Quit Deckpet")
        act_quit.triggered.connect(self.quit_requested.emit)

        self.setContextMenu(menu)
        self.menu = menu

    def update_stats_label(self) -> None:
        water_count = self.config_mgr.get_water_count()
        goal = self.config_mgr.get_water_goal()
        self.act_stats.setText(f"💧 Today: {water_count}/{goal} glasses")

    def _on_tray_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            # Single click on tray toggles pet
            self.toggle_visibility_requested.emit()
