export const getToken = () => localStorage.getItem("aarogyaaid_token");

/**
 * Clears all session data and redirects to login.
 * Called when the server returns 401 (expired/invalid token).
 */
const handleUnauthorized = () => {
  localStorage.removeItem("aarogyaaid_token");
  localStorage.removeItem("aarogyaaid_user");
  localStorage.removeItem("aarogyaaid_profile");
  localStorage.removeItem("aarogyaaid_result");
  localStorage.removeItem("aarogyaaid_chat_history");
  // Hard redirect — context will re-initialise from empty localStorage
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
};

const handleResponse = async (res) => {
  if (res.status === 401) {
    handleUnauthorized();
    throw new Error("Session expired. Please log in again.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "API Error");
  }
  return res.json();
};

export const apiGet = async (path) => {
  const res = await fetch(path, {
    headers: { "Authorization": `Bearer ${getToken()}` },
  });
  return handleResponse(res);
};

export const apiPost = async (path, body) => {
  const res = await fetch(path, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${getToken()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
};

export const apiUpload = async (path, formData) => {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Authorization": `Bearer ${getToken()}` },
    body: formData,
  });
  return handleResponse(res);
};

export const apiPatch = async (path, body) => {
  const res = await fetch(path, {
    method: "PATCH",
    headers: {
      "Authorization": `Bearer ${getToken()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
};

export const apiDelete = async (path) => {
  const res = await fetch(path, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${getToken()}` },
  });
  return handleResponse(res);
};
