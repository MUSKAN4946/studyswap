from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import get_conn, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # App start hote hi tables / trigger / index ban jayenge
    init_db()
    yield


app = FastAPI(
    title="StudySwap",
    description="Study session booking API that can never overbook.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    """Check karta hai ki app aur database dono chal rahe hain."""
    conn = get_conn()
    try:
        conn.execute("SELECT 1").fetchone()
        return {"status": "ok", "database": "connected"}
    finally:
        conn.close()