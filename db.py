import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "job_outreach.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    linkedin_job_id TEXT UNIQUE,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    job_url TEXT,
    posted_date TEXT,
    keyword_score REAL DEFAULT 0,
    ai_score REAL DEFAULT 0,
    ai_summary TEXT,
    status TEXT DEFAULT 'scraped',
    scraped_at TEXT
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES jobs(id),
    name TEXT,
    title TEXT,
    email TEXT,
    linkedin_profile_url TEXT,
    source TEXT,
    found_at TEXT
);

CREATE TABLE IF NOT EXISTS outreach (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER REFERENCES jobs(id),
    contact_id INTEGER REFERENCES contacts(id),
    email_subject TEXT,
    email_body TEXT,
    sent_at TEXT,
    status TEXT DEFAULT 'draft',
    response_received INTEGER DEFAULT 0,
    response_date TEXT,
    notes TEXT
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


def insert_job(job: dict) -> int | None:
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT OR IGNORE INTO jobs (linkedin_job_id, title, company, location, description, job_url, posted_date, scraped_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (job["linkedin_job_id"], job["title"], job["company"],
             job.get("location"), job.get("description"), job.get("job_url"),
             job.get("posted_date"), datetime.now().isoformat()),
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
        return cur.lastrowid
    finally:
        conn.close()


def update_scores(job_id: int, keyword_score: float, ai_score: float, ai_summary: str):
    conn = get_conn()
    conn.execute(
        "UPDATE jobs SET keyword_score=?, ai_score=?, ai_summary=?, status='scored' WHERE id=?",
        (keyword_score, ai_score, ai_summary, job_id),
    )
    conn.commit()
    conn.close()


def get_top_jobs(limit: int = 5) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """SELECT * FROM jobs
           WHERE status = 'scored' AND ai_score >= ?
           ORDER BY ai_score DESC, keyword_score DESC
           LIMIT ?""",
        (6.0, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unsent_jobs(limit: int = 5) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        """SELECT j.* FROM jobs j
           WHERE j.status = 'scored'
           AND j.ai_score >= ?
           AND j.id NOT IN (SELECT job_id FROM outreach WHERE status = 'sent')
           ORDER BY j.ai_score DESC, j.keyword_score DESC
           LIMIT ?""",
        (6.0, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_contact(contact: dict) -> int:
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO contacts (job_id, name, title, email, linkedin_profile_url, source, found_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (contact["job_id"], contact.get("name"), contact.get("title"),
         contact.get("email"), contact.get("linkedin_profile_url"),
         contact.get("source"), datetime.now().isoformat()),
    )
    conn.commit()
    contact_id = cur.lastrowid
    conn.close()
    return contact_id


def insert_outreach(outreach: dict) -> int:
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO outreach (job_id, contact_id, email_subject, email_body, status)
           VALUES (?, ?, ?, ?, ?)""",
        (outreach["job_id"], outreach["contact_id"],
         outreach["email_subject"], outreach["email_body"], outreach.get("status", "draft")),
    )
    conn.commit()
    outreach_id = cur.lastrowid
    conn.close()
    return outreach_id


def mark_sent(outreach_id: int):
    conn = get_conn()
    conn.execute(
        "UPDATE outreach SET status='sent', sent_at=? WHERE id=?",
        (datetime.now().isoformat(), outreach_id),
    )
    conn.commit()
    conn.close()


def already_scraped(linkedin_job_id: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM jobs WHERE linkedin_job_id = ?", (linkedin_job_id,)).fetchone()
    conn.close()
    return row is not None
