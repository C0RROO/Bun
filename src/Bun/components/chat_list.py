from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from Bun.data import CHAT_USERS, ChatUser, get_users_by_group


class ChatListItem(Widget):
    """Single chat preview row."""

    class Selected(Message):
        """Posted when a chat row is selected."""

        def __init__(self, item: ChatListItem, user: ChatUser) -> None:
            self.item = item
            self.user = user
            super().__init__()

    def __init__(
        self,
        user: ChatUser,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.user = user

    def on_click(self, _: events.Click) -> None:
        self.post_message(self.Selected(self, self.user))

    def compose(self) -> ComposeResult:
        status_class = "chat-status chat-status-online"
        if not self.user.status:
            status_class = "chat-status chat-status-offline"

        unread_classes = "chat-unread"
        if self.user.count_new_messages == 0:
            unread_classes = "chat-unread chat-unread-empty"

        with Vertical(classes="chat-card-content"):
            with Horizontal(classes="chat-row-top"):
                yield Static("●", classes=status_class)
                yield Static(self.user.login, classes="chat-login")
                yield Static(str(self.user.count_new_messages), classes=unread_classes)
            with Horizontal(classes="chat-row-bottom"):
                with Vertical(classes="chat-main"):
                    yield Static(self.user.last_message, classes="chat-message")
                yield Static(self.user.last_message_time, classes="chat-time")


class ChatList(Widget):
    """Scrollable list of chat previews."""

    def __init__(
        self,
        users: list[ChatUser] | None = None,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._users = users or get_users_by_group("Все")

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="chat-list-scroll"):
            last_index = len(self._users) - 1
            for index, user in enumerate(self._users):
                yield ChatListItem(user)
                if index != last_index:
                    yield Static(classes="chat-divider")

    def set_users(self, users: list[ChatUser]) -> None:
        self._users = users
        self.refresh(recompose=True)
