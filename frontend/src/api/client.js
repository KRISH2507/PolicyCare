const BASE_URL =
  import.meta.env.VITE_API_URL || "https://policycare.onrender.com";

export const getToken = () => localStorage.getItem("aarogyaaid_token");

const handleUnauthorized = () => {
  localStorage.removeItem("aarogyaaid_token");
  localStorage.removeItem("aarogyaaid_user");
  localStorage.removeItem("aarogyaaid_profile");
  localStorage.removeItem("aarogyaaid_result");
  localStorage.removeItem("aarogyaaid_chat_history");

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

const buildUrl = (path) => `${BASE_URL}${path}`;

export const apiGet = async (path) => {
  const res = await fetch(buildUrl(path), {
    headers: {
      Authorization: `Bearer ${getToken()}`,
    },
  });

  return handleResponse(res);
};

export const apiPost = async (path, body) => {
  const res = await fetch(buildUrl(path), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${getToken()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  return handleResponse(res);
};

export const apiUpload = async (path, formData) => {
  const res = await fetch(buildUrl(path), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${getToken()}`,
    },
    body: formData,
  });

  return handleResponse(res);
};

export const apiPatch = async (path, body) => {
  const res = await fetch(buildUrl(path), {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${getToken()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  return handleResponse(res);
};

export const apiDelete = async (path) => {
  const res = await fetch(buildUrl(path), {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${getToken()}`,
    },
  });

  return handleResponse(res);
};