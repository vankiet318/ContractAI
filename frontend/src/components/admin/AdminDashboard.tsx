import { ArrowLeft, RefreshCw, ThumbsDown, ThumbsUp } from "lucide-react";
import { useRef, useState } from "react";
import { useAdminDashboard } from "../../hooks/useAdminDashboard";
import type {
  AdminOverview,
  MessageFeedback,
  RatedMessage,
} from "../../types";
import { AppLogo } from "../AppLogo";
import { LoadErrorMessage } from "../LoadErrorMessage";
import { Button, IconButton, TextButton } from "../ui/Button";
import { DailyBarChart } from "./DailyBarChart";
import { FeedbackList } from "./FeedbackList";
import { FeedbackPanel } from "./FeedbackPanel";
import { LogsView } from "./LogsView";
import { formatDay, QUERY_COLOR, UPLOAD_COLOR } from "./format";
import { UserUsagePanel } from "./UserUsagePanel";
import { useUserActions } from "./useUserActions";
import { UsersTable } from "./UsersTable";

const WINDOW_OPTIONS = [7, 30, 90];

type AdminTab = "overview" | "users" | "logs";

const TABS: { value: AdminTab; label: string }[] = [
  { value: "overview", label: "Tổng quan" },
  { value: "users", label: "Người dùng" },
  { value: "logs", label: "Log hệ thống" },
];

function StatTile({
  label,
  value,
  detail,
}: {
  label: string;
  value: React.ReactNode;
  detail?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 flex items-center gap-2 text-2xl font-semibold tabular-nums text-slate-900">
        {value}
      </p>
      {detail && (
        <div className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
          {detail}
        </div>
      )}
    </div>
  );
}

function StatTiles({
  overview,
  onShowFeedback,
}: {
  overview: AdminOverview;
  onShowFeedback: (rating: MessageFeedback) => void;
}) {
  const rated = overview.likes + overview.dislikes;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      <StatTile
        label="Người dùng"
        value={overview.total_users}
        detail={`+${overview.new_users} mới trong ${overview.days} ngày`}
      />
      <StatTile
        label="Người dùng hoạt động"
        value={overview.active_users}
        detail="Có hỏi hoặc tải tài liệu"
      />
      <StatTile label="Câu hỏi" value={overview.queries} />
      <StatTile label="Tài liệu tải lên" value={overview.uploads} />
      <StatTile
        label="Phản hồi"
        value={
          rated > 0 ? (
            <>
              <ThumbsUp className="h-5 w-5 text-slate-400" aria-label="Tỉ lệ hữu ích" />
              {Math.round((overview.likes / rated) * 100)}%
            </>
          ) : (
            "—"
          )
        }
        detail={
          <>
            <button
              type="button"
              onClick={() => onShowFeedback("like")}
              className="inline-flex items-center gap-1 hover:text-slate-900 hover:underline"
              title="Xem phản hồi hữu ích"
            >
              <ThumbsUp className="h-3.5 w-3.5" aria-label="Hữu ích" />
              {overview.likes}
            </button>
            <span className="mx-1">·</span>
            <button
              type="button"
              onClick={() => onShowFeedback("dislike")}
              className="inline-flex items-center gap-1 hover:text-slate-900 hover:underline"
              title="Xem phản hồi chưa tốt"
            >
              <ThumbsDown className="h-3.5 w-3.5" aria-label="Chưa tốt" />
              {overview.dislikes}
            </button>
          </>
        }
      />
    </div>
  );
}

function DailyTable({ overview }: { overview: AdminOverview }) {
  return (
    <div className="max-h-80 overflow-y-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-white">
          <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
            <th className="px-4 py-2 font-medium">Ngày</th>
            <th className="px-4 py-2 text-right font-medium">Câu hỏi</th>
            <th className="px-4 py-2 text-right font-medium">Tài liệu</th>
          </tr>
        </thead>
        <tbody>
          {[...overview.daily].reverse().map((day) => (
            <tr key={day.date} className="border-b border-slate-100 last:border-0">
              <td className="px-4 py-1.5 text-slate-600">
                {formatDay(day.date, true)}
              </td>
              <td className="px-4 py-1.5 text-right tabular-nums">
                {day.queries}
              </td>
              <td className="px-4 py-1.5 text-right tabular-nums">
                {day.uploads}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AdminDashboard({
  currentUserId,
  onBack,
}: {
  currentUserId: string;
  onBack: () => void;
}) {
  const [activeTab, setActiveTab] = useState<AdminTab>("overview");
  const [days, setDays] = useState(30);
  // Only one side panel is open at a time.
  const [panel, setPanel] = useState<
    | { kind: "user"; userId: string }
    | { kind: "feedback"; message: RatedMessage }
    | null
  >(null);
  const [feedbackRating, setFeedbackRating] =
    useState<MessageFeedback>("dislike");
  const feedbackRef = useRef<HTMLDivElement>(null);
  const [showTable, setShowTable] = useState(false);
  const { overview, users, isLoading, loadError, reload } =
    useAdminDashboard(days);

  // Bumped after a user action so an open details panel loads them again.
  const [userVersion, setUserVersion] = useState(0);

  const selectedUserId = panel?.kind === "user" ? panel.userId : null;
  const openUser = (userId: string) => setPanel({ kind: "user", userId });

  const userActions = useUserActions({
    currentUserId,
    onOpenDetails: openUser,
    onChanged: () => {
      setUserVersion((version) => version + 1);
      reload();
    },
    onDeleted: (userId) => {
      if (selectedUserId === userId) setPanel(null);
    },
  });

  const showFeedback = (rating: MessageFeedback) => {
    setFeedbackRating(rating);
    feedbackRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="flex h-screen bg-slate-50">
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-3">
          <div className="flex items-center gap-4">
            <AppLogo />
            <span className="text-sm text-slate-400">/</span>
            <h1 className="text-sm font-semibold text-slate-900">Quản trị</h1>
          </div>
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
            Về đoạn chat
          </Button>
        </header>

        <nav className="flex items-center gap-1 border-b border-slate-200 bg-white px-6 pt-2">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setActiveTab(tab.value)}
              className={`rounded-t-md px-3 py-1.5 text-sm font-medium ${
                activeTab === tab.value
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              {tab.label}
              {tab.value === "users" && overview && ` (${users.length})`}
            </button>
          ))}
        </nav>

        <main className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
          {/* The log tab has its own controls; it does not use the window. */}
          {activeTab !== "logs" && (
            <>
              <div className="flex items-center justify-between gap-3">
                <div
                  className="inline-flex rounded-md border border-slate-300 bg-white p-0.5"
                  role="group"
                  aria-label="Khoảng thời gian"
                >
                  {WINDOW_OPTIONS.map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setDays(option)}
                      className={`rounded px-3 py-1 text-sm ${
                        days === option
                          ? "bg-slate-900 text-white"
                          : "text-slate-600 hover:bg-slate-100"
                      }`}
                    >
                      {option} ngày
                    </button>
                  ))}
                </div>
                <IconButton onClick={reload} title="Tải lại" disabled={isLoading}>
                  <RefreshCw
                    className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
                  />
                </IconButton>
              </div>

              {loadError && <LoadErrorMessage message={loadError} onRetry={reload} />}

              {!overview && isLoading && (
                <p className="text-sm text-slate-500">Đang tải...</p>
              )}
            </>
          )}

          {overview && activeTab === "overview" && (
            <>
              <StatTiles overview={overview} onShowFeedback={showFeedback} />

              <div className="grid gap-3 lg:grid-cols-2">
                <DailyBarChart
                  title="Câu hỏi mỗi ngày"
                  unit="câu hỏi"
                  color={QUERY_COLOR}
                  points={overview.daily.map((day) => ({
                    date: day.date,
                    value: day.queries,
                  }))}
                />
                <DailyBarChart
                  title="Tài liệu tải lên mỗi ngày"
                  unit="tài liệu"
                  color={UPLOAD_COLOR}
                  points={overview.daily.map((day) => ({
                    date: day.date,
                    value: day.uploads,
                  }))}
                />
              </div>

              <TextButton onClick={() => setShowTable((value) => !value)}>
                {showTable ? "Ẩn bảng số liệu" : "Xem dạng bảng"}
              </TextButton>
              {showTable && <DailyTable overview={overview} />}

              <div ref={feedbackRef} className="scroll-mt-4">
                <FeedbackList
                  days={days}
                  rating={feedbackRating}
                  onRatingChange={setFeedbackRating}
                  likes={overview.likes}
                  dislikes={overview.dislikes}
                  selectedMessageId={
                    panel?.kind === "feedback" ? panel.message.message_id : null
                  }
                  onSelect={(message) => setPanel({ kind: "feedback", message })}
                />
              </div>
            </>
          )}

          {overview && activeTab === "users" && (
            <UsersTable
              users={users}
              days={days}
              selectedUserId={selectedUserId}
              onSelect={openUser}
              menuItems={userActions.menuItems}
            />
          )}

          {activeTab === "logs" && <LogsView />}
        </main>
      </div>

      {panel?.kind === "user" && (
        <UserUsagePanel
          key={panel.userId}
          userId={panel.userId}
          days={days}
          version={userVersion}
          onClose={() => setPanel(null)}
        />
      )}

      {panel?.kind === "feedback" && (
        <FeedbackPanel
          message={panel.message}
          onClose={() => setPanel(null)}
          onOpenUser={openUser}
        />
      )}

      {userActions.dialog}
    </div>
  );
}
