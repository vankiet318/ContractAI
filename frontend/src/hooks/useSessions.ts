import { useCallback, useEffect, useState } from "react";
import {
  createSession,
  deleteSession,
  listSessions,
} from "../api/sessions";
import type { ChatSessionSummary } from "../types";

export function useSessions() {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    const result = await listSessions();
    setSessions(result);
    setIsLoading(false);
    return result;
  }, []);

  useEffect(() => {
    refresh().catch(() => setIsLoading(false));
  }, [refresh]);

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
    refresh,
    create,
    remove,
    setSessionTitle,
  };
}
