import { useEffect, useRef, useState } from "react";
import { listMessages, querySession } from "../api/query";
import { ApiError } from "../api/client";
import type { ChatMessage, Citation } from "../types";
import { CitationList } from "./CitationList";
import { TypingIndicator } from "./TypingIndicator";
import { TypewriterMarkdown } from "./TypewriterMarkdown";

const THINKING_LABELS = [
  "Đang truy vấn tài liệu...",
  "Đang phân tích ngữ cảnh liên quan...",
  "Đang soạn câu trả lời...",
];

function useThinkingLabel(isActive: boolean): string {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!isActive) {
      setIndex(0);
      return;
    }

    const timer = setInterval(() => {
      setIndex((previous) => (previous + 1) % THINKING_LABELS.length);
    }, 2200);

    return () => clearInterval(timer);
  }, [isActive]);

  return THINKING_LABELS[index];
}

function AnswerBubble({
  message,
  onCitationSelect,
}: {
  message: ChatMessage;
  onCitationSelect: (citation: Citation) => void;
}) {
  const [isRevealed, setIsRevealed] = useState(!message.animate);

  if (message.answer === null) return null;

  return (
    <div className="self-start bg-slate-50 rounded-lg px-3 py-2 max-w-[80%]">
      <div className="text-sm prose prose-sm prose-slate max-w-none prose-p:my-1.5 prose-ul:my-1.5 prose-ol:my-1.5">
        <TypewriterMarkdown
          text={message.answer}
          animate={message.animate}
          onComplete={() => setIsRevealed(true)}
        />
      </div>
      {isRevealed && (
        <CitationList
          citations={message.citations}
          onSelect={onCitationSelect}
        />
      )}
    </div>
  );
}

export function ChatPanel({
  sessionId,
  onCitationSelect,
  onTitleGenerated,
}: {
  sessionId: string;
  onCitationSelect: (citation: Citation) => void;
  onTitleGenerated?: (title: string) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const thinkingLabel = useThinkingLabel(isAsking);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isCancelled = false;

    setIsLoadingHistory(true);

    listMessages(sessionId)
      .then((history) => {
        if (isCancelled) return;

        setMessages(
          history.map((record) => ({
            id: record.message_id,
            question: record.question,
            status: "done",
            answer: record.answer,
            citations: record.citations,
            errorMessage: null,
            animate: false,
          })),
        );
      })
      .catch(() => {
        if (!isCancelled) setMessages([]);
      })
      .finally(() => {
        if (!isCancelled) setIsLoadingHistory(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    const trimmed = question.trim();
    if (!trimmed || isAsking) return;

    const messageId = crypto.randomUUID();

    setMessages((previous) => [
      ...previous,
      {
        id: messageId,
        question: trimmed,
        status: "pending",
        answer: null,
        citations: [],
        errorMessage: null,
        animate: true,
      },
    ]);
    setQuestion("");
    setIsAsking(true);

    try {
      const response = await querySession(sessionId, trimmed);

      setMessages((previous) =>
        previous.map((message) =>
          message.id === messageId
            ? {
                ...message,
                status: "done",
                answer: response.answer,
                citations: response.citations,
              }
            : message,
        ),
      );

      if (response.session_title && onTitleGenerated) {
        onTitleGenerated(response.session_title);
      }
    } catch (err) {
      setMessages((previous) =>
        previous.map((message) =>
          message.id === messageId
            ? {
                ...message,
                status: "error",
                errorMessage:
                  err instanceof ApiError ? err.message : "Query failed",
              }
            : message,
        ),
      );
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {!isLoadingHistory && messages.length === 0 && (
          <p className="text-sm text-slate-500">
            Đặt câu hỏi về các tài liệu trong đoạn chat này.
          </p>
        )}

        {messages.map((message) => (
          <div key={message.id} className="flex flex-col gap-1.5 mb-3">
            <p className="self-end text-sm font-medium bg-slate-900 text-white rounded-lg px-3 py-2 inline-block max-w-[80%]">
              {message.question}
            </p>

            {message.status === "pending" && (
              <div className="self-start flex flex-col items-start gap-1">
                <TypingIndicator />
                <p className="text-xs text-slate-400">{thinkingLabel}</p>
              </div>
            )}

            {message.status === "error" && (
              <p className="self-start text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2 inline-block max-w-[80%]">
                {message.errorMessage}
              </p>
            )}

            {message.status === "done" && (
              <AnswerBubble
                message={message}
                onCitationSelect={onCitationSelect}
              />
            )}
          </div>
        ))}

        <div ref={scrollAnchorRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-slate-200 flex gap-2"
      >
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about this contract..."
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={isAsking}
          className="rounded-md bg-slate-900 text-white text-sm font-medium px-4 py-2 hover:bg-slate-700 disabled:opacity-50 disabled:hover:bg-slate-900"
        >
          {isAsking ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
