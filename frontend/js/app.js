// app.js: page logic for StudySwap (cards, booking popup, cancel, toasts).

const ALIAS_PATTERN = /^[A-Za-z0-9_-]{3,30}$/;

const $ = (id) => document.getElementById(id);
const els = {
  health: $("health"),
  statSessions: $("stat-sessions"),
  statPlaces: $("stat-places"),
  statLeft: $("stat-left"),
  grid: $("sessions"),
  modal: $("modal"),
  modalSession: $("modal-session"),
  aliasInput: $("alias-input"),
  modalError: $("modal-error"),
  modalCancel: $("modal-cancel"),
  modalConfirm: $("modal-confirm"),
  toasts: $("toasts"),
};

let activeSession = null; // the session shown in the booking popup

// ---------- Small helpers ----------

// Build an element safely (text is set with textContent, never innerHTML).
function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function showToast(message, kind) {
  const toast = make("div", "toast " + (kind === "error" ? "toast-err" : "toast-ok"), message);
  els.toasts.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

function statusFor(session) {
  if (session.seatsLeft === 0) return { label: "Full", badge: "badge-full", meter: "full" };
  if (session.seatsLeft / session.capacity <= 0.34) {
    return { label: "Almost full", badge: "badge-low", meter: "low" };
  }
  return { label: "Open", badge: "badge-open", meter: "" };
}

// ---------- Server health ----------

async function checkHealth() {
  try {
    await api.health();
    els.health.textContent = "Server online";
    els.health.className = "pill pill-ok";
  } catch (err) {
    els.health.textContent = "Server offline";
    els.health.className = "pill pill-bad";
  }
}

// ---------- Rendering ----------

function renderSummary(sessions) {
  const places = sessions.reduce((sum, s) => sum + s.capacity, 0);
  const left = sessions.reduce((sum, s) => sum + s.seatsLeft, 0);
  els.statSessions.textContent = sessions.length;
  els.statPlaces.textContent = places;
  els.statLeft.textContent = left;
}

function buildCard(session) {
  const status = statusFor(session);
  const card = make("article", "card");

  // Title, time and status badge
  const top = make("div", "card-top");
  const titleBox = make("div");
  titleBox.appendChild(make("h2", "card-title", session.title));
  titleBox.appendChild(make("p", "card-time", session.start));
  top.appendChild(titleBox);
  top.appendChild(make("span", "badge " + status.badge, status.label));
  card.appendChild(top);

  // Seats text and meter
  const seatBox = make("div");
  const seatText = make("div", "seats-text");
  seatText.appendChild(make("span", "", session.booked + " of " + session.capacity + " places taken"));
  const left = make("span");
  left.appendChild(make("strong", "", String(session.seatsLeft)));
  left.appendChild(document.createTextNode(" left"));
  seatText.appendChild(left);
  seatBox.appendChild(seatText);

  const meter = make("div", "meter");
  const fill = make("div", "meter-fill " + status.meter);
  fill.style.width = Math.round((session.booked / session.capacity) * 100) + "%";
  meter.appendChild(fill);
  seatBox.appendChild(meter);
  card.appendChild(seatBox);

  // Confirmed bookings with a cancel button on each
  const attendeesBox = make("div");
  attendeesBox.appendChild(make("p", "attendees-title", "Booked aliases"));
  const list = make("div", "attendees");
  if (session.bookings.length === 0) {
    list.appendChild(make("span", "none-yet", "No bookings yet. Be the first."));
  }
  session.bookings.forEach((booking) => {
    const chip = make("span", "chip");
    chip.appendChild(make("span", "", booking.alias));
    const cancelBtn = make("button", "chip-cancel", "\u00d7");
    cancelBtn.type = "button";
    cancelBtn.setAttribute("aria-label", "Cancel booking for " + booking.alias);
    cancelBtn.title = "Cancel this booking";
    cancelBtn.addEventListener("click", () => cancelBooking(booking, session));
    chip.appendChild(cancelBtn);
    list.appendChild(chip);
  });
  attendeesBox.appendChild(list);
  card.appendChild(attendeesBox);

  // Book button
  const bookBtn = make(
    "button",
    "btn btn-primary btn-block",
    session.seatsLeft === 0 ? "Session full" : "Book a place"
  );
  bookBtn.type = "button";
  bookBtn.disabled = session.seatsLeft === 0;
  bookBtn.addEventListener("click", () => openModal(session));
  card.appendChild(bookBtn);

  return card;
}

async function loadSessions() {
  try {
    const list = await api.listSessions();
    // Fetch the details of every session (they include the booked aliases)
    const sessions = await Promise.all(list.map((s) => api.getSession(s.id)));

    els.grid.replaceChildren();
    if (sessions.length === 0) {
      els.grid.appendChild(make("p", "empty", "No sessions available yet."));
    }
    sessions.forEach((s) => els.grid.appendChild(buildCard(s)));
    renderSummary(sessions);
  } catch (err) {
    els.grid.replaceChildren(make("div", "error-box", err.message));
  }
}

// ---------- Booking popup ----------

function openModal(session) {
  activeSession = session;
  els.modalSession.textContent = session.title + " \u00b7 " + session.start;
  els.aliasInput.value = "";
  hideModalError();
  els.modal.hidden = false;
  els.aliasInput.focus();
}

function closeModal() {
  els.modal.hidden = true;
  activeSession = null;
}

function showModalError(message) {
  els.modalError.textContent = message;
  els.modalError.hidden = false;
}

function hideModalError() {
  els.modalError.textContent = "";
  els.modalError.hidden = true;
}

async function confirmBooking() {
  if (!activeSession) return;
  const alias = els.aliasInput.value.trim();

  if (!ALIAS_PATTERN.test(alias)) {
    showModalError("Alias must be 3 to 30 characters: letters, digits, underscore or hyphen.");
    return;
  }

  hideModalError();
  els.modalConfirm.disabled = true;
  els.modalConfirm.textContent = "Booking...";
  try {
    const booking = await api.book(activeSession.id, alias);
    const title = activeSession.title;
    closeModal();
    showToast("Booked " + title + " for " + booking.alias + ".", "ok");
    await loadSessions();
  } catch (err) {
    // The backend sends a readable reason, for example session_full
    showModalError(err.message);
    if (err.code === "session_full" || err.code === "already_booked") {
      loadSessions(); // refresh the numbers behind the popup
    }
  } finally {
    els.modalConfirm.disabled = false;
    els.modalConfirm.textContent = "Confirm booking";
  }
}

// ---------- Cancel ----------

async function cancelBooking(booking, session) {
  const ok = window.confirm("Cancel the booking of " + booking.alias + " for " + session.title + "?");
  if (!ok) return;
  try {
    await api.cancel(booking.id);
    showToast("Cancelled the booking of " + booking.alias + ". The place is free again.", "ok");
  } catch (err) {
    showToast(err.message, "error");
  }
  await loadSessions();
}

// ---------- Wire up events ----------

els.modalCancel.addEventListener("click", closeModal);
els.modalConfirm.addEventListener("click", confirmBooking);
els.aliasInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") confirmBooking();
});
els.modal.addEventListener("click", (event) => {
  if (event.target === els.modal) closeModal(); // click on the dark background
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !els.modal.hidden) closeModal();
});

checkHealth();
loadSessions();