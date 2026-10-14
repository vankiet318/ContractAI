import { useCallback, useEffect, useState } from "react";

const ADMIN_PATH = "/admin";

function isAdminPath(): boolean {
  return window.location.pathname.replace(/\/+$/, "") === ADMIN_PATH;
}

/** Whether the admin dashboard is open, kept in the URL (/admin) so a
 * reload or the back button keeps the user where they were. The servers
 * answer every path with index.html (Vite dev, Caddy's try_files). */
export function useAdminRoute(): [
  boolean,
  (open: boolean, options?: { replace?: boolean }) => void,
] {
  const [isOpen, setIsOpenState] = useState(isAdminPath);

  useEffect(() => {
    const handlePopState = () => setIsOpenState(isAdminPath());

    window.addEventListener("popstate", handlePopState);

    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const setIsOpen = useCallback(
    (open: boolean, options?: { replace?: boolean }) => {
      if (open !== isAdminPath()) {
        const url = open ? ADMIN_PATH : "/";

        // replace: the current URL should not stay in the history, e.g. a
        // regular user who typed /admin.
        if (options?.replace) {
          history.replaceState(null, "", url);
        } else {
          history.pushState(null, "", url);
        }
      }

      setIsOpenState(open);
    },
    [],
  );

  return [isOpen, setIsOpen];
}
