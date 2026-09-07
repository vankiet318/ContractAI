import { useState } from "react";
import { DocumentList } from "./components/DocumentList";
import { ChatPanel } from "./components/ChatPanel";
import { useDocuments } from "./hooks/useDocuments";

export function App() {
  const { documents, isLoading, refresh } = useDocuments();
  const [selectedDocumentId, setSelectedDocumentId] = useState<
    string | null
  >(null);

  const selectedDocument = documents.find(
    (document) => document.document_id === selectedDocumentId,
  );

  return (
    <div className="flex h-screen">
      <DocumentList
        documents={documents}
        isLoading={isLoading}
        selectedDocumentId={selectedDocumentId}
        onSelect={setSelectedDocumentId}
        onUploaded={refresh}
      />

      <main className="flex-1">
        {selectedDocument ? (
          <ChatPanel document={selectedDocument} />
        ) : (
          <div className="flex items-center justify-center h-full text-sm text-slate-500">
            Select a document to start asking questions.
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
