from textual import on
from textual.app import ComposeResult
from textual.containers import Container

from Bun.components.box_tabs import BoxTabs
from Bun.components.chat_list import ChatList, ChatListItem
from Bun.components.navbar import NavBar
from Bun.components.status_footer import StatusFooter
from Bun.screens.chat_detail import ChatDetailScreen
from Bun.screens.base import BasePage


class ChatsScreen(BasePage):
    PAGE_ID = "--chats"
    PAGE_TITLE = "Chats"
    PAGE_SUBTITLE = "Screen with the list of conversations and messages."

    def compose(self) -> ComposeResult:
        with Container(classes="page"):
            yield self.build_header()
            with Container(classes="page-content"):
                yield BoxTabs(classes="page-box-tabs")
                yield ChatList(
                    group="Все",
                    classes="page-chat-list",
                )
            yield NavBar()
            yield StatusFooter()

    @on(ChatListItem.Selected)
    def open_chat(self, event: ChatListItem.Selected) -> None:
        self.app.push_screen(ChatDetailScreen(event.user))

    @on(BoxTabs.TabChanged)
    def filter_chats(self, event: BoxTabs.TabChanged) -> None:
        chat_list = self.query_one(ChatList)
        chat_list.set_group(event.tab)
