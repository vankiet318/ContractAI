import { useCallback, useEffect, useState } from "react";
import { listDocuments } from "../api/documents";
import type { DocumentSummary } from "../types";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    const result = await listDocuments();
    setDocuments(result);
    setIsLoading(false);
    return result;
  }, []);

  useEffect(() => {
    refresh().catch(() => {
      setIsLoading(false);
    });
  }, [refresh]);

  return { documents, isLoading, refresh };
}
