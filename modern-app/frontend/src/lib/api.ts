/**
 * Centralised API client for the CardDemo User Administration API.
 *
 * All HTTP calls go through this module. The auth token is read from
 * localStorage (set by the auth/login flow).
 */
import axios, { AxiosError, type AxiosInstance } from "axios";
import type {
  CreateUserPayload,
  DeleteUserResponse,
  UpdateUserPayload,
  User,
  UserListParams,
  UserListResponse,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: { "Content-Type": "application/json" },
  });

  // Attach JWT from localStorage on every request
  client.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return config;
  });

  // Normalise error messages
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
}

const apiClient = createApiClient();

/** Extract a human-readable error message from an Axios error. */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || String(d)).join("; ");
    }
    return error.message;
  }
  return "An unexpected error occurred";
}

// ---------------------------------------------------------------------------
// User Administration API calls
// ---------------------------------------------------------------------------

/** GET /api/users — mirrors COUSR00C browse with pagination */
export async function listUsers(params: UserListParams = {}): Promise<UserListResponse> {
  const { data } = await apiClient.get<UserListResponse>("/api/users", { params });
  return data;
}

/** GET /api/users/:id — mirrors COUSR02C Phase 1 fetch */
export async function getUser(userId: string): Promise<User> {
  const { data } = await apiClient.get<User>(`/api/users/${encodeURIComponent(userId)}`);
  return data;
}

/** POST /api/users — mirrors COUSR01C add user (returns 201) */
export async function createUser(payload: CreateUserPayload): Promise<User> {
  const { data } = await apiClient.post<User>("/api/users", payload);
  return data;
}

/** PUT /api/users/:id — mirrors COUSR02C Phase 2 save */
export async function updateUser(
  userId: string,
  payload: UpdateUserPayload
): Promise<User> {
  const { data } = await apiClient.put<User>(
    `/api/users/${encodeURIComponent(userId)}`,
    payload
  );
  return data;
}

/** DELETE /api/users/:id — mirrors COUSR03C Phase 2 confirm delete */
export async function deleteUser(userId: string): Promise<DeleteUserResponse> {
  const { data } = await apiClient.delete<DeleteUserResponse>(
    `/api/users/${encodeURIComponent(userId)}`
  );
  return data;
}
