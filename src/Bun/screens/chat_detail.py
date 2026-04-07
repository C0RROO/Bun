from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from messenger_tui.components.action_input import ActionInput
from messenger_tui.components.header import AppHeader
from messenger_tui.components.status_footer import StatusFooter
from messenger_tui.data import ChatUser
from messenger_tui.screens.base import BasePage


class ChatDetailScreen(BasePage):
    """Temporary chat detail screen."""

    SHOW_NAVBAR = False

    def __init__(self, user: ChatUser) -> None:
        super().__init__()
        self.user = user

    def build_header(self) -> AppHeader:
        meta = "online"
        if not self.user.status:
            meta = "offline"
        meta = f"{meta} • {self.user.group}"
        return AppHeader(title=self.user.login, meta=meta, show_back=True)

    def compose(self) -> ComposeResult:
        with Container(classes="page"):
            yield self.build_header()
            with Container(classes="page-content"):
                with Container(classes="chat-detail-placeholder"):
                    yield Static(f"Чат с {self.user.login}", classes="chat-detail-title")
            yield ActionInput(
                placeholder="Введите сообщение...",
                button_label="Отправить",
                clear_on_submit=True,
                classes="chat-action-input",
            )
            yield StatusFooter()

    def on_button_pressed(self, event) -> None:
        if event.button.id == "header-back":
            self.app.pop_screen()
