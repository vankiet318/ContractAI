import { useEffect, useState } from "react";
import { listLlmProviders } from "../api/llm";
import type { LlmProvider } from "../types";

const STORAGE_KEY = "contractai_llm_provider";

function readStoredProvider(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function storeProvider(providerId: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, providerId);
  } catch {
    // ignore storage failures (private mode, disabled storage, ...)
  }
}

/** The configured LLM providers and the user's pick, remembered across
 * visits. selectedId stays null until the list loads (or if it fails),
 * in which case queries fall back to the server default. */
export function useLlmProvider() {
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    listLlmProviders()
      .then((result) => {
        if (isCancelled) return;

        const stored = readStoredProvider();
        const isStoredAvailable = result.providers.some(
          (provider) => provider.id === stored,
        );

        setProviders(result.providers);
        setSelectedId(isStoredAvailable ? stored : result.default);
      })
      .catch(() => {
        // Best-effort: without the list the selector stays hidden and
        // the server's default provider answers.
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  const select = (providerId: string) => {
    setSelectedId(providerId);
    storeProvider(providerId);
  };

  return { providers, selectedId, select };
}
