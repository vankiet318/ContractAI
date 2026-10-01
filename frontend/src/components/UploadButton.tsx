import { useRef, useState } from "react";
import { uploadDocument } from "../api/documents";
import { toErrorMessage } from "../api/client";
import { useToast } from "../hooks/useToast";

export function UploadButton({
  sessionId,
  onUploaded,
}: {
  sessionId: string;
  onUploaded: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const { showToast } = useToast();

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);

    try {
      const uploaded = await uploadDocument(sessionId, file);
      onUploaded();

      // Indexing errors come back as a FAILED document, not an HTTP error.
      if (uploaded.status === "failed") {
        showToast(
          uploaded.error_message ?? `Không xử lý được "${file.name}".`,
          "error",
        );
      } else {
        showToast(`Đã tải lên "${file.name}".`, "success");
      }
    } catch (error) {
      showToast(toErrorMessage(error, "Tải lên thất bại."), "error");
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        disabled={isUploading}
        onChange={handleFileChange}
      />
      <button
        type="button"
        disabled={isUploading}
        title="Có thể mất một lúc tùy độ dài tài liệu"
        onClick={() => inputRef.current?.click()}
        className="flex items-center justify-center gap-2 rounded-md bg-slate-900 text-white text-xs font-medium px-3 py-1.5 hover:bg-slate-700 disabled:opacity-50 disabled:hover:bg-slate-900"
      >
        {isUploading && (
          <span className="h-3 w-3 rounded-full border-2 border-white/40 border-t-white animate-spin" />
        )}
        {isUploading ? "Đang xử lý..." : "+ Upload PDF"}
      </button>
    </div>
  );
}
