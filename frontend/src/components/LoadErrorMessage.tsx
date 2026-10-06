import { TextButton } from "./ui/Button";

export function LoadErrorMessage({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="p-3 text-sm text-red-600">
      <p>{message}</p>
      <TextButton onClick={onRetry} className="mt-1">
        Thử lại
      </TextButton>
    </div>
  );
}
