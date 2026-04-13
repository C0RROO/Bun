from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual import on
from textual.widgets import Button, Input, Static, Tab, Tabs


class AuthScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        with Container(classes="auth-wrapper"):
            with Vertical(classes="auth-card"):
                yield Static("Bun", classes="auth-title")
                yield Static("Авторизация", classes="auth-subtitle")
                yield Tabs(
                    Tab("Вход", id="auth-login"),
                    Tab("Регистрация", id="auth-register"),
                    id="auth-tabs",
                    classes="auth-tabs",
                )
                with Container(classes="auth-panels"):
                    with Vertical(
                        classes="auth-panel is-active",
                        id="auth-login",
                    ):
                        with Vertical(classes="auth-form"):
                            yield Input(
                                placeholder="Логин",
                                classes="auth-input",
                                id="auth-login-input",
                            )
                            yield Input(
                                placeholder="Пароль",
                                password=True,
                                classes="auth-input",
                            )
                            yield Button("Войти", classes="auth-button")
                    with Vertical(classes="auth-panel", id="auth-register"):
                        with Vertical(classes="auth-form"):
                            yield Input(
                                placeholder="Логин",
                                classes="auth-input",
                            )
                            yield Input(
                                placeholder="Пароль",
                                password=True,
                                classes="auth-input",
                            )
                            yield Input(
                                placeholder="Подтвердите пароль",
                                password=True,
                                classes="auth-input",
                            )
                            yield Button("Создать аккаунт", classes="auth-button")

    @on(Tabs.TabActivated, "#auth-tabs")
    def on_auth_tab(self, event: Tabs.TabActivated) -> None:
        active_id = event.tab.id
        if active_id is None:
            return
        for panel in self.query(".auth-panel"):
            if panel.id == active_id:
                panel.add_class("is-active")
            else:
                panel.remove_class("is-active")

    @on(Button.Pressed, ".auth-button")
    def on_auth_submit(self) -> None:
        try:
            login_input = self.query_one("#auth-login-input", Input)
            login = login_input.value.strip() or "Corroo"
        except Exception:
            login = "Corroo"
        if hasattr(self.app, "login_user"):
            self.app.login_user(login)
        if hasattr(self.app, "action_show_chats"):
            self.app.action_show_chats()
