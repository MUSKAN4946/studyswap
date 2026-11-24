from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import get_conn, init_db
from app.errors import register_error_handlers
from app.routes import bookings, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: make sure tables, index and trigger exist.
    init_db()
    yield


app = FastAPI(
    title="StudySwap",
    description="Study session booking API that can never overbook.",
    version="1.0.0",
    lifespan=lifespan,
)

# Every error gets the same shape: {"error": "...", "message": "..."}
register_error_handlers(app)

app.include_router(sessions.router)
app.include_router(bookings.router)


@app.get("/health", tags=["Health"], summary="Check that the app and database work")
def health():
    conn = get_conn()
    try:
        conn.execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "connected"}
    finally:
        conn.close()