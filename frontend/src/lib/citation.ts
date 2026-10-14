import type { Citation } from "../types";

export function formatCitationLabel(citation: Citation): string {
  const pages =
    citation.page_start === citation.page_end
      ? `${citation.page_start}`
      : `${citation.page_start}-${citation.page_end}`;

  if (!citation.section_number) return `Trang ${pages}`;

  return `Điều ${citation.section_number} · trang ${pages}`;
}
