from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Static


class AppHeader(Widget):
    """Shared application header."""

    def __init__(
        self,
        *,
        title: str = "Corroo",
        meta: str = "online • программист",
        show_back: bool = False,
        show_settings: bool = False,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        header_classes = "app-header-default"
        if show_back:
            header_classes = "app-header-chat"
        if classes:
            header_classes = f"{header_classes} {classes}"
        super().__init__(id=id, classes=header_classes)
        self.title = title
        self.meta = meta
        self.show_back = show_back
        self.show_settings = show_settings

    def compose(self) -> ComposeResult:
        with Horizontal(classes="header-inner"):
            if self.show_back:
                yield Button("❮", id="header-back", classes="header-button", flat=True)
            with Horizontal(classes="header-center"):
                yield Static(self.title, classes="header-name")
                yield Static(self.meta, classes="header-meta")
            if self.show_settings:
                yield Button(
                    "≡",
                    id="header-settings",
                    classes="header-button",
                    flat=True,
                )
