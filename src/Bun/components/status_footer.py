from __future__ import annotations

from textual import events
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Static


class StatusFooter(Static):
    """Bottom status bar with rotating messages."""

    messages = (
        "А вы знали, что булочки бывают с корицей? А вы знали, что булочки бывают с корицей?",
        "Новая булочка в компании!",
        "Тишина. Булочка отдыхает.",
        "Dimon записал голосовое (12 сек)",
        "В сети: 47 булочек.",
    )

    active_index = reactive(0, init=False)
    marquee_offset = reactive(0, init=False)

    def __init__(self) -> None:
        super().__init__()
        self._rotation_timer: Timer | None = None
        self._marquee_timer: Timer | None = None

    def on_mount(self) -> None:
        self._sync_message()
        self._rotation_timer = self.set_interval(10.0, self._advance_message)
        self._marquee_timer = self.set_interval(0.2, self._advance_marquee)

    def watch_active_index(self, _: int, __: int) -> None:
        self.marquee_offset = 0
        self._sync_message()

    def watch_marquee_offset(self, _: int, __: int) -> None:
        self._sync_message()

    def _advance_message(self) -> None:
        self.active_index = (self.active_index + 1) % len(self.messages)

    def _advance_marquee(self) -> None:
        message = self.messages[self.active_index]
        available_width = self._available_width
        if len(message) <= available_width:
            if self.marquee_offset != 0:
                self.marquee_offset = 0
            return
        scroll_text = f"{message}   "
        self.marquee_offset = (self.marquee_offset + 1) % len(scroll_text)

    @property
    def _available_width(self) -> int:
        return max(1, self.size.width - 4)

    def _sync_message(self) -> None:
        message = self.messages[self.active_index]
        available_width = self._available_width
        if len(message) <= available_width:
            self.update(message)
            return

        scroll_text = f"{message}   {message}"
        start = self.marquee_offset
        end = start + available_width
        self.update(scroll_text[start:end])

    def on_enter(self, _: events.Enter) -> None:
        if self._rotation_timer is not None:
            self._rotation_timer.pause()

    def on_leave(self, _: events.Leave) -> None:
        if self._rotation_timer is not None:
            self._rotation_timer.resume()
