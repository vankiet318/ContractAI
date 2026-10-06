import { SendHorizontal, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { listMessages, setMessageFeedback, streamQuery } from "../api/query";
import { toErrorMessage } from "../api/client";
import { MAX_QUESTION_LENGTH } from "../constants";
import { generateId } from "../lib/id";
import type { ChatMessage, Citation, MessageFeedback } from "../types";
import { CitationList } from "./CitationList";
import { LoadErrorMessage } from "./LoadErrorMessage";
import { TypingIndicator } from "./TypingIndicator";
import { Button, IconButton } from "./ui/Button";
import { TextInput } from "./ui/TextInput";

const THINKING_LABELS = [
  "Đang truy vấn tài liệu...",
  "Đang phân tích ngữ cảnh liên quan...",
  "Đang soạn câu trả lời...",
];

function useThinkingLabel(isActive: boolean): string {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!isActive) return;

    const timer = setInterval(() => {
      setIndex((previous) => (previous + 1) % THINKING_LABELS.length);
    }, 2200);

    return () => {
      clearInterval(timer);
      setIndex(0);
    };
  }, [isActive]);

  return THINKING_LABELS[index];
}

const FEEDBACK_THANKS_DURATION_MS = 2000;

function FeedbackButtons({
  initialFeedback,
  disabled,
  onFeedback,
}: {
  initialFeedback: MessageFeedback | null;
  disabled: boolean;
  onFeedback: (feedback: MessageFeedback) => void;
}) {
  const [isSubmitted, setIsSubmitted] = useState(initialFeedback !== null);
  const [showThanks, setShowThanks] = useState(false);

  useEffect(() => {
    if (!showThanks) return;

    const timer = setTimeout(
      () => setShowThanks(false),
      FEEDBACK_THANKS_DURATION_MS,
    );

    return () => clearTimeout(timer);
  }, [showThanks]);

  const submit = (value: MessageFeedback) => {
    if (disabled || isSubmitted) return;
    onFeedback(value);
    setIsSubmitted(true);
    setShowThanks(true);
  };

  if (showThanks) {
    return (
      <p className="mt-2 text-xs text-slate-500">Cảm ơn bạn đã phản hồi!</p>
    );
  }

  if (isSubmitted) return null;

  return (
    <div className="mt-2 flex items-center gap-1">
      <IconButton
        title="Câu trả lời hữu ích"
        disabled={disabled}
        onClick={() => submit("like")}
      >
        <ThumbsUp className="w-4 h-4" />
      </IconButton>
      <IconButton
        title="Câu trả lời chưa tốt"
        disabled={disabled}
        onClick={() => submit("dislike")}
      >
        <ThumbsDown className="w-4 h-4" />
      </IconButton>
    </div>
  );
}

function AnswerBubble({
  message,
  onCitationSelect,
  onFeedback,
}: {
  message: ChatMessage;
  onCitationSelect: (citation: Citation) => void;
  onFeedback: (feedback: MessageFeedback) => void;
}) {
  if (message.answer === null) return null;

  return (
    <div className="self-start bg-slate-50 rounded-lg px-3 py-2 max-w-[80%]">
      <div className="text-sm prose prose-sm prose-slate max-w-none prose-p:my-1.5 prose-ul:my-1.5 prose-ol:my-1.5">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {message.answer}
        </ReactMarkdown>
      </div>
      {message.status === "done" && (
        <>
          <CitationList
            citations={message.citations}
            onSelect={onCitationSelect}
          />
          <FeedbackButtons
            initialFeedback={message.feedback}
            disabled={message.messageId === null}
            onFeedback={onFeedback}
          />
        </>
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
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyLoadAttempt, setHistoryLoadAttempt] = useState(0);
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const thinkingLabel = useThinkingLabel(isAsking);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isCancelled = false;

    listMessages(sessionId)
      .then((history) => {
        if (isCancelled) return;

        setMessages(
          history.map((record) => ({
            id: record.message_id,
            messageId: record.message_id,
            question: record.question,
            status: "done",
            answer: record.answer,
            citations: record.citations,
            errorMessage: null,
            feedback: record.feedback,
          })),
        );
      })
      .catch((error) => {
        if (isCancelled) return;

        setHistoryError(
          toErrorMessage(error, "Không tải được lịch sử đoạn chat."),
        );
      })
      .finally(() => {
        if (!isCancelled) setIsLoadingHistory(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [sessionId, historyLoadAttempt]);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const retryLoadHistory = () => {
    setIsLoadingHistory(true);
    setHistoryError(null);
    setHistoryLoadAttempt((attempt) => attempt + 1);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    const trimmed = question.trim();
    if (!trimmed || isAsking) return;

    const messageId = generateId();

    setMessages((previous) => [
      ...previous,
      {
        id: messageId,
        messageId: null,
        question: trimmed,
        status: "pending",
        answer: null,
        citations: [],
        errorMessage: null,
        feedback: null,
      },
    ]);
    setQuestion("");
    setIsAsking(true);

    const updateMessage = (update: (message: ChatMessage) => ChatMessage) =>
      setMessages((previous) =>
        previous.map((message) =>
          message.id === messageId ? update(message) : message,
        ),
      );

    try {
      await streamQuery(sessionId, trimmed, {
        onCitations: (citations) =>
          updateMessage((message) => ({ ...message, citations })),
        onDelta: (text) =>
          updateMessage((message) => ({
            ...message,
            status: "streaming",
            answer: (message.answer ?? "") + text,
          })),
        onDone: (savedMessageId) =>
          updateMessage((message) => ({
            ...message,
            status: "done",
            messageId: savedMessageId,
          })),
        onTitle: (title) => onTitleGenerated?.(title),
      });
    } catch (err) {
      updateMessage((message) => ({
        ...message,
        status: "error",
        errorMessage: toErrorMessage(
          err,
          "Không gửi được câu hỏi. Vui lòng thử lại.",
        ),
      }));
    } finally {
      setIsAsking(false);
    }
  };

  const handleFeedback = (message: ChatMessage, feedback: MessageFeedback) => {
    if (!message.messageId) return;

    setMessageFeedback(sessionId, message.messageId, feedback).catch(() => {
      // Best-effort: the thank-you toast has already shown, no UI state
      // depends on this succeeding.
    });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {!isLoadingHistory && historyError && (
          <LoadErrorMessage
            message={historyError}
            onRetry={retryLoadHistory}
          />
        )}

        {!isLoadingHistory && !historyError && messages.length === 0 && (
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
                <p className="text-xs text-slate-500">{thinkingLabel}</p>
              </div>
            )}

            {message.status === "error" && (
              <p className="self-start text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 inline-block max-w-[80%]">
                {message.errorMessage}
              </p>
            )}

            {(message.status === "streaming" || message.status === "done") && (
              <AnswerBubble
                message={message}
                onCitationSelect={onCitationSelect}
                onFeedback={(feedback) => handleFeedback(message, feedback)}
              />
            )}
          </div>
        ))}

        <div ref={scrollAnchorRef} />
      </div>

      <form
        onSubmit={handleSubmit}
        className="px-4 pb-4 pt-2 flex gap-2"
      >
        <TextInput
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          maxLength={MAX_QUESTION_LENGTH}
          placeholder="Đặt câu hỏi về tài liệu..."
          className="flex-1"
        />
        <Button type="submit" disabled={isAsking}>
          <SendHorizontal className="w-4 h-4" />
          Gửi
        </Button>
      </form>
    </div>
  );
}
