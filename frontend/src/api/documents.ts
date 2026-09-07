import { apiClient } from "./client";
import type { DocumentSummary } from "../types";

export function listDocuments(): Promise<DocumentSummary[]> {
  return apiClient.request<DocumentSummary[]>("/documents");
}

export function getDocument(
  documentId: string,
): Promise<DocumentSummary> {
  return apiClient.request<DocumentSummary>(
    `/documents/${documentId}`,
  );
}

export function uploadDocument(
  file: File,
): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient.request<DocumentSummary>("/documents", {
    method: "POST",
    body: formData,
  });
}
