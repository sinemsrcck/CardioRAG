
import re
import sqlite3
from pathlib import Path


class BM25Store:
    def __init__(self, db_path="data/bm25_v4.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")

        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(
                chunk_id UNINDEXED,
                file_id UNINDEXED,
                filename UNINDEXED,
                page UNINDEXED,
                content,
                tokenize='unicode61'
            )
        """)
        self.conn.commit()

    def add_chunks(self, records):
        """
        records:
        [
            {
                "id": "...",
                "file_id": "...",
                "filename": "...",
                "page": 1,
                "text": "..."
            }
        ]
        """
        with self.conn:
            for record in records:
                self.conn.execute(
                    "DELETE FROM chunks_fts WHERE chunk_id = ?",
                    (record["id"],)
                )
                self.conn.execute(
                    """
                    INSERT INTO chunks_fts (
                        chunk_id, file_id, filename, page, content
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        record["id"],
                        record["file_id"],
                        record["filename"],
                        record["page"],
                        record["text"]
                    )
                )

    def delete_file(self, file_id):
        with self.conn:
            self.conn.execute(
                "DELETE FROM chunks_fts WHERE file_id = ?",
                (file_id,)
            )

    def search(self, query, top_k=20):
        tokens = re.findall(r"\w+", query.lower())

        if not tokens:
            return []

        # FTS5 sorgu sözdiziminde güvenli terim kullanımı
        match_query = " OR ".join(
            '"' + token.replace('"', '""') + '"'
            for token in tokens
        )

        rows = self.conn.execute(
            """
            SELECT chunk_id, content, filename, page,
                   bm25(chunks_fts) AS score
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            ORDER BY score ASC
            LIMIT ?
            """,
            (match_query, top_k)
        ).fetchall()

        return [
            {
                "id": row[0],
                "text": row[1],
                "metadata": {
                    "filename": row[2],
                    "page": int(row[3])
                },
                "bm25_score": float(-row[4])
            }
            for row in rows
        ]

    def count(self):
        return self.conn.execute(
            "SELECT COUNT(*) FROM chunks_fts"
        ).fetchone()[0]

    def close(self):
        self.conn.close()
