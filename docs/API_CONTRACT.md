# StudySwap: API Contract

Base URL (local): `http://127.0.0.1:8000`

All requests and responses use JSON. Interactive docs are available at `/docs`.

## Error format

Every error uses the same shape and a proper HTTP status code. An error is never returned with status 200, and never with an empty body.

```json
{ "error": "<machine_code>", "message": "<readable reason>" }
```

## Endpoint summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Check that the app and database work |
| GET | `/sessions` | List all sessions with seats left |
| GET | `/sessions/{session_id}` | Show one session with its confirmed bookings |
| POST | `/bookings` | Book a place in a session |
| DELETE | `/bookings/{booking_id}` | Cancel a booking |

---

## GET /health

**Input:** none

**Success: 200**

```json
{ "status": "ok", "database": "connected" }
```

**Errors:** none expected.

---

## GET /sessions

**Input:** none

**Success: 200**

```json
[
  { "id": "S1", "title": "Algebra", "start": "Monday 16:00", "capacity": 3, "booked": 0, "seatsLeft": 3 },
  { "id": "S2", "title": "Resume review", "start": "Tuesday 17:00", "capacity": 2, "booked": 0, "seatsLeft": 2 },
  { "id": "S3", "title": "Python", "start": "Wednesday 16:00", "capacity": 4, "booked": 0, "seatsLeft": 4 }
]
```

`booked` counts only bookings with status `confirmed`. `seatsLeft = capacity - booked`.

**Errors:** none expected.

---

## GET /sessions/{session_id}

**Input:** `session_id` in the path, for example `S1`.

**Success: 200**

```json
{
  "id": "S1",
  "title": "Algebra",
  "start": "Monday 16:00",
  "capacity": 3,
  "booked": 2,
  "seatsLeft": 1,
  "bookings": [
    { "id": 1, "sessionId": "S1", "alias": "owl42", "status": "confirmed" },
    { "id": 2, "sessionId": "S1", "alias": "fox17", "status": "confirmed" }
  ]
}
```

Only confirmed bookings are listed.

**Errors**

| Status | `error` | When | Message |
|---|---|---|---|
| 404 | `session_not_found` | The session id does not exist | `Session 'S99' does not exist.` |

---

## POST /bookings

**Input (JSON body)**

| Field | Type | Rules |
|---|---|---|
| `sessionId` | string | Required, 1 to 20 characters |
| `alias` | string | Required, 3 to 30 characters, only letters, digits, `_` and `-`. Use a fictional alias, never a real name or email. |

```json
{ "sessionId": "S1", "alias": "owl42" }
```

**Success: 201 Created**

```json
{ "id": 1, "sessionId": "S1", "alias": "owl42", "status": "confirmed" }
```

**Errors**

| Status | `error` | When | Message |
|---|---|---|---|
| 409 | `session_full` | The session already has as many confirmed bookings as its capacity | `This session has no places left.` |
| 409 | `already_booked` | The alias already has a confirmed booking in this session | `Alias 'owl42' already has a confirmed booking for session 'S3'.` |
| 404 | `session_not_found` | The session id does not exist (nothing is stored) | `Session 'S99' does not exist.` |
| 422 | `validation_error` | Missing field, empty value, or an alias that breaks the rules | `Invalid input for 'alias': ...` |

Example of the rejected fourth booking on a three-place session:

```json
{ "error": "session_full", "message": "This session has no places left." }
```

---

## DELETE /bookings/{booking_id}

**Input:** `booking_id` (integer) in the path, for example `3`.

**Success: 200**

The booking is kept in the database with status `cancelled`. It no longer counts towards capacity, so the place returns to the pool.

```json
{ "id": 3, "sessionId": "S1", "alias": "cat99", "status": "cancelled" }
```

**Errors**

| Status | `error` | When | Message |
|---|---|---|---|
| 404 | `booking_not_found` | The booking id does not exist | `Booking 99 does not exist.` |
| 409 | `already_cancelled` | The booking was already cancelled | `Booking 3 is already cancelled.` |
| 422 | `validation_error` | `booking_id` is not an integer | `Invalid input for 'booking_id': ...` |

---

## Errors that can come from any endpoint

| Status | `error` | When |
|---|---|---|
| 404 | `http_error` | The URL does not exist |
| 405 | `http_error` | The HTTP method is not allowed for that URL |
| 500 | `internal_error` | Unexpected server problem. Body is always `{"error": "internal_error", "message": "Something went wrong on the server."}` |

## Business rules

1. **Capacity:** a session can never have more confirmed bookings than its capacity. This is enforced by the database trigger `trg_capacity`, not only by application code.
2. **Double booking:** one alias can hold only one confirmed booking per session. Enforced by the partial unique index `uq_active_booking`. After a cancellation, the same alias may book that session again.
3. **Unknown session:** a booking for a session that does not exist is rejected and never stored (check in the handler, plus a foreign key in the database).
4. **Cancel:** sets `status = 'cancelled'` and keeps the row. Only `confirmed` rows are counted everywhere.
5. **Persistence:** all data is stored in the SQLite file `studyswap.db`, so bookings survive a server restart.