from textual import on
from textual.app import ComposeResult
from textual.containers import Container

from messenger_tui.components.box_tabs import BoxTabs
from messenger_tui.components.chat_list import ChatList, ChatListItem
from messenger_tui.components.navbar import NavBar
from messenger_tui.components.status_footer import StatusFooter
from messenger_tui.data import get_users_by_group
from messenger_tui.screens.chat_detail import ChatDetailScreen
from messenger_tui.screens.base import BasePage


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
                    users=get_users_by_group("Все"),
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
        chat_list.set_users(get_users_by_group(event.tab))
