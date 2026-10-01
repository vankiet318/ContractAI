import { useState } from "react";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { LoginPage } from "./components/LoginPage";
import { RegisterPage } from "./components/RegisterPage";
import { SessionList } from "./components/SessionList";
import { SessionMain } from "./components/SessionMain";
import { useAuth } from "./hooks/useAuth";
import { useSessions } from "./hooks/useSessions";

function AuthenticatedApp({ onLogout }: { onLogout: () => void }) {
  const {
    sessions,
    isLoading,
    create,
    remove,
    setSessionTitle,
  } = useSessions();
  const [selectedSessionId, setSelectedSessionId] = useState<
    string | null
  >(null);
  const [sessionPendingDeleteId, setSessionPendingDeleteId] = useState<
    string | null
  >(null);

  const selectedSession = sessions.find(
    (session) => session.session_id === selectedSessionId,
  );

  const sessionPendingDelete = sessions.find(
    (session) => session.session_id === sessionPendingDeleteId,
  );

  const handleCreate = async () => {
    const session = await create("Đoạn chat mới");
    setSelectedSessionId(session.session_id);
  };

  const confirmDeleteSession = async () => {
    if (!sessionPendingDeleteId) return;

    const sessionId = sessionPendingDeleteId;
    setSessionPendingDeleteId(null);

    await remove(sessionId);

    if (selectedSessionId === sessionId) {
      setSelectedSessionId(null);
    }
  };

  return (
    <div className="flex h-screen">
      <SessionList
        sessions={sessions}
        isLoading={isLoading}
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
