from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.containers import VerticalScroll
from textual.widgets import LoadingIndicator

from Bun.components.action_input import ActionInput
from Bun.components.action_bar import ActionBar
from Bun.components.chat_thread import ChatThread
from Bun.components.header import AppHeader
from Bun.components.status_footer import StatusFooter
from Bun.storage import ChatSummary
from Bun.screens.base import BasePage


class ChatDetailScreen(BasePage):
    """Temporary chat detail screen."""

    SHOW_NAVBAR = False

    def __init__(self, user: ChatSummary) -> None:
        super().__init__()
        self.user = user

    def build_header(self) -> AppHeader:
        db = getattr(self.app, "db", None)
        info = db.get_chat_info(self.user.chat_id) if db else {}
        if info.get("kind") == "group":
            title = info.get("title") or self.user.login
            meta = f"{info.get('member_count', 0)} участников • {info.get('online_count', 0)} онлайн"
        else:
            title = self.user.login
            meta = "в сети" if self.user.status else "не в сети"
        return AppHeader(title=title, meta=meta, show_back=True)

    def compose(self) -> ComposeResult:
        with Container(classes="page"):
            yield self.build_header()
            with Container(classes="page-content"):
                with Container(classes="chat-loading", id="chat-loading"):
                    yield LoadingIndicator()
                yield Container(classes="chat-thread-host", id="chat-thread-host")
            yield ActionBar(
                button_label="Прокрутить вниз",
                action="scroll-bottom",
                classes="chat-action-bar is-hidden",
            )
            yield ActionInput(
                placeholder="Введите сообщение...",
                button_label="Отправить",
                secondary_button_label="◉",
                attach_button_label="⎘",
                clear_on_submit=True,
                classes="chat-action-input",
            )
            yield StatusFooter()

    def on_mount(self) -> None:
        self.call_after_refresh(self._load_chat_thread)
        self.set_interval(0.2, self._update_scroll_action_bar)
        try:
            input_widget = self.query_one(ActionInput).query_one("Input")
            self.set_focus(input_widget)
        except Exception:
            pass

    def _load_chat_thread(self) -> None:
        host = self.query_one("#chat-thread-host", Container)
        if not host.query(ChatThread):
            host.mount(ChatThread(self.user.chat_id, classes="chat-detail-thread"))
        self.query_one("#chat-loading", Container).add_class("is-hidden")
        self.call_after_refresh(self._scroll_chat_to_bottom)
        self.set_timer(0.2, self._scroll_chat_to_bottom)

    def on_button_pressed(self, event) -> None:
        if event.button.id == "header-back":
            self.app.pop_screen()

    @on(ActionBar.ActionPressed)
    def on_action_bar_pressed(self, event: ActionBar.ActionPressed) -> None:
        if event.action == "scroll-bottom":
            self._scroll_chat_to_bottom()
            self._set_action_bar_visible(False)

    def _scroll_chat_to_bottom(self) -> None:
        try:
            scroll = self.query_one(ChatThread).query_one(".chat-thread-scroll", VerticalScroll)
        except Exception:
            return
        scroll.scroll_end(animate=False, immediate=True)

    def _update_scroll_action_bar(self) -> None:
        try:
            scroll = self.query_one(ChatThread).query_one(".chat-thread-scroll", VerticalScroll)
        except Exception:
            return
        distance_to_bottom = max(scroll.max_scroll_y - scroll.scroll_offset.y, 0)
        self._set_action_bar_visible(distance_to_bottom > 6)

    def _set_action_bar_visible(self, visible: bool) -> None:
        action_bar = self.query_one(ActionBar)
        action_bar.set_class(not visible, "is-hidden")
