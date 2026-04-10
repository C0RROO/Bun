from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.widget import Widget


class GlobalVolumeOverlay(Widget):
    """Global volume toast shown under the header."""

    def __init__(self) -> None:
        super().__init__(id="global-volume-toast")
        self._volume = 0.8
        self._hide_timer = None

    def on_mount(self) -> None:
        self.display = False

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        self.display = True
        self.refresh()
        if self._hide_timer is not None:
            self._hide_timer.stop()
        self._hide_timer = self.set_timer(1.5, self._hide)

    def _hide(self) -> None:
        self.display = False

    def render(self) -> Text:
        label = Style(color="#F4F4F4")
        percent = f"Громкость {int(self._volume * 100)}%"
        return Text(percent, style=label)
