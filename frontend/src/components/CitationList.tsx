import type { Citation } from "../types";

export function CitationList({
  citations,
  onSelect,
}: {
  citations: Citation[];
  onSelect: (citation: Citation) => void;
}) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {citations.map((citation) => (
        <button
          key={citation.chunk_id}
          type="button"
          title={citation.section_title ?? undefined}
          onClick={() => onSelect(citation)}
          className="text-xs bg-slate-100 text-slate-700 rounded px-2 py-0.5 hover:bg-slate-200"
        >
          {citation.source_id}
          {citation.section_number
            ? ` · Điều ${citation.section_number}`
            : ""}
          {" · trang "}
          {citation.page_start === citation.page_end
            ? citation.page_start
            : `${citation.page_start}-${citation.page_end}`}
        </button>
      ))}
    </div>
  );
}
