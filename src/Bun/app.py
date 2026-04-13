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
from Bun.storage import Database
from pathlib import Path

logging.getLogger("textual_image._terminal").setLevel(logging.ERROR)


class Bun(App[None]):
    """Main application for the Bun TUI."""

    CSS_PATH = [
        "styles/base.tcss",
        "styles/auth.tcss",
        "styles/header.tcss",
        "styles/global_volume.tcss",
        "styles/status_footer.tcss",
        "styles/box_tabs.tcss",
        "styles/navbar.tcss",
        "styles/action_input.tcss",
        "styles/action_bar.tcss",
        "styles/chat_list.tcss",
        "styles/chat_thread.tcss",
        "styles/friend_list.tcss",
        "styles/settings.tcss",
    ]
    MODES = {
        "auth": AuthScreen,
        "chats": ChatsScreen,
        "friends": FriendsScreen,
        "settings": SettingsScreen,
    }
    DEFAULT_MODE = "auth"

    BINDINGS = [
        Binding("shift+p", "show_settings", "Настройки"),
        Binding("q", "quit", "Выход"),
    ]


    def __init__(self) -> None:
        super().__init__()
        self.global_volume_percent = 80
        self.register_theme(BUN_THEME)
        self.theme = BUN_THEME.name
        self.db: Database | None = None
        self.user_dir: Path | None = None

    def on_mount(self) -> None:
        self._ensure_volume_toast()

    def on_screen_resume(self, event) -> None:  # noqa: ANN001
        self._ensure_volume_toast()

    def action_show_auth(self) -> None:
        self.switch_mode("auth")
        self._sync_navbar()

    def action_show_chats(self) -> None:
        self.ensure_db()
        self.switch_mode("chats")
        self._sync_navbar()

    def action_show_friends(self) -> None:
        self.ensure_db()
        self.switch_mode("friends")
        self._sync_navbar()

    def action_show_settings(self) -> None:
        self.ensure_db()
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

    def action_command_palette(self) -> None:
        if self.use_command_palette:
            from textual.command import CommandPalette, SimpleProvider

            if not CommandPalette.is_open(self):
                commands = []
                if self.screen.query("HelpPanel"):
                    commands.append(
                        (
                            "Клавиши",
                            self.action_hide_help_panel,
                            "Скрыть подсказки по клавишам и виджету",
                        )
                    )
                else:
                    commands.append(
                        (
                            "Клавиши",
                            self.action_show_help_panel,
                            "Показать подсказки по клавишам и виджету",
                        )
                    )
                commands.append(
                    (
                        "Скриншот",
                        lambda: self.action_screenshot(),
                        "Сохранить SVG-снимок текущего экрана",
                    )
                )
                if not self.ansi_color:
                    def _open_themes() -> None:
                        themes = sorted(
                            self.available_themes.values(), key=lambda theme: theme.name
                        )
                        theme_commands = [
                            (
                                theme.name,
                                (lambda name=theme.name: setattr(self, "theme", name)),
                                getattr(theme, "description", None),
                            )
                            for theme in themes
                        ]
                        self.push_screen(
                            CommandPalette(
                                providers=[SimpleProvider(self.screen, theme_commands)],
                                placeholder="Поиск тем…",
                            )
                        )

                    commands.append(
                        (
                            "Темы",
                            _open_themes,
                            "Выбрать тему оформления",
                        )
                    )
                commands.append(
                    (
                        "Настройки",
                        self.action_show_settings,
                        "Открыть настройки приложения",
                    )
                )
                commands.append(
                    (
                        "Выход",
                        self.action_quit,
                        "Закрыть приложение",
                    )
                )
                self.push_screen(
                    CommandPalette(
                        providers=[SimpleProvider(self.screen, commands)],
                        placeholder="Поиск команд…",
                    )
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

    def ensure_db(self) -> None:
        if self.db is not None:
            return
        self.login_user("Corroo")

    def login_user(self, login: str) -> None:
        login = login.strip() or "Corroo"
        base_dir = Path.home() / ".local" / "share" / "bun" / "users" / login
        base_dir.mkdir(parents=True, exist_ok=True)
        (base_dir / "Downloads").mkdir(parents=True, exist_ok=True)
        self.user_dir = base_dir
        db_path = base_dir / "bun.db"
        self.db = Database(db_path, base_dir, login)
