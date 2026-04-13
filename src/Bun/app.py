import logging

from textual.app import App, ScreenStackError, SystemCommand
from textual import events
from textual.binding import Binding

from Bun.screens.auth import AuthScreen
from Bun.screens.chats import ChatsScreen
from Bun.screens.friends import FriendsScreen
from Bun.screens.settings import SettingsScreen
from Bun.themes import BUN_THEME
from Bun.components.global_volume import GlobalVolumeOverlay
from Bun.components.voice_message import VoiceMessage

logging.getLogger("textual_image._terminal").setLevel(logging.ERROR)


class Bun(App[None]):
    """Main application for the Bun TUI."""

    CSS_PATH = "styles/app.tcss"
    MODES = {
        "auth": AuthScreen,
        "chats": ChatsScreen,
        "friends": FriendsScreen,
        "settings": SettingsScreen,
    }
    DEFAULT_MODE = "auth"

    BINDINGS = [
        Binding("shift+p", "show_settings", "Settings"),
        Binding("q", "quit", "Quit"),
    ]


    def __init__(self) -> None:
        super().__init__()
        self.global_volume_percent = 80
        self.register_theme(BUN_THEME)
        self.theme = BUN_THEME.name

    def on_mount(self) -> None:
        self._ensure_volume_toast()

    def on_screen_resume(self, event) -> None:  # noqa: ANN001
        self._ensure_volume_toast()

    def action_show_auth(self) -> None:
        self.switch_mode("auth")
        self._sync_navbar()

    def action_show_chats(self) -> None:
        self.switch_mode("chats")
        self._sync_navbar()

    def action_show_friends(self) -> None:
        self.switch_mode("friends")
        self._sync_navbar()

    def action_show_settings(self) -> None:
        self._last_mode = self.current_mode
        self.switch_mode("settings")
        self._sync_navbar()

    def _sync_navbar(self) -> None:
        def _do() -> None:
            try:
                navbar = self.screen.query_one("NavBar")
                if hasattr(navbar, "sync_active"):
                    navbar.sync_active()
            except Exception:
                pass

        self.call_after_refresh(_do)

    def get_return_mode(self) -> str:
        return getattr(self, "_last_mode", "chats")

    def on_key(self, event: events.Key) -> None:
        key = event.key
        if key not in {"shift+up", "shift+down", "shift_down"}:
            return
        if "up" in key:
            self.adjust_global_volume_percent(5, show=True)
        else:
            self.adjust_global_volume_percent(-5, show=True)
        event.stop()

    def get_system_commands(self, screen):  # noqa: ANN001
        yield from super().get_system_commands(screen)
        yield SystemCommand(
            "Settings",
            "Открыть настройки",
            self.action_show_settings,
        )

    def clear_selection(self) -> None:
        try:
            super().clear_selection()
        except ScreenStackError:
            return

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
