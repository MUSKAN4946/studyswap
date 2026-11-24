"""Automatic tests for the four mandatory cases of StudySwap.

Every test runs on a fresh temporary database, so the real studyswap.db
file is never touched.

Run from the project root:
    python -m pytest -v
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

SESSIONS = [
    ("S1", "Algebra", "Monday 16:00", 3),
    ("S2", "Resume review", "Tuesday 17:00", 2),
    ("S3", "Python", "Wednesday 16:00", 4),
]

FULL_ERROR = {"error": "session_full", "message": "This session has no places left."}


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client that uses a brand new temporary database file."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    with TestClient(app) as test_client:  # startup creates tables, index, trigger
        conn = db.get_conn()
        conn.executemany(
            "INSERT INTO sessions (id, title, start, capacity) VALUES (?, ?, ?, ?)",
            SESSIONS,
        )
        conn.commit()
        conn.close()
        yield test_client


def book(client, session_id, alias):
    return client.post("/bookings", json={"sessionId": session_id, "alias": alias})


def count_confirmed(session_id):
    conn = db.get_conn()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE session_id = ? AND status = 'confirmed'",
            (session_id,),
        ).fetchone()[0]
    finally:
        conn.close()


# ---------- Basics ----------

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_list_sessions_shows_three_seeded_sessions(client):
    response = client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert [s["id"] for s in data] == ["S1", "S2", "S3"]
    assert [s["capacity"] for s in data] == [3, 2, 4]
    assert all(s["seatsLeft"] == s["capacity"] for s in data)


def test_session_details_and_unknown_session(client):
    book(client, "S1", "owl42")
    detail = client.get("/sessions/S1")
    assert detail.status_code == 200
    assert detail.json()["booked"] == 1
    assert detail.json()["bookings"][0]["alias"] == "owl42"

    missing = client.get("/sessions/S99")
    assert missing.status_code == 404
    assert missing.json()["error"] == "session_not_found"


# ---------- Case 1: the fourth booking on a three-place session ----------

def test_fourth_booking_on_three_place_session_is_rejected(client):
    for alias in ["owl42", "fox17", "cat99"]:
        assert book(client, "S1", alias).status_code == 201

    fourth = book(client, "S1", "owl43")
    assert fourth.status_code == 409
    assert fourth.json() == FULL_ERROR

    # Must remain true: the session still has exactly 3 bookings.
    assert count_confirmed("S1") == 3
    assert client.get("/sessions/S1").json()["seatsLeft"] == 0


def test_cancel_returns_the_place_and_same_request_then_succeeds(client):
    ids = []
    for alias in ["owl42", "fox17", "cat99"]:
        ids.append(book(client, "S1", alias).json()["id"])

    assert book(client, "S1", "owl43").status_code == 409  # full

    cancelled = client.delete(f"/bookings/{ids[2]}")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert count_confirmed("S1") == 2

    again = book(client, "S1", "owl43")  # the very same request as before
    assert again.status_code == 201
    assert count_confirmed("S1") == 3


def test_capacity_is_enforced_by_the_database_itself(client):
    """Bypass the API completely: the database trigger must still refuse."""
    conn = db.get_conn()
    try:
        for alias in ["owl42", "fox17"]:
            conn.execute(
                "INSERT INTO bookings (session_id, alias, status) VALUES ('S2', ?, 'confirmed')",
                (alias,),
            )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="session_full"):
            conn.execute(
                "INSERT INTO bookings (session_id, alias, status) VALUES ('S2', 'cat99', 'confirmed')"
            )
        conn.rollback()
    finally:
        conn.close()
    assert count_confirmed("S2") == 2


# ---------- Case 2: a session that does not exist ----------

def test_booking_for_unknown_session_is_rejected_and_not_stored(client):
    response = book(client, "S99", "ghost77")
    assert response.status_code == 404
    assert response.json()["error"] == "session_not_found"

    conn = db.get_conn()
    try:
        assert conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] == 0
    finally:
        conn.close()


def test_database_refuses_booking_with_unknown_session(client):
    """The foreign key is the hard guarantee behind the check in the handler."""
    conn = db.get_conn()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO bookings (session_id, alias, status) VALUES ('S99', 'ghost77', 'confirmed')"
            )
    finally:
        conn.close()


# ---------- Case 3: the same person booking twice ----------

def test_same_alias_cannot_book_the_same_session_twice(client):
    assert book(client, "S3", "owl42").status_code == 201
    second = book(client, "S3", "owl42")
    assert second.status_code == 409
    assert second.json()["error"] == "already_booked"
    assert count_confirmed("S3") == 1


def test_same_alias_can_book_a_different_session(client):
    assert book(client, "S1", "owl42").status_code == 201
    assert book(client, "S3", "owl42").status_code == 201


def test_same_alias_can_book_again_after_cancelling(client):
    first = book(client, "S3", "owl42").json()["id"]
    assert client.delete(f"/bookings/{first}").status_code == 200
    assert book(client, "S3", "owl42").status_code == 201


# ---------- Case 4: the server restarts ----------

def test_bookings_survive_a_server_restart(client):
    book(client, "S1", "owl42")
    book(client, "S3", "fox17")

    # A new TestClient runs the startup again, like a restarted server.
    # It uses the same database file, so the data must still be there.
    with TestClient(app) as restarted:
        sessions = {s["id"]: s for s in restarted.get("/sessions").json()}
    assert sessions["S1"]["booked"] == 1
    assert sessions["S3"]["booked"] == 1


# ---------- Errors always have a readable body ----------

def test_invalid_alias_gives_readable_422(client):
    response = book(client, "S1", "no")  # too short
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["message"]


def test_missing_field_gives_readable_422(client):
    response = client.post("/bookings", json={"sessionId": "S1"})
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_cancel_unknown_and_already_cancelled_booking(client):
    assert client.delete("/bookings/999").status_code == 404

    booking_id = book(client, "S1", "owl42").json()["id"]
    assert client.delete(f"/bookings/{booking_id}").status_code == 200
    again = client.delete(f"/bookings/{booking_id}")
    assert again.status_code == 409
    assert again.json()["error"] == "already_cancelled"