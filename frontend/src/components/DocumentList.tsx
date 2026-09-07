import type { DocumentSummary } from "../types";
import { StatusBadge } from "./StatusBadge";
import { UploadButton } from "./UploadButton";

interface DocumentListProps {
  documents: DocumentSummary[];
  isLoading: boolean;
  selectedDocumentId: string | null;
  onSelect: (documentId: string) => void;
  onUploaded: () => void;
}

export function DocumentList({
  documents,
  isLoading,
  selectedDocumentId,
  onSelect,
  onUploaded,
}: DocumentListProps) {
  return (
    <aside className="w-72 shrink-0 border-r border-slate-200 flex flex-col h-full">
      <div className="p-3 border-b border-slate-200">
        <UploadButton onUploaded={onUploaded} />
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <p className="p-3 text-sm text-slate-500">
            Đang tải danh sách tài liệu...
          </p>
        )}

        {!isLoading && documents.length === 0 && (
          <p className="p-3 text-sm text-slate-500">
            No documents yet.
          </p>
        )}

        <ul>
          {documents.map((document) => (
            <li key={document.document_id}>
              <button
                type="button"
                onClick={() => onSelect(document.document_id)}
                disabled={document.status !== "ready"}
                className={`w-full text-left px-3 py-2 border-b border-slate-100 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50 ${
                  selectedDocumentId === document.document_id
                    ? "bg-slate-100"
                    : ""
                }`}
              >
                <p className="text-sm font-medium truncate">
                  {document.filename}
                </p>
                <div className="mt-1 flex items-center justify-between">
                  <StatusBadge status={document.status} />
                </div>
                {document.status === "failed" &&
                  document.error_message && (
                    <p className="mt-1 text-xs text-red-600 truncate">
                      {document.error_message}
                    </p>
                  )}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
