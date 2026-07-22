import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
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
    scraped_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    name TEXT,
    title TEXT,
    email TEXT,
    linkedin_profile_url TEXT,
    source TEXT,
    found_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outreach (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    contact_id INTEGER REFERENCES contacts(id),
    email_subject TEXT,
    email_body TEXT,
    sent_at TIMESTAMP,
    status TEXT DEFAULT 'draft',
    response_received BOOLEAN DEFAULT FALSE,
    response_date TIMESTAMP,
    notes TEXT
);
"""


def get_conn():
    return psycopg2.connect(DB_URL)


def init_db():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
    conn.commit()
    conn.close()


def insert_job(job: dict) -> int | None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO jobs (linkedin_job_id, title, company, location, description, job_url, posted_date)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (linkedin_job_id) DO NOTHING
                   RETURNING id""",
                (job["linkedin_job_id"], job["title"], job["company"],
                 job.get("location"), job.get("description"), job.get("job_url"), job.get("posted_date")),
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
    finally:
        conn.close()


def update_scores(job_id: int, keyword_score: float, ai_score: float, ai_summary: str):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE jobs SET keyword_score=%s, ai_score=%s, ai_summary=%s, status='scored' WHERE id=%s",
            (keyword_score, ai_score, ai_summary, job_id),
        )
    conn.commit()
    conn.close()


def get_top_jobs(limit: int = 5) -> list[dict]:
    conn = get_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT * FROM jobs
               WHERE status = 'scored' AND ai_score >= %s
               ORDER BY ai_score DESC, keyword_score DESC
               LIMIT %s""",
            (6.0, limit),
        )
        rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unsent_jobs(limit: int = 5) -> list[dict]:
    conn = get_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT j.* FROM jobs j
               WHERE j.status = 'scored'
               AND j.ai_score >= %s
               AND j.id NOT IN (SELECT job_id FROM outreach WHERE status = 'sent')
               ORDER BY j.ai_score DESC, j.keyword_score DESC
               LIMIT %s""",
            (6.0, limit),
        )
        rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_contact(contact: dict) -> int:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO contacts (job_id, name, title, email, linkedin_profile_url, source)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (contact["job_id"], contact.get("name"), contact.get("title"),
             contact.get("email"), contact.get("linkedin_profile_url"), contact.get("source")),
        )
        row = cur.fetchone()
        conn.commit()
    conn.close()
    return row[0]


def insert_outreach(outreach: dict) -> int:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO outreach (job_id, contact_id, email_subject, email_body, status)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            (outreach["job_id"], outreach["contact_id"],
             outreach["email_subject"], outreach["email_body"], outreach.get("status", "draft")),
        )
        row = cur.fetchone()
        conn.commit()
    conn.close()
    return row[0]


def mark_sent(outreach_id: int):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE outreach SET status='sent', sent_at=NOW() WHERE id=%s",
            (outreach_id,),
        )
    conn.commit()
    conn.close()


def already_scraped(linkedin_job_id: str) -> bool:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM jobs WHERE linkedin_job_id = %s", (linkedin_job_id,))
        exists = cur.fetchone() is not None
    conn.close()
    return exists
