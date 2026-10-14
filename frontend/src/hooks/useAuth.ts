import { useCallback, useEffect, useState } from "react";
import { fetchCurrentUser, login as loginRequest } from "../api/auth";
import { clearToken, getToken, setToken } from "../api/authStorage";
import { AUTH_UNAUTHORIZED_EVENT } from "../constants";
import type { CurrentUser } from "../types";

interface LoadedUser {
  /** The token the user was fetched with; a result for an older token is
   * stale. */
  token: string;
  /** Null when the fetch failed. */
  user: CurrentUser | null;
}

export function useAuth() {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [loaded, setLoaded] = useState<LoadedUser | null>(null);

  useEffect(() => {
    const handleUnauthorized = () => setTokenState(null);

    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);

    return () =>
      window.removeEventListener(
        AUTH_UNAUTHORIZED_EVENT,
        handleUnauthorized,
      );
  }, []);

  // The role decides whether the admin dashboard is offered.
  useEffect(() => {
    // login() already fetched the user for its token.
    if (token === null || loaded?.token === token) return;

    let cancelled = false;

    fetchCurrentUser()
      .then((user) => {
        if (!cancelled) setLoaded({ token, user });
      })
      .catch(() => {
        // A 401 also logs out through AUTH_UNAUTHORIZED_EVENT. Otherwise the
        // app carries on as for a regular user.
        if (!cancelled) setLoaded({ token, user: null });
      });

    return () => {
      cancelled = true;
    };
  }, [token, loaded]);

  /** Resolves with the logged-in user, fetched before the app switches over
   * so the first screen already knows the role; null if that fetch failed. */
  const login = useCallback(
    async (email: string, password: string): Promise<CurrentUser | null> => {
      const response = await loginRequest(email, password);
      setToken(response.access_token);

      const user = await fetchCurrentUser().catch(() => null);

      setLoaded({ token: response.access_token, user });
      setTokenState(response.access_token);
      return user;
    },
    [],
  );

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
  }, []);

  const isCurrent = token !== null && loaded?.token === token;

  return {
    isAuthenticated: token !== null,
    user: isCurrent ? loaded.user : null,
    /** Logged in, but who the user is (and their role) is not known yet. */
    isUserLoading: token !== null && !isCurrent,
    login,
    logout,
  };
}
