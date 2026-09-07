const DOT_DELAYS = ["0ms", "150ms", "300ms"];

export function TypingIndicator() {
  return (
    <div className="bg-slate-50 rounded-lg px-3 py-2.5 max-w-[80%] inline-flex">
      <div className="flex gap-1">
        {DOT_DELAYS.map((delay) => (
          <span
            key={delay}
            style={{ animationDelay: delay }}
            className="h-2 w-2 rounded-full bg-slate-400 animate-bounce"
          />
        ))}
      </div>
    </div>
  );
}
