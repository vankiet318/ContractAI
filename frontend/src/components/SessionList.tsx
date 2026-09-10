import type { ChatSessionSummary } from "../types";

interface SessionListProps {
  sessions: ChatSessionSummary[];
  isLoading: boolean;
  selectedSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onCreate: () => void;
  onDelete: (sessionId: string) => void;
  onLogout: () => void;
}

export function SessionList({
  sessions,
  isLoading,
  selectedSessionId,
  onSelect,
  onCreate,
  onDelete,
  onLogout,
}: SessionListProps) {
  return (
    <aside className="w-64 shrink-0 border-r border-slate-200 flex flex-col h-full">
      <div className="p-3 border-b border-slate-200">
        <button
          type="button"
          onClick={onCreate}
          className="w-full rounded-md bg-slate-900 text-white text-sm font-medium py-2 hover:bg-slate-700"
        >
          + Đoạn chat mới
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <p className="p-3 text-sm text-slate-500">Đang tải...</p>
        )}

        {!isLoading && sessions.length === 0 && (
          <p className="p-3 text-sm text-slate-500">
            Chưa có đoạn chat nào.
          </p>
        )}

        <ul>
          {sessions.map((session) => (
            <li
              key={session.session_id}
              className={`group flex items-center border-b border-slate-100 ${
                selectedSessionId === session.session_id
                  ? "bg-slate-100"
                  : ""
              }`}
            >
              <button
                type="button"
                onClick={() => onSelect(session.session_id)}
                className="flex-1 text-left px-3 py-2 hover:bg-slate-50 truncate text-sm"
              >
                {session.title}
              </button>
              <button
                type="button"
                onClick={() => onDelete(session.session_id)}
                title="Xóa đoạn chat"
                className="mr-2 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-slate-400 opacity-0 group-hover:opacity-100 hover:bg-red-100 hover:text-red-600"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="p-3 border-t border-slate-200">
        <button
          type="button"
          onClick={onLogout}
          className="w-full text-xs text-slate-500 hover:text-slate-900"
        >
          Đăng xuất
        </button>
      </div>
    </aside>
  );
}
