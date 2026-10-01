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
      <button
        type="button"
        onClick={onRetry}
        className="mt-1 text-xs font-medium text-slate-700 underline hover:text-slate-900"
      >
        Thử lại
      </button>
    </div>
  );
}
