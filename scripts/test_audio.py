from __future__ import annotations

import os
from pathlib import Path

import sounddevice as sd
import soundfile as sf


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    audio_path = project_root / "media" / "voice" / "voice_test.WAV"
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    device = os.environ.get("BUN_AUDIO_DEVICE")
    if device is not None:
        try:
            device = int(device)
        except ValueError:
            pass

    data, samplerate = sf.read(str(audio_path), always_2d=True)
    sd.play(data, samplerate, device=device)
    sd.wait()


if __name__ == "__main__":
    main()
