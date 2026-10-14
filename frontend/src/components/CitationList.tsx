import { formatCitationLabel } from "../lib/citation";
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
          className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 hover:bg-slate-200"
        >
          {formatCitationLabel(citation)}
        </button>
      ))}
    </div>
  );
}
