# 🤖 Deckpet — EMO Robotic Desktop Companion for Ubuntu

An **EMO-style robotic desktop companion** for Ubuntu (Wayland & X11). Features expressive procedural glowing OLED eyes, native activity/idle monitoring, hydration tracking with daily counters, posture & stretch checks, and quick-toggle controls.

---

## ✨ Features

- **Cyber EMO Robotic Face**:
  - Procedurally rendered glowing OLED digital eyes running at 60 FPS.
  - Realistic blinking, eye glances, and expressions:
    - `NEUTRAL`: Electric cyan glowing eyes, wanders and blinks naturally.
    - `HAPPY`: Emerald green smiling arcs (`^ ^`), cheers when you drink water or finish stretching.
    - `THIRSTY`: Amber/cyan pleading eyes with an animated water drop badge.
    - `POSTURE ALERT`: Amber alert eyes with a stretch icon after prolonged continuous desk work.
    - `SLEEPY`: Enters standby mode (`— —`) with floating glowing `Zzz` when you are away from your PC.
    - `PICKED UP`: Startled wide round eyes (`o o`) when dragging the pet.

- **Activity & Idle Monitoring (Wayland Native)**:
  - Uses Ubuntu's native `org.gnome.Mutter.IdleMonitor` over session D-Bus.
  - 100% Wayland-compatible with **zero root/sudo privileges required**.
  - Automatically transitions to sleep when you step away, and powers back on with a chime when you return.

- **Health & Wellness Reminders**:
  - **Hydration Timer**: Configurable interval (default: 35 mins) with speech bubble notifications.
  - **Daily Water Counter**: Tracks glasses logged today (e.g. `5 / 8 glasses`) with automatic daily rollover at midnight.
  - **Posture & Stretch Check**: Tracks continuous active keyboard/mouse time and alerts you to stretch and rest your eyes (20-20-20 rule).

- **Quick Controls & Flexibility**:
  - **System Tray Icon**: 1-click toggle to show/hide the robot; right-click to switch moods, log water, or view daily stats.
  - **Right-Click Radial Menu**: Right-click directly on the pet for instant mood overrides, audio muting, and hydration logging.
  - **Interactive Drag & Double-Click**: Drag anywhere on screen to reposition (position is remembered across restarts). Double-click the robot to quickly log a glass of water!
  - **Gentle Robotic Beeps & Chimes**: Pure synthesized retro-cyber beeps and ascending hydration melodies.

---

## 🚀 Quick Start

### 1. Launch Deckpet
Run the startup script (it automatically prepares the virtual environment if not already present):

```bash
./run.sh
```

Or manually:
```bash
./venv/bin/python3 main.py
```

---

## 🎮 How to Interact with EMO

| Action | Result |
|---|---|
| **Left Click + Drag** | Pick up and move EMO anywhere on your screen. EMO makes a surprised face (`o o`) and remembers its position when dropped! |
| **Double Click** | Quickly logs a glass of water (+1) with a happy cheer (`^ ^`) and pleasant chime! |
| **Right Click** | Opens the context menu to quickly change emotions, toggle sound, or log water. |
| **System Tray Icon** | Single-click to show/hide EMO from your desktop. Right-click for full controls. |
| **Speech Bubble Buttons** | Click `[+1 Drank! 💧]` to log water, or `[Snooze 5m]` to postpone reminders. |

---

## ⚙️ Configuration & Data Storage

Settings and statistics are saved in `~/.config/deckpet/`:
- `~/.config/deckpet/config.json`:
  - `water_interval_minutes`: Reminder frequency (default: 35).
  - `daily_water_goal`: Daily target glasses (default: 8).
  - `posture_interval_minutes`: Continuous desk work limit before alert (default: 50).
  - `idle_sleep_seconds`: Idle time before entering sleep mode (default: 300 / 5 mins).
  - `sound_enabled`: Toggle synthesized sound effects (`true`/`false`).
- `~/.config/deckpet/stats.json`:
  - Stores daily water glasses and completed posture stretches, auto-resetting every midnight.
