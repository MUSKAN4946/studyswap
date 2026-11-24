"""Stretch: fire many bookings at the same moment and prove the limit holds.

Every worker is a separate thread with its own database connection. A barrier
makes all threads start at the same instant. Each worker runs the same single
INSERT that the API uses, so the capacity trigger and the unique index are
tested under real simultaneous writers.

Two ways to run it (from the project root):
    python -m pytest -v tests/concurrency_test.py
    python -m tests.concurrency_test

A temporary database is used, so the real studyswap.db is never touched.
"""

import sqlite3
import tempfile
import threading
from pathlib import Path

from app import db

SESSIONS = [
    ("S1", "Algebra", "Monday 16:00", 3),
    ("S2", "Resume review", "Tuesday 17:00", 2),
    ("S3", "Python", "Wednesday 16:00", 4),
]

INSERT_SQL = "INSERT INTO bookings (session_id, alias, status) VALUES (?, ?, 'confirmed')"


def setup_database() -> None:
    """Create tables, index and trigger in the database at db.DB_PATH and add the sessions."""
    db.init_db()
    conn = db.get_conn()
    try:
        conn.executemany(
            "INSERT INTO sessions (id, title, start, capacity) VALUES (?, ?, ?, ?)",
            SESSIONS,
        )
        conn.commit()
    finally:
        conn.close()


def count_confirmed(session_id: str) -> int:
    conn = db.get_conn()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE session_id = ? AND status = 'confirmed'",
            (session_id,),
        ).fetchone()[0]
    finally:
        conn.close()


def fire(session_id: str, aliases: list) -> list:
    """Try to book the session once per alias, all at the same moment.

    Returns one outcome string per alias.
    """
    barrier = threading.Barrier(len(aliases))
    lock = threading.Lock()
    outcomes = []

    def worker(alias: str) -> None:
        conn = db.get_conn()
        try:
            barrier.wait()  # every thread waits here, then they all start together
            try:
                conn.execute(INSERT_SQL, (session_id, alias))
                conn.commit()
                outcome = "confirmed"
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                text = str(exc)
                if "session_full" in text:
                    outcome = "session_full"
                elif "UNIQUE" in text:
                    outcome = "already_booked"
                else:
                    outcome = "unexpected: " + text
            except sqlite3.Error as exc:
                outcome = "unexpected: " + str(exc)
        finally:
            conn.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=worker, args=(a,)) for a in aliases]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return outcomes


# ---------- pytest tests ----------

def test_many_simultaneous_bookings_never_exceed_capacity(tmp_path, monkeypatch):
    """30 people try to take the 3 places of S1 at once, repeated in 5 rounds."""
    for round_no in range(5):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / f"round{round_no}.db")
        setup_database()

        aliases = [f"user{i:02d}" for i in range(30)]
        outcomes = fire("S1", aliases)

        assert len(outcomes) == 30
        assert outcomes.count("confirmed") == 3
        assert outcomes.count("session_full") == 27
        assert count_confirmed("S1") == 3


def test_simultaneous_bookings_on_a_two_place_session(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "two_places.db")
    setup_database()

    outcomes = fire("S2", [f"user{i:02d}" for i in range(20)])

    assert outcomes.count("confirmed") == 2
    assert outcomes.count("session_full") == 18
    assert count_confirmed("S2") == 2


def test_same_alias_fired_ten_times_at_once_books_only_once(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "same_alias.db")
    setup_database()

    outcomes = fire("S3", ["owl42"] * 10)

    assert outcomes.count("confirmed") == 1
    assert outcomes.count("already_booked") == 9
    assert count_confirmed("S3") == 1


# ---------- runnable report (python -m tests.concurrency_test) ----------

def main() -> int:
    failed = False
    with tempfile.TemporaryDirectory() as folder:
        for round_no in range(1, 6):
            db.DB_PATH = Path(folder) / f"round{round_no}.db"
            setup_database()

            outcomes = fire("S1", [f"user{i:02d}" for i in range(30)])
            confirmed = outcomes.count("confirmed")
            full = outcomes.count("session_full")
            other = len(outcomes) - confirmed - full
            in_db = count_confirmed("S1")

            print(
                f"Round {round_no}: 30 simultaneous requests for S1 (capacity 3) -> "
                f"{confirmed} confirmed, {full} session_full, {other} other | "
                f"confirmed rows in database: {in_db}"
            )
            if confirmed != 3 or in_db != 3 or other != 0:
                failed = True

    print()
    print("RESULT: capacity held in every round." if not failed else "RESULT: FAILED, capacity was broken.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())