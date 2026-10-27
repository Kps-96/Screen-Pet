"""Synthesized audio sound effects for EMO robotic pet."""

import io
import math
import os
import shutil
import struct
import subprocess
import threading
import wave
from typing import Dict, List, Tuple


class SoundEngine:
    """Generates and plays gentle robotic beeps and chimes."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._player = self._find_player()
        self._sounds: Dict[str, bytes] = {
            "happy": self._synth_tones([(659.25, 0.08), (880.0, 0.12)], wave_type="sine"),
            "water": self._synth_tones([(523.25, 0.1), (659.25, 0.1), (783.99, 0.15), (1046.5, 0.25)], wave_type="sine"),
            "posture": self._synth_tones([(440.0, 0.12), (554.37, 0.12), (659.25, 0.2)], wave_type="sine"),
            "sleep": self._synth_tones([(440.0, 0.12), (329.63, 0.15), (220.0, 0.25)], wave_type="sine"),
            "wake": self._synth_tones([(261.63, 0.08), (392.0, 0.1), (523.25, 0.15)], wave_type="sine"),
            "click": self._synth_tones([(880.0, 0.04), (1174.66, 0.06)], wave_type="triangle"),
        }

    def _find_player(self) -> str | None:
        for player in ("pw-play", "aplay", "paplay"):
            p = shutil.which(player)
            if p:
                return p
        return None

    def _synth_tones(self, notes: List[Tuple[float, float]], wave_type: str = "sine") -> bytes:
        buf = io.BytesIO()
        rate = 44100
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)

            for freq, duration in notes:
                samples = int(rate * duration)
                for i in range(samples):
                    t = i / rate
                    # Smooth decay envelope
                    envelope = math.exp(-3.5 * (i / samples))
                    if wave_type == "sine":
                        val_float = math.sin(2 * math.pi * freq * t)
                    else:  # triangle / pulse
                        val_float = 2 * abs(2 * (t * freq - math.floor(t * freq + 0.5))) - 1

                    sample_val = int(32767 * 0.18 * val_float * envelope)
                    sample_val = max(-32767, min(32767, sample_val))
                    wav.writeframes(struct.pack("<h", sample_val))

        return buf.getvalue()

    def play(self, sound_name: str) -> None:
        if not self.enabled or not self._player:
            return

        wav_bytes = self._sounds.get(sound_name)
        if not wav_bytes:
            return

        def _worker():
            try:
                proc = subprocess.Popen(
                    [self._player, "-"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                proc.communicate(input=wav_bytes, timeout=3)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()
