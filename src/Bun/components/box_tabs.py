from __future__ import annotations

from collections.abc import Sequence

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button


class BoxTabs(Widget, can_focus=True):
    """Compact horizontally scrollable tabs."""

    BINDINGS = [
        Binding("left", "previous_tab", "Previous tab", show=False),
        Binding("right", "next_tab", "Next tab", show=False),
    ]

    class TabChanged(Message):
        """Posted when the active tab changes."""

        def __init__(self, box_tabs: BoxTabs, tab: str, index: int) -> None:
            self.box_tabs = box_tabs
            self.tab = tab
            self.index = index
            super().__init__()

    active_index = reactive(0, init=False)

    def __init__(
        self,
        tabs: Sequence[str] | None = None,
        *,
        active_tab: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._tabs = list(tabs or ["Все", "Семья", "Работа", "Игровой", "Архив"])
        if not self._tabs:
            raise ValueError("BoxTabs requires at least one tab")
        self._initial_active_tab = active_tab

    def compose(self) -> ComposeResult:
        with HorizontalScroll(classes="box-tabs-scroll"):
            for index, tab in enumerate(self._tabs):
                classes = "box-tab-button"
                if tab == "Архив":
                    classes = "box-tab-button box-tab-button-archive"
                yield Button(
                    tab,
                    id=f"box-tab-{index}",
                    classes=classes,
                    compact=True,
                )

    def on_mount(self) -> None:
        if self._initial_active_tab in self._tabs:
            self.active_index = self._tabs.index(self._initial_active_tab)
        else:
            self.active_index = 0
        self.call_after_refresh(self._sync_active_tab)

    def watch_active_index(self, _: int, __: int) -> None:
        if self.is_mounted:
            self.call_after_refresh(self._sync_active_tab)

    def action_previous_tab(self) -> None:
        self.active_index = (self.active_index - 1) % len(self._tabs)
        self._sync_active_tab()

    def action_next_tab(self) -> None:
        self.active_index = (self.active_index + 1) % len(self._tabs)
        self._sync_active_tab()

    @on(Button.Pressed, ".box-tab-button")
    def on_tab_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        self.active_index = int(button_id.removeprefix("box-tab-"))
        self._sync_active_tab()

    def _sync_active_tab(self) -> None:
        scroll = self.query_one(".box-tabs-scroll", HorizontalScroll)
        buttons = list(self.query(".box-tab-button").results(Button))
        active_button: Button | None = None
        for index, button in enumerate(buttons):
            is_active = index == self.active_index
            button.set_class(is_active, "is-active")
            if is_active:
                active_button = button
        if active_button is not None:
            scroll.scroll_to_widget(active_button, animate=False)
            self.post_message(
                self.TabChanged(self, self._tabs[self.active_index], self.active_index)
            )
