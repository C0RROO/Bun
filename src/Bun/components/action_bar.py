from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Static


class ActionBar(Widget):
    """Reusable compact action bar for contextual chat actions."""

    class ActionPressed(Message):
        def __init__(self, action_bar: ActionBar, action: str) -> None:
            self.action_bar = action_bar
            self.action = action
            super().__init__()

    def __init__(
        self,
        *,
        label: str = "",
        button_label: str = "Действие",
        action: str = "action",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.label = label
        self.button_label = button_label
        self.action = action

    def compose(self) -> ComposeResult:
        with Horizontal(classes="action-bar-inner"):
            if self.label:
                yield Static(self.label, classes="action-bar-label")
            yield Button(
                self.button_label,
                id=f"action-bar-{self.action}",
                classes="action-bar-button",
            )

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.post_message(self.ActionPressed(self, self.action))
