import { apiClient } from "./client";
import type {
  AdminOverview,
  AdminUser,
  AdminUserSummary,
  AdminUserUsage,
  UserRole,
} from "../types";

export function fetchOverview(days: number): Promise<AdminOverview> {
  return apiClient.request<AdminOverview>(`/admin/overview?days=${days}`);
}

export function fetchUsers(days: number): Promise<AdminUserSummary[]> {
  return apiClient.request<AdminUserSummary[]>(`/admin/users?days=${days}`);
}

export function fetchUserUsage(
  userId: string,
  days: number,
): Promise<AdminUserUsage> {
  return apiClient.request<AdminUserUsage>(
    `/admin/users/${userId}/usage?days=${days}`,
  );
}

export function setUserRole(
  userId: string,
  role: UserRole,
): Promise<AdminUser> {
  return apiClient.request<AdminUser>(`/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
}
