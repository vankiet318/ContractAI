import { useCallback, useEffect, useState } from "react";
import { login as loginRequest } from "../api/auth";
import { clearToken, getToken, setToken } from "../api/authStorage";
import { AUTH_UNAUTHORIZED_EVENT } from "../constants";

export function useAuth() {
  const [token, setTokenState] = useState<string | null>(() => getToken());

  useEffect(() => {
    const handleUnauthorized = () => setTokenState(null);

    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);

    return () =>
      window.removeEventListener(
        AUTH_UNAUTHORIZED_EVENT,
        handleUnauthorized,
      );
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginRequest(email, password);
    setToken(response.access_token);
    setTokenState(response.access_token);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
  }, []);

  return {
    isAuthenticated: token !== null,
    login,
    logout,
  };
}
