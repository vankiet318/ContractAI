import { ThumbsDown, ThumbsUp, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { formatCitationLabel } from "../../lib/citation";
import type { RatedMessage } from "../../types";
import { IconButton } from "../ui/Button";
import { formatDateTime } from "./format";

export function FeedbackPanel({
  message,
  onClose,
  onOpenUser,
}: {
  message: RatedMessage;
  onClose: () => void;
  onOpenUser: (userId: string) => void;
}) {
  const isDislike = message.feedback === "dislike";

  return (
    <aside className="flex h-full w-[32rem] shrink-0 flex-col border-l border-slate-200 bg-white">
      <header className="flex items-start justify-between gap-2 border-b border-slate-200 px-4 py-3">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-sm font-semibold text-slate-900">
            {isDislike ? (
              <ThumbsDown className="h-4 w-4" />
            ) : (
              <ThumbsUp className="h-4 w-4" />
            )}
            Phản hồi
          </p>
          <p className="mt-1 truncate text-xs text-slate-500">
            <button
              type="button"
              onClick={() => onOpenUser(message.user_id)}
              className="hover:text-slate-900 hover:underline"
              title="Xem thống kê người dùng"
            >
              {message.user_email}
            </button>
            {" · "}
            {message.session_title} · {formatDateTime(message.created_at)}
          </p>
        </div>
        <IconButton onClick={onClose} title="Đóng">
          <X className="h-4 w-4" />
        </IconButton>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        <section>
          <h3 className="text-xs font-medium text-slate-500">Câu hỏi</h3>
          <p className="mt-1.5 inline-block rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white">
            {message.question}
          </p>
        </section>

        <section>
          <h3 className="text-xs font-medium text-slate-500">Câu trả lời</h3>
          <div className="mt-1.5 rounded-lg bg-slate-50 px-3 py-2">
            {message.answer ? (
              <div className="prose prose-sm prose-slate max-w-none text-sm prose-p:my-1.5 prose-ul:my-1.5 prose-ol:my-1.5">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.answer}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm text-slate-500">(Không có câu trả lời)</p>
            )}
          </div>
        </section>

        <section>
          <h3 className="text-xs font-medium text-slate-500">
            Nguồn đã dùng ({message.citations.length})
          </h3>
          {message.citations.length === 0 ? (
            <p className="mt-1.5 text-sm text-slate-500">
              Câu trả lời không dựa trên đoạn nào trong tài liệu, có thể hệ
              thống đã không tìm thấy nội dung liên quan.
            </p>
          ) : (
            <ul className="mt-1.5 space-y-2">
              {message.citations.map((citation) => (
                <li
                  key={citation.chunk_id}
                  className="rounded-md border border-slate-200 px-3 py-2"
                >
                  <p className="text-xs font-medium text-slate-700">
                    {formatCitationLabel(citation)}
                    {citation.section_title && (
                      <span className="font-normal text-slate-500">
                        {" "}
                        · {citation.section_title}
                      </span>
                    )}
                  </p>
                  <p className="mt-1 whitespace-pre-line text-sm text-slate-600">
                    {citation.text_snippet}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </aside>
  );
}
