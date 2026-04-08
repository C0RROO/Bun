from __future__ import annotations

from pathlib import Path
import wave

from textual import on
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
            Path(__file__).resolve().parents[3] / "media" / "audio" / "voice_test.WAV"
        )
        self.total_seconds = total_seconds
        self._playback_timer = None
        self._player = None
        self._sparkline_data = [
            2,
            4,
            5,
            8,
            6,
            7,
            10,
            5,
            3,
            9,
            8,
            6,
            4,
            7,
            11,
            8,
            5,
            4,
            6,
            9,
            7,
            5,
            3,
            6,
            8,
            10,
            7,
            4,
        ]
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
        with Horizontal(classes="voice-message"):
            yield Button("▶", classes="voice-toggle-button", id="voice-toggle")
            with Vertical(classes="voice-main"):
                yield Sparkline(self._sparkline_data, classes="voice-sparkline")
                with Horizontal(classes="voice-meta-row"):
                    yield Static(self._format_time(self.position_seconds), id="voice-current-time")
                    yield Static(self._format_time(self.total_seconds), classes="voice-total-time")

    def on_mount(self) -> None:
        self._playback_timer = self.set_interval(0.25, self._tick_playback, pause=True)

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
        current_time = self.query_one("#voice-current-time", Static)
        current_time.update(self._format_time(value))

    def _tick_playback(self) -> None:
        self.position_seconds = min(self.position_seconds + 0.25, self.total_seconds)
        if self.position_seconds >= self.total_seconds:
            self._stop(reset=False)

    def _play(self) -> None:
        if self.position_seconds >= self.total_seconds:
            self.position_seconds = 0.0
        self.is_playing = True
        if self._playback_timer is not None:
            self._playback_timer.resume()
        self._start_audio_backend()

    def _pause(self) -> None:
        self.is_playing = False
        if self._playback_timer is not None:
            self._playback_timer.pause()
        if self._player is not None:
            try:
                self._player.pause()
            except Exception:
                pass

    def _stop(self, *, reset: bool) -> None:
        self.is_playing = False
        if self._playback_timer is not None:
            self._playback_timer.pause()
        if self._player is not None:
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
        if self._player is None:
            try:
                from simpleplayer.simpleplayer import simpleplayer as AudioBackend

                self._player = AudioBackend(str(self.audio_path))
                self._player.play()
                return
            except Exception:
                self._player = None
                return
        try:
            self._player.resume()
        except Exception:
            pass

    @staticmethod
    def _format_time(value: float) -> str:
        total = max(int(value), 0)
        minutes, seconds = divmod(total, 60)
        return f"{minutes}:{seconds:02d}"
