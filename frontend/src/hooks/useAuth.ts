import { useCallback, useEffect, useState } from "react";
import { fetchCurrentUser, login as loginRequest } from "../api/auth";
import { clearToken, getToken, setToken } from "../api/authStorage";
import { AUTH_UNAUTHORIZED_EVENT } from "../constants";
import type { CurrentUser } from "../types";

export function useAuth() {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    const handleUnauthorized = () => {
      setTokenState(null);
      setUser(null);
    };

    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);

    return () =>
      window.removeEventListener(
        AUTH_UNAUTHORIZED_EVENT,
        handleUnauthorized,
      );
  }, []);

  // The role decides whether the admin dashboard is offered; until it is
  // known the app behaves as for a regular user.
  useEffect(() => {
    // Cleared together with the token on logout.
    if (token === null) return;

    let cancelled = false;

    fetchCurrentUser()
      .then((result) => {
        if (!cancelled) setUser(result);
      })
      .catch(() => {
        // A 401 already logs out through AUTH_UNAUTHORIZED_EVENT.
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginRequest(email, password);
    setToken(response.access_token);
    setTokenState(response.access_token);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUser(null);
  }, []);

  return {
    isAuthenticated: token !== null,
    user,
    login,
    logout,
  };
}
