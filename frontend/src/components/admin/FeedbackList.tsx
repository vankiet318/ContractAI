import { ArrowLeft, ArrowRight, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchFeedback } from "../../api/admin";
import { toErrorMessage } from "../../api/client";
import type { FeedbackPage, MessageFeedback, RatedMessage } from "../../types";
import { LoadErrorMessage } from "../LoadErrorMessage";
import { IconButton } from "../ui/Button";
import { formatDateTime } from "./format";

const PAGE_SIZE = 10;
const QUESTION_PREVIEW_CHARS = 60;
const ANSWER_PREVIEW_CHARS = 70;

/** One line of plain text: Markdown marks dropped, cut at a word. The full
 * text is in the detail panel. */
function preview(text: string, maxChars: number): string {
  const plain = text
    .replace(/[*_`#>|]+/g, "")
    .replace(/\s+/g, " ")
    .trim();

  if (plain.length <= maxChars) return plain;

  const cut = plain.slice(0, maxChars);
  const lastSpace = cut.lastIndexOf(" ");

  return `${lastSpace > maxChars / 2 ? cut.slice(0, lastSpace) : cut}…`;
}

export function FeedbackList({
  days,
  rating,
  onRatingChange,
  likes,
  dislikes,
  selectedMessageId,
  onSelect,
}: {
  days: number;
  rating: MessageFeedback;
  onRatingChange: (rating: MessageFeedback) => void;
  likes: number;
  dislikes: number;
  selectedMessageId: string | null;
  onSelect: (message: RatedMessage) => void;
}) {
  const [page, setPage] = useState<FeedbackPage | null>(null);
  const [offset, setOffset] = useState(0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // A new filter starts again from the first page.
  const [filterKey, setFilterKey] = useState(`${days}:${rating}`);
  if (filterKey !== `${days}:${rating}`) {
    setFilterKey(`${days}:${rating}`);
    setOffset(0);
  }

  useEffect(() => {
    let cancelled = false;

    fetchFeedback(days, rating, PAGE_SIZE, offset)
      .then((result) => {
        if (cancelled) return;
        setPage(result);
        setLoadError(null);
      })
      .catch((error) => {
        if (cancelled) return;
        setLoadError(toErrorMessage(error, "Không tải được phản hồi."));
      });

    return () => {
      cancelled = true;
    };
  }, [days, rating, offset, reloadKey]);

  const tabs: { value: MessageFeedback; label: string; count: number }[] = [
    { value: "dislike", label: "Chưa tốt", count: dislikes },
    { value: "like", label: "Hữu ích", count: likes },
  ];

  const total = page?.total ?? 0;

  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-medium text-slate-900">Phản hồi</h2>
        <div
          className="inline-flex rounded-md border border-slate-300 bg-white p-0.5"
          role="group"
          aria-label="Loại phản hồi"
        >
          {tabs.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => onRatingChange(tab.value)}
              title={tab.label}
              aria-label={tab.label}
              className={`inline-flex items-center gap-1.5 rounded px-3 py-1 text-sm ${
                rating === tab.value
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {tab.value === "dislike" ? (
                <ThumbsDown className="h-3.5 w-3.5" />
              ) : (
                <ThumbsUp className="h-3.5 w-3.5" />
              )}
              <span className="tabular-nums opacity-70">{tab.count}</span>
            </button>
          ))}
        </div>
      </div>

      {loadError && (
        <LoadErrorMessage
          message={loadError}
          onRetry={() => setReloadKey((key) => key + 1)}
        />
      )}

      {page && page.items.length === 0 && (
        <p className="px-4 py-6 text-center text-sm text-slate-500">
          Không có phản hồi nào trong {days} ngày qua.
        </p>
      )}

      {page && page.items.length > 0 && (
        <>
          <table className="w-full table-fixed text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                <th className="w-[30%] px-4 py-2 font-medium">Câu hỏi</th>
                <th className="w-[34%] px-4 py-2 font-medium">Câu trả lời</th>
                <th className="w-[20%] px-4 py-2 font-medium">Tài khoản</th>
                <th className="w-[16%] px-4 py-2 font-medium">Thời gian</th>
              </tr>
            </thead>
            <tbody>
              {page.items.map((item) => (
                <tr
                  key={item.message_id}
                  tabIndex={0}
                  onClick={() => onSelect(item)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") onSelect(item);
                  }}
                  title="Xem chi tiết"
                  className={`cursor-pointer border-b border-slate-100 hover:bg-slate-50 focus-visible:bg-slate-50 focus-visible:outline-none ${
                    selectedMessageId === item.message_id ? "bg-slate-100" : ""
                  }`}
                >
                  <td className="truncate px-4 py-2 font-medium text-slate-900">
                    {preview(item.question, QUESTION_PREVIEW_CHARS)}
                  </td>
                  <td className="truncate px-4 py-2 text-slate-500">
                    {item.answer
                      ? preview(item.answer, ANSWER_PREVIEW_CHARS)
                      : "—"}
                  </td>
                  <td className="truncate px-4 py-2 text-slate-600">
                    {item.user_email}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-slate-600">
                    {formatDateTime(item.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex items-center justify-between px-4 py-2 text-xs text-slate-500">
            <span className="tabular-nums">
              {offset + 1}–{offset + page.items.length} / {total}
            </span>
            <div className="flex gap-1">
              <IconButton
                title="Trang trước"
                aria-label="Trang trước"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              >
                <ArrowLeft className="h-4 w-4" />
              </IconButton>
              <IconButton
                title="Trang sau"
                aria-label="Trang sau"
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              >
                <ArrowRight className="h-4 w-4" />
              </IconButton>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
