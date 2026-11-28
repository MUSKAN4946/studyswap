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



## Automatic tests (pytest)

- **Expected:** every automatic test passes. The tests cover the four mandatory cases, the cancel and book-again cycle, readable errors, and a direct test that the database itself (not the API) refuses a fourth booking and a booking for an unknown session. They run on a temporary database, so the real data is never touched.
- **Actual:** command `python -m pytest -v`, last line of the terminal output:

  `18 passed, 1 warning in 2.39s`

- **Proof:** `screenshots/15_pytest_passed.png` (tests in `tests/test_cases.py`) and `screenshots/17_pytest_all_passed.png` (all tests, including `tests/concurrency_test.py`).
- **Conclusion:** the behaviour shown by hand above is also checked by code, so a future change that breaks a rule will be caught.

---

## Stretch: simultaneous bookings

- **Expected:** 30 people try to book the three places of S1 at the same instant. Exactly 3 bookings are confirmed, 27 are refused with `session_full`, and the database holds 3 confirmed rows, in every round.
- **Actual:** command `python -m tests.concurrency_test`, five rounds. Every round printed: `3 confirmed, 27 session_full, 0 other | confirmed rows in database: 3`. The final line printed: `RESULT: capacity held in every round.`
- **Proof:** `screenshots/16_concurrency_test.png`
- **How it works:** 30 threads, each with its own database connection, wait at a barrier and then start together. Each one runs the same single INSERT that the API uses, so the capacity trigger and the unique index are tested against real simultaneous writers. The `pytest` file `tests/concurrency_test.py` also checks 20 simultaneous requests on the two-place session S2, and the same alias fired 10 times at once (only one may succeed).
- **Conclusion:** under 30 simultaneous writers on one machine, capacity was never exceeded and no duplicate booking was stored.

---



## Fresh clone: the README works from an empty folder

- **Expected:** following the README from an empty folder, with nothing copied from my working copy, gives a running app with the three seeded sessions and no bookings.
- **What I did:** created a new folder `fresh_test` outside the project, ran `git clone https://github.com/MUSKAN4946/studyswap.git`, created a new virtual environment, activated it, ran `pip install -r requirements.txt`, ran `python seed.py`, started the server with `uvicorn app.main:app --reload`, and opened http://127.0.0.1:8000.
- **Actual:**
  - The clone finished without errors (79 objects received).
  - `pip install -r requirements.txt` completed; the only message shown at the end was pip's optional notice that a newer pip version exists.
  - `python seed.py` printed the three sessions: S1 Algebra (capacity 3), S2 Resume review (capacity 2), S3 Python (capacity 4).
  - The website opened and showed a fresh state: Server online, Places left 9, "No bookings yet" on every card, and none of the aliases from my earlier tests. This confirms that the old `studyswap.db` is not part of the repository and that no data was carried over.
- **Proof:** `screenshots/18_fresh_clone_running.png`
- **One slip during the test:** my first `uvicorn` command failed with "not recognized" because I ran it in a different terminal where the virtual environment was not active. After activating the virtual environment in the fresh folder it worked. README step 2 already tells the reader to activate the virtual environment.
- **Conclusion:** the setup steps in the README, in the order written, produce a working app with seeded sessions from a fresh clone.

---






## What this evidence does NOT establish

- **Simultaneous requests:** the manual cases above were run one request at a time. The stretch test then fired 30 threads at once on one computer, each with its own database connection, and capacity held in every round. This does not cover several server processes or several machines, a database other than SQLite, or a much larger number of simultaneous requests. It also exercises the same database insert that the API uses, not the full HTTP layer under load.
- **Other machines:** everything was run on one Windows computer with Python 3.14.10. The README was followed from a fresh clone in an empty folder on that same computer, with a new virtual environment, and it worked. It has not been followed on a different computer or operating system, and other Python versions were not tested.
- **Large data:** only the three seeded sessions and a handful of bookings were used. Performance with many sessions or bookings was not tested.
- **Security:** there are no accounts or passwords by design. Anyone can cancel any booking if they know its id. This is outside the scope of the brief.
- **Other browsers and devices:** only manual testing in one browser was done.