import { apiClient } from "./client";
import type { ChatSessionSummary } from "../types";

export function listSessions(): Promise<ChatSessionSummary[]> {
  return apiClient.request<ChatSessionSummary[]>("/sessions");
}

export function createSession(
  title: string,
): Promise<ChatSessionSummary> {
  return apiClient.request<ChatSessionSummary>("/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export function deleteSession(sessionId: string): Promise<void> {
  return apiClient.request<void>(`/sessions/${sessionId}`, {
    method: "DELETE",
  });
}
