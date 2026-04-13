from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from Bun.storage import ChatSummary


class ChatListItem(Widget):
    """Single chat preview row."""

    class Selected(Message):
        """Posted when a chat row is selected."""

        def __init__(self, item: ChatListItem, user: ChatSummary) -> None:
            self.item = item
            self.user = user
            super().__init__()

    def __init__(
        self,
        user: ChatSummary,
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

        is_group = self.user.kind == "group"
        status_class = "chat-status chat-status-group" if is_group else status_class

        unread_classes = "chat-unread"
        if self.user.count_new_messages == 0:
            unread_classes = "chat-unread chat-unread-empty"

        with Vertical(classes="chat-card-content"):
            with Horizontal(classes="chat-row-top"):
                yield Static("●", classes=status_class)
                title = self.user.login
                if self.user.kind == "group":
                    title = f"[Группа] {self.user.title or self.user.login}"
                yield Static(title, classes="chat-login")
                yield Static(str(self.user.count_new_messages), classes=unread_classes)
            with Horizontal(classes="chat-row-bottom"):
                with Vertical(classes="chat-main"):
                    preview = self.user.last_message
                    if self.user.kind == "group" and preview:
                        preview = f"{self.user.login}: {preview}"
                    yield Static(preview, classes="chat-message")
                yield Static(self.user.last_message_time, classes="chat-time")


class ChatList(Widget):
    """Scrollable list of chat previews."""

    def __init__(
        self,
        users: list[ChatSummary] | None = None,
        group: str = "Все",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._users = users or []
        self._group = group

    def compose(self) -> ComposeResult:
        if not self._users:
            db = getattr(self.app, "db", None)
            if db is not None:
                self._users = db.get_chat_summaries(self._group)
        with VerticalScroll(classes="chat-list-scroll"):
            last_index = len(self._users) - 1
            for index, user in enumerate(self._users):
                yield ChatListItem(user)
                if index != last_index:
                    yield Static(classes="chat-divider")

    def set_group(self, group: str) -> None:
        self._group = group
        db = getattr(self.app, "db", None)
        if db is not None:
            self._users = db.get_chat_summaries(group)
        else:
            self._users = []
        self.refresh(recompose=True)
