import { apiClient } from "./client";
import type {
  AdminOverview,
  AdminUser,
  AdminUserSummary,
  AdminUserUsage,
  FeedbackPage,
  LogEntry,
  MessageFeedback,
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

export function unlockUser(userId: string): Promise<AdminUser> {
  return apiClient.request<AdminUser>(`/admin/users/${userId}/unlock`, {
    method: "POST",
  });
}

export function deleteUser(userId: string): Promise<void> {
  return apiClient.request<void>(`/admin/users/${userId}`, {
    method: "DELETE",
  });
}

export function fetchFeedback(
  days: number,
  rating: MessageFeedback,
  limit: number,
  offset: number,
): Promise<FeedbackPage> {
  return apiClient.request<FeedbackPage>(
    `/admin/feedback?days=${days}&rating=${rating}&limit=${limit}&offset=${offset}`,
  );
}

export function fetchLogs(limit: number): Promise<LogEntry[]> {
  return apiClient.request<LogEntry[]>(`/admin/logs?limit=${limit}`);
}
