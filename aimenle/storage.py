from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    url        TEXT PRIMARY KEY,
    source     TEXT NOT NULL,
    data       TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen  TEXT NOT NULL
)
"""

UPSERT = """
INSERT INTO products (url, source, data, first_seen, last_seen)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(url) DO UPDATE SET
    source = excluded.source,
    data = excluded.data,
    last_seen = excluded.last_seen
"""


class Store:
    def __init__(self, path):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def save(self, source: str, items: List[Dict]) -> int:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self.conn:
            for item in items:
                self.conn.execute(
                    UPSERT,
                    (item["url"], source, json.dumps(item, ensure_ascii=False), now, now),
                )
        return len(items)

    def count(self, source: Optional[str] = None) -> int:
        if source:
            cur = self.conn.execute("SELECT COUNT(*) FROM products WHERE source = ?", (source,))
        else:
            cur = self.conn.execute("SELECT COUNT(*) FROM products")
        return cur.fetchone()[0]

    def rows(self, source: Optional[str] = None) -> List[Dict]:
        query = "SELECT source, data, first_seen, last_seen FROM products"
        args = ()
        if source:
            query += " WHERE source = ?"
            args = (source,)
        query += " ORDER BY first_seen, url"

        out = []
        for src, data, first_seen, last_seen in self.conn.execute(query, args):
            row = json.loads(data)
            row.update(source=src, first_seen=first_seen, last_seen=last_seen)
            out.append(row)
        return out

    def export(self, path, fmt: str, source: Optional[str] = None) -> int:
        rows = self.rows(source)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "json":
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        elif fmt == "csv":
            columns: List[str] = []
            for row in rows:
                for key in row:
                    if key not in columns:
                        columns.append(key)
            with path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
        else:
            raise ValueError(f"unsupported export format: {fmt}")
        return len(rows)

    def close(self) -> None:
        self.conn.close()
