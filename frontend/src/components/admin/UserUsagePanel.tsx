import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchUserUsage } from "../../api/admin";
import { toErrorMessage } from "../../api/client";
import type { AdminUserUsage } from "../../types";
import { LoadErrorMessage } from "../LoadErrorMessage";
import { IconButton } from "../ui/Button";
import { DailyBarChart } from "./DailyBarChart";
import { formatDate, formatDay, QUERY_COLOR, UPLOAD_COLOR } from "./format";
import { LockedBadge, RoleBadge } from "./UsersTable";

export function UserUsagePanel({
  userId,
  days,
  version,
  onClose,
}: {
  userId: string;
  days: number;
  /** Bumped when the user was changed elsewhere, to load them again. */
  version: number;
  onClose: () => void;
}) {
  const [usage, setUsage] = useState<AdminUserUsage | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    fetchUserUsage(userId, days)
      .then((result) => {
        if (cancelled) return;
        setUsage(result);
        setLoadError(null);
      })
      .catch((error) => {
        if (cancelled) return;
        setLoadError(
          toErrorMessage(error, "Không tải được thống kê người dùng."),
        );
      });

    return () => {
      cancelled = true;
    };
  }, [userId, days, version, reloadKey]);

  const user = usage?.user;

  // Newest first, only days with activity.
  const activeDays = (usage?.daily ?? [])
    .filter((day) => day.queries > 0 || day.uploads > 0)
    .reverse();

  return (
    <aside className="flex h-full w-[28rem] shrink-0 flex-col border-l border-slate-200 bg-white">
      <header className="flex items-start justify-between gap-2 border-b border-slate-200 px-4 py-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-slate-900">
            {user?.email ?? "Đang tải..."}
          </p>
          {user && (
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <RoleBadge role={user.role} />
              {user.is_locked && <LockedBadge />}
              <span>Tham gia {formatDate(user.created_at)}</span>
            </div>
          )}
        </div>
        <IconButton onClick={onClose} title="Đóng">
          <X className="h-4 w-4" />
        </IconButton>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {loadError && (
          <LoadErrorMessage
            message={loadError}
            onRetry={() => setReloadKey((key) => key + 1)}
          />
        )}

        {usage && (
          <>
            <DailyBarChart
              title={`Câu hỏi mỗi ngày (${days} ngày)`}
              unit="câu hỏi"
              color={QUERY_COLOR}
              points={usage.daily.map((day) => ({
                date: day.date,
                value: day.queries,
              }))}
            />
            <DailyBarChart
              title={`Tài liệu tải lên mỗi ngày (${days} ngày)`}
              unit="tài liệu"
              color={UPLOAD_COLOR}
              points={usage.daily.map((day) => ({
                date: day.date,
                value: day.uploads,
              }))}
            />

            <section>
              <h3 className="text-sm font-medium text-slate-900">
                Chi tiết theo ngày
              </h3>
              {activeDays.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">
                  Không có hoạt động trong {days} ngày qua.
                </p>
              ) : (
                <table className="mt-2 w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                      <th className="py-1.5 font-medium">Ngày</th>
                      <th className="py-1.5 text-right font-medium">Câu hỏi</th>
                      <th className="py-1.5 text-right font-medium">Tài liệu</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeDays.map((day) => (
                      <tr
                        key={day.date}
                        className="border-b border-slate-100 last:border-0"
                      >
                        <td className="py-1.5 text-slate-600">
                          {formatDay(day.date, true)}
                        </td>
                        <td className="py-1.5 text-right tabular-nums">
                          {day.queries}
                        </td>
                        <td className="py-1.5 text-right tabular-nums">
                          {day.uploads}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </>
        )}
      </div>
    </aside>
  );
}
