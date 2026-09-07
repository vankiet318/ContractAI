import { useRef, useState } from "react";
import { uploadDocument } from "../api/documents";
import { ApiError } from "../api/client";

export function UploadButton({ onUploaded }: { onUploaded: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      await uploadDocument(file);
      onUploaded();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Upload failed",
      );
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  };

  return (
    <div>
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
        onClick={() => inputRef.current?.click()}
        className="w-full flex items-center justify-center gap-2 rounded-md bg-slate-900 text-white text-sm font-medium py-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading && (
          <span className="h-3.5 w-3.5 rounded-full border-2 border-white/40 border-t-white animate-spin" />
        )}
        {isUploading ? "Đang tải lên & xử lý..." : "Upload PDF"}
      </button>
      {isUploading && (
        <p className="mt-1 text-xs text-slate-500">
          Có thể mất một lúc tùy độ dài tài liệu, vui lòng đợi.
        </p>
      )}
      {error && (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      )}
    </div>
  );
}
