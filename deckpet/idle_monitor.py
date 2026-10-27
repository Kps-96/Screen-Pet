"""Wayland / GNOME Mutter D-Bus Idle & Activity Monitor."""

import time
from PyQt6 import QtCore, QtDBus


class WaylandIdleMonitor(QtCore.QObject):
    """Monitors desktop idle time on Ubuntu GNOME Wayland via Mutter D-Bus."""

    # Signals:
    # is_idle (True: idle/away, False: active)
    idle_status_changed = QtCore.pyqtSignal(bool)
    # Emits current idle seconds and active continuous seconds periodically
    activity_tick = QtCore.pyqtSignal(float, float)

    def __init__(self, idle_threshold_seconds: int = 300, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.idle_threshold_seconds = idle_threshold_seconds
        self.is_idle = False
        self.continuous_work_seconds = 0.0
        self._last_check_time = time.time()
        self._dbus_available = False

        self._bus = QtDBus.QDBusConnection.sessionBus()
        if self._bus.isConnected():
            self._dbus_available = True

        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.setInterval(1000)  # Check every second
        self._poll_timer.timeout.connect(self._check_idle)

    def start(self) -> None:
        self._last_check_time = time.time()
        self._poll_timer.start()

    def stop(self) -> None:
        self._poll_timer.stop()

    def get_idle_milliseconds(self) -> int:
        if not self._dbus_available:
            return 0

        msg = QtDBus.QDBusMessage.createMethodCall(
            "org.gnome.Mutter.IdleMonitor",
            "/org/gnome/Mutter/IdleMonitor/Core",
            "org.gnome.Mutter.IdleMonitor",
            "GetIdletime",
        )
        reply = self._bus.call(msg)
        if reply.type() == QtDBus.QDBusMessage.MessageType.ReplyMessage and reply.arguments():
            try:
                return int(reply.arguments()[0])
            except (ValueError, TypeError):
                return 0
        return 0

    def _check_idle(self) -> None:
        now = time.time()
        dt = max(0.0, now - self._last_check_time)
        self._last_check_time = now

        idle_ms = self.get_idle_milliseconds()
        idle_sec = idle_ms / 1000.0

        previously_idle = self.is_idle
        if idle_sec >= self.idle_threshold_seconds:
            self.is_idle = True
            # User is away, reset or pause continuous work timer
            self.continuous_work_seconds = max(0.0, self.continuous_work_seconds - dt)
        else:
            self.is_idle = False
            self.continuous_work_seconds += dt

        if previously_idle != self.is_idle:
            self.idle_status_changed.emit(self.is_idle)

        self.activity_tick.emit(idle_sec, self.continuous_work_seconds)

    def reset_continuous_work(self) -> None:
        self.continuous_work_seconds = 0.0
