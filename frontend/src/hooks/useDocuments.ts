import { useCallback, useEffect, useState } from "react";
import { deleteDocument, listDocuments } from "../api/documents";
import { toErrorMessage } from "../api/client";
import type { DocumentSummary } from "../types";

export function useDocuments(sessionId: string) {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const result = await listDocuments(sessionId);
    setDocuments(result);
    setLoadError(null);
    return result;
  }, [sessionId]);

  const load = useCallback(() => {
    setIsLoading(true);

    refresh()
      .catch((error) =>
        setLoadError(toErrorMessage(error, "Không tải được danh sách tài liệu.")),
      )
      .finally(() => setIsLoading(false));
  }, [refresh]);

  useEffect(() => {
    load();
  }, [load]);

  const remove = useCallback(
    async (documentId: string) => {
      await deleteDocument(sessionId, documentId);
      await refresh();
    },
    [sessionId, refresh],
  );

  return { documents, isLoading, loadError, reload: load, refresh, remove };
}
