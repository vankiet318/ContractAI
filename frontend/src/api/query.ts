import { apiClient } from "./client";
import type {
  ChatMessageRecord,
  MessageFeedback,
  QueryResponse,
} from "../types";

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

export function setMessageFeedback(
  sessionId: string,
  messageId: string,
  feedback: MessageFeedback | null,
): Promise<void> {
  return apiClient.request<void>(
    `/sessions/${sessionId}/messages/${messageId}/feedback`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback }),
    },
  );
}
