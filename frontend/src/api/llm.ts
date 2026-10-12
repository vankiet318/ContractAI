import { apiClient } from "./client";
import type { LlmProviders } from "../types";

export function listLlmProviders(): Promise<LlmProviders> {
  return apiClient.request<LlmProviders>("/llm/providers");
}
