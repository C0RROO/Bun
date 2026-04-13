from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input


class ActionInput(Widget):
    """Reusable input row with a single action button."""

    class Submitted(Message):
        """Posted when the user submits the current input value."""

        def __init__(self, action_input: ActionInput, value: str) -> None:
            self.action_input = action_input
            self.value = value
            super().__init__()

    class SecondaryPressed(Message):
        """Posted when the optional secondary action button is pressed."""

        def __init__(self, action_input: ActionInput) -> None:
            self.action_input = action_input
            super().__init__()

    def __init__(
        self,
        *,
        placeholder: str = "",
        button_label: str = "Отправить",
        secondary_button_label: str | None = None,
        attach_button_label: str | None = None,
        value: str = "",
        clear_on_submit: bool = False,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.placeholder = placeholder
        self.button_label = button_label
        self.secondary_button_label = secondary_button_label
        self.attach_button_label = attach_button_label
        self.value = value
        self.clear_on_submit = clear_on_submit

    def compose(self) -> ComposeResult:
        with Horizontal(classes="action-input"):
            if self.attach_button_label is not None:
                yield Button(
                    self.attach_button_label,
                    classes="action-input-attach-button",
                    id="action-input-attach",
                )
            yield Input(
                value=self.value,
                placeholder=self.placeholder,
                classes="action-input-field",
            )
            if self.secondary_button_label is not None:
                yield Button(
                    self.secondary_button_label,
                    classes="action-input-audio-button",
                    id="action-input-secondary",
                )
            yield Button(
                self.button_label,
                classes="action-input-button",
                id="action-input-submit",
            )

    def get_value(self) -> str:
        return self.query_one(Input).value

    def _submit(self) -> None:
        value = self.get_value().strip()
        self.post_message(self.Submitted(self, value))
        if self.clear_on_submit:
            self.query_one(Input).value = ""

    @on(Input.Submitted)
    def on_input_submitted(self, _: Input.Submitted) -> None:
        self._submit()

    @on(Button.Pressed, "#action-input-submit")
    def on_button_pressed(self, _: Button.Pressed) -> None:
        self._submit()

    @on(Button.Pressed, "#action-input-secondary")
    def on_secondary_button_pressed(self, _: Button.Pressed) -> None:
        self.post_message(self.SecondaryPressed(self))
