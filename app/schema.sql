-- Table 1: sessions (study sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id       TEXT PRIMARY KEY,
    title    TEXT NOT NULL,
    start    TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);

-- Table 2: bookings (kisne kaunsa session book kiya)
CREATE TABLE IF NOT EXISTS bookings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    alias      TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'confirmed'
               CHECK (status IN ('confirmed', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Rule: ek alias ek session mein sirf EK active booking rakh sakta hai
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_booking
    ON bookings(session_id, alias)
    WHERE status = 'confirmed';

-- Capacity enforcement DATABASE ke andar:
-- agar confirmed bookings capacity ke barabar ho chuki hain,
-- to naya insert abort ho jayega.
CREATE TRIGGER IF NOT EXISTS trg_capacity
BEFORE INSERT ON bookings
WHEN NEW.status = 'confirmed'
BEGIN
    SELECT RAISE(ABORT, 'session_full')
    WHERE (SELECT COUNT(*) FROM bookings
           WHERE session_id = NEW.session_id AND status = 'confirmed')
          >= (SELECT capacity FROM sessions WHERE id = NEW.session_id);
END;