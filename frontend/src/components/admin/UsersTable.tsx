import { ArrowDown, Lock, Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { AdminUserSummary } from "../../types";
import { TextInput } from "../ui/TextInput";
import { formatDate, formatDateTime } from "./format";

type SortKey =
  | "queries"
  | "uploads"
  | "total_queries"
  | "total_uploads"
  | "last_active_at"
  | "created_at";

function sortValue(user: AdminUserSummary, key: SortKey): number {
  const value = user[key];

  if (typeof value === "number") return value;
  return value ? new Date(value).getTime() : 0;
}

export function RoleBadge({ role }: { role: AdminUserSummary["role"] }) {
  if (role !== "admin") return null;

  return (
    <span className="rounded border border-slate-300 px-1.5 text-[11px] font-medium text-slate-600">
      Admin
    </span>
  );
}

export function LockedBadge() {
  return (
    <span
      className="inline-flex items-center gap-1 text-xs text-slate-500"
      title="Tạm khoá do đăng nhập sai nhiều lần"
    >
      <Lock className="h-3 w-3 text-red-500" />
      Tạm khoá
    </span>
  );
}

export function UsersTable({
  users,
  days,
  selectedUserId,
  onSelect,
}: {
  users: AdminUserSummary[];
  days: number;
  selectedUserId: string | null;
  onSelect: (userId: string) => void;
}) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("queries");

  const visibleUsers = useMemo(() => {
    const query = search.trim().toLowerCase();

    return users
      .filter((user) => user.email.toLowerCase().includes(query))
      .sort((a, b) => sortValue(b, sortKey) - sortValue(a, sortKey));
  }, [users, search, sortKey]);

  const columns: { key: SortKey; label: string }[] = [
    { key: "queries", label: `Câu hỏi (${days} ngày)` },
    { key: "uploads", label: `Tài liệu (${days} ngày)` },
    { key: "total_queries", label: "Tổng câu hỏi" },
    { key: "total_uploads", label: "Tổng tài liệu" },
    { key: "last_active_at", label: "Hoạt động gần nhất" },
    { key: "created_at", label: "Ngày tham gia" },
  ];

  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-medium text-slate-900">
          Người dùng ({users.length})
        </h2>
        <label className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <TextInput
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Tìm theo email"
            className="w-60 py-1.5 pl-8"
          />
        </label>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
              <th className="px-4 py-2 font-medium">Email</th>
              {columns.map((column) => (
                <th key={column.key} className="px-4 py-2 font-medium">
                  <button
                    type="button"
                    onClick={() => setSortKey(column.key)}
                    className={`inline-flex items-center gap-1 whitespace-nowrap hover:text-slate-900 ${
                      sortKey === column.key ? "text-slate-900" : ""
                    }`}
                    title="Sắp xếp giảm dần"
                  >
                    {column.label}
                    {sortKey === column.key && (
                      <ArrowDown className="h-3 w-3" />
                    )}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleUsers.map((user) => (
              <tr
                key={user.user_id}
                onClick={() => onSelect(user.user_id)}
                className={`cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50 ${
                  selectedUserId === user.user_id ? "bg-slate-100" : ""
                }`}
              >
                <td className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium text-slate-900">
                      {user.email}
                    </span>
                    <RoleBadge role={user.role} />
                    {user.is_locked && <LockedBadge />}
                  </div>
                </td>
                <td className="px-4 py-2 tabular-nums">{user.queries}</td>
                <td className="px-4 py-2 tabular-nums">{user.uploads}</td>
                <td className="px-4 py-2 tabular-nums text-slate-600">
                  {user.total_queries}
                </td>
                <td className="px-4 py-2 tabular-nums text-slate-600">
                  {user.total_uploads}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-slate-600">
                  {formatDateTime(user.last_active_at)}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-slate-600">
                  {formatDate(user.created_at)}
                </td>
              </tr>
            ))}

            {visibleUsers.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length + 1}
                  className="px-4 py-6 text-center text-slate-500"
                >
                  Không có người dùng phù hợp.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
