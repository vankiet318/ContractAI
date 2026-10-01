import { useCallback, useEffect, useState } from "react";

const SESSION_QUERY_PARAM = "session";

function readSessionIdFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get(SESSION_QUERY_PARAM);
}

function buildUrl(sessionId: string | null): string {
  const url = new URL(window.location.href);

  if (sessionId) {
    url.searchParams.set(SESSION_QUERY_PARAM, sessionId);
  } else {
    url.searchParams.delete(SESSION_QUERY_PARAM);
  }

  return url.toString();
}

/**
 * The selected session lives in the URL (?session=<id>) so it survives a
 * page reload and the browser's back/forward buttons move between sessions.
 */
export function useSelectedSessionId() {
  const [selectedSessionId, setSelectedSessionIdState] = useState(
    readSessionIdFromUrl,
  );

  useEffect(() => {
    const syncFromUrl = () => setSelectedSessionIdState(readSessionIdFromUrl());

    window.addEventListener("popstate", syncFromUrl);

    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const setSelectedSessionId = useCallback((sessionId: string | null) => {
    if (sessionId === readSessionIdFromUrl()) return;

    window.history.pushState(null, "", buildUrl(sessionId));
    setSelectedSessionIdState(sessionId);
  }, []);

  return [selectedSessionId, setSelectedSessionId] as const;
}
