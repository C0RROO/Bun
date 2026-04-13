from __future__ import annotations

from collections.abc import Sequence

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

# Импортируем Image из textual-image
from textual_image.widget import Image

from Bun.components.voice_message import VoiceMessage


def _open_file(path: Path) -> None:
    target = path.resolve()
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        elif os.name == "nt":
            os.startfile(target)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(target)])
        return
    except Exception:
        pass
    try:
        webbrowser.open(target.as_uri(), new=1)
    except Exception:
        pass


class ClickableImage(Widget):
    can_focus = True

    def __init__(self, path: Path, **kwargs) -> None:
        super().__init__(classes="chat-image-wrapper", **kwargs)
        self.path = path

    def compose(self) -> ComposeResult:
        yield Image(str(self.path), classes="chat-image")

    @on(events.MouseDown)
    def on_mouse_down(self, event: events.MouseDown) -> None:
        if event.button != 1:
            return
        if self.path.exists():
            _open_file(self.path)
            event.stop()


class IncomingBubble(Widget):
    def __init__(self, text: str, time_text: str) -> None:
        super().__init__(classes="chat-bubble chat-bubble-incoming")
        self.text = text
        self.time_text = time_text

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-bubble-inner"):
            yield Static(self.text, classes="chat-bubble-text")
            with Horizontal(classes="chat-bubble-meta-row"):
                yield Static(self.time_text, classes="chat-bubble-time")


class OutgoingBubble(Widget):
    def __init__(
        self,
        text: str,
        time_text: str,
        *,
        delivered: bool,
        read: bool,
    ) -> None:
        super().__init__(classes="chat-bubble chat-bubble-outgoing")
        self.text = text
        self.time_text = time_text
        self.delivered = delivered
        self.read = read

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-bubble-inner"):
            yield Static(self.text, classes="chat-bubble-text")
            with Horizontal(classes="chat-bubble-meta-row"):
                yield Static(self.time_text, classes="chat-bubble-time")
                yield Static(
                    "●",
                    classes="chat-delivery-dot chat-delivery-dot-first is-on"
                    if self.delivered
                    else "chat-delivery-dot chat-delivery-dot-first",
                )
                yield Static(
                    "●",
                    classes="chat-delivery-dot is-on"
                    if self.read
                    else "chat-delivery-dot",
                )


class IncomingMessageGroup(Widget):
    def __init__(self, messages: Sequence[str], time_text: str) -> None:
        super().__init__(classes="chat-group chat-group-incoming")
        self.messages = list(messages)
        self.time_text = time_text

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            last_index = len(self.messages) - 1
            for index, message in enumerate(self.messages):
                time_text = self.time_text if index == last_index else ""
                yield IncomingBubble(message, time_text)


class OutgoingMessageGroup(Widget):
    def __init__(
        self,
        messages: Sequence[str],
        time_text: str,
        *,
        delivered: bool,
        read: bool,
    ) -> None:
        super().__init__(classes="chat-group chat-group-outgoing")
        self.messages = list(messages)
        self.time_text = time_text
        self.delivered = delivered
        self.read = read

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            last_index = len(self.messages) - 1
            for index, message in enumerate(self.messages):
                yield OutgoingBubble(
                    message,
                    self.time_text if index == last_index else "",
                    delivered=self.delivered if index == last_index else False,
                    read=self.read if index == last_index else False,
                )


class OutgoingVoiceMessageGroup(Widget):
    def __init__(
        self,
        time_text: str,
        *,
        delivered: bool,
        read: bool,
    ) -> None:
        super().__init__(classes="chat-group chat-group-outgoing")
        self.time_text = time_text
        self.delivered = delivered
        self.read = read

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            with Vertical(classes="chat-bubble chat-bubble-outgoing voice-bubble"):
                yield VoiceMessage(classes="chat-voice-message")
                with Horizontal(classes="chat-bubble-meta-row"):
                    yield Static(self.time_text, classes="chat-bubble-time")
                    with Horizontal(classes="chat-delivery-group"):
                        yield Static(
                            "●",
                            classes="chat-delivery-dot chat-delivery-dot-first is-on"
                            if self.delivered
                            else "chat-delivery-dot chat-delivery-dot-first",
                        )
                        yield Static(
                            "●",
                            classes="chat-delivery-dot is-on"
                            if self.read
                            else "chat-delivery-dot",
                        )


class IncomingVoiceMessageGroup(Widget):
    def __init__(self, time_text: str) -> None:
        super().__init__(classes="chat-group chat-group-incoming")
        self.time_text = time_text

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            with Vertical(classes="chat-bubble chat-bubble-incoming voice-bubble"):
                yield VoiceMessage(classes="chat-voice-message")
                with Horizontal(classes="chat-bubble-meta-row"):
                    yield Static(self.time_text, classes="chat-bubble-time")


class IncomingImageMessageGroup(Widget):
    """Группа входящих сообщений с изображением (использует textual-image)."""

    def __init__(self, time_text: str) -> None:
        super().__init__(classes="chat-group chat-group-incoming")
        self.time_text = time_text
        self.image_path = (
            Path(__file__).resolve().parents[3]
            / "media"
            / "images"
            / "bun-daily.jpg"
        )

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            with Vertical(classes="chat-bubble chat-bubble-incoming image-bubble"):
                if self.image_path.exists():
                    yield ClickableImage(self.image_path)
                else:
                    yield Static(
                        "🖼️ Изображение недоступно",
                        classes="chat-image-fallback"
                    )
                with Horizontal(classes="chat-bubble-meta-row chat-image-meta-row"):
                    yield Static(self.time_text, classes="chat-bubble-time chat-image-time")

class ChatThread(Widget):
    """Static mock chat thread for the chat detail screen."""

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="chat-thread-scroll"):
            yield Static("Вчера", classes="chat-date-separator")
            yield IncomingMessageGroup(
                [
                    "Привет. Ты уже смотрел, как будет выглядеть новый интерфейс?",
                    "Я хочу, чтобы чат ощущался очень чисто и спокойно.",
                ],
                "21:08",
            )
            yield OutgoingMessageGroup(
                [
                    "Да, как раз собираю минималистичный вариант.",
                    "Хочу, чтобы всё было спокойно и без перегруза.",
                    "Без имён, только текст, время и индикаторы.",
                ],
                "21:10",
                delivered=True,
                read=True,
            )
            yield IncomingMessageGroup(
                [
                    "Это звучит хорошо.",
                    "Главное, чтобы в длинной переписке всё читалось без шума.",
                ],
                "21:12",
            )
            # Теперь здесь реальное изображение, а не псевдографика
            yield IncomingImageMessageGroup("21:14")
            yield Static("Сегодня", classes="chat-date-separator")
            yield IncomingMessageGroup(
                [
                    "Супер. Тогда давай ещё подумаем над отображением сообщений и дат.",
                    "Важно, чтобы было понятно, где мои сообщения, а где сообщения собеседника.",
                    "И чтобы длинный чат нормально скроллился.",
                ],
                "10:15",
            )
            yield OutgoingMessageGroup(
                [
                    "Сделаем сообщения слева и справа, без имён.",
                    "Даты оставим по центру и второстепенным цветом.",
                ],
                "10:18",
                delivered=True,
                read=False,
            )
            yield IncomingMessageGroup(
                [
                    "Хорошо.",
                    "А время лучше показывать прямо внутри блока сообщения, а не отдельно снизу.",
                ],
                "10:21",
            )
            yield OutgoingMessageGroup(
                [
                    "Да, так оно выглядит аккуратнее.",
                    "И ещё добавим два кружка для доставки и прочтения.",
                    "Первый загорелся — сообщение дошло.",
                    "Второй загорелся — сообщение прочитано.",
                ],
                "10:24",
                delivered=True,
                read=False,
            )
            yield IncomingMessageGroup(
                [
                    "Отлично.",
                    "Давай ещё добавим побольше сообщений, чтобы сразу проверить ленту на реальном объёме.",
                ],
                "10:26",
            )
            yield OutgoingMessageGroup(
                [
                    "Уже добавляю.",
                    "После этого можно будет заняться тонкой шлифовкой отступов, ширины пузырей и общей плотности чата.",
                ],
                "10:29",
                delivered=True,
                read=False,
            )
            yield OutgoingVoiceMessageGroup(
                "10:31",
                delivered=True,
                read=False,
            )
