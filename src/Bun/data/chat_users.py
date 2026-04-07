from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ChatGroup = Literal["default", "Семья", "Работа", "Игровой", "Архив"]


@dataclass(frozen=True, slots=True)
class ChatUser:
    status: bool
    login: str
    last_message: str
    last_message_time: str
    count_new_messages: int
    group: ChatGroup = "default"


CHAT_USERS: list[ChatUser] = [
    ChatUser(
        status=True,
        login="mila",
        last_message="Ты дома или еще в дороге?",
        last_message_time="08:12",
        count_new_messages=2,
        group="Семья",
    ),
    ChatUser(
        status=False,
        login="dadcore",
        last_message="Не забудь позвонить бабушке вечером.",
        last_message_time="Вчера",
        count_new_messages=0,
        group="Семья",
    ),
    ChatUser(
        status=True,
        login="teamlead_ivan",
        last_message="Созвон перенесли на 14:30, успеваешь?",
        last_message_time="09:41",
        count_new_messages=4,
        group="Работа",
    ),
    ChatUser(
        status=False,
        login="qa_nika",
        last_message="Я завела баг по авторизации, посмотри позже.",
        last_message_time="09:05",
        count_new_messages=1,
        group="Работа",
    ),
    ChatUser(
        status=True,
        login="backend_max",
        last_message="API уже отдает unread_count, можно подключать.",
        last_message_time="10:16",
        count_new_messages=0,
        group="Работа",
    ),
    ChatUser(
        status=True,
        login="pixel_fox",
        last_message="Вечером идем в рейд, не опаздывай.",
        last_message_time="11:03",
        count_new_messages=7,
        group="Игровой",
    ),
    ChatUser(
        status=False,
        login="raid_boss",
        last_message="Я собрал новый билд, потом скину скрин.",
        last_message_time="Вчера",
        count_new_messages=0,
        group="Игровой",
    ),
    ChatUser(
        status=True,
        login="nord",
        last_message="Слушай, скинь потом свой конфиг терминала.",
        last_message_time="12:28",
        count_new_messages=3,
        group="default",
    ),
    ChatUser(
        status=False,
        login="luna",
        last_message="Увидела твой новый интерфейс, выглядит сильно.",
        last_message_time="Пн",
        count_new_messages=0,
        group="default",
    ),
    ChatUser(
        status=True,
        login="siberian_cat",
        last_message="Погнали вечером кофе пить и кодить.",
        last_message_time="13:12",
        count_new_messages=5,
        group="default",
    ),
    ChatUser(
        status=False,
        login="hexbyte",
        last_message="Я тебе кинул ссылку на классную TUI-библиотеку.",
        last_message_time="Вт",
        count_new_messages=0,
        group="Архив",
    ),
    ChatUser(
        status=True,
        login="ghost_mode",
        last_message="Сегодня буду поздно, но в сети появлюсь.",
        last_message_time="13:44",
        count_new_messages=1,
        group="Архив",
    ),
]


def get_users_by_group(group: str) -> list[ChatUser]:
    if group == "Все":
        return [user for user in CHAT_USERS if user.group == "default"]
    return [user for user in CHAT_USERS if user.group == group]
