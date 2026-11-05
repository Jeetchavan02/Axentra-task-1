const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "subscription-tracker-token";

export class ApiError extends Error {
  constructor(message, status, fields = []) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

// Kept for the browser tab only, so closing the tab logs the user out.
export const getToken = () => sessionStorage.getItem(TOKEN_KEY);
export const setToken = (token) => sessionStorage.setItem(TOKEN_KEY, token);
export const clearToken = () => sessionStorage.removeItem(TOKEN_KEY);

let onSessionExpired = () => {};
export const setSessionExpiredHandler = (handler) => {
  onSessionExpired = handler;
};

export async function api(path, { method = "GET", body, params } = {}) {
  const query = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, value]) => value !== "" && value != null),
  ).toString();
  const token = getToken();

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}${query ? `?${query}` : ""}`, {
      method,
      headers: {
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Can't reach the API. Is the backend running?", 0);
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) onSessionExpired();
    throw new ApiError(
      payload?.message ?? `Request failed (${response.status})`,
      response.status,
      payload?.data?.errors ?? [],
    );
  }
  return payload.data;
}
