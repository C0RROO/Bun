import os

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Input, Select, Static

from Bun.components.box_tabs import BoxTabs
from Bun.components.header import AppHeader
from Bun.screens.base import BasePage


class SettingsScreen(BasePage):
    PAGE_ID = "--settings"
    PAGE_TITLE = "Settings"
    PAGE_SUBTITLE = "Screen for profile, preferences and account settings."
    SHOW_NAVBAR = False

    active_tab = reactive("Общие")

    def __init__(self) -> None:
        super().__init__()
        self.audio_device_options = self._get_audio_device_options()
        self.selected_audio_device = os.environ.get("BUN_AUDIO_DEVICE", "default")

    STATUS_OPTIONS = [
        ("Программист", "Программист"),
        ("Дизайнер", "Дизайнер"),
        ("Геймер", "Геймер"),
        ("Разработчик", "Разработчик"),
        ("Киноман", "Киноман"),
        ("Аудиофил", "Аудиофил"),
        ("Фотограф", "Фотограф"),
        ("Музыкант", "Музыкант"),
        ("Писатель", "Писатель"),
        ("Инженер", "Инженер"),
        ("DevOps", "DevOps"),
        ("Аналитик", "Аналитик"),
        ("QA", "QA"),
        ("Архитектор", "Архитектор"),
        ("UI/UX", "UI/UX"),
        ("Иллюстратор", "Иллюстратор"),
        ("Продюсер", "Продюсер"),
        ("Саунд-дизайнер", "Саунд-дизайнер"),
        ("Студент", "Студент"),
        ("Исследователь", "Исследователь"),
        ("Другое", "Другое"),
    ]

    DELETE_UNITS = [
        ("Минуты", "Минуты"),
        ("Часы", "Часы"),
        ("Дни", "Дни"),
    ]

    LANGUAGE_OPTIONS = [
        ("Русский", "Русский"),
        ("English", "English"),
    ]

    START_SCREEN_OPTIONS = [
        ("Чаты", "Чаты"),
        ("Друзья", "Друзья"),
        ("Настройки", "Настройки"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="page"):
            yield self.build_header()
            with Container(classes="page-content"):
                yield BoxTabs(
                    tabs=["Общие", "Приватность"],
                    active_tab=self.active_tab,
                    classes="page-box-tabs",
                )
                with VerticalScroll(classes="settings-scroll"):
                    with Container(
                        classes="settings-tab-content",
                        id="settings-general-tab",
                    ):
                        yield from self.compose_general_settings()
                    with Container(
                        classes="settings-tab-content is-hidden",
                        id="settings-privacy-tab",
                    ):
                        yield from self.compose_privacy_settings()
            yield self.build_footer()

    def on_button_pressed(self, event) -> None:
        if event.button.id == "header-back":
            self.app.switch_mode(self.app.get_return_mode())

    def build_footer(self):
        from Bun.components.status_footer import StatusFooter

        return StatusFooter()

    def compose_general_settings(self) -> ComposeResult:
        with Container(classes="settings-section"):
            yield Static("Профиль", classes="settings-section-title")
            yield Static(
                "Основные данные профиля, которые будут видны в интерфейсе.",
                classes="settings-section-subtitle",
            )
            with Container(classes="settings-field"):
                yield Static("Логин", classes="settings-label")
                yield Input(value="Corroo", classes="settings-input", id="settings-login")
            with Container(classes="settings-field"):
                yield Static("Статус", classes="settings-label")
                yield Select(
                    self.STATUS_OPTIONS,
                    value="Программист",
                    classes="settings-select",
                    id="settings-status-select",
                    allow_blank=False,
                )
            with Container(classes="settings-field is-hidden", id="settings-status-other-wrap"):
                yield Static("Свой статус", classes="settings-label")
                yield Input(
                    placeholder="Введите свой статус...",
                    classes="settings-input",
                    id="settings-status-other",
                )

        with Container(classes="settings-section"):
            yield Static("Интерфейс", classes="settings-section-title")
            yield Static(
                "Внешние настройки приложения и поведение при запуске.",
                classes="settings-section-subtitle",
            )
            with Container(classes="settings-field"):
                yield Static("Язык интерфейса", classes="settings-label")
                yield Select(
                    self.LANGUAGE_OPTIONS,
                    value="Русский",
                    classes="settings-select",
                    allow_blank=False,
                )
            with Container(classes="settings-field"):
                yield Static("Стартовый экран", classes="settings-label")
                yield Select(
                    self.START_SCREEN_OPTIONS,
                    value="Чаты",
                    classes="settings-select",
                    allow_blank=False,
                )
            with Container(classes="settings-field"):
                yield Static("Устройство воспроизведения", classes="settings-label")
                yield Select(
                    self.audio_device_options,
                    value=self._resolve_audio_device_value(),
                    classes="settings-select",
                    id="settings-audio-device",
                    allow_blank=False,
                )

    def compose_privacy_settings(self) -> ComposeResult:
        with Container(classes="settings-section"):
            yield Static("История сообщений", classes="settings-section-title")
            yield Static(
                "Автоматическая очистка и управление локальным хранилищем.",
                classes="settings-section-subtitle",
            )
            with Container(classes="settings-field"):
                yield Static("Очищать сообщения через", classes="settings-label")
                with Horizontal(classes="settings-inline-field"):
                    with Container(classes="settings-inline-part settings-inline-time"):
                        yield Input(value="7", classes="settings-input", id="settings-retention")
                    with Container(classes="settings-inline-part settings-inline-unit"):
                        yield Select(
                            self.DELETE_UNITS,
                            value="Дни",
                            classes="settings-select",
                            allow_blank=False,
                        )
            with Horizontal(classes="settings-actions-row"):
                yield Button(
                    "Экспорт\nсообщений",
                    classes="settings-secondary-button settings-actions-button settings-actions-primary",
                )
                yield Button(
                    "Импорт\nсообщений",
                    classes="settings-secondary-button settings-actions-button",
                )
            yield Button("Удалить все сообщения", classes="settings-danger-button")

    @on(BoxTabs.TabChanged)
    def on_settings_tab_changed(self, event: BoxTabs.TabChanged) -> None:
        self.active_tab = event.tab
        self._sync_settings_tabs()

    @on(Select.Changed, "#settings-status-select")
    def on_status_changed(self, event: Select.Changed) -> None:
        other_wrap = self.query_one("#settings-status-other-wrap", Container)
        other_wrap.set_class(event.value != "Другое", "is-hidden")

    @on(Select.Changed, "#settings-audio-device")
    def on_audio_device_changed(self, event: Select.Changed) -> None:
        os.environ["BUN_AUDIO_DEVICE"] = str(event.value)

    @on(Input.Changed, "#settings-retention")
    def on_retention_changed(self, event: Input.Changed) -> None:
        value = event.value
        digits = "".join(ch for ch in value if ch.isdigit())
        if value != digits:
            event.input.value = digits

    def _resolve_audio_device_value(self) -> str:
        available = {str(value) for _, value in self.audio_device_options}
        if self.selected_audio_device in available:
            return self.selected_audio_device
        return next(iter(available))

    def _get_audio_device_options(self) -> list[tuple[str, str]]:
        try:
            import sounddevice as sd

            options: list[tuple[str, str]] = [("default", "default")]
            for idx, device in enumerate(sd.query_devices()):
                name = device.get("name", f"Device {idx}")
                options.append((f"{idx}: {name}", str(idx)))
            return options
        except Exception:
            return [("default", "default")]

    def on_mount(self) -> None:
        self._sync_settings_tabs()

    def _sync_settings_tabs(self) -> None:
        general = self.query_one("#settings-general-tab", Container)
        privacy = self.query_one("#settings-privacy-tab", Container)
        is_general = self.active_tab == "Общие"
        general.set_class(not is_general, "is-hidden")
        privacy.set_class(is_general, "is-hidden")
    def build_header(self) -> AppHeader:
        return AppHeader(title="Настройки", meta="", show_back=True)
