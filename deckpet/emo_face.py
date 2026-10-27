"""EMO Robotic Face renderer with procedural glowing digital eyes and expressions."""

import math
import random
import time
from enum import Enum
from PyQt6 import QtCore, QtGui, QtWidgets


class Emotion(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    THIRSTY = "thirsty"
    POSTURE = "posture"
    SLEEPY = "sleepy"
    WAKING = "waking"
    PICKED_UP = "picked_up"


class EmoFaceWidget(QtWidgets.QWidget):
    """Draws an EMO-style robotic companion head with animated OLED eyes."""

    clicked = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(170, 140)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.current_emotion = Emotion.NEUTRAL
        self.forced_emotion: Emotion | None = None

        # Animation states
        self.blink_ratio = 0.0  # 0.0 (open) to 1.0 (closed)
        self.eye_offset_x = 0.0
        self.eye_offset_y = 0.0
        self.target_offset_x = 0.0
        self.target_offset_y = 0.0
        self.bounce_y = 0.0

        # Timers & cycles
        self.tick_count = 0
        self.last_blink_time = time.time()
        self.blink_duration = 0.16
        self.is_blinking = False

        self.last_look_time = time.time()
        self.look_interval = 3.5

        # Sleep Zzz particles
        self.zzz_list = []  # list of [x, y, alpha, size]

        # 60 FPS animation loop
        self.anim_timer = QtCore.QTimer(self)
        self.anim_timer.setInterval(16)  # ~60 fps
        self.anim_timer.timeout.connect(self._on_tick)
        self.anim_timer.start()

    def set_emotion(self, emotion: Emotion, is_override: bool = False) -> None:
        if is_override:
            self.forced_emotion = emotion
        self.current_emotion = emotion
        self.update()

    def clear_override(self) -> None:
        self.forced_emotion = None
        self.current_emotion = Emotion.NEUTRAL
        self.update()

    def _on_tick(self) -> None:
        self.tick_count += 1
        now = time.time()
        active_emotion = self.forced_emotion or self.current_emotion

        # 1. Handle Sleepy Zzz animation
        if active_emotion == Emotion.SLEEPY:
            if self.tick_count % 35 == 0:
                self.zzz_list.append([115.0, 50.0, 1.0, 12])
            for z in self.zzz_list:
                z[0] += 0.35  # drift right
                z[1] -= 0.65  # float up
                z[2] -= 0.015  # fade out
            self.zzz_list = [z for z in self.zzz_list if z[2] > 0.05]
            self.blink_ratio = 0.95
            self.bounce_y = math.sin(self.tick_count * 0.03) * 1.5
            self.update()
            return
        else:
            self.zzz_list.clear()

        # 2. Handle Blinking
        if active_emotion in (Emotion.NEUTRAL, Emotion.THIRSTY, Emotion.POSTURE):
            if not self.is_blinking:
                if now - self.last_blink_time > random.uniform(3.0, 5.5):
                    self.is_blinking = True
                    self.blink_start = now
            else:
                progress = (now - self.blink_start) / self.blink_duration
                if progress >= 1.0:
                    self.is_blinking = False
                    self.blink_ratio = 0.0
                    self.last_blink_time = now
                else:
                    # Sinusoidal blink curve (0 -> 1 -> 0)
                    self.blink_ratio = math.sin(progress * math.pi)
        elif active_emotion == Emotion.HAPPY:
            self.blink_ratio = 0.0
            self.bounce_y = abs(math.sin(self.tick_count * 0.15)) * -4.0
        elif active_emotion == Emotion.PICKED_UP:
            self.blink_ratio = 0.0
            self.bounce_y = math.sin(self.tick_count * 0.2) * 2.0
        else:
            self.blink_ratio = 0.0
            self.bounce_y = 0.0

        # 3. Handle Eye Glances (Smooth interpolation towards target)
        if active_emotion == Emotion.NEUTRAL:
            if now - self.last_look_time > self.look_interval:
                self.target_offset_x = random.choice([-8.0, -4.0, 0.0, 0.0, 4.0, 8.0])
                self.target_offset_y = random.choice([-3.0, 0.0, 0.0, 3.0])
                self.look_interval = random.uniform(2.5, 6.0)
                self.last_look_time = now
        elif active_emotion == Emotion.PICKED_UP:
            self.target_offset_x = 0.0
            self.target_offset_y = 0.0
        else:
            self.target_offset_x = 0.0
            self.target_offset_y = 0.0

        # Smooth glide
        self.eye_offset_x += (self.target_offset_x - self.eye_offset_x) * 0.12
        self.eye_offset_y += (self.target_offset_y - self.eye_offset_y) * 0.12

        self.update()

    def paintEvent(self, a0: QtGui.QPaintEvent | None) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        active_emotion = self.forced_emotion or self.current_emotion

        # Robot head placement
        head_x, head_y = 15.0, 12.0 + self.bounce_y
        head_w, head_h = 140.0, 114.0

        # --- 1. Ear Headphones / Cyber Pods ---
        ear_color = QtGui.QColor("#22252e")
        ear_glow = self._get_glow_color(active_emotion)

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        # Left headphone
        painter.setBrush(ear_color)
        painter.drawRoundedRect(QtCore.QRectF(head_x - 9, head_y + 30, 12, 45), 5, 5)
        # Left LED ring
        painter.setBrush(ear_glow)
        painter.drawEllipse(QtCore.QPointF(head_x - 3, head_y + 52), 3, 7)

        # Right headphone
        painter.setBrush(ear_color)
        painter.drawRoundedRect(QtCore.QRectF(head_x + head_w - 3, head_y + 30, 12, 45), 5, 5)
        # Right LED ring
        painter.setBrush(ear_glow)
        painter.drawEllipse(QtCore.QPointF(head_x + head_w + 3, head_y + 52), 3, 7)

        # --- 2. Outer Head Body (Matte Cyber Plastic with rounded corners) ---
        body_grad = QtGui.QLinearGradient(head_x, head_y, head_x, head_y + head_h)
        body_grad.setColorAt(0.0, QtGui.QColor("#2d313b"))
        body_grad.setColorAt(0.5, QtGui.QColor("#1f2229"))
        body_grad.setColorAt(1.0, QtGui.QColor("#14161a"))

        painter.setPen(QtGui.QPen(QtGui.QColor("#3d4250"), 2.0))
        painter.setBrush(body_grad)
        head_rect = QtCore.QRectF(head_x, head_y, head_w, head_h)
        painter.drawRoundedRect(head_rect, 34, 34)

        # Subtle top specular highlight
        highlight_pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 30), 1.5)
        painter.setPen(highlight_pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QtCore.QRectF(head_x + 6, head_y + 3, head_w - 12, head_h - 6), 30, 30)

        # --- 3. Screen Face Area (Glossy OLED Glass) ---
        screen_margin = 12.0
        screen_rect = QtCore.QRectF(
            head_x + screen_margin,
            head_y + screen_margin + 2,
            head_w - (screen_margin * 2),
            head_h - (screen_margin * 2) - 4,
        )
        screen_grad = QtGui.QLinearGradient(screen_rect.topLeft(), screen_rect.bottomLeft())
        screen_grad.setColorAt(0.0, QtGui.QColor("#0d0e12"))
        screen_grad.setColorAt(1.0, QtGui.QColor("#050508"))

        painter.setPen(QtGui.QPen(QtGui.QColor("#101217"), 1.5))
        painter.setBrush(screen_grad)
        painter.drawRoundedRect(screen_rect, 24, 24)

        # Glass gloss overlay
        gloss_path = QtGui.QPainterPath()
        gloss_path.moveTo(screen_rect.left(), screen_rect.top() + 20)
        gloss_path.lineTo(screen_rect.right(), screen_rect.top() + 6)
        gloss_path.lineTo(screen_rect.right(), screen_rect.top())
        gloss_path.lineTo(screen_rect.left(), screen_rect.top())
        gloss_path.closeSubpath()
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.fillPath(gloss_path, QtGui.QColor(255, 255, 255, 12))

        # --- 4. Digital OLED Eyes ---
        self._draw_eyes(painter, screen_rect, active_emotion)

        # --- 5. Status Badges & Zzz ---
        if active_emotion == Emotion.THIRSTY:
            self._draw_water_drop(painter, head_x + head_w / 2, head_y + 24)
        elif active_emotion == Emotion.POSTURE:
            self._draw_posture_icon(painter, head_x + head_w / 2, head_y + 24)
        elif active_emotion == Emotion.SLEEPY:
            self._draw_zzz(painter)

    def _get_glow_color(self, emotion: Emotion) -> QtGui.QColor:
        if emotion == Emotion.HAPPY:
            return QtGui.QColor("#00ff9d")  # Bright neon green
        elif emotion == Emotion.THIRSTY:
            return QtGui.QColor("#00c8ff")  # Aqua / cyan
        elif emotion == Emotion.POSTURE:
            return QtGui.QColor("#ffaa00")  # Amber warning
        elif emotion == Emotion.SLEEPY:
            return QtGui.QColor("#2d4875")  # Deep calm night blue
        elif emotion == Emotion.PICKED_UP:
            return QtGui.QColor("#bf55ec")  # Violet surprise
        return QtGui.QColor("#00f0ff")  # Default electric cyan

    def _draw_eyes(self, painter: QtGui.QPainter, screen: QtCore.QRectF, emotion: Emotion) -> None:
        glow_col = self._get_glow_color(emotion)
        eye_w, eye_h = 28.0, 38.0
        gap = 18.0

        center_x = screen.center().x() + self.eye_offset_x
        center_y = screen.center().y() + 2.0 + self.eye_offset_y

        left_eye_cx = center_x - (eye_w / 2) - (gap / 2)
        right_eye_cx = center_x + (eye_w / 2) + (gap / 2)

        # Outer Soft Glow
        if emotion != Emotion.SLEEPY:
            glow_pen = QtGui.QPen(QtGui.QColor(glow_col.red(), glow_col.green(), glow_col.blue(), 45), 8)
            painter.setPen(glow_pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            for cx in (left_eye_cx, right_eye_cx):
                painter.drawRoundedRect(QtCore.QRectF(cx - eye_w / 2, center_y - eye_h / 2, eye_w, eye_h), 14, 14)

        # Eye Shapes depending on emotion
        if emotion == Emotion.HAPPY:
            # Upside-down curved happy arcs (^ ^)
            arc_pen = QtGui.QPen(glow_col, 5.5, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap)
            painter.setPen(arc_pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            for cx in (left_eye_cx, right_eye_cx):
                path = QtGui.QPainterPath()
                path.moveTo(cx - 14, center_y + 4)
                path.quadTo(cx, center_y - 12, cx + 14, center_y + 4)
                painter.drawPath(path)

        elif emotion == Emotion.SLEEPY:
            # Sleeping slits (— —)
            slit_pen = QtGui.QPen(glow_col, 4.0, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap)
            painter.setPen(slit_pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            for cx in (left_eye_cx, right_eye_cx):
                painter.drawLine(QtCore.QPointF(cx - 13, center_y + 2), QtCore.QPointF(cx + 13, center_y + 2))

        elif emotion == Emotion.PICKED_UP:
            # Wide startled round eyes
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(glow_col)
            for cx in (left_eye_cx, right_eye_cx):
                painter.drawEllipse(QtCore.QPointF(cx, center_y), 15, 17)
                # Inner highlight pupil
                painter.setBrush(QtGui.QColor("#ffffff"))
                painter.drawEllipse(QtCore.QPointF(cx + 4, center_y - 4), 5, 5)
                painter.setBrush(glow_col)

        else:
            # NEUTRAL, THIRSTY, POSTURE
            # Draw standard expressive OLED eyes with blink height scaling
            h_eff = max(3.0, eye_h * (1.0 - self.blink_ratio))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(glow_col)

            for cx in (left_eye_cx, right_eye_cx):
                eye_rect = QtCore.QRectF(cx - eye_w / 2, center_y - h_eff / 2, eye_w, h_eff)
                corner_radius = min(14.0, h_eff / 2)
                painter.drawRoundedRect(eye_rect, corner_radius, corner_radius)

                # Pupil catch-light when open
                if self.blink_ratio < 0.3:
                    painter.setBrush(QtGui.QColor(255, 255, 255, 200))
                    painter.drawEllipse(QtCore.QPointF(cx + 5, center_y - h_eff * 0.22), 3.5, 3.5)
                    painter.setBrush(glow_col)

    def _draw_water_drop(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        """Animated bouncing water droplet badge."""
        bounce = math.sin(self.tick_count * 0.1) * 3.0
        y = cy + bounce
        drop_color = QtGui.QColor("#00d2ff")

        drop_path = QtGui.QPainterPath()
        drop_path.moveTo(cx, y - 7)
        drop_path.quadTo(cx - 6, y, cx - 6, y + 4)
        drop_path.arcTo(QtCore.QRectF(cx - 6, y - 1, 12, 10), 180, 180)
        drop_path.quadTo(cx + 6, y, cx, y - 7)
        drop_path.closeSubpath()

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.fillPath(drop_path, drop_color)
        # Specular shine
        painter.setBrush(QtGui.QColor(255, 255, 255, 190))
        painter.drawEllipse(QtCore.QPointF(cx - 2, y + 2), 1.5, 2)

    def _draw_posture_icon(self, painter: QtGui.QPainter, cx: float, cy: float) -> None:
        """Warning / Stretch icon above eyes."""
        bounce = math.sin(self.tick_count * 0.12) * 2.5
        y = cy + bounce
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor("#ffaa00"))
        # Draw alert badge
        painter.drawRoundedRect(QtCore.QRectF(cx - 7, y - 6, 14, 14), 4, 4)
        painter.setPen(QtGui.QPen(QtGui.QColor("#121212"), 2))
        painter.drawLine(QtCore.QPointF(cx, y - 3), QtCore.QPointF(cx, y + 1))
        painter.drawEllipse(QtCore.QPointF(cx, y + 4), 1.0, 1.0)

    def _draw_zzz(self, painter: QtGui.QPainter) -> None:
        """Floating sleeping Zzz."""
        for x, y, alpha, size in self.zzz_list:
            painter.setFont(QtGui.QFont("Ubuntu", size, QtGui.QFont.Weight.Bold))
            painter.setPen(QtGui.QColor(100, 160, 255, int(alpha * 230)))
            painter.drawText(QtCore.QPointF(x, y), "Z")

    # Forward mouse events to parent window for smooth dragging and interactivity
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.parent():
            self.parent().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.parent():
            self.parent().mouseMoveEvent(event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.parent():
            self.parent().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.parent():
            self.parent().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)
