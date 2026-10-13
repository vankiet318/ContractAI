import { useRef, useState } from "react";
import { toErrorMessage } from "./api/client";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { LoginPage } from "./components/LoginPage";
import { RegisterPage } from "./components/RegisterPage";
import { SessionList } from "./components/SessionList";
import { SessionMain } from "./components/SessionMain";
import { useAuth } from "./hooks/useAuth";
import { useSelectedSessionId } from "./hooks/useSelectedSessionId";
import { useSessions } from "./hooks/useSessions";
import { useToast } from "./hooks/useToast";

function AuthenticatedApp({ onLogout }: { onLogout: () => void }) {
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
  const { isAuthenticated, login, logout } = useAuth();
  const [authView, setAuthView] = useState<"login" | "register">("login");

  if (!isAuthenticated) {
    return authView === "login" ? (
      <LoginPage
        onLogin={login}
        onSwitchToRegister={() => setAuthView("register")}
      />
    ) : (
      <RegisterPage onSwitchToLogin={() => setAuthView("login")} />
    );
  }

  return <AuthenticatedApp onLogout={logout} />;
}

export default App;
