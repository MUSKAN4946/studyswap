# StudySwap

A study session booking app where a session can never be overbooked.
Built for the CareerSwami Full Stack Web Development internship (Project 1).

Students can list study sessions, see one in detail, book a place with a fictional alias, and cancel a booking. There are no accounts, passwords or payments (as the brief requires).

**The key rule:** a session with 3 places must never hold a 4th confirmed booking, however the requests arrive. This is enforced inside the database (a trigger), not only with an `if` in the code.

## What is in this repository

- **Backend:** Python, FastAPI, SQLite (`app/`)
- **Website (frontend):** plain HTML, CSS and JavaScript (`frontend/`), served by the same server
- **Tests:** automatic tests with pytest, including a simultaneous-bookings test (`tests/`)
- **Documents:** entity diagram, API contract, evidence log, AI disclosure (`docs/`)
- **Screenshots:** proof of every test (`screenshots/`)

## Tech stack and versions

| Tool | Version |
|---|---|
| Python | 3.14.10 |
| FastAPI | 0.165.0 |
| Uvicorn | 0.54.0 |
| Pydantic | 2.14.4 |
| SQLite | built into Python (`sqlite3` module) |
| pytest | 9.2.0 |
| httpx | 0.28.1 |
| Git | 2.56.0 |

All exact package versions are pinned in `requirements.txt`. This project was developed and tested on Python 3.14.10 on Windows. Python 3.11 or newer should also work, but that has not been tested.

## Setup (you only need Python and Git installed)

**1. Get the code**

```bash
git clone https://github.com/MUSKAN4946/studyswap.git
cd studyswap
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
```

```bash
# Windows (PowerShell)
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

**3. Install the dependencies**

```bash
pip install -r requirements.txt
```

**4. Create the database and add the three sessions (seed)**

```bash
python seed.py
```

Expected output:

```
Sessions in database:
  S1 | Algebra | Monday 16:00 | capacity 3
  S2 | Resume review | Tuesday 17:00 | capacity 2
  S3 | Python | Wednesday 16:00 | capacity 4
```

This creates the file `studyswap.db`. Running the seed again is safe: existing sessions are not duplicated.

**5. Start the server**

```bash
uvicorn app.main:app --reload
```

The terminal should show `Application startup complete.` Keep this terminal open while you use the app. Evidence that the app starts: `screenshots/01_server_start.png`.

## Open the app

| What | Address |
|---|---|
| The website | http://127.0.0.1:8000 |
| Health check | http://127.0.0.1:8000/health |
| Interactive API docs (Swagger) | http://127.0.0.1:8000/docs |

Health check expected response:

```json
{"status": "ok", "database": "connected"}
```

## Run the tests

Stop the server first (press Ctrl+C), then run:

```bash
python -m pytest -v
```

The tests run on a temporary database, so your real `studyswap.db` is never touched. To see the simultaneous-bookings demonstration (30 requests at the same instant for 3 places):

```bash
python -m tests.concurrency_test
```

## API at a glance

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Check that the app and database work |
| GET | `/sessions` | List all sessions with seats left |
| GET | `/sessions/{id}` | One session with its confirmed bookings |
| POST | `/bookings` | Book a place |
| DELETE | `/bookings/{id}` | Cancel a booking |

Full details of every input, success response and error: [docs/API_CONTRACT.md](docs/API_CONTRACT.md).

Example: the fourth booking on a three-place session is rejected.

```
POST /bookings
{ "sessionId": "S1", "alias": "owl43" }

409 Conflict
{ "error": "session_full", "message": "This session has no places left." }
```

Every error uses a proper status code and the same readable shape: `{"error": "...", "message": "..."}`.

## Rules I chose

- **Capacity:** enforced in the database by the trigger `trg_capacity`. A session can never have more confirmed bookings than its capacity.
- **Double booking:** one alias can hold only one confirmed booking per session (a second attempt returns 409 `already_booked`). Enforced by the partial unique index `uq_active_booking`. After a cancellation, the same alias may book that session again. The same alias may book different sessions.
- **Unknown session:** a booking for a session that does not exist returns 404 and nothing is stored (checked in the handler, plus a foreign key in the database).
- **Cancel:** sets the booking `status` to `cancelled` and keeps the row. Only `confirmed` bookings are counted, so a cancelled booking returns its place to the pool.
- **Persistence:** all data is in the SQLite file `studyswap.db`, so bookings survive a server restart.
- **Aliases:** 3 to 30 characters, letters, digits, underscore or hyphen. Use fictional aliases only, never real names or emails.

## Documents

- [Entity diagram and where capacity is enforced](docs/ER_DIAGRAM.md)
- [API contract](docs/API_CONTRACT.md)
- [Evidence log (expected, actual, proof, conclusion, and what is not proven)](docs/EVIDENCE_LOG.md)
- [AI assistance disclosure](docs/AI_DISCLOSURE.md)

## Project structure

```
studyswap/
├── app/                  backend
│   ├── main.py           app, startup, health check, serves the website
│   ├── db.py             database connection
│   ├── schema.sql        tables, unique index and capacity trigger
│   ├── models.py         request and response shapes
│   ├── errors.py         one error format for every error
│   └── routes/           sessions.py and bookings.py
├── frontend/             website (index.html, css/, js/)
├── tests/                test_cases.py and concurrency_test.py
├── docs/                 diagram, API contract, evidence log, AI disclosure
├── screenshots/          proof of every test
├── seed.py               creates the three starting sessions
└── requirements.txt
```

## Known limits

- There is no login, by design (the brief says no accounts). Anyone who knows a booking id can cancel it.
- It runs locally only. It is not deployed, as the brief requires no public hosting.
- The simultaneous-bookings test used threads on one computer. It does not cover several server processes or several machines.

## Project status

- [x] Part 1: schema, database connection, health endpoint, entity diagram, setup README
- [x] Part 2: list, details, book and cancel endpoints, seed script, API contract, captured examples
- [x] Website (frontend)
- [x] Automatic tests and the simultaneous-bookings stretch test
- [x] Evidence log and AI disclosure

## AI assistance

An AI assistant helped with this project. What it did and what I did and checked myself is described in [docs/AI_DISCLOSURE.md](docs/AI_DISCLOSURE.md).