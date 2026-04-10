from textual.app import App
from textual import events
from textual.binding import Binding

from Bun.screens.auth import AuthScreen
from Bun.screens.chats import ChatsScreen
from Bun.screens.friends import FriendsScreen
from Bun.screens.settings import SettingsScreen
from Bun.themes import MESSENGER_THEME
from Bun.components.global_volume import GlobalVolumeOverlay
from Bun.components.voice_message import VoiceMessage


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
        self.global_volume_percent = 80
        self.register_theme(MESSENGER_THEME)
        self.theme = MESSENGER_THEME.name

    def on_mount(self) -> None:
        self._ensure_volume_toast()

    def on_screen_resume(self, event) -> None:  # noqa: ANN001
        self._ensure_volume_toast()

    def action_show_auth(self) -> None:
        self.switch_mode("auth")

    def action_show_chats(self) -> None:
        self.switch_mode("chats")

    def action_show_friends(self) -> None:
        self.switch_mode("friends")

    def action_show_settings(self) -> None:
        self.switch_mode("settings")

    def on_key(self, event: events.Key) -> None:
        key = event.key
        if key not in {"shift+up", "shift+down", "shift_down"}:
            return
        if "up" in key:
            self.adjust_global_volume_percent(5, show=True)
        else:
            self.adjust_global_volume_percent(-5, show=True)
        event.stop()

    @property
    def global_volume(self) -> float:
        return self.global_volume_percent / 100

    def adjust_global_volume_percent(self, delta: int, *, show: bool) -> None:
        self.global_volume_percent = max(
            0, min(100, self.global_volume_percent + delta)
        )
        if show:
            self.show_global_volume()
        self._notify_volume_changed()

    def show_global_volume(self) -> None:
        overlay = self._ensure_volume_toast()
        if overlay is None:
            return
        overlay.set_volume(self.global_volume)

    def _notify_volume_changed(self) -> None:
        try:
            voices = list(self.screen.query(VoiceMessage))
        except Exception:
            voices = []
        if not voices:
            voices = list(self.query(VoiceMessage))
        for voice in voices:
            voice.on_global_volume_changed()

    def _ensure_volume_toast(self) -> GlobalVolumeOverlay | None:
        try:
            overlay = self.screen.query_one(GlobalVolumeOverlay)
            return overlay
        except Exception:
            pass
        try:
            overlay = GlobalVolumeOverlay()
            self.screen.mount(overlay)
            return overlay
        except Exception:
            return None
