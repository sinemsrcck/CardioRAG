
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class IndexState:
    def __init__(self, db_path="data/index_state_v4.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pdf_index_state (
                file_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                error_message TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def get(self, file_id):
        row = self.conn.execute(
            """
            SELECT status, chunk_count
            FROM pdf_index_state
            WHERE file_id = ?
            """,
            (file_id,)
        ).fetchone()

        if row is None:
            return None

        return {
            "status": row[0],
            "chunk_count": row[1]
        }

    def set_status(
        self,
        file_id,
        file_path,
        status,
        chunk_count=0,
        error_message=None
    ):
        self.conn.execute(
            """
            INSERT INTO pdf_index_state (
                file_id, file_path, status,
                chunk_count, error_message, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_id) DO UPDATE SET
                file_path = excluded.file_path,
                status = excluded.status,
                chunk_count = excluded.chunk_count,
                error_message = excluded.error_message,
                updated_at = excluded.updated_at
            """,
            (
                file_id,
                str(file_path),
                status,
                chunk_count,
                error_message,
                utc_now()
            )
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
