from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def now_et() -> datetime:
    return datetime.now(ET)


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists applications (
                    job_key text primary key,
                    title text,
                    company text,
                    url text,
                    status text,
                    reason text,
                    created_at text
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def already_filed(self, job_key: str) -> bool:
        with self._connect() as conn:
            row = conn.execute("select status from applications where job_key = ?", (job_key,)).fetchone()
        return bool(row and row[0] == "filed")

    def filed_today(self, today: str | None = None) -> int:
        day = today or now_et().strftime("%Y-%m-%d")
        with self._connect() as conn:
            row = conn.execute(
                "select count(*) from applications where status = 'filed' and created_at like ?",
                (day + "%",),
            ).fetchone()
        return int(row[0] if row else 0)

    def record(self, job_key: str, title: str, company: str, url: str, status: str, reason: str) -> None:
        with self._connect() as conn:
            existing = conn.execute("select status from applications where job_key = ?", (job_key,)).fetchone()
            if existing and existing[0] == "filed" and status != "filed":
                return
            stamp = now_et().strftime("%Y-%m-%d %H:%M:%S ET")
            conn.execute(
                """
                insert into applications (job_key, title, company, url, status, reason, created_at)
                values (?, ?, ?, ?, ?, ?, ?)
                on conflict(job_key) do update set
                    title = excluded.title,
                    company = excluded.company,
                    url = excluded.url,
                    status = excluded.status,
                    reason = excluded.reason,
                    created_at = excluded.created_at
                """,
                (job_key, title, company, url, status, reason, stamp),
            )
