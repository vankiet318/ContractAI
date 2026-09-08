import { apiClient } from "./client";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function register(
  email: string,
  password: string,
): Promise<{ user_id: string; email: string }> {
  return apiClient.request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  return apiClient.request<TokenResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}
