from __future__ import annotations

from pathlib import Path
import os
import math
import wave
import random
import threading
import time

from textual import on, events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Sparkline, Static


class VoiceMessage(Widget):
    """Minimal voice message widget with play / pause and waveform."""

    is_playing = reactive(False)
    position_seconds = reactive(0.0)

    def __init__(
        self,
        *,
        total_seconds: float = 18.0,
        classes: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(classes=classes, id=id)
        self.audio_path = (
            Path(__file__).resolve().parents[3]
            / "media"
            / "voice"
            / "voice_test.WAV"
        )
        self.total_seconds = total_seconds
        self._playback_timer = None
        self._player = None
        self._sd_data = None
        self._sd_fs = None
        self._sd_device = None
        self._sd_mono = None
        self._sparkline_data = [1] * 28
        self._sparkline_phase = 0.0
        self._freq_bins = 28
        self._fft_window = 1024
        self._fft_hop = 512
        self._freq_frames = None
        self._sparkline_display = None
        self._freq_building = False
        self._play_start_epoch = None
        self._play_start_offset = 0.0
        self._freq_seed = None
        self.playback_speed = 1.0
        self._resolve_duration()

    def _resolve_duration(self) -> None:
        if not self.audio_path.exists():
            return
        try:
            with wave.open(str(self.audio_path), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                if rate:
                    self.total_seconds = frames / rate
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with Vertical(classes="voice-message"):
            yield Sparkline(self._sparkline_data, classes="voice-sparkline")
            with Horizontal(classes="voice-meta-row"):
                yield Button("▶", classes="voice-toggle-button", id="voice-toggle")
                yield Static(
                    self._format_time(self.position_seconds),
                    classes="voice-current-time",
                )
                yield Static(
                    self._format_time(self.total_seconds),
                    classes="voice-total-time",
                )

    def on_mount(self) -> None:
        self._playback_timer = self.set_interval(0.1, self._tick_playback, pause=True)
        self._update_sparkline(animated=False)

    @on(Button.Pressed, "#voice-toggle")
    def on_voice_toggle(self) -> None:
        if self.is_playing:
            self._pause()
        else:
            self._play()

    def watch_is_playing(self, is_playing: bool) -> None:
        if not self.is_mounted:
            return
        button = self.query_one("#voice-toggle", Button)
        button.label = "⏸" if is_playing else "▶"

    def watch_position_seconds(self, value: float) -> None:
        if not self.is_mounted:
            return
        current_time = self.query_one(".voice-current-time", Static)
        current_time.update(self._format_time(value))

    def _tick_playback(self) -> None:
        if self._play_start_epoch is not None:
            elapsed = max(time.monotonic() - self._play_start_epoch, 0.0)
            self.position_seconds = min(
                self._play_start_offset + elapsed * self.playback_speed,
                self.total_seconds,
            )
        else:
            self.position_seconds = min(
                self.position_seconds + 0.1 * self.playback_speed,
                self.total_seconds,
            )
        self._update_sparkline(animated=self.is_playing)
        if self.position_seconds >= self.total_seconds:
            self._stop(reset=False)

    def _play(self) -> None:
        if self.position_seconds >= self.total_seconds:
            self.position_seconds = 0.0
        self.is_playing = True
        if self._playback_timer is not None:
            self._playback_timer.resume()
        self._update_sparkline(animated=True)
        self._start_audio_backend()
        self._play_start_offset = self.position_seconds
        if self._start_sounddevice_playback():
            self._play_start_epoch = time.monotonic()
            return

    def _pause(self) -> None:
        self.is_playing = False
        if self._playback_timer is not None:
            self._playback_timer.pause()
        self._play_start_epoch = None
        self._update_sparkline(animated=False)
        if self._sd_data is not None:
            try:
                import sounddevice as sd

                sd.stop()
            except Exception:
                pass
        elif self._player is not None:
            try:
                self._player.pause()
            except Exception:
                pass

    def _stop(self, *, reset: bool) -> None:
        self.is_playing = False
        if self._playback_timer is not None:
            self._playback_timer.pause()
        self._play_start_epoch = None
        self._update_sparkline(animated=False)
        if self._sd_data is not None:
            try:
                import sounddevice as sd

                sd.stop()
            except Exception:
                pass
        elif self._player is not None:
            try:
                self._player.stop()
            except Exception:
                pass
            self._player = None
        if reset:
            self.position_seconds = 0.0

    def _start_audio_backend(self) -> None:
        if not self.audio_path.exists():
            return
        if self._sd_data is not None and self._sd_fs is not None:
            return
        # Prefer sounddevice + soundfile for smoother playback
        try:
            import sounddevice as sd
            import soundfile as sf

            device = os.environ.get("BUN_AUDIO_DEVICE")
            if device is not None:
                try:
                    device = int(device)
                except ValueError:
                    pass
            self._sd_device = device

            self._sd_data, self._sd_fs = sf.read(
                str(self.audio_path),
                dtype="float32",
                always_2d=True,
            )
            self._prepare_audio_buffers()
            return
        except Exception:
            pass

        # Fallback to simpleplayer if available
        try:
            from simpleplayer.playsong import PlaySong

            self._player = PlaySong(str(self.audio_path))
            self._player.play()
        except Exception:
            self._player = None

    def _start_sounddevice_playback(self) -> bool:
        if self._sd_data is None or self._sd_fs is None:
            return False
        try:
            import sounddevice as sd

            if self._sd_device is not None:
                sd.default.device = self._sd_device
            sd.default.latency = "high"
            sd.default.blocksize = 8192

            start_frame = int(self.position_seconds * self._sd_fs)
            if start_frame >= len(self._sd_data):
                start_frame = 0
                self.position_seconds = 0.0
            audio = self._sd_data[start_frame:]
            volume = getattr(self.app, "global_volume", 1.0)
            if volume != 1.0:
                audio = audio * volume
                audio = audio.clip(-1.0, 1.0)
            sd.play(
                audio,
                int(self._sd_fs * self.playback_speed),
                device=self._sd_device,
                blocking=False,
            )
            return True
        except Exception:
            return False

    def _update_sparkline(self, *, animated: bool) -> None:
        if not self.is_mounted:
            return
        if self._sd_mono is not None and self._sd_fs is not None:
            if animated:
                data = self._compute_frequency_bars(self.position_seconds)
            else:
                data = [1] * len(self._sparkline_data)
        elif not animated:
            data = [1] * len(self._sparkline_data)
        else:
            data = []
            self._sparkline_phase += 0.35
            for i in range(len(self._sparkline_data)):
                phase = self._sparkline_phase + (i / 4.0)
                value = 1 + int((math.sin(phase) + 1.0) * 4)
                data.append(max(1, value))
        if animated:
            data = self._smooth_bars(data)
        self._sparkline_data = data
        try:
            spark = self.query_one(Sparkline)
            spark.data = data
        except Exception:
            pass

    def _prepare_audio_buffers(self) -> None:
        if self._sd_data is None:
            return
        samples = self._sd_data
        if samples.ndim == 2 and samples.shape[1] > 1:
            samples = samples.mean(axis=1)
        else:
            samples = samples.reshape(-1)
        self._sd_mono = samples
        self._schedule_frequency_build()

    def _compute_frequency_bars(self, position_seconds: float) -> list[int]:
        if self._sd_mono is None or self._sd_fs is None:
            return [1] * self._freq_bins
        if self._freq_frames:
            if self._freq_seed is None and self._freq_frames:
                self._freq_seed = self._freq_frames[0]
            index = int(
                (position_seconds * self._sd_fs) / max(self._fft_hop, 1)
            )
            index = max(0, min(index, len(self._freq_frames) - 1))
            return self._freq_frames[index]
        if self._freq_seed is None:
            self._freq_seed = self._compute_seed_frame()
        return self._freq_seed

    def _schedule_frequency_build(self) -> None:
        if self._freq_building:
            return
        self._freq_building = True

        def _worker() -> None:
            try:
                self._build_frequency_frames()
            finally:
                self._freq_building = False

        threading.Thread(target=_worker, daemon=True).start()

    def _build_frequency_frames(self) -> None:
        if self._sd_mono is None or self._sd_fs is None:
            return
        total = len(self._sd_mono)
        if total == 0:
            return
        nyquist = self._sd_fs / 2.0
        min_freq = 80.0
        max_freq = min(6000.0, nyquist)
        if max_freq <= min_freq:
            return

        def band_center(index: int) -> float:
            ratio = index / max(self._freq_bins - 1, 1)
            return min_freq * ((max_freq / min_freq) ** ratio)

        def goertzel(window: list[float], target_freq: float) -> float:
            k = int(0.5 + (self._fft_window * target_freq / self._sd_fs))
            omega = (2.0 * math.pi * k) / self._fft_window
            coeff = 2.0 * math.cos(omega)
            s_prev = 0.0
            s_prev2 = 0.0
            for sample in window:
                s = sample + coeff * s_prev - s_prev2
                s_prev2 = s_prev
                s_prev = s
            power = s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2
            return math.sqrt(max(power, 0.0))

        frames = []
        for start in range(0, total, self._fft_hop):
            end = min(total, start + self._fft_window)
            window = list(self._sd_mono[start:end])
            if len(window) < self._fft_window:
                window += [0.0] * (self._fft_window - len(window))
            for i in range(self._fft_window):
                window[i] *= 0.5 - 0.5 * math.cos(
                    (2.0 * math.pi * i) / self._fft_window
                )
            magnitudes = []
            for i in range(self._freq_bins):
                freq = band_center(i)
                magnitudes.append(goertzel(window, freq))
            peak = max(magnitudes) if magnitudes else 0.0
            if peak <= 0.0:
                frames.append([1] * self._freq_bins)
                continue
            bars = []
            for value in magnitudes:
                height = 1 + int((value / peak) * 6)
                bars.append(max(1, min(height, 7)))
            frames.append(bars)
        self._freq_frames = frames or None
        if self._freq_frames and self._freq_seed is None:
            self._freq_seed = self._freq_frames[0]

    def _smooth_bars(self, target: list[int]) -> list[int]:
        if not target:
            return [1] * self._freq_bins
        if self._sparkline_display is None:
            self._sparkline_display = list(target)
            return list(target)
        smoothed = []
        for idx, value in enumerate(target):
            current = self._sparkline_display[idx]
            updated = current + (value - current) * 0.55
            if value > 2 and random.random() < 0.12:
                updated += 0.6
            updated = max(1.0, min(updated, 7.0))
            smoothed.append(int(round(updated)))
        self._sparkline_display = smoothed
        return list(smoothed)

    def _compute_seed_frame(self) -> list[int]:
        if self._sd_mono is None or self._sd_fs is None:
            return [1] * self._freq_bins
        total = len(self._sd_mono)
        if total == 0:
            return [1] * self._freq_bins
        end = min(total, self._fft_window)
        window = list(self._sd_mono[0:end])
        if len(window) < self._fft_window:
            window += [0.0] * (self._fft_window - len(window))
        for i in range(self._fft_window):
            window[i] *= 0.5 - 0.5 * math.cos(
                (2.0 * math.pi * i) / self._fft_window
            )
        nyquist = self._sd_fs / 2.0
        min_freq = 80.0
        max_freq = min(6000.0, nyquist)
        if max_freq <= min_freq:
            return [1] * self._freq_bins

        def band_center(index: int) -> float:
            ratio = index / max(self._freq_bins - 1, 1)
            return min_freq * ((max_freq / min_freq) ** ratio)

        def goertzel(window: list[float], target_freq: float) -> float:
            k = int(0.5 + (self._fft_window * target_freq / self._sd_fs))
            omega = (2.0 * math.pi * k) / self._fft_window
            coeff = 2.0 * math.cos(omega)
            s_prev = 0.0
            s_prev2 = 0.0
            for sample in window:
                s = sample + coeff * s_prev - s_prev2
                s_prev2 = s_prev
                s_prev = s
            power = s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2
            return math.sqrt(max(power, 0.0))

        magnitudes = []
        for i in range(self._freq_bins):
            freq = band_center(i)
            magnitudes.append(goertzel(window, freq))
        peak = max(magnitudes) if magnitudes else 0.0
        if peak <= 0.0:
            return [1] * self._freq_bins
        bars = []
        for value in magnitudes:
            height = 1 + int((value / peak) * 6)
            bars.append(max(1, min(height, 7)))
        return bars

    @staticmethod
    def _format_time(value: float) -> str:
        total = max(int(value), 0)
        minutes, seconds = divmod(total, 60)
        return f"{minutes}:{seconds:02d}"

    def _restart_playback(self) -> None:
        if not self.is_playing:
            return
        self._play_start_epoch = None
        if self._sd_data is not None:
            try:
                import sounddevice as sd

                sd.stop()
            except Exception:
                pass
        self._play()

    def on_global_volume_changed(self) -> None:
        if self.is_playing or self._play_start_epoch is not None:
            self._restart_playback()

    @on(events.MouseDown, ".voice-sparkline")
    def on_sparkline_click(self, event: events.MouseDown) -> None:
        spark = event.control
        width = spark.size.width
        if width <= 1:
            return
        ratio = event.offset.x / max(width - 1, 1)
        ratio = max(0.0, min(1.0, ratio))
        self.position_seconds = ratio * self.total_seconds
        self._play_start_offset = self.position_seconds
        if self.is_playing:
            self._restart_playback()
        else:
            self._update_sparkline(animated=False)
