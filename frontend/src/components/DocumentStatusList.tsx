import type { DocumentSummary } from "../types";
import { StatusBadge } from "./StatusBadge";

export function DocumentStatusList({
  documents,
  isLoading,
  onDelete,
}: {
  documents: DocumentSummary[];
  isLoading: boolean;
  onDelete: (documentId: string) => void;
}) {
  if (isLoading) {
    return (
      <p className="p-4 text-sm text-slate-500">
        Đang tải danh sách tài liệu...
      </p>
    );
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
          className="group flex items-center justify-between gap-3 rounded-md border border-slate-200 px-3 py-2"
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
            <button
              type="button"
              onClick={() => onDelete(document.document_id)}
              title="Xóa tài liệu"
              className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-slate-400 opacity-0 group-hover:opacity-100 hover:bg-red-100 hover:text-red-600"
            >
              ×
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
