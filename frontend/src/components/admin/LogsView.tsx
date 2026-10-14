import {
  ArrowLeft,
  ArrowRight,
  ChevronRight,
  RefreshCw,
  Search,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchLogs } from "../../api/admin";
import { toErrorMessage } from "../../api/client";
import type { LogEntry } from "../../types";
import { LoadErrorMessage } from "../LoadErrorMessage";
import { IconButton } from "../ui/Button";
import { TextInput } from "../ui/TextInput";

const FETCH_LIMIT = 2000;
const AUTO_REFRESH_MS = 5000;
const PAGE_SIZE = 50;
const ACCESS_LOGGER = "uvicorn.access";

type LevelFilter = "all" | "warning" | "error";

const LEVEL_FILTERS: { value: LevelFilter; label: string; minRank: number }[] = [
  { value: "all", label: "Tất cả", minRank: 0 },
  { value: "warning", label: "Cảnh báo", minRank: 30 },
  { value: "error", label: "Lỗi", minRank: 40 },
];

const LEVEL_RANKS: Record<string, number> = {
  DEBUG: 10,
  INFO: 20,
  WARNING: 30,
  ERROR: 40,
  CRITICAL: 50,
};

// Same treatment as document statuses: a coloured dot, text in ink.
function levelDot(level: string): string {
  const rank = LEVEL_RANKS[level] ?? 0;
  if (rank >= 40) return "bg-red-500";
  if (rank >= 30) return "bg-amber-500";
  return "bg-slate-300";
}

function formatLogTime(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function LogsView() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [levelFilter, setLevelFilter] = useState<LevelFilter>("all");
  const [search, setSearch] = useState("");
  const [hideAccess, setHideAccess] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [pageIndex, setPageIndex] = useState(0);

  // A new filter starts again from the first page.
  const filterKey = `${levelFilter}:${search}:${hideAccess}`;
  const [lastFilterKey, setLastFilterKey] = useState(filterKey);
  if (lastFilterKey !== filterKey) {
    setLastFilterKey(filterKey);
    setPageIndex(0);
  }

  const refresh = useCallback(async () => {
    try {
      setEntries(await fetchLogs(FETCH_LIMIT));
      setLoadError(null);
    } catch (error) {
      setLoadError(toErrorMessage(error, "Không tải được log."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!autoRefresh) return;

    const timer = window.setInterval(refresh, AUTO_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [autoRefresh, refresh]);

  const visibleEntries = useMemo(() => {
    const minRank =
      LEVEL_FILTERS.find((filter) => filter.value === levelFilter)?.minRank ?? 0;
    const query = search.trim().toLowerCase();

    return entries.filter(
      (entry) =>
        (LEVEL_RANKS[entry.level] ?? 0) >= minRank &&
        !(hideAccess && entry.logger === ACCESS_LOGGER) &&
        (!query ||
          entry.message.toLowerCase().includes(query) ||
          entry.logger.toLowerCase().includes(query) ||
          entry.exception?.toLowerCase().includes(query)),
    );
  }, [entries, levelFilter, search, hideAccess]);

  const pageCount = Math.max(1, Math.ceil(visibleEntries.length / PAGE_SIZE));
  // A refresh can leave fewer pages than the one being viewed.
  const currentPage = Math.min(pageIndex, pageCount - 1);
  const pageStart = currentPage * PAGE_SIZE;
  const pageEntries = visibleEntries.slice(pageStart, pageStart + PAGE_SIZE);

  const toggleExpanded = (entryId: number) => {
    setExpandedIds((current) => {
      const next = new Set(current);
      if (next.has(entryId)) {
        next.delete(entryId);
      } else {
        next.add(entryId);
      }
      return next;
    });
  };

  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 px-4 py-3">
        <div
          className="inline-flex rounded-md border border-slate-300 bg-white p-0.5"
          role="group"
          aria-label="Mức log"
        >
          {LEVEL_FILTERS.map((filter) => (
            <button
              key={filter.value}
              type="button"
              onClick={() => setLevelFilter(filter.value)}
              className={`rounded px-3 py-1 text-sm ${
                levelFilter === filter.value
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <label className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <TextInput
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Tìm trong log"
            className="w-64 py-1.5 pl-8"
          />
        </label>

        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={hideAccess}
            onChange={(event) => setHideAccess(event.target.checked)}
            className="accent-slate-900"
          />
          Ẩn request HTTP
        </label>

        <div className="ml-auto flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(event) => setAutoRefresh(event.target.checked)}
              className="accent-slate-900"
            />
            Tự làm mới
          </label>
          <IconButton onClick={refresh} title="Tải lại">
            <RefreshCw className="h-4 w-4" />
          </IconButton>
        </div>
      </div>

      {loadError && <LoadErrorMessage message={loadError} onRetry={refresh} />}

      {isLoading && (
        <p className="px-4 py-6 text-center text-sm text-slate-500">
          Đang tải...
        </p>
      )}

      {!isLoading && visibleEntries.length === 0 && (
        <p className="px-4 py-6 text-center text-sm text-slate-500">
          Không có dòng log nào phù hợp.
        </p>
      )}

      {visibleEntries.length > 0 && (
        <table className="w-full table-fixed text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
              <th className="w-36 px-4 py-2 font-medium">Thời gian</th>
              <th className="w-28 px-4 py-2 font-medium">Mức</th>
              <th className="w-56 px-4 py-2 font-medium">Nguồn</th>
              <th className="px-4 py-2 font-medium">Nội dung</th>
            </tr>
          </thead>
          <tbody className="font-mono text-xs">
            {pageEntries.map((entry) => {
              const isExpanded = expandedIds.has(entry.entry_id);

              return (
                <tr
                  key={entry.entry_id}
                  tabIndex={0}
                  onClick={() => toggleExpanded(entry.entry_id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") toggleExpanded(entry.entry_id);
                  }}
                  className="cursor-pointer border-b border-slate-100 align-top hover:bg-slate-50 focus-visible:bg-slate-50 focus-visible:outline-none"
                >
                  <td className="whitespace-nowrap px-4 py-1.5 text-slate-500">
                    {formatLogTime(entry.created_at)}
                  </td>
                  <td className="px-4 py-1.5">
                    <span className="inline-flex items-center gap-1.5 text-slate-600">
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${levelDot(entry.level)}`}
                      />
                      {entry.level}
                    </span>
                  </td>
                  <td className="truncate px-4 py-1.5 text-slate-500" title={entry.logger}>
                    {entry.logger}
                  </td>
                  <td className="px-4 py-1.5 text-slate-800">
                    <div className="flex items-start gap-1">
                      <ChevronRight
                        className={`mt-0.5 h-3 w-3 shrink-0 text-slate-400 transition-transform ${
                          isExpanded ? "rotate-90" : ""
                        } ${entry.exception ? "" : "invisible"}`}
                      />
                      <div className="min-w-0 flex-1">
                        <p className={isExpanded ? "whitespace-pre-wrap break-words" : "truncate"}>
                          {entry.message}
                        </p>
                        {isExpanded && entry.exception && (
                          <pre className="mt-1.5 overflow-x-auto rounded-md bg-slate-50 p-2 text-[11px] leading-relaxed text-slate-700">
                            {entry.exception}
                          </pre>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {entries.length > 0 && (
        <div className="flex items-center justify-between gap-3 px-4 py-2 text-xs text-slate-500">
          <span>
            {visibleEntries.length > 0 && (
              <span className="tabular-nums">
                {pageStart + 1}–{pageStart + pageEntries.length} /{" "}
                {visibleEntries.length}
                {visibleEntries.length !== entries.length &&
                  ` (lọc từ ${entries.length})`}
                {" · "}
              </span>
            )}
            Log được giữ trong bộ nhớ và mất khi server khởi động lại.
          </span>
          {pageCount > 1 && (
            <div className="flex shrink-0 gap-1">
              <IconButton
                title="Trang trước"
                aria-label="Trang trước"
                disabled={currentPage === 0}
                onClick={() => setPageIndex(currentPage - 1)}
              >
                <ArrowLeft className="h-4 w-4" />
              </IconButton>
              <IconButton
                title="Trang sau"
                aria-label="Trang sau"
                disabled={currentPage >= pageCount - 1}
                onClick={() => setPageIndex(currentPage + 1)}
              >
                <ArrowRight className="h-4 w-4" />
              </IconButton>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
