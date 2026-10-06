import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { fetchDocumentFileBlob } from "../api/documents";
import type { Citation } from "../types";
import { Button, IconButton } from "./ui/Button";

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
  const [pageWidth, setPageWidth] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const CONTAINER_PADDING_PX = 16;

    const observer = new ResizeObserver(([entry]) => {
      setPageWidth(entry.contentRect.width - CONTAINER_PADDING_PX);
    });

    observer.observe(container);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let objectUrl: string | null = null;

    fetchDocumentFileBlob(sessionId, citation.document_id)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setFileUrl(objectUrl);
      })
      .catch(() => setError("Không tải được tài liệu."));

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [sessionId, citation.document_id]);

  return (
    <aside className="w-[640px] shrink-0 border-l border-slate-200 flex flex-col h-full">
      <header className="flex items-center justify-between px-4 py-2 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            title="Trang trước"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((page) => Math.max(1, page - 1))}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm text-slate-600">
            Trang {pageNumber}
            {numPages ? ` / ${numPages}` : ""}
          </span>
          <Button
            variant="secondary"
            size="sm"
            title="Trang sau"
            disabled={numPages !== null && pageNumber >= numPages}
            onClick={() =>
              setPageNumber((page) =>
                numPages ? Math.min(numPages, page + 1) : page + 1,
              )
            }
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
        <IconButton title="Đóng" onClick={onClose}>
          <X className="w-4 h-4" />
        </IconButton>
      </header>

      <div className="flex-1 overflow-auto p-2" ref={containerRef}>
        {error && <p className="text-sm text-red-600">{error}</p>}

        {fileUrl && (
          <Document
            file={fileUrl}
            loading={
              <p className="text-sm text-slate-500">Đang tải PDF...</p>
            }
            onLoadSuccess={({ numPages: total }) => setNumPages(total)}
          >
            <Page
              pageNumber={pageNumber}
              width={pageWidth ?? undefined}
              renderAnnotationLayer={false}
            />
          </Document>
        )}
      </div>
    </aside>
  );
}
