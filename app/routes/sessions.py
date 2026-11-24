"""Endpoints for listing sessions and showing one session in detail."""

from typing import List

from fastapi import APIRouter

from app.db import get_conn
from app.errors import AppError
from app.models import ErrorOut, SessionDetail, SessionOut

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# Only 'confirmed' bookings use up a place. Cancelled ones are ignored.
LIST_SQL = """
SELECT s.id, s.title, s.start, s.capacity,
       COUNT(b.id) AS booked
FROM sessions s
LEFT JOIN bookings b
       ON b.session_id = s.id AND b.status = 'confirmed'
GROUP BY s.id
ORDER BY s.id
"""

ONE_SQL = """
SELECT s.id, s.title, s.start, s.capacity,
       COUNT(b.id) AS booked
FROM sessions s
LEFT JOIN bookings b
       ON b.session_id = s.id AND b.status = 'confirmed'
WHERE s.id = ?
GROUP BY s.id
"""


def _session_dict(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "start": row["start"],
        "capacity": row["capacity"],
        "booked": row["booked"],
        "seatsLeft": row["capacity"] - row["booked"],
    }


@router.get("", response_model=List[SessionOut], summary="List all sessions")
def list_sessions():
    conn = get_conn()
    try:
        rows = conn.execute(LIST_SQL).fetchall()
        return [_session_dict(r) for r in rows]
    finally:
        conn.close()


@router.get(
    "/{session_id}",
    response_model=SessionDetail,
    summary="Show one session with its confirmed bookings",
    responses={404: {"model": ErrorOut}},
)
def get_session(session_id: str):
    conn = get_conn()
    try:
        row = conn.execute(ONE_SQL, (session_id,)).fetchone()
        if row is None:
            raise AppError(
                404,
                "session_not_found",
                f"Session '{session_id}' does not exist.",
            )

        booking_rows = conn.execute(
            "SELECT id, session_id, alias, status FROM bookings "
            "WHERE session_id = ? AND status = 'confirmed' ORDER BY id",
            (session_id,),
        ).fetchall()

        data = _session_dict(row)
        data["bookings"] = [
            {
                "id": b["id"],
                "sessionId": b["session_id"],
                "alias": b["alias"],
                "status": b["status"],
            }
            for b in booking_rows
        ]
        return data
    finally:
        conn.close()