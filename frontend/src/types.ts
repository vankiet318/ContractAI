export type DocumentStatus = "processing" | "ready" | "failed";

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
  page_start: number;
  page_end: number;
  section_number: string | null;
  section_title: string | null;
}

export interface QueryResponse {
  question: string;
  answer: string;
  citations: Citation[];
}

export type ChatMessageStatus = "pending" | "done" | "error";

export interface ChatMessage {
  id: string;
  question: string;
  status: ChatMessageStatus;
  answer: string | null;
  citations: Citation[];
  errorMessage: string | null;
}
