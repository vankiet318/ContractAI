import { useState } from "react";
import { toErrorMessage } from "../api/client";
import { useDocuments } from "../hooks/useDocuments";
import { useToast } from "../hooks/useToast";
import type { Citation } from "../types";
import { ChatPanel } from "./ChatPanel";
import { ConfirmDialog } from "./ConfirmDialog";
import { DocumentPreviewPanel } from "./DocumentPreviewPanel";
import { DocumentStatusList } from "./DocumentStatusList";
import { UploadButton } from "./UploadButton";

type WorkspaceTab = "chat" | "documents";

export function SessionMain({
  sessionId,
  sessionTitle,
  onTitleGenerated,
}: {
  sessionId: string;
  sessionTitle: string;
  onTitleGenerated: (title: string) => void;
}) {
  const { showToast } = useToast();
  const { documents, isLoading, loadError, reload, refresh, remove } =
    useDocuments(sessionId);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("chat");
  const [previewCitation, setPreviewCitation] = useState<Citation | null>(
    null,
  );
  const [documentPendingDeleteId, setDocumentPendingDeleteId] = useState<
    string | null
  >(null);

  const documentPendingDelete = documents.find(
    (document) => document.document_id === documentPendingDeleteId,
  );

  const confirmDeleteDocument = async () => {
    if (!documentPendingDeleteId) return;

    const documentId = documentPendingDeleteId;
    setDocumentPendingDeleteId(null);

    try {
      await remove(documentId);
    } catch (error) {
      showToast(toErrorMessage(error, "Không xóa được tài liệu."), "error");
      return;
    }

    showToast("Đã xóa tài liệu.", "success");

    setPreviewCitation((current) =>
      current?.document_id === documentId ? null : current,
    );
  };

  return (
    <div className="flex-1 min-w-0 flex h-full">
      <div className="flex-1 min-w-0 flex flex-col h-full">
        <header className="flex items-center justify-between px-4 pt-3">
          <h1 className="text-sm font-semibold truncate">
            {sessionTitle}
          </h1>
          <UploadButton sessionId={sessionId} onUploaded={refresh} />
        </header>

        <div className="flex items-center gap-1 px-4 pt-2 border-b border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab("chat")}
            className={`px-3 py-1.5 rounded-t-md text-sm font-medium ${
              activeTab === "chat"
                ? "bg-slate-100 text-slate-900"
                : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
            }`}
          >
            Chat
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("documents")}
            className={`px-3 py-1.5 rounded-t-md text-sm font-medium ${
              activeTab === "documents"
                ? "bg-slate-100 text-slate-900"
                : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
            }`}
          >
            Tài liệu ({documents.length})
          </button>
        </div>

        <div className="flex-1 min-h-0">
          {/* Both tabs stay mounted so switching tabs never resets chat state. */}
          <div className={activeTab === "chat" ? "h-full" : "hidden"}>
            <ChatPanel
              sessionId={sessionId}
              onCitationSelect={setPreviewCitation}
              onTitleGenerated={onTitleGenerated}
            />
          </div>
          <div
            className={
              activeTab === "documents" ? "h-full overflow-y-auto" : "hidden"
            }
          >
            <DocumentStatusList
              documents={documents}
              isLoading={isLoading}
              loadError={loadError}
              onRetry={reload}
              onDelete={setDocumentPendingDeleteId}
            />
          </div>
        </div>
      </div>

      {previewCitation && (
        // Remount per citation so the preview starts from a clean state.
        <DocumentPreviewPanel
          key={`${previewCitation.document_id}:${previewCitation.chunk_id}:${previewCitation.page_start}`}
          sessionId={sessionId}
          citation={previewCitation}
          onClose={() => setPreviewCitation(null)}
        />
      )}

      <ConfirmDialog
        open={documentPendingDelete !== undefined}
        title="Xóa tài liệu"
        message={`Xóa "${documentPendingDelete?.filename}"? Tài liệu này sẽ bị xóa vĩnh viễn và không thể khôi phục.`}
        onConfirm={confirmDeleteDocument}
        onCancel={() => setDocumentPendingDeleteId(null)}
      />
    </div>
  );
}
