import { ApiError, apiClient, type ServerSentEvent } from "./client";
import type {
  ChatMessageRecord,
  Citation,
  MessageFeedback,
} from "../types";

export function listMessages(
  sessionId: string,
): Promise<ChatMessageRecord[]> {
  return apiClient.request<ChatMessageRecord[]>(
    `/sessions/${sessionId}/messages`,
  );
}

export interface QueryStreamHandlers {
  onCitations: (citations: Citation[]) => void;
  onDelta: (text: string) => void;
  onDone: (messageId: string) => void;
  onTitle: (title: string) => void;
}

export async function streamQuery(
  sessionId: string,
  question: string,
  handlers: QueryStreamHandlers,
): Promise<void> {
  let isCompleted = false;

  await apiClient.requestEventStream(
    `/sessions/${sessionId}/query`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    },
    (event) => {
      if (event.event === "done") isCompleted = true;
      dispatchQueryEvent(event, handlers);
    },
  );

  if (!isCompleted) {
    throw new ApiError("Kết nối bị gián đoạn trước khi trả lời xong.", 0);
  }
}

function dispatchQueryEvent(
  { event, data }: ServerSentEvent,
  handlers: QueryStreamHandlers,
) {
  const payload = JSON.parse(data);

  switch (event) {
    case "citations":
      handlers.onCitations(payload.citations);
      break;
    case "delta":
      handlers.onDelta(payload.text);
      break;
    case "done":
      handlers.onDone(payload.message_id);
      break;
    case "title":
      handlers.onTitle(payload.title);
      break;
    case "error":
      throw new ApiError(payload.detail, 500);
  }
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
