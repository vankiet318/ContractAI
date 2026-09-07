import type { Citation } from "../types";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {citations.map((citation) => (
        <span
          key={citation.chunk_id}
          title={citation.section_title ?? undefined}
          className="text-xs bg-slate-100 text-slate-700 rounded px-2 py-0.5"
        >
          {citation.source_id}
          {citation.section_number
            ? ` · Điều ${citation.section_number}`
            : ""}
          {" · trang "}
          {citation.page_start === citation.page_end
            ? citation.page_start
            : `${citation.page_start}-${citation.page_end}`}
        </span>
      ))}
    </div>
  );
}
