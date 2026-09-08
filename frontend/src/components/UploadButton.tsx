import { useRef, useState } from "react";
import { uploadDocument } from "../api/documents";
import { ApiError } from "../api/client";

export function UploadButton({
  sessionId,
  onUploaded,
}: {
  sessionId: string;
  onUploaded: () => void;
}) {
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
      await uploadDocument(sessionId, file);
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
      {error && (
        <p className="absolute right-0 top-full mt-1 w-48 text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}
