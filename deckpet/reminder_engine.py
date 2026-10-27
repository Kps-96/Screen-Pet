"""Scheduler and logic for water hydration and posture reminders."""

import time
from PyQt6 import QtCore
from deckpet.config import ConfigManager


class ReminderEngine(QtCore.QObject):
    """Manages reminder countdowns, continuous desk sessions, and snoozes."""

    water_alert = QtCore.pyqtSignal(int, int)  # current_count, goal
    posture_alert = QtCore.pyqtSignal(int)  # active_minutes

    def __init__(self, config_mgr: ConfigManager, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self.config_mgr = config_mgr

        self.water_timer_seconds = self.config_mgr.config.get("water_interval_minutes", 35) * 60
        self.posture_threshold_seconds = self.config_mgr.config.get("posture_interval_minutes", 50) * 60

        self.water_remaining_seconds = float(self.water_timer_seconds)
        self.continuous_work_seconds = 0.0

        self.is_paused = False

        # 1-second ticker
        self.tick_timer = QtCore.QTimer(self)
        self.tick_timer.setInterval(1000)
        self.tick_timer.timeout.connect(self._on_second_tick)

    def start(self) -> None:
        self.tick_timer.start()

    def stop(self) -> None:
        self.tick_timer.stop()

    def pause(self, paused: bool) -> None:
        self.is_paused = paused

    def update_continuous_work(self, seconds: float) -> None:
        """Called by idle monitor with continuous active time."""
        self.continuous_work_seconds = seconds
        # Check posture threshold
        if self.continuous_work_seconds >= self.posture_threshold_seconds:
            active_min = int(self.continuous_work_seconds // 60)
            self.posture_alert.emit(active_min)
            # Reset after alert to avoid spamming
            self.continuous_work_seconds = 0.0

    def _on_second_tick(self) -> None:
        if self.is_paused:
            return

        self.water_remaining_seconds -= 1.0
        if self.water_remaining_seconds <= 0:
            count = self.config_mgr.get_water_count()
            goal = self.config_mgr.get_water_goal()
            self.water_alert.emit(count, goal)
            # Reset to full interval
            self.water_remaining_seconds = float(self.water_timer_seconds)

    def log_water(self) -> int:
        new_count = self.config_mgr.increment_water()
        # Reset countdown for next glass
        self.water_remaining_seconds = float(self.water_timer_seconds)
        return new_count

    def log_posture(self) -> int:
        new_count = self.config_mgr.increment_posture()
        self.continuous_work_seconds = 0.0
        return new_count

    def snooze_water(self, minutes: int = 5) -> None:
        self.water_remaining_seconds = float(minutes * 60)

    def snooze_posture(self, minutes: int = 5) -> None:
        # Give a 5 min grace period
        self.continuous_work_seconds = max(0.0, self.posture_threshold_seconds - (minutes * 60))
