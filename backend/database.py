import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import config

DB_PATH = config.BASE_DIR / "conversations.db"


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            result_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrievals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            chunk_rank INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            page INTEGER,
            distance REAL NOT NULL,
            was_rejected INTEGER NOT NULL DEFAULT 0,
            was_injection INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def create_conversation(title: str) -> int:
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO conversations (title, created_at) VALUES (?, ?)",
        (title, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def list_conversations():
    conn = _get_connection()
    rows = conn.execute(
        "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_messages(conversation_id: int):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT id, role, content, result_json, created_at FROM messages "
        "WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_message(conversation_id: int, role: str, content: str, result_json: str = None) -> int:
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO messages (conversation_id, role, content, result_json, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (conversation_id, role, content, result_json, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_message_result(message_id: int, result_json: str):
    conn = _get_connection()
    conn.execute(
        "UPDATE messages SET result_json = ? WHERE id = ?",
        (result_json, message_id),
    )
    conn.commit()
    conn.close()


def add_retrieval_log(
    message_id: int,
    question: str,
    chunks: list,
    was_rejected: bool = False,
    was_injection: bool = False,
):
    """
    chunks: list of dicts، كل واحد فيه {rank, text, page, distance}
    """
    conn = _get_connection()
    now = datetime.now(timezone.utc).isoformat()
    for chunk in chunks:
        conn.execute(
            """
            INSERT INTO retrievals
                (message_id, question, chunk_rank, chunk_text, page, distance, was_rejected, was_injection, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                question,
                chunk["rank"],
                chunk["text"],
                chunk.get("page"),
                chunk["distance"],
                int(was_rejected),
                int(was_injection),
                now,
            ),
        )
    conn.commit()
    conn.close()


def get_retrievals_for_message(message_id: int):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT chunk_rank, chunk_text, page, distance, was_rejected, was_injection "
        "FROM retrievals WHERE message_id = ? ORDER BY chunk_rank ASC",
        (message_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_retrievals():
    conn = _get_connection()
    rows = conn.execute(
        "SELECT id, message_id, question, chunk_rank, chunk_text, page, distance, "
        "was_rejected, was_injection, created_at FROM retrievals ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_conversation(conversation_id: int):
    conn = _get_connection()
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()


def conversation_exists(conversation_id: int) -> bool:
    conn = _get_connection()
    row = conn.execute(
        "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    conn.close()
    return row is not None