from textual.app import App
from textual.binding import Binding

from messenger_tui.screens.auth import AuthScreen
from messenger_tui.screens.chats import ChatsScreen
from messenger_tui.screens.friends import FriendsScreen
from messenger_tui.screens.settings import SettingsScreen
from messenger_tui.themes import MESSENGER_THEME


class MessengerApp(App[None]):
    """Main application for the messenger TUI."""

    CSS_PATH = "styles/app.tcss"
    MODES = {
        "auth": "auth",
        "chats": "chats",
        "friends": "friends",
        "settings": "settings",
    }
    DEFAULT_MODE = "auth"

    BINDINGS = [
        Binding("a", "show_auth", "Auth"),
        Binding("c", "show_chats", "Chats"),
        Binding("f", "show_friends", "Friends"),
        Binding("s", "show_settings", "Settings"),
        Binding("q", "quit", "Quit"),
    ]

    SCREENS = {
        "auth": AuthScreen,
        "chats": ChatsScreen,
        "friends": FriendsScreen,
        "settings": SettingsScreen,
    }

    def __init__(self) -> None:
        super().__init__()
        self.register_theme(MESSENGER_THEME)
        self.theme = MESSENGER_THEME.name

    def action_show_auth(self) -> None:
        self.switch_mode("auth")

    def action_show_chats(self) -> None:
        self.switch_mode("chats")

    def action_show_friends(self) -> None:
        self.switch_mode("friends")

    def action_show_settings(self) -> None:
        self.switch_mode("settings")
