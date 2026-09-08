import { apiClient } from "./client";
import type { DocumentSummary } from "../types";

export function listDocuments(
  sessionId: string,
): Promise<DocumentSummary[]> {
  return apiClient.request<DocumentSummary[]>(
    `/sessions/${sessionId}/documents`,
  );
}

export function uploadDocument(
  sessionId: string,
  file: File,
): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient.request<DocumentSummary>(
    `/sessions/${sessionId}/documents`,
    {
      method: "POST",
      body: formData,
    },
  );
}

export function fetchDocumentFileBlob(
  sessionId: string,
  documentId: string,
): Promise<Blob> {
  return apiClient.requestBlob(
    `/sessions/${sessionId}/documents/${documentId}/file`,
  );
}

export function deleteDocument(
  sessionId: string,
  documentId: string,
): Promise<void> {
  return apiClient.request<void>(
    `/sessions/${sessionId}/documents/${documentId}`,
    { method: "DELETE" },
  );
}
