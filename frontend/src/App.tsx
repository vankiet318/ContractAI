import { useEffect, useRef, useState } from "react";
import { toErrorMessage } from "./api/client";
import { AdminDashboard } from "./components/admin/AdminDashboard";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { LoginPage } from "./components/LoginPage";
import { RegisterPage } from "./components/RegisterPage";
import { SessionList } from "./components/SessionList";
import { SessionMain } from "./components/SessionMain";
import { useAdminRoute } from "./hooks/useAdminRoute";
import { useAuth } from "./hooks/useAuth";
import { useSelectedSessionId } from "./hooks/useSelectedSessionId";
import { useSessions } from "./hooks/useSessions";
import { useToast } from "./hooks/useToast";

function AuthenticatedApp({
  onLogout,
  onOpenAdmin,
}: {
  onLogout: () => void;
  onOpenAdmin?: () => void;
}) {
  const { showToast } = useToast();
  const {
    sessions,
    isLoading,
    loadError,
    reload,
    refresh,
    create,
    remove,
    setSessionTitle,
  } = useSessions();
  const [selectedSessionId, setSelectedSessionId] = useSelectedSessionId();
  const [sessionPendingDeleteId, setSessionPendingDeleteId] = useState<
    string | null
  >(null);

  const selectedSession = sessions.find(
    (session) => session.session_id === selectedSessionId,
  );

  const sessionPendingDelete = sessions.find(
    (session) => session.session_id === sessionPendingDeleteId,
  );

  const isCreatingRef = useRef(false);

  const handleCreate = async () => {
    // A double click would otherwise race two creates past the server's
    // reuse of an empty session.
    if (isCreatingRef.current) return;
    isCreatingRef.current = true;

    try {
      // The server returns the existing empty session if there is one.
      const session = await create("Đoạn chat mới");
      setSelectedSessionId(session.session_id);
    } catch (error) {
      showToast(toErrorMessage(error, "Không tạo được đoạn chat."), "error");
    } finally {
      isCreatingRef.current = false;
    }
  };

  const confirmDeleteSession = async () => {
    if (!sessionPendingDeleteId) return;

    const sessionId = sessionPendingDeleteId;
    setSessionPendingDeleteId(null);

    try {
      await remove(sessionId);
    } catch (error) {
      showToast(toErrorMessage(error, "Không xóa được đoạn chat."), "error");
      return;
    }

    showToast("Đã xóa đoạn chat.", "success");

    if (selectedSessionId === sessionId) {
      setSelectedSessionId(null);
    }
  };

  return (
    <div className="flex h-screen">
      <SessionList
        sessions={sessions}
        isLoading={isLoading}
        loadError={loadError}
        onRetry={reload}
        selectedSessionId={selectedSessionId}
        onSelect={setSelectedSessionId}
        onCreate={handleCreate}
        onDelete={setSessionPendingDeleteId}
        onLogout={onLogout}
        onOpenAdmin={onOpenAdmin}
      />

      <ConfirmDialog
        open={sessionPendingDelete !== undefined}
        title="Xóa đoạn chat"
        message={`Xóa "${sessionPendingDelete?.title}"? Toàn bộ file và lịch sử chat của đoạn chat này sẽ bị xóa vĩnh viễn.`}
        onConfirm={confirmDeleteSession}
        onCancel={() => setSessionPendingDeleteId(null)}
      />

      {selectedSession ? (
        <SessionMain
          key={selectedSession.session_id}
          sessionId={selectedSession.session_id}
          sessionTitle={selectedSession.title}
          onTitleGenerated={(title) =>
            setSessionTitle(selectedSession.session_id, title)
          }
          onAnswerSavedWhileAway={() => {
            // Best-effort: picks up a title generated with the answer.
            refresh().catch(() => {});
          }}
        />
      ) : (
        <main className="flex-1 flex items-center justify-center text-sm text-slate-500">
          Chọn hoặc tạo một đoạn chat để bắt đầu.
        </main>
      )}
    </div>
  );
}

export function App() {
  const { isAuthenticated, user, isUserLoading, login, logout } = useAuth();
  const [authView, setAuthView] = useState<"login" | "register">("login");
  const [isAdminView, setIsAdminView] = useAdminRoute();
  const isAdmin = user?.role === "admin";

  // An admin who logs in goes straight to the dashboard; a reload keeps
  // whichever page the URL names.
  const handleLogin = async (email: string, password: string) => {
    const loggedInUser = await login(email, password);
    if (loggedInUser?.role === "admin") {
      setIsAdminView(true, { replace: true });
    }
  };

  // /admin opened by someone who turns out not to be an admin: back to the
  // chat, and the URL with it. Logged-out visitors keep /admin so an admin
  // lands on the dashboard after logging in.
  useEffect(() => {
    if (isAuthenticated && !isUserLoading && !isAdmin && isAdminView) {
      setIsAdminView(false, { replace: true });
    }
  }, [isAuthenticated, isUserLoading, isAdmin, isAdminView, setIsAdminView]);

  if (!isAuthenticated) {
    return authView === "login" ? (
      <LoginPage
        onLogin={handleLogin}
        onSwitchToRegister={() => setAuthView("register")}
      />
    ) : (
      <RegisterPage onSwitchToLogin={() => setAuthView("login")} />
    );
  }

  // Only /admin waits for the role; the chat does not depend on it.
  if (isAdminView && isUserLoading) {
    return (
      <div className="flex h-screen items-center justify-center gap-2 text-sm text-slate-500">
        <span className="h-4 w-4 rounded-full border-2 border-slate-300 border-t-slate-600 animate-spin" />
        Đang tải...
      </div>
    );
  }

  if (isAdmin && isAdminView) {
    return (
      <AdminDashboard
        currentUserId={user.user_id}
        onBack={() => setIsAdminView(false)}
      />
    );
  }

  return (
    <AuthenticatedApp
      onLogout={logout}
      onOpenAdmin={isAdmin ? () => setIsAdminView(true) : undefined}
    />
  );
}

export default App;
