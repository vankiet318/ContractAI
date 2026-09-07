import { apiClient } from "./client";
import type { QueryResponse } from "../types";

export function queryDocument(
  documentId: string,
  question: string,
): Promise<QueryResponse> {
  return apiClient.request<QueryResponse>(
    `/documents/${documentId}/query`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    },
  );
}
