import { Upload } from "lucide-react";
import { useRef, useState } from "react";
import { uploadDocument } from "../api/documents";
import { toErrorMessage } from "../api/client";
import { useToast } from "../hooks/useToast";
import { Button } from "./ui/Button";

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
      <Button
        size="sm"
        disabled={isUploading}
        title="Có thể mất một lúc tùy độ dài tài liệu"
        onClick={() => inputRef.current?.click()}
      >
        {isUploading ? (
          <span className="h-4 w-4 rounded-full border-2 border-white/40 border-t-white animate-spin" />
        ) : (
          <Upload className="w-4 h-4" />
        )}
        {isUploading ? "Đang xử lý..." : "Tải lên PDF"}
      </Button>
    </div>
  );
}
