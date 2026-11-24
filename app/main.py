from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import get_conn, init_db
from app.errors import register_error_handlers
from app.routes import bookings, sessions

# studyswap/frontend (the website files)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


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


# ---------- Website (frontend) ----------

# CSS and JavaScript files are served under /static/...
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    """The main page of the website."""
    return FileResponse(FRONTEND_DIR / "index.html")