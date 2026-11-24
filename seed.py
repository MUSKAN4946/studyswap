"""Seed script: creates the three starting study sessions.

Run from the project root:
    python seed.py

It is safe to run more than once: existing sessions are left unchanged.
"""

from app.db import get_conn, init_db

SESSIONS = [
    ("S1", "Algebra", "Monday 16:00", 3),
    ("S2", "Resume review", "Tuesday 17:00", 2),
    ("S3", "Python", "Wednesday 16:00", 4),
]


def seed() -> None:
    # Make sure tables, index and trigger exist before inserting data
    init_db()
    conn = get_conn()
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO sessions (id, title, start, capacity) "
            "VALUES (?, ?, ?, ?)",
            SESSIONS,
        )
        conn.commit()

        rows = conn.execute(
            "SELECT id, title, start, capacity FROM sessions ORDER BY id"
        ).fetchall()
        print("Sessions in database:")
        for r in rows:
            print(f"  {r['id']} | {r['title']} | {r['start']} | capacity {r['capacity']}")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()