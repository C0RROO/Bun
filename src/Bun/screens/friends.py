from textual.app import ComposeResult
from textual.containers import Container

from Bun.components.action_input import ActionInput
from Bun.components.navbar import NavBar
from Bun.components.status_footer import StatusFooter
from Bun.screens.base import BasePage


class FriendsScreen(BasePage):
    PAGE_ID = "--friends"
    PAGE_TITLE = "Friends"
    PAGE_SUBTITLE = "Screen for contacts, friend requests and user search."

    def compose(self) -> ComposeResult:
        with Container(classes="page"):
            yield self.build_header()
            yield ActionInput(
                placeholder="Поиск друзей...",
                button_label="Поиск",
                classes="friends-search-input",
            )
            with Container(classes="page-content page-intro"):
                yield from self.build_page_intro()
            yield NavBar()
            yield StatusFooter()
