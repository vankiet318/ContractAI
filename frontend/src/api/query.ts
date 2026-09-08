import { apiClient } from "./client";
import type { ChatMessageRecord, QueryResponse } from "../types";

export function listMessages(
  sessionId: string,
): Promise<ChatMessageRecord[]> {
  return apiClient.request<ChatMessageRecord[]>(
    `/sessions/${sessionId}/messages`,
  );
}

export function querySession(
  sessionId: string,
  question: string,
): Promise<QueryResponse> {
  return apiClient.request<QueryResponse>(
    `/sessions/${sessionId}/query`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    },
  );
}
