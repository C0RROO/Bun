from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Static

from Bun.data import CHAT_USERS, ChatUser


class FriendListItem(Widget):
    def __init__(self, user: ChatUser) -> None:
        super().__init__()
        self.user = user

    def compose(self) -> ComposeResult:
        status_class = "friend-status friend-status-online"
        if not self.user.status:
            status_class = "friend-status friend-status-offline"

        with Horizontal(classes="friend-list-item"):
            yield Static("●", classes=status_class)
            yield Static(self.user.login, classes="friend-name")
            yield Button("Удалить", classes="friend-delete-button")


class FriendList(Widget):
    def __init__(self, users: list[ChatUser] | None = None) -> None:
        super().__init__()
        self.users = users or CHAT_USERS

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="friend-list-scroll"):
            last_index = len(self.users) - 1
            for index, user in enumerate(self.users):
                yield FriendListItem(user)
                if index != last_index:
                    yield Static(classes="friend-divider")
