import { useCallback, useEffect, useState } from "react";
import { deleteDocument, listDocuments } from "../api/documents";
import type { DocumentSummary } from "../types";

export function useDocuments(sessionId: string) {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    const result = await listDocuments(sessionId);
    setDocuments(result);
    setIsLoading(false);
    return result;
  }, [sessionId]);

  useEffect(() => {
    setIsLoading(true);
    refresh().catch(() => setIsLoading(false));
  }, [refresh]);

  const remove = useCallback(
    async (documentId: string) => {
      await deleteDocument(sessionId, documentId);
      await refresh();
    },
    [sessionId, refresh],
  );

  return { documents, isLoading, refresh, remove };
}
