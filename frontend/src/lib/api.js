import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API_BASE });

// Keep admin and customer sessions completely separate so that signing in as
// a customer on the same browser never wipes the admin session and vice-versa.
const ADMIN_TOKEN = "bgs_admin_token";
const ADMIN_USER = "bgs_admin_user";
const CUST_TOKEN = "bgs_token";
const CUST_USER = "bgs_user";

function isAdminPath(url = "") {
  return url.includes("/admin/") || url.includes("/auth/admin-login");
}

api.interceptors.request.use((config) => {
  const adminUrl = isAdminPath(config.url || "");
  const token = adminUrl ? localStorage.getItem(ADMIN_TOKEN) : localStorage.getItem(CUST_TOKEN);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const status = error?.response?.status;
    const url = error?.config?.url || "";
    // If admin session is invalid, clear admin keys so the UI shows the login page.
    if ((status === 401 || status === 403) && isAdminPath(url)) {
      localStorage.removeItem(ADMIN_TOKEN);
      localStorage.removeItem(ADMIN_USER);
    }
    return Promise.reject(error);
  }
);

export function saveSession(data, kind = "customer") {
  if (kind === "admin") {
    localStorage.setItem(ADMIN_TOKEN, data.token);
    localStorage.setItem(ADMIN_USER, JSON.stringify(data.user));
  } else {
    localStorage.setItem(CUST_TOKEN, data.token);
    localStorage.setItem(CUST_USER, JSON.stringify(data.user));
  }
}

export function getUser(kind = "customer") {
  try {
    const key = kind === "admin" ? ADMIN_USER : CUST_USER;
    return JSON.parse(localStorage.getItem(key) || "null");
  } catch {
    return null;
  }
}

export function logout(kind = "customer") {
  if (kind === "admin") {
    localStorage.removeItem(ADMIN_TOKEN);
    localStorage.removeItem(ADMIN_USER);
  } else {
    localStorage.removeItem(CUST_TOKEN);
    localStorage.removeItem(CUST_USER);
  }
}
