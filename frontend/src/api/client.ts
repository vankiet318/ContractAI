import { AUTH_UNAUTHORIZED_EVENT } from "../constants";
import { clearToken, getToken } from "./authStorage";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function withAuthHeaders(init?: RequestInit): RequestInit {
  const headers = new Headers(init?.headers);
  const token = getToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return { ...init, headers };
}

async function handleUnauthorized(response: Response) {
  if (response.status === 401) {
    clearToken();
    window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
    withAuthHeaders(init),
  );

  if (!response.ok) {
    await handleUnauthorized(response);

    const body = await response.json().catch(() => null);
    throw new ApiError(
      body?.detail ?? `Request failed: ${response.status}`,
      response.status,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function requestBlob(
  path: string,
  init?: RequestInit,
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
    withAuthHeaders(init),
  );

  if (!response.ok) {
    await handleUnauthorized(response);
    throw new ApiError(`Request failed: ${response.status}`, response.status);
  }

  return response.blob();
}

export const apiClient = { request, requestBlob };
