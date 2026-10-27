"""Global hotkey management for Deckpet on Ubuntu (GNOME Wayland / X11)."""

import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable
from PyQt6 import QtGui, QtWidgets


GNOME_CUSTOM_DIR = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/deckpet/"
GNOME_SCHEMA = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{GNOME_CUSTOM_DIR}"


def setup_gnome_global_shortcut() -> bool:
    """Registers Ctrl+Shift+P with GNOME media keys so it works system-wide under Wayland."""
    if not shutil.which("gsettings"):
        return False

    try:
        # 1. Read existing custom keybinding list
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
            capture_output=True,
            text=True,
            check=True,
        )
        current = res.stdout.strip()

        # Build list
        bindings = []
        if current.startswith("@as [") or current.startswith("["):
            # Parse simple string array
            raw = current.replace("@as", "").strip()
            if raw != "[]":
                # Remove enclosing brackets
                inner = raw.strip("[]").strip()
                if inner:
                    bindings = [b.strip().strip("'\"") for b in inner.split(",") if b.strip()]

        if GNOME_CUSTOM_DIR not in bindings:
            bindings.append(GNOME_CUSTOM_DIR)

        # Format array for gsettings: ['/path/1/', '/path/2/']
        formatted_bindings = str(bindings)

        # Set array
        subprocess.run(
            ["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", formatted_bindings],
            check=True,
        )

        # Set individual properties
        run_script = str(Path(__file__).resolve().parent.parent / "run.sh")
        toggle_cmd = f"{run_script} --toggle"

        subprocess.run(["gsettings", "set", GNOME_SCHEMA, "name", "Deckpet Toggle"], check=True)
        subprocess.run(["gsettings", "set", GNOME_SCHEMA, "command", toggle_cmd], check=True)
        subprocess.run(["gsettings", "set", GNOME_SCHEMA, "binding", "<Control><Shift>p"], check=True)

        return True
    except Exception as e:
        print(f"[Deckpet] Note: Could not register GNOME shortcut: {e}")
        return False


def setup_qt_shortcut(window: QtWidgets.QWidget, on_toggle: Callable[[], None]) -> QtGui.QShortcut:
    """Registers in-app shortcut Ctrl+Shift+P on the pet window."""
    shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+P"), window)
    shortcut.activated.connect(on_toggle)
    return shortcut


def start_pynput_listener(on_toggle: Callable[[], None]) -> None:
    """Fallback background global hotkey listener using pynput."""
    def _worker():
        try:
            from pynput import keyboard

            current_keys = set()

            def on_press(key):
                current_keys.add(key)
                # Check for Ctrl + Shift + P
                ctrl_down = (
                    keyboard.Key.ctrl in current_keys
                    or keyboard.Key.ctrl_l in current_keys
                    or keyboard.Key.ctrl_r in current_keys
                )
                shift_down = (
                    keyboard.Key.shift in current_keys
                    or keyboard.Key.shift_l in current_keys
                    or keyboard.Key.shift_r in current_keys
                )
                p_down = False
                try:
                    if hasattr(key, "char") and key.char and key.char.lower() == "p":
                        p_down = True
                except Exception:
                    pass

                if ctrl_down and shift_down and p_down:
                    on_toggle()

            def on_release(key):
                current_keys.discard(key)

            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
