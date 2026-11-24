// api.js: talks to the StudySwap backend.
// The page is served by the same server, so we use relative URLs.

async function request(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(path, options);
  } catch (networkError) {
    const err = new Error("Cannot reach the server. Is it running?");
    err.code = "network_error";
    err.status = 0;
    throw err;
  }

  let data = null;
  try {
    data = await response.json();
  } catch (parseError) {
    data = null;
  }

  if (!response.ok) {
    // Backend errors look like {"error": "...", "message": "..."}
    const err = new Error(
      (data && data.message) || "Something went wrong. Please try again."
    );
    err.code = (data && data.error) || "unknown_error";
    err.status = response.status;
    throw err;
  }
  return data;
}

const api = {
  health: () => request("GET", "/health"),
  listSessions: () => request("GET", "/sessions"),
  getSession: (id) => request("GET", "/sessions/" + encodeURIComponent(id)),
  book: (sessionId, alias) => request("POST", "/bookings", { sessionId, alias }),
  cancel: (bookingId) => request("DELETE", "/bookings/" + bookingId),
};