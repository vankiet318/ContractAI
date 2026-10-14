/** "2026-10-14" → "14/10", or "14/10/2026" with the year. */
export function formatDay(isoDate: string, withYear = false): string {
  const [year, month, day] = isoDate.split("-");
  return withYear ? `${day}/${month}/${year}` : `${day}/${month}`;
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "—";

  return new Date(iso).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

// Categorical slots 1 and 2 of the chart palette.
export const QUERY_COLOR = "#2a78d6";
export const UPLOAD_COLOR = "#eb6834";
