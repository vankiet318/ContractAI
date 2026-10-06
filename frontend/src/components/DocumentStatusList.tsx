import { X } from "lucide-react";
import type { DocumentSummary } from "../types";
import { LoadErrorMessage } from "./LoadErrorMessage";
import { StatusBadge } from "./StatusBadge";
import { IconButton } from "./ui/Button";

export function DocumentStatusList({
  documents,
  isLoading,
  loadError,
  onRetry,
  onDelete,
}: {
  documents: DocumentSummary[];
  isLoading: boolean;
  loadError: string | null;
  onRetry: () => void;
  onDelete: (documentId: string) => void;
}) {
  if (isLoading) {
    return (
      <p className="p-4 text-sm text-slate-500">
        Đang tải danh sách tài liệu...
      </p>
    );
  }

  if (loadError) {
    return <LoadErrorMessage message={loadError} onRetry={onRetry} />;
  }

  if (documents.length === 0) {
    return (
      <p className="p-4 text-sm text-slate-500">
        Chưa có tài liệu nào trong đoạn chat này.
      </p>
    );
  }

  return (
    <ul className="p-4 space-y-2">
      {documents.map((document) => (
        <li
          key={document.document_id}
          className="group flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2"
        >
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">
              {document.filename}
            </p>
            {document.status === "failed" && document.error_message && (
              <p className="mt-0.5 text-xs text-red-600 truncate">
                {document.error_message}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <StatusBadge status={document.status} />
            <IconButton
              tone="danger"
              onClick={() => onDelete(document.document_id)}
              title="Xóa tài liệu"
              className="opacity-0 group-hover:opacity-100"
            >
              <X className="w-4 h-4" />
            </IconButton>
          </div>
        </li>
      ))}
    </ul>
  );
}
