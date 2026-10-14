import { LayoutDashboard, Plus, Trash2 } from "lucide-react";
import type { ChatSessionSummary } from "../types";
import { AppLogo } from "./AppLogo";
import { LoadErrorMessage } from "./LoadErrorMessage";
import { Button, IconButton, TextButton } from "./ui/Button";

interface SessionListProps {
  sessions: ChatSessionSummary[];
  isLoading: boolean;
  loadError: string | null;
  onRetry: () => void;
  selectedSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onCreate: () => void;
  onDelete: (sessionId: string) => void;
  onLogout: () => void;
  /** Shown only to admins. */
  onOpenAdmin?: () => void;
}

export function SessionList({
  sessions,
  isLoading,
  loadError,
  onRetry,
  selectedSessionId,
  onSelect,
  onCreate,
  onDelete,
  onLogout,
  onOpenAdmin,
}: SessionListProps) {
  return (
    <aside className="w-64 shrink-0 border-r border-slate-200 flex flex-col h-full">
      <div className="p-3 border-b border-slate-200 flex flex-col gap-3">
        <AppLogo />
        <Button onClick={onCreate} className="w-full">
          <Plus className="w-4 h-4" />
          Đoạn chat mới
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <p className="p-3 text-sm text-slate-500">Đang tải...</p>
        )}

        {!isLoading && loadError && (
          <LoadErrorMessage message={loadError} onRetry={onRetry} />
        )}

        {!isLoading && !loadError && sessions.length === 0 && (
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
              <IconButton
                onClick={() => onDelete(session.session_id)}
                title="Xóa đoạn chat"
                className="mr-2 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
              >
                <Trash2 className="w-4 h-4" />
              </IconButton>
            </li>
          ))}
        </ul>
      </div>

      <div className="p-3 border-t border-slate-200 flex flex-col gap-2">
        {onOpenAdmin && (
          <Button variant="secondary" size="sm" onClick={onOpenAdmin}>
            <LayoutDashboard className="w-4 h-4" />
            Quản trị
          </Button>
        )}
        <TextButton onClick={onLogout} className="w-full">
          Đăng xuất
        </TextButton>
      </div>
    </aside>
  );
}
