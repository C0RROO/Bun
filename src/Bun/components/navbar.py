from textual import events, on
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

    def on_mount(self) -> None:
        self.sync_active()

    def on_screen_resume(self, _: events.ScreenResume) -> None:
        self.sync_active()

    def on_screen_suspend(self, _: events.ScreenSuspend) -> None:
        self.sync_active()

    def sync_active(self) -> None:
        mode = getattr(self.app, "current_mode", "")
        chats = self.query_one("#navbar-chats")
        friends = self.query_one("#navbar-friends")
        chats.remove_class("-active")
        friends.remove_class("-active")
        if mode == "chats":
            chats.add_class("-active")
        elif mode == "friends":
            friends.add_class("-active")

    @on(Button.Pressed, "#navbar-chats")
    def on_chats_pressed(self) -> None:
        if hasattr(self.app, "action_show_chats"):
            self.app.action_show_chats()
        self.call_after_refresh(self.sync_active)

    @on(Button.Pressed, "#navbar-friends")
    def on_friends_pressed(self) -> None:
        if hasattr(self.app, "action_show_friends"):
            self.app.action_show_friends()
        self.call_after_refresh(self.sync_active)
