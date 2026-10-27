#!/usr/bin/env python3
"""Main entry point for Deckpet Desktop Companion."""

import os
import signal
import sys
from pathlib import Path

# Ensure XCB libraries are loaded for reliable Always-On-Top and positioning
PROJECT_DIR = Path(__file__).resolve().parent
LIBS_DIR = PROJECT_DIR / "libs" / "usr" / "lib" / "x86_64-linux-gnu"
if LIBS_DIR.exists():
    current_ld = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["LD_LIBRARY_PATH"] = f"{LIBS_DIR}:{current_ld}"

os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PyQt6 import QtCore, QtNetwork, QtWidgets
from deckpet.audio import SoundEngine
from deckpet.config import ConfigManager
from deckpet.hotkey import (
    setup_gnome_global_shortcut,
    setup_qt_shortcut,
    start_pynput_listener,
)
from deckpet.idle_monitor import WaylandIdleMonitor
from deckpet.pet_window import PetWindow
from deckpet.reminder_engine import ReminderEngine
from deckpet.tray_icon import DeckpetTrayIcon


IPC_SERVER_NAME = "deckpet_ipc_socket"


def send_ipc_command(command: str) -> bool:
    """Sends a command to an already running Deckpet instance."""
    socket = QtNetwork.QLocalSocket()
    socket.connectToServer(IPC_SERVER_NAME)
    if socket.waitForConnected(500):
        socket.write(f"{command}\n".encode("utf-8"))
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        return True
    return False


def main() -> None:
    # Allow Ctrl+C to terminate cleanly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Deckpet")
    app.setOrganizationName("Deckpet")
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # If --toggle argument is given, communicate with existing instance
    if "--toggle" in sys.argv or "-t" in sys.argv:
        if send_ipc_command("toggle"):
            sys.exit(0)
        # If no instance was running, continue to start Deckpet normally

    # Single instance IPC server
    ipc_server = QtNetwork.QLocalServer()
    # Remove stale socket if needed
    QtNetwork.QLocalServer.removeServer(IPC_SERVER_NAME)
    ipc_server.listen(IPC_SERVER_NAME)

    # 1. Initialize Core Managers
    config_mgr = ConfigManager()
    sound_engine = SoundEngine(enabled=config_mgr.config.get("sound_enabled", True))

    # 2. UI Widgets
    pet_window = PetWindow(config_mgr, sound_engine)
    tray_icon = DeckpetTrayIcon(config_mgr)

    # 3. Background Services
    idle_monitor = WaylandIdleMonitor(
        idle_threshold_seconds=config_mgr.config.get("idle_sleep_seconds", 300)
    )
    reminder_engine = ReminderEngine(config_mgr)

    # --- Wire Signals ---

    # Tray & Shortcut visibility toggle
    def toggle_pet_visibility():
        if pet_window.isVisible():
            pet_window.hide()
        else:
            pet_window.show()
            pet_window.raise_()
            pet_window.activateWindow()

    tray_icon.toggle_visibility_requested.connect(toggle_pet_visibility)
    tray_icon.emotion_changed.connect(
        lambda emo: pet_window.face.set_emotion(emo, is_override=True)
        if emo
        else pet_window.face.clear_override()
    )
    tray_icon.water_log_requested.connect(pet_window.on_water_logged)
    tray_icon.quit_requested.connect(app.quit)

    # IPC command handler (e.g. from Ctrl+Shift+P GNOME shortcut)
    def on_ipc_new_connection():
        client_socket = ipc_server.nextPendingConnection()
        if client_socket:
            client_socket.waitForReadyRead(300)
            data = bytes(client_socket.readAll()).decode("utf-8").strip()
            if data == "toggle":
                toggle_pet_visibility()
            client_socket.disconnectFromServer()

    ipc_server.newConnection.connect(on_ipc_new_connection)

    # Setup Shortcuts:
    # 1. Ubuntu GNOME global keybinding for Ctrl+Shift+P
    setup_gnome_global_shortcut()
    # 2. In-app Qt Shortcut for Ctrl+Shift+P
    setup_qt_shortcut(pet_window, toggle_pet_visibility)
    # 3. pynput background listener for Ctrl+Shift+P
    start_pynput_listener(toggle_pet_visibility)

    # Idle Monitor -> Pet and Reminder
    idle_monitor.idle_status_changed.connect(pet_window.handle_idle_change)
    idle_monitor.activity_tick.connect(
        lambda idle_sec, work_sec: reminder_engine.update_continuous_work(work_sec)
    )

    # Reminder Engine -> Pet
    reminder_engine.water_alert.connect(pet_window.trigger_water_alert)
    reminder_engine.posture_alert.connect(pet_window.trigger_posture_alert)

    # Speech Bubble / Pet Log -> Tray Stats Update
    def _on_stats_updated():
        tray_icon.update_stats_label()

    pet_window.bubble.water_logged.connect(_on_stats_updated)
    pet_window.bubble.posture_done.connect(_on_stats_updated)

    # Snooze connections
    pet_window.bubble.snooze_requested.connect(lambda: reminder_engine.snooze_water(5))

    # Start services
    idle_monitor.start()
    reminder_engine.start()

    # Show Pet & Tray
    tray_icon.show()
    pet_window.show()

    # Play wake greeting sound
    sound_engine.play("wake")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
