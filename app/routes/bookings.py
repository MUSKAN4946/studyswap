"""Endpoints for booking a place and cancelling a booking.

Capacity is NOT checked here with an if-statement. It is enforced by the
database trigger `trg_capacity` (see app/schema.sql). This code only
translates the database's refusal into a readable HTTP error.
"""

import sqlite3

from fastapi import APIRouter

from app.db import get_conn
from app.errors import AppError
from app.models import BookingOut, BookingRequest, ErrorOut

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _booking_dict(row) -> dict:
    return {
        "id": row["id"],
        "sessionId": row["session_id"],
        "alias": row["alias"],
        "status": row["status"],
    }


@router.post(
    "",
    status_code=201,
    response_model=BookingOut,
    summary="Book a place in a session",
    responses={
        404: {"model": ErrorOut, "description": "session_not_found"},
        409: {"model": ErrorOut, "description": "session_full or already_booked"},
        422: {"model": ErrorOut, "description": "validation_error"},
    },
)
def create_booking(body: BookingRequest):
    conn = get_conn()
    try:
        # Friendly early check: a booking must point at a real session.
        # (The foreign key in the database is the hard guarantee.)
        session = conn.execute(
            "SELECT id FROM sessions WHERE id = ?", (body.sessionId,)
        ).fetchone()
        if session is None:
            raise AppError(
                404,
                "session_not_found",
                f"Session '{body.sessionId}' does not exist.",
            )

        try:
            # One single INSERT. The trigger counts confirmed bookings and
            # aborts the insert if the session is already full.
            cursor = conn.execute(
                "INSERT INTO bookings (session_id, alias, status) "
                "VALUES (?, ?, 'confirmed')",
                (body.sessionId, body.alias),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            reason = str(exc)
            if "session_full" in reason:
                raise AppError(
                    409, "session_full", "This session has no places left."
                )
            if "UNIQUE" in reason:
                raise AppError(
                    409,
                    "already_booked",
                    f"Alias '{body.alias}' already has a confirmed booking "
                    f"for session '{body.sessionId}'.",
                )
            if "FOREIGN KEY" in reason:
                raise AppError(
                    404,
                    "session_not_found",
                    f"Session '{body.sessionId}' does not exist.",
                )
            raise

        return {
            "id": cursor.lastrowid,
            "sessionId": body.sessionId,
            "alias": body.alias,
            "status": "confirmed",
        }
    finally:
        conn.close()


@router.delete(
    "/{booking_id}",
    response_model=BookingOut,
    summary="Cancel a booking (the place returns to the pool)",
    responses={
        404: {"model": ErrorOut, "description": "booking_not_found"},
        409: {"model": ErrorOut, "description": "already_cancelled"},
    },
)
def cancel_booking(booking_id: int):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, session_id, alias, status FROM bookings WHERE id = ?",
            (booking_id,),
        ).fetchone()
        if row is None:
            raise AppError(
                404,
                "booking_not_found",
                f"Booking {booking_id} does not exist.",
            )
        if row["status"] == "cancelled":
            raise AppError(
                409,
                "already_cancelled",
                f"Booking {booking_id} is already cancelled.",
            )

        # Row is kept, only the status changes. Only 'confirmed' rows are
        # counted for capacity, so the place goes back to the pool.
        conn.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
            (booking_id,),
        )
        conn.commit()

        data = _booking_dict(row)
        data["status"] = "cancelled"
        return data
    finally:
        conn.close()