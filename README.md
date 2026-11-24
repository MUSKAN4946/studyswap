# StudySwap

A study session booking API where a session can never be overbooked.
Built for the CareerSwami Full Stack Web Development internship (Project 1).

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

All exact package versions are pinned in `requirements.txt`.

## Setup (clean machine)

You only need Python 3.11 or newer and Git installed.

```bash
git clone https://github.com/MUSKAN4946/studyswap.git
cd studyswap
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows (PowerShell)
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

Install dependencies and start the server:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The database file `studyswap.db` is created automatically on first start.

## Health check

Open http://127.0.0.1:8000/health in a browser.

Expected response:

```json
{"status": "ok", "database": "connected"}
```

Interactive API docs (Swagger) are available at http://127.0.0.1:8000/docs.

## Entity diagram

See [docs/ER_DIAGRAM.md](docs/ER_DIAGRAM.md). It shows the `sessions` and `bookings` tables, their relationship, and where capacity is enforced.

## Capacity rule

Capacity is enforced inside the database by the trigger `trg_capacity`, not only in application code. A session with 3 places can never hold a 4th confirmed booking.

## Double-booking rule

One alias can hold only one confirmed booking per session. A second attempt is rejected. This is enforced by the partial unique index `uq_active_booking`.

## Cancel rule

Cancelling sets the booking `status` to `cancelled` (the row is not deleted). Only `confirmed` bookings count towards capacity, so a cancelled booking returns its place to the pool.

## Project status

- [x] Phase 1: schema, database connection, health endpoint, entity diagram, setup README
- [ ] Phase 2: API endpoints (list, details, book, cancel), seed script, API contract
- [ ] Phase 3: frontend, tests, evidence log