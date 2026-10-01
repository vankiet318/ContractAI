export type DocumentStatus = "processing" | "ready" | "failed";

export interface ChatSessionSummary {
  session_id: string;
  title: string;
  created_at: string;
}

export interface DocumentSummary {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  created_at: string;
  error_message: string | null;
}

export interface Citation {
  source_id: string;
  chunk_id: string;
  document_id: string;
  page_start: number;
  page_end: number;
  section_number: string | null;
  section_title: string | null;
  text_snippet: string;
}

export type MessageFeedback = "like" | "dislike";

export interface ChatMessageRecord {
  message_id: string;
  question: string;
  answer: string;
  citations: Citation[];
  created_at: string;
  feedback: MessageFeedback | null;
}

/** pending: retrieving, no text yet. streaming: answer text arriving.
 * done: answer saved, citations and feedback can be shown. */
export type ChatMessageStatus = "pending" | "streaming" | "done" | "error";

export interface ChatMessage {
  id: string;
  /** The backend message_id, used to submit feedback. Null until the
   * query response (or history) supplies it. */
  messageId: string | null;
  question: string;
  status: ChatMessageStatus;
  answer: string | null;
  citations: Citation[];
  errorMessage: string | null;
  feedback: MessageFeedback | null;
}
