from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

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
from Bun.storage import MessageRow


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
    def __init__(self, messages: Sequence[str], time_text: str, sender_name: str | None = None) -> None:
        super().__init__(classes="chat-group chat-group-incoming")
        self.messages = list(messages)
        self.time_text = time_text
        self.sender_name = sender_name

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            if self.sender_name:
                yield Static(self.sender_name, classes="chat-sender-name")
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
        sender_name: str | None = None,
    ) -> None:
        super().__init__(classes="chat-group chat-group-outgoing")
        self.messages = list(messages)
        self.time_text = time_text
        self.delivered = delivered
        self.read = read
        self.sender_name = sender_name

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            if self.sender_name:
                yield Static(self.sender_name, classes="chat-sender-name")
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
        audio_bytes: bytes | None = None,
    ) -> None:
        super().__init__(classes="chat-group chat-group-outgoing")
        self.time_text = time_text
        self.delivered = delivered
        self.read = read
        self.audio_bytes = audio_bytes

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            with Vertical(classes="chat-bubble chat-bubble-outgoing voice-bubble"):
                yield VoiceMessage(
                    audio_bytes=self.audio_bytes,
                    classes="chat-voice-message",
                )
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
    def __init__(self, time_text: str, audio_bytes: bytes | None = None) -> None:
        super().__init__(classes="chat-group chat-group-incoming")
        self.time_text = time_text
        self.audio_bytes = audio_bytes

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            with Vertical(classes="chat-bubble chat-bubble-incoming voice-bubble"):
                yield VoiceMessage(
                    audio_bytes=self.audio_bytes,
                    classes="chat-voice-message",
                )
                with Horizontal(classes="chat-bubble-meta-row"):
                    yield Static(self.time_text, classes="chat-bubble-time")


class IncomingImageMessageGroup(Widget):
    """Группа входящих сообщений с изображением (использует textual-image)."""

    def __init__(self, time_text: str, image_path: Path | None) -> None:
        super().__init__(classes="chat-group chat-group-incoming")
        self.time_text = time_text
        self.image_path = image_path

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            with Vertical(classes="chat-bubble chat-bubble-incoming image-bubble"):
                if self.image_path is not None and self.image_path.exists():
                    yield ClickableImage(self.image_path)
                else:
                    yield Static(
                        "🖼️ Изображение недоступно",
                        classes="chat-image-fallback"
                    )
                with Horizontal(classes="chat-bubble-meta-row chat-image-meta-row"):
                    yield Static(self.time_text, classes="chat-bubble-time chat-image-time")


class OutgoingImageMessageGroup(Widget):
    def __init__(self, time_text: str, image_path: Path | None) -> None:
        super().__init__(classes="chat-group chat-group-outgoing")
        self.time_text = time_text
        self.image_path = image_path

    def compose(self) -> ComposeResult:
        with Vertical(classes="chat-group-stack"):
            with Vertical(classes="chat-bubble chat-bubble-outgoing image-bubble"):
                if self.image_path is not None and self.image_path.exists():
                    yield ClickableImage(self.image_path)
                else:
                    yield Static(
                        "🖼️ Изображение недоступно",
                        classes="chat-image-fallback",
                    )
                with Horizontal(classes="chat-bubble-meta-row chat-image-meta-row"):
                    yield Static(self.time_text, classes="chat-bubble-time chat-image-time")

class ChatThread(Widget):
    """Chat thread rendered from the database."""

    def __init__(self, chat_id: int, *, classes: str | None = None) -> None:
        super().__init__(classes=classes)
        self.chat_id = chat_id

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="chat-thread-scroll"):
            db = getattr(self.app, "db", None)
            if db is None:
                return
            messages = db.get_messages(self.chat_id)
            info = db.get_chat_info(self.chat_id)
            current_date = None
            for message in messages:
                date_label = self._format_date_label(message)
                if date_label != current_date:
                    current_date = date_label
                    yield Static(date_label, classes="chat-date-separator")

                time_label = self._format_time(message)
                if message.kind == "voice":
                    if message.sender_is_self:
                        yield OutgoingVoiceMessageGroup(
                            time_label,
                            delivered=message.delivered,
                            read=message.read,
                            audio_bytes=message.attachment_blob,
                        )
                    else:
                        yield IncomingVoiceMessageGroup(
                            time_label,
                            audio_bytes=message.attachment_blob,
                        )
                elif message.kind == "image":
                    image_path = Path(message.attachment_path) if message.attachment_path else None
                    if message.sender_is_self:
                        yield OutgoingImageMessageGroup(time_label, image_path)
                    else:
                        yield IncomingImageMessageGroup(time_label, image_path)
                else:
                    sender_name = message.sender_login if info.get("kind") == "group" else None
                    if message.sender_is_self:
                        yield OutgoingMessageGroup(
                            [message.body],
                            time_label,
                            delivered=message.delivered,
                            read=message.read,
                            sender_name=sender_name,
                        )
                    else:
                        yield IncomingMessageGroup(
                            [message.body],
                            time_label,
                            sender_name=sender_name,
                        )

    def _format_date_label(self, message: MessageRow) -> str:
        try:
            dt = datetime.fromisoformat(message.created_at)
            today = datetime.now().date()
            if dt.date() == today:
                return "Сегодня"
            if dt.date() == (today - timedelta(days=1)):
                return "Вчера"
            return dt.strftime("%d.%m.%Y")
        except Exception:
            return "Сегодня"

    def _format_time(self, message: MessageRow) -> str:
        try:
            dt = datetime.fromisoformat(message.created_at)
            return dt.strftime("%H:%M")
        except Exception:
            return ""
