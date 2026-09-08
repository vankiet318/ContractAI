import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const REVEAL_CHUNK_SIZE = 10;
const REVEAL_INTERVAL_MS = 8;

export function TypewriterMarkdown({
  text,
  onComplete,
  animate = true,
}: {
  text: string;
  onComplete?: () => void;
  animate?: boolean;
}) {
  const [visibleLength, setVisibleLength] = useState(
    animate ? 0 : text.length,
  );
  const hasCompletedRef = useRef(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (visibleLength >= text.length) {
      if (!hasCompletedRef.current) {
        hasCompletedRef.current = true;
        onCompleteRef.current?.();
      }
      return;
    }

    const timer = setTimeout(() => {
      setVisibleLength((length) =>
        Math.min(length + REVEAL_CHUNK_SIZE, text.length),
      );
    }, REVEAL_INTERVAL_MS);

    return () => clearTimeout(timer);
    // onComplete is read via a ref so it never re-triggers this effect;
    // only actual reveal progress or a new answer should restart it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visibleLength, text]);

  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]}>
      {text.slice(0, visibleLength)}
    </ReactMarkdown>
  );
}
