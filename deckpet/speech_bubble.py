"""Interactive Cyber Speech Bubble widget for Deckpet notifications."""

from PyQt6 import QtCore, QtGui, QtWidgets


class SpeechBubbleWidget(QtWidgets.QWidget):
    """Floating speech bubble with quick-action buttons."""

    water_logged = QtCore.pyqtSignal()
    posture_done = QtCore.pyqtSignal()
    snooze_requested = QtCore.pyqtSignal()
    closed = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(230)

        # Main Layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 14)
        self.layout.setSpacing(8)

        # Header Title
        self.title_label = QtWidgets.QLabel("EMO Reminder")
        self.title_label.setStyleSheet("color: #00f0ff; font-weight: bold; font-size: 13px;")
        self.layout.addWidget(self.title_label)

        # Message Body
        self.body_label = QtWidgets.QLabel("Time for a quick break!")
        self.body_label.setWordWrap(True)
        self.body_label.setStyleSheet("color: #e2e8f0; font-size: 11px; line-height: 1.3;")
        self.layout.addWidget(self.body_label)

        # Subtitle / Counter (e.g. "Today: 3 / 8 glasses")
        self.sub_label = QtWidgets.QLabel("")
        self.sub_label.setStyleSheet("color: #94a3b8; font-size: 10px; font-style: italic;")
        self.layout.addWidget(self.sub_label)

        # Action Buttons Container
        self.btn_layout = QtWidgets.QHBoxLayout()
        self.btn_layout.setSpacing(6)

        # Primary Action Button
        self.btn_primary = QtWidgets.QPushButton("I Drank! 💧")
        self.btn_primary.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.btn_primary.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00d2ff, stop:1 #0088cc);
                color: #0b0f19;
                font-weight: bold;
                font-size: 11px;
                border-radius: 6px;
                padding: 5px 8px;
                border: none;
            }
            QPushButton:hover {
                background: #33ddff;
            }
            QPushButton:pressed {
                background: #0077b3;
            }
        """
        )
        self.btn_primary.clicked.connect(self._on_primary_click)
        self.btn_layout.addWidget(self.btn_primary)

        # Snooze Button
        self.btn_snooze = QtWidgets.QPushButton("Snooze 5m")
        self.btn_snooze.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.btn_snooze.setStyleSheet(
            """
            QPushButton {
                background: #272a36;
                color: #cbd5e1;
                font-size: 10px;
                border-radius: 6px;
                padding: 5px 6px;
                border: 1px solid #3e4457;
            }
            QPushButton:hover {
                background: #363b4b;
                color: #ffffff;
            }
        """
        )
        self.btn_snooze.clicked.connect(self._on_snooze_click)
        self.btn_layout.addWidget(self.btn_snooze)

        self.layout.addLayout(self.btn_layout)

        # Auto-dismiss timer
        self.auto_timer = QtCore.QTimer(self)
        self.auto_timer.setSingleShot(True)
        self.auto_timer.timeout.connect(self.hide_bubble)

        self.reminder_type = "water"  # 'water' or 'posture'

    def show_water_reminder(self, count: int, goal: int) -> None:
        self.reminder_type = "water"
        self.title_label.setText("💧 Hydration Time!")
        self.title_label.setStyleSheet("color: #00d2ff; font-weight: bold; font-size: 12px;")
        self.body_label.setText("Take a break and have a sip of water.")
        self.sub_label.setText(f"Today's Progress: {count}/{goal} glasses")
        self.btn_primary.setText("+1 Drank! 💧")
        self.btn_primary.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00d2ff, stop:1 #0088cc);
                color: #0b0f19; font-weight: bold; font-size: 11px; border-radius: 6px; padding: 5px 8px; border: none;
            }
            QPushButton:hover { background: #38e1ff; }
        """
        )
        self.show()
        self.raise_()
        self.auto_timer.start(35000)  # 35 seconds auto-hide

    def show_posture_reminder(self, active_minutes: int) -> None:
        self.reminder_type = "posture"
        self.title_label.setText("🧘 Stretch & Posture")
        self.title_label.setStyleSheet("color: #ffaa00; font-weight: bold; font-size: 12px;")
        self.body_label.setText(f"You've been at your desk for {active_minutes}m. Straighten your back & roll shoulders!")
        self.sub_label.setText("Look 20ft away to rest your eyes.")
        self.btn_primary.setText("Done! ✨")
        self.btn_primary.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffaa00, stop:1 #d97706);
                color: #0b0f19; font-weight: bold; font-size: 11px; border-radius: 6px; padding: 5px 8px; border: none;
            }
            QPushButton:hover { background: #ffbb33; }
        """
        )
        self.show()
        self.raise_()
        self.auto_timer.start(35000)

    def show_custom_message(self, title: str, text: str, sub: str = "") -> None:
        self.reminder_type = "info"
        self.title_label.setText(title)
        self.title_label.setStyleSheet("color: #00f0ff; font-weight: bold; font-size: 12px;")
        self.body_label.setText(text)
        self.sub_label.setText(sub)
        self.btn_primary.setText("OK 👍")
        self.show()
        self.raise_()
        self.auto_timer.start(10000)

    def _on_primary_click(self) -> None:
        self.auto_timer.stop()
        if self.reminder_type == "water":
            self.water_logged.emit()
        elif self.reminder_type == "posture":
            self.posture_done.emit()
        self.hide_bubble()

    def _on_snooze_click(self) -> None:
        self.auto_timer.stop()
        self.snooze_requested.emit()
        self.hide_bubble()

    def hide_bubble(self) -> None:
        self.hide()
        self.closed.emit()

    def paintEvent(self, a0: QtGui.QPaintEvent | None) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        rect = QtCore.QRectF(self.rect()).adjusted(2, 2, -2, -2)

        # Bubble background
        grad = QtGui.QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0.0, QtGui.QColor(22, 26, 35, 235))
        grad.setColorAt(1.0, QtGui.QColor(14, 16, 22, 245))

        painter.setPen(QtGui.QPen(QtGui.QColor(60, 70, 95, 200), 1.5))
        painter.setBrush(grad)
        painter.drawRoundedRect(rect, 12, 12)

        # Glow border
        accent_col = QtGui.QColor(0, 210, 255, 60)
        if self.reminder_type == "posture":
            accent_col = QtGui.QColor(255, 170, 0, 60)
        painter.setPen(QtGui.QPen(accent_col, 2.0))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 11, 11)
