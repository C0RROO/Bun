from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import sqlite3


@dataclass(frozen=True, slots=True)
class ChatSummary:
    chat_id: int
    user_id: int
    status: bool
    login: str
    last_message: str
    last_message_time: str
    count_new_messages: int
    group: str
    kind: str
    title: str | None


@dataclass(frozen=True, slots=True)
class MessageRow:
    id: int
    chat_id: int
    sender_id: int
    sender_login: str
    sender_is_self: bool
    body: str
    created_at: str
    delivered: bool
    read: bool
    kind: str
    attachment_path: str | None
    attachment_blob: bytes | None
    duration_seconds: float | None


class Database:
    def __init__(self, db_path: Path, user_dir: Path, login: str) -> None:
        self.db_path = db_path
        self.user_dir = user_dir
        self.login = login
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()
        self._ensure_profile()
        self._seed_if_empty()

    def close(self) -> None:
        self.conn.close()

    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                login TEXT UNIQUE NOT NULL,
                status INTEGER NOT NULL DEFAULT 0,
                role TEXT,
                is_self INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                device_name TEXT,
                public_key TEXT,
                last_seen TEXT,
                UNIQUE(user_id, device_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                title TEXT,
                kind TEXT NOT NULL DEFAULT 'direct',
                group_name TEXT NOT NULL DEFAULT 'default',
                last_message_id INTEGER,
                unread_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS participants (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(chat_id, user_id),
                FOREIGN KEY(chat_id) REFERENCES chats(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY,
                kind TEXT NOT NULL,
                path TEXT,
                blob BLOB,
                mime TEXT,
                size_bytes INTEGER,
                duration_seconds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                body TEXT,
                created_at TEXT NOT NULL,
                delivered INTEGER NOT NULL DEFAULT 0,
                read INTEGER NOT NULL DEFAULT 0,
                edited_at TEXT,
                deleted_at TEXT,
                kind TEXT NOT NULL DEFAULT 'text',
                attachment_id INTEGER,
                FOREIGN KEY(chat_id) REFERENCES chats(id),
                FOREIGN KEY(sender_id) REFERENCES users(id),
                FOREIGN KEY(attachment_id) REFERENCES attachments(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'pending'
            );
            """
        )
        cur.execute("SELECT COUNT(*) as count FROM schema_version")
        if cur.fetchone()["count"] == 0:
            cur.execute("INSERT INTO schema_version(version) VALUES (1)")
        self.conn.commit()
        self._ensure_columns()

    def _ensure_columns(self) -> None:
        cur = self.conn.cursor()
        # chats.kind, chats.title may be missing in older dbs
        cur.execute("PRAGMA table_info(chats)")
        columns = {row[1] for row in cur.fetchall()}
        if "kind" not in columns:
            cur.execute("ALTER TABLE chats ADD COLUMN kind TEXT NOT NULL DEFAULT 'direct'")
        if "title" not in columns:
            cur.execute("ALTER TABLE chats ADD COLUMN title TEXT")
        if "group_name" not in columns:
            cur.execute("ALTER TABLE chats ADD COLUMN group_name TEXT NOT NULL DEFAULT 'default'")
        self.conn.commit()

    def _ensure_profile(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM users WHERE is_self = 1")
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO users(login, status, role, is_self) VALUES (?, ?, ?, 1)",
                (self.login, 1, "программист"),
            )
            self.conn.commit()

    def _seed_if_empty(self) -> None:
        if os.environ.get("BUN_SEED") != "1":
            return
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM chats")
        if cur.fetchone()["count"] > 0:
            return

        test_data_dir = self._get_test_data_dir()

        # Seed users
        users = [
            (self.login, 1, "программист", 1),
            ("mila", 1, "дизайнер", 0),
            ("nord", 1, "разработчик", 0),
            ("ghost", 0, "геймер", 0),
        ]
        for login, status, role, is_self in users:
            cur.execute(
                "INSERT OR IGNORE INTO users(login, status, role, is_self) VALUES (?, ?, ?, ?)",
                (login, status, role, is_self),
            )

        cur.execute("SELECT id, login FROM users")
        user_ids = {row["login"]: row["id"] for row in cur.fetchall()}

        # Direct chat (1:1)
        cur.execute(
            """
            INSERT INTO chats(title, kind, group_name, updated_at)
            VALUES (?, 'direct', 'default', ?)
            """,
            (None, datetime.now().isoformat(timespec="seconds")),
        )
        direct_chat_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO participants(chat_id, user_id, role) VALUES (?, ?, ?)",
            [
                (direct_chat_id, user_ids[self.login], "owner"),
                (direct_chat_id, user_ids["mila"], "member"),
            ],
        )

        # Group chat
        cur.execute(
            """
            INSERT INTO chats(title, kind, group_name, updated_at)
            VALUES (?, 'group', 'default', ?)
            """,
            ("Bun Team", datetime.now().isoformat(timespec="seconds")),
        )
        group_chat_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO participants(chat_id, user_id, role) VALUES (?, ?, ?)",
            [
                (group_chat_id, user_ids[self.login], "owner"),
                (group_chat_id, user_ids["nord"], "member"),
                (group_chat_id, user_ids["ghost"], "member"),
            ],
        )

        # Messages (direct)
        messages_direct = [
            (direct_chat_id, user_ids["mila"], "Привет! Это приватный чат.", 1, 1),
            (direct_chat_id, user_ids[self.login], "Да, вижу. Тестируем переписку.", 1, 1),
        ]
        for chat_id, sender_id, body, delivered, read in messages_direct:
            cur.execute(
                """
                INSERT INTO messages(chat_id, sender_id, body, created_at, delivered, read, kind)
                VALUES (?, ?, ?, ?, ?, ?, 'text')
                """,
                (
                    chat_id,
                    sender_id,
                    body,
                    datetime.now().isoformat(timespec="seconds"),
                    delivered,
                    read,
                ),
            )

        # Messages (group)
        messages_group = [
            (group_chat_id, user_ids[self.login], "Всем привет! Это групповой чат.", 1, 0),
            (group_chat_id, user_ids["nord"], "Я на связи. Давайте обсудим задачи.", 1, 0),
            (group_chat_id, user_ids["ghost"], "Я сегодня оффлайн, но сообщения вижу.", 1, 0),
        ]
        for chat_id, sender_id, body, delivered, read in messages_group:
            cur.execute(
                """
                INSERT INTO messages(chat_id, sender_id, body, created_at, delivered, read, kind)
                VALUES (?, ?, ?, ?, ?, ?, 'text')
                """,
                (
                    chat_id,
                    sender_id,
                    body,
                    datetime.now().isoformat(timespec="seconds"),
                    delivered,
                    read,
                ),
            )

        # Update last_message_id and unread_count
        for chat_id in (direct_chat_id, group_chat_id):
            cur.execute(
                "SELECT id FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT 1",
                (chat_id,),
            )
            last_id = cur.fetchone()["id"]
            cur.execute(
                "UPDATE chats SET last_message_id = ?, unread_count = 1 WHERE id = ?",
                (last_id, chat_id),
            )

        self.conn.commit()

        # Optional seed media from test_data
        if test_data_dir is not None:
            self._seed_media(test_data_dir, direct_chat_id, user_ids["mila"])

    def _seed_media(self, test_data_dir: Path, chat_id: int, sender_id: int) -> None:
        cur = self.conn.cursor()
        downloads_dir = self.user_dir / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)

        image_source = test_data_dir / "images" / "bun-daily.jpg"
        if image_source.exists():
            image_target = downloads_dir / image_source.name
            if not image_target.exists():
                image_target.write_bytes(image_source.read_bytes())
            cur.execute(
                "INSERT INTO attachments(kind, path, mime) VALUES (?, ?, ?)",
                ("image", str(image_target), "image/jpeg"),
            )
            attachment_id = cur.lastrowid
            cur.execute(
                """
                INSERT INTO messages(chat_id, sender_id, created_at, delivered, read, kind, attachment_id)
                VALUES (?, ?, ?, ?, ?, 'image', ?)
                """,
                (
                    chat_id,
                    sender_id,
                    datetime.now().isoformat(timespec="seconds"),
                    1,
                    0,
                    attachment_id,
                ),
            )

        voice_source = test_data_dir / "voice" / "voice_test.WAV"
        if voice_source.exists():
            voice_blob = voice_source.read_bytes()
            cur.execute(
                "INSERT INTO attachments(kind, blob, mime) VALUES (?, ?, ?)",
                ("voice", voice_blob, "audio/wav"),
            )
            voice_id = cur.lastrowid
            cur.execute(
                """
                INSERT INTO messages(chat_id, sender_id, created_at, delivered, read, kind, attachment_id)
                VALUES (?, ?, ?, ?, ?, 'voice', ?)
                """,
                (
                    chat_id,
                    sender_id,
                    datetime.now().isoformat(timespec="seconds"),
                    1,
                    0,
                    voice_id,
                ),
            )
        self.conn.commit()

    def _get_test_data_dir(self) -> Path | None:
        env_path = os.environ.get("BUN_TEST_DATA_DIR")
        if env_path:
            path = Path(env_path)
            return path if path.exists() else None
        return None

    # --- Query layer (kept for UI wiring) ---
    def get_chat_summaries(self, group: str) -> list[ChatSummary]:
        group_key = "default" if group == "Все" else group
        cur = self.conn.cursor()
        if group == "Все":
            cur.execute(
                """
                SELECT c.id as chat_id,
                       MIN(u.id) as user_id,
                       MIN(u.login) as login,
                       MAX(u.status) as status,
                       c.group_name,
                       c.unread_count,
                       m.body as last_message,
                       m.created_at as last_time,
                       c.kind,
                       c.title
                FROM chats c
                LEFT JOIN participants p ON p.chat_id = c.id
                LEFT JOIN users u ON u.id = p.user_id AND u.is_self = 0
                LEFT JOIN messages m ON m.id = c.last_message_id
                WHERE c.group_name = 'default'
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                """
            )
        else:
            cur.execute(
                """
                SELECT c.id as chat_id,
                       MIN(u.id) as user_id,
                       MIN(u.login) as login,
                       MAX(u.status) as status,
                       c.group_name,
                       c.unread_count,
                       m.body as last_message,
                       m.created_at as last_time,
                       c.kind,
                       c.title
                FROM chats c
                LEFT JOIN participants p ON p.chat_id = c.id
                LEFT JOIN users u ON u.id = p.user_id AND u.is_self = 0
                LEFT JOIN messages m ON m.id = c.last_message_id
                WHERE c.group_name = ?
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                """,
                (group_key,),
            )
        rows = cur.fetchall()
        return [
            ChatSummary(
                chat_id=row["chat_id"],
                user_id=row["user_id"],
                status=bool(row["status"]),
                login=row["login"],
                last_message=row["last_message"] or "",
                last_message_time=self._format_time(row["last_time"]) if row["last_time"] else "",
                count_new_messages=row["unread_count"],
                group=row["group_name"],
                kind=row["kind"],
                title=row["title"],
            )
            for row in rows
        ]

    def get_friends(self) -> list[ChatSummary]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT c.id as chat_id, u.id as user_id, u.login, u.status, c.group_name,
                   c.unread_count, m.body as last_message, m.created_at as last_time,
                   c.kind, c.title
            FROM chats c
            JOIN participants p ON p.chat_id = c.id
            JOIN users u ON u.id = p.user_id AND u.is_self = 0
            LEFT JOIN messages m ON m.id = c.last_message_id
            WHERE c.kind = 'direct'
            ORDER BY u.login
            """
        )
        rows = cur.fetchall()
        return [
            ChatSummary(
                chat_id=row["chat_id"],
                user_id=row["user_id"],
                status=bool(row["status"]),
                login=row["login"],
                last_message=row["last_message"] or "",
                last_message_time=self._format_time(row["last_time"]) if row["last_time"] else "",
                count_new_messages=row["unread_count"],
                group=row["group_name"],
                kind=row["kind"],
                title=row["title"],
            )
            for row in rows
        ]

    def get_messages(self, chat_id: int) -> list[MessageRow]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT m.id, m.chat_id, m.sender_id, u.login, u.is_self,
                   m.body, m.created_at, m.delivered, m.read, m.kind,
                   a.path, a.blob, a.duration_seconds
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            LEFT JOIN attachments a ON a.id = m.attachment_id
            WHERE m.chat_id = ?
            ORDER BY m.created_at ASC, m.id ASC
            """,
            (chat_id,),
        )
        rows = cur.fetchall()
        return [
            MessageRow(
                id=row["id"],
                chat_id=row["chat_id"],
                sender_id=row["sender_id"],
                sender_login=row["login"],
                sender_is_self=bool(row["is_self"]),
                body=row["body"] or "",
                created_at=row["created_at"],
                delivered=bool(row["delivered"]),
                read=bool(row["read"]),
                kind=row["kind"],
                attachment_path=row["path"],
                attachment_blob=row["blob"],
                duration_seconds=row["duration_seconds"],
            )
            for row in rows
        ]

    def get_chat_info(self, chat_id: int) -> dict[str, object]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT c.id, c.kind, c.title, c.group_name
            FROM chats c
            WHERE c.id = ?
            """,
            (chat_id,),
        )
        chat = cur.fetchone()
        if chat is None:
            return {}
        cur.execute(
            """
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN u.status = 1 THEN 1 ELSE 0 END) as online
            FROM participants p
            JOIN users u ON u.id = p.user_id
            WHERE p.chat_id = ?
            """,
            (chat_id,),
        )
        counts = cur.fetchone()
        cur.execute(
            """
            SELECT u.login
            FROM participants p
            JOIN users u ON u.id = p.user_id
            WHERE p.chat_id = ? AND p.role = 'owner'
            LIMIT 1
            """,
            (chat_id,),
        )
        owner = cur.fetchone()
        return {
            "kind": chat["kind"],
            "title": chat["title"],
            "group_name": chat["group_name"],
            "member_count": counts["total"] or 0,
            "online_count": counts["online"] or 0,
            "owner_login": owner["login"] if owner else None,
        }

    def _format_time(self, raw: str | None) -> str:
        if not raw:
            return ""
        try:
            dt = datetime.fromisoformat(raw)
            return dt.strftime("%H:%M")
        except Exception:
            return raw
