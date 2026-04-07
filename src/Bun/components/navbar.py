from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button


class NavBar(Widget):
    """Primary navigation bar."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="navbar"):
            yield Button("чаты", id="navbar-chats", classes="navbar-button")
            yield Button("друзья", id="navbar-friends", classes="navbar-button")
