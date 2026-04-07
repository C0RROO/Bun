from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Label, Static

from messenger_tui.components.header import AppHeader
from messenger_tui.components.navbar import NavBar
from messenger_tui.components.status_footer import StatusFooter


class BasePage(Screen[None]):
    """Base screen layout for application pages."""

    PAGE_ID = "page"
    PAGE_TITLE = "Page"
    PAGE_SUBTITLE = "Page content will be added here."
    SHOW_NAVBAR = True

    def build_header(self) -> AppHeader:
        return AppHeader()

    def build_page_intro(self) -> tuple[Widget, ...]:
        return (
            Label(self.PAGE_ID, classes="page-route"),
            Static(self.PAGE_TITLE, classes="page-title"),
            Static(self.PAGE_SUBTITLE, classes="page-subtitle"),
        )

    def compose(self) -> ComposeResult:
        with Container(classes="page"):
            yield self.build_header()
            with Container(classes="page-content page-intro"):
                yield from self.build_page_intro()
            if self.SHOW_NAVBAR:
                yield NavBar()
            yield StatusFooter()
