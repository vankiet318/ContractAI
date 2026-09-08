import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { fetchDocumentFileBlob } from "../api/documents";
import {
  PREVIEW_HIGHLIGHT_CLASS,
  PREVIEW_HIGHLIGHT_DURATION_MS,
} from "../constants";
import { findSpanForSnippet } from "../lib/snippetMatch";
import type { Citation } from "../types";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

export function DocumentPreviewPanel({
  sessionId,
  citation,
  onClose,
}: {
  sessionId: string;
  citation: Citation;
  onClose: () => void;
}) {
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(citation.page_start);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    setFileUrl(null);
    setError(null);
    setNumPages(null);
    setPageNumber(citation.page_start);

    fetchDocumentFileBlob(sessionId, citation.document_id)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setFileUrl(objectUrl);
      })
      .catch(() => setError("Không tải được tài liệu."));

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [sessionId, citation.document_id, citation.page_start, citation.chunk_id]);

  const handleTextLayerSuccess = () => {
    if (pageNumber !== citation.page_start) return;

    const container = containerRef.current;
    if (!container) return;

    const spans = Array.from(
      container.querySelectorAll(
        ".react-pdf__Page__textContent span",
      ),
    ) as HTMLSpanElement[];

    const match = findSpanForSnippet(spans, citation.text_snippet);
    if (!match) return;

    match.scrollIntoView({ behavior: "smooth", block: "center" });
    match.classList.add(PREVIEW_HIGHLIGHT_CLASS);

    setTimeout(() => {
      match.classList.remove(PREVIEW_HIGHLIGHT_CLASS);
    }, PREVIEW_HIGHLIGHT_DURATION_MS);
  };

  return (
    <aside className="w-[420px] shrink-0 border-l border-slate-200 flex flex-col h-full">
      <header className="flex items-center justify-between px-4 py-2 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((page) => Math.max(1, page - 1))}
            className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent"
          >
            ‹
          </button>
          <span className="text-xs text-slate-600">
            Trang {pageNumber}
            {numPages ? ` / ${numPages}` : ""}
          </span>
          <button
            type="button"
            disabled={numPages !== null && pageNumber >= numPages}
            onClick={() =>
              setPageNumber((page) =>
                numPages ? Math.min(numPages, page + 1) : page + 1,
              )
            }
            className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent"
          >
            ›
          </button>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded px-2 py-1 text-xs text-slate-500 hover:bg-slate-100 hover:text-slate-900"
        >
          Đóng
        </button>
      </header>

      <div className="flex-1 overflow-auto p-2" ref={containerRef}>
        {error && <p className="text-xs text-red-600">{error}</p>}

        {fileUrl && (
          <Document
            file={fileUrl}
            loading={
              <p className="text-xs text-slate-500">Đang tải PDF...</p>
            }
            onLoadSuccess={({ numPages: total }) => setNumPages(total)}
          >
            <Page
              pageNumber={pageNumber}
              renderAnnotationLayer={false}
              onRenderTextLayerSuccess={handleTextLayerSuccess}
            />
          </Document>
        )}
      </div>
    </aside>
  );
}
