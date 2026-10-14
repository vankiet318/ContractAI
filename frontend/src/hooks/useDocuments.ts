import { useCallback, useEffect, useRef, useState } from "react";
import { deleteDocument, listDocuments } from "../api/documents";
import { toErrorMessage } from "../api/client";
import type { DocumentSummary } from "../types";

// Documents are indexed in the background after upload; the list is
// re-fetched at this interval while any of them is still processing.
const PROCESSING_POLL_MS = 3000;

export function useDocuments(
  sessionId: string,
  /** Called once per document that finished processing (ready or failed)
   * while this hook was watching it. */
  onProcessed?: (document: DocumentSummary) => void,
) {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const onProcessedRef = useRef(onProcessed);

  useEffect(() => {
    onProcessedRef.current = onProcessed;
  });

  // Ids seen as processing, to notice when they finish.
  const processingIdsRef = useRef<Set<string>>(new Set());

  const refresh = useCallback(async () => {
    const result = await listDocuments(sessionId);

    for (const document of result) {
      if (
        document.status !== "processing" &&
        processingIdsRef.current.has(document.document_id)
      ) {
        onProcessedRef.current?.(document);
      }
    }

    processingIdsRef.current = new Set(
      result
        .filter((document) => document.status === "processing")
        .map((document) => document.document_id),
    );

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

  const hasProcessing = documents.some(
    (document) => document.status === "processing",
  );

  useEffect(() => {
    if (!hasProcessing) return;

    const timer = window.setInterval(() => {
      // A failed poll is retried on the next tick.
      refresh().catch(() => {});
    }, PROCESSING_POLL_MS);

    return () => window.clearInterval(timer);
  }, [hasProcessing, refresh]);

  const remove = useCallback(
    async (documentId: string) => {
      await deleteDocument(sessionId, documentId);
      await refresh();
    },
    [sessionId, refresh],
  );

  return { documents, isLoading, loadError, reload: load, refresh, remove };
}
