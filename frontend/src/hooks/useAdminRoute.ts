import { useCallback, useEffect, useState } from "react";

const ADMIN_HASH = "#admin";

/** Whether the admin dashboard is open, kept in the URL hash so a reload
 * or the back button keeps the user where they were. */
export function useAdminRoute(): [boolean, (open: boolean) => void] {
  const [isOpen, setIsOpenState] = useState(
    () => window.location.hash === ADMIN_HASH,
  );

  useEffect(() => {
    const handleHashChange = () =>
      setIsOpenState(window.location.hash === ADMIN_HASH);

    window.addEventListener("hashchange", handleHashChange);

    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const setIsOpen = useCallback((open: boolean) => {
    if (open) {
      window.location.hash = ADMIN_HASH;
    } else {
      // Drop the hash without leaving a bare "#" in the URL.
      history.pushState(
        null,
        "",
        window.location.pathname + window.location.search,
      );
    }

    setIsOpenState(open);
  }, []);

  return [isOpen, setIsOpen];
}
