import { useCallback, useEffect, useState } from "react";
import { fetchOverview, fetchUsers } from "../api/admin";
import { toErrorMessage } from "../api/client";
import type { AdminOverview, AdminUserSummary } from "../types";

export function useAdminDashboard(days: number) {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [users, setUsers] = useState<AdminUserSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    setIsLoading(true);

    Promise.all([fetchOverview(days), fetchUsers(days)])
      .then(([nextOverview, nextUsers]) => {
        if (cancelled) return;
        setOverview(nextOverview);
        setUsers(nextUsers);
        setLoadError(null);
      })
      .catch((error) => {
        if (cancelled) return;
        setLoadError(
          toErrorMessage(error, "Không tải được dữ liệu quản trị."),
        );
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [days]);

  useEffect(() => load(), [load]);

  return { overview, users, isLoading, loadError, reload: load };
}
