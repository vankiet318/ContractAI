import { useCallback, useEffect, useState } from "react";
import {
  createSession,
  deleteSession,
  listSessions,
} from "../api/sessions";
import { toErrorMessage } from "../api/client";
import type { ChatSessionSummary } from "../types";

export function useSessions() {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const result = await listSessions();
    setSessions(result);
    setLoadError(null);
    return result;
  }, []);

  const load = useCallback(() => {
    setIsLoading(true);

    refresh()
      .catch((error) =>
        setLoadError(toErrorMessage(error, "Không tải được danh sách đoạn chat.")),
      )
      .finally(() => setIsLoading(false));
  }, [refresh]);

  useEffect(() => {
    load();
  }, [load]);

  const create = useCallback(
    async (title: string) => {
      const session = await createSession(title);
      await refresh();
      return session;
    },
    [refresh],
  );

  const remove = useCallback(
    async (sessionId: string) => {
      await deleteSession(sessionId);
      await refresh();
    },
    [refresh],
  );

  const setSessionTitle = useCallback(
    (sessionId: string, title: string) => {
      setSessions((previous) =>
        previous.map((session) =>
          session.session_id === sessionId
            ? { ...session, title }
            : session,
        ),
      );
    },
    [],
  );

  return {
    sessions,
    isLoading,
    loadError,
    reload: load,
    refresh,
    create,
    remove,
    setSessionTitle,
  };
}
