import { ArrowLeft, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useAdminDashboard } from "../../hooks/useAdminDashboard";
import type { AdminOverview } from "../../types";
import { AppLogo } from "../AppLogo";
import { LoadErrorMessage } from "../LoadErrorMessage";
import { Button, IconButton, TextButton } from "../ui/Button";
import { DailyBarChart } from "./DailyBarChart";
import { formatDay, QUERY_COLOR, UPLOAD_COLOR } from "./format";
import { UserUsagePanel } from "./UserUsagePanel";
import { UsersTable } from "./UsersTable";

const WINDOW_OPTIONS = [7, 30, 90];

function StatTile({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">
        {value}
      </p>
      {detail && <p className="mt-0.5 text-xs text-slate-500">{detail}</p>}
    </div>
  );
}

function StatTiles({ overview }: { overview: AdminOverview }) {
  const rated = overview.likes + overview.dislikes;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      <StatTile
        label="Người dùng"
        value={overview.total_users}
        detail={`+${overview.new_users} mới trong ${overview.days} ngày`}
      />
      <StatTile
        label="Người dùng hoạt động"
        value={overview.active_users}
        detail="Có hỏi hoặc tải tài liệu"
      />
      <StatTile label="Câu hỏi" value={overview.queries} />
      <StatTile label="Tài liệu tải lên" value={overview.uploads} />
      <StatTile
        label="Phản hồi hữu ích"
        value={rated > 0 ? `${Math.round((overview.likes / rated) * 100)}%` : "—"}
        detail={`${overview.likes} 👍 · ${overview.dislikes} 👎`}
      />
    </div>
  );
}

function DailyTable({ overview }: { overview: AdminOverview }) {
  return (
    <div className="max-h-80 overflow-y-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-white">
          <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
            <th className="px-4 py-2 font-medium">Ngày</th>
            <th className="px-4 py-2 text-right font-medium">Câu hỏi</th>
            <th className="px-4 py-2 text-right font-medium">Tài liệu</th>
          </tr>
        </thead>
        <tbody>
          {[...overview.daily].reverse().map((day) => (
            <tr key={day.date} className="border-b border-slate-100 last:border-0">
              <td className="px-4 py-1.5 text-slate-600">
                {formatDay(day.date, true)}
              </td>
              <td className="px-4 py-1.5 text-right tabular-nums">
                {day.queries}
              </td>
              <td className="px-4 py-1.5 text-right tabular-nums">
                {day.uploads}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AdminDashboard({
  currentUserId,
  onBack,
}: {
  currentUserId: string;
  onBack: () => void;
}) {
  const [days, setDays] = useState(30);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [showTable, setShowTable] = useState(false);
  const { overview, users, isLoading, loadError, reload } =
    useAdminDashboard(days);

  return (
    <div className="flex h-screen bg-slate-50">
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-3">
          <div className="flex items-center gap-4">
            <AppLogo />
            <span className="text-sm text-slate-400">/</span>
            <h1 className="text-sm font-semibold text-slate-900">Quản trị</h1>
          </div>
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
            Về đoạn chat
          </Button>
        </header>

        <main className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
          <div className="flex items-center justify-between gap-3">
            <div
              className="inline-flex rounded-md border border-slate-300 bg-white p-0.5"
              role="group"
              aria-label="Khoảng thời gian"
            >
              {WINDOW_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setDays(option)}
                  className={`rounded px-3 py-1 text-sm ${
                    days === option
                      ? "bg-slate-900 text-white"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {option} ngày
                </button>
              ))}
            </div>
            <IconButton onClick={reload} title="Tải lại" disabled={isLoading}>
              <RefreshCw
                className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
              />
            </IconButton>
          </div>

          {loadError && <LoadErrorMessage message={loadError} onRetry={reload} />}

          {!overview && isLoading && (
            <p className="text-sm text-slate-500">Đang tải...</p>
          )}

          {overview && (
            <>
              <StatTiles overview={overview} />

              <div className="grid gap-3 lg:grid-cols-2">
                <DailyBarChart
                  title="Câu hỏi mỗi ngày"
                  unit="câu hỏi"
                  color={QUERY_COLOR}
                  points={overview.daily.map((day) => ({
                    date: day.date,
                    value: day.queries,
                  }))}
                />
                <DailyBarChart
                  title="Tài liệu tải lên mỗi ngày"
                  unit="tài liệu"
                  color={UPLOAD_COLOR}
                  points={overview.daily.map((day) => ({
                    date: day.date,
                    value: day.uploads,
                  }))}
                />
              </div>

              <TextButton onClick={() => setShowTable((value) => !value)}>
                {showTable ? "Ẩn bảng số liệu" : "Xem dạng bảng"}
              </TextButton>
              {showTable && <DailyTable overview={overview} />}

              <UsersTable
                users={users}
                days={days}
                selectedUserId={selectedUserId}
                onSelect={setSelectedUserId}
              />
            </>
          )}
        </main>
      </div>

      {selectedUserId && (
        <UserUsagePanel
          key={selectedUserId}
          userId={selectedUserId}
          days={days}
          isCurrentUser={selectedUserId === currentUserId}
          onClose={() => setSelectedUserId(null)}
          onRoleChanged={reload}
        />
      )}
    </div>
  );
}
