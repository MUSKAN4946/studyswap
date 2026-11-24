# StudySwap: Evidence Log

Each entry follows the same format: **expected result → actual result → captured proof → conclusion**. The last section lists what this evidence does **not** establish.

All tests were run by hand on a local machine (Windows, Python 3.14.10, FastAPI 0.165.0, SQLite) using the Swagger page at `/docs` and the browser. All aliases are fictional.

---

## E1. The app starts on a clean setup

- **Expected:** the server starts and reports that application startup is complete.
- **Actual:** the terminal shows `Application startup complete.`
- **Proof:** `screenshots/01_server_start.png`
- **Conclusion:** the app starts with the commands written in the README.

## E2. The health check works

- **Expected:** `GET /health` returns status 200 and `{"status": "ok", "database": "connected"}`.
- **Actual:** the browser shows that exact body.
- **Proof:** `screenshots/02_health.png`
- **Conclusion:** the app and the database connection work.

---

## Case 1. The fourth booking on a three-place session is rejected

Setup: session S1 (Algebra) has capacity 3. Three bookings were made with aliases `owl42`, `fox17` and `cat99`; each returned 201.

- **Expected:** `POST /bookings {"sessionId": "S1", "alias": "owl43"}` returns **409** with body `{"error": "session_full", "message": "This session has no places left."}`.
- **Actual:** status 409 with exactly that body.
- **Proof:** `screenshots/03_fourth_booking_409.png`
- **Must remain true:** after the rejection, S1 still has 3 confirmed bookings.
  - **Actual:** `GET /sessions/S1` shows `booked: 3`, `seatsLeft: 0`, and only `owl42`, `fox17`, `cat99` are listed. `owl43` is not stored.
  - **Proof:** `screenshots/04_s1_still_three.png`
- **Conclusion:** the fourth booking is refused with a clear reason and nothing is stored. Capacity is enforced by the database trigger `trg_capacity`.

## Case 1b. Cancelling returns the place, and the same request then succeeds

- **Expected:** cancelling booking 3 (`cat99`) returns 200 with status `cancelled`, S1 shows `booked: 2` and `seatsLeft: 1`, and the earlier rejected request (`owl43`) now succeeds with 201.
- **Actual (cancel):** `DELETE /bookings/3` returned 200 with `"status": "cancelled"`. `GET /sessions/S1` then showed `booked: 2`, `seatsLeft: 1`.
  - **Proof:** `screenshots/05_after_cancel_seat_freed.png`
- **Actual (book again):** `POST /bookings {"sessionId": "S1", "alias": "owl43"}` returned 201 with status `confirmed`.
  - **Proof:** `screenshots/06_rebook_after_cancel.png`
- **Conclusion:** the full cycle book → refuse → cancel → book again works. A cancelled booking does not leak capacity.

---

## Case 2. A booking for a session that does not exist is rejected

- **Expected:** `POST /bookings {"sessionId": "S99", "alias": "ghost77"}` returns **404** with `session_not_found` and nothing is stored.
- **Actual:** status 404 with body `{"error": "session_not_found", "message": "Session 'S99' does not exist."}`.
- **Proof:** `screenshots/08_session_not_found_404.png`
- **Conclusion:** a booking pointing at nothing is refused with a readable reason.

---

## Case 3. The same person booking twice

- **Rule chosen:** one alias can hold only one confirmed booking per session. A second attempt is rejected. After a cancellation, the same alias may book that session again.
- **Expected:** a second `POST /bookings {"sessionId": "S3", "alias": "owl42"}` returns **409** with `already_booked`.
- **Actual:** the first request returned 201. The identical second request returned 409 with `already_booked`.
- **Proof:** `screenshots/07_duplicate_booking_409.png`
- **Conclusion:** the rule is enforced by the partial unique index `uq_active_booking`. The same alias `owl42` could still book S1 earlier because the rule applies per session.

---

## Case 4. The server restarts and every booking is still there

- **Expected:** the booking counts are identical before and after stopping and starting the server (without running the seed script again).
- **Actual (before restart):** `GET /sessions` showed S1 `booked: 3`, S2 `booked: 0`, S3 `booked: 1`.
  - **Proof:** `screenshots/09_before_restart.png`
- **Actual (after restart):** the server was stopped with Ctrl+C and started again. `GET /sessions` showed the same counts.
  - **Proof:** `screenshots/10_after_restart.png`
- **Conclusion:** data is stored in the SQLite file `studyswap.db`, not in memory, so it survives a restart.

---

## What this evidence does NOT establish

- **Simultaneous requests:** all tests above sent one request at a time by hand. They show the capacity rule works, but they do not prove it holds when many requests arrive at the same moment. The design argument (trigger inside the database, SQLite allows one writer at a time) supports it, but it has not been measured here. A concurrency test is planned as a separate item.
- **Other machines:** everything was run on one Windows computer. The README has not yet been followed on a different, clean machine.
- **Large data:** only the three seeded sessions and a handful of bookings were used. Performance with many sessions or bookings was not tested.
- **Security:** there are no accounts or passwords by design. Anyone can cancel any booking if they know its id. This is outside the scope of the brief.
- **Other browsers and devices:** only manual testing in one browser was done.