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

export interface QueryResponse {
  question: string;
  answer: string;
  citations: Citation[];
  session_title: string | null;
}

export interface ChatMessageRecord {
  message_id: string;
  question: string;
  answer: string;
  citations: Citation[];
  created_at: string;
}

export type ChatMessageStatus = "pending" | "done" | "error";

export interface ChatMessage {
  id: string;
  question: string;
  status: ChatMessageStatus;
  answer: string | null;
  citations: Citation[];
  errorMessage: string | null;
  /** False for messages loaded from history, so they render instantly
   * instead of replaying the typewriter reveal animation. */
  animate: boolean;
}
