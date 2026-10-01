// The PDF text layer splits text into arbitrary spans and its whitespace
// rarely matches the extracted chunk text, so matching ignores all
// whitespace and case.
const PREFIX_LENGTHS = [60, 40, 20];

function compact(text: string): string {
  return text.replace(/\s+/g, "").toLowerCase();
}

export function findSpanForSnippet(
  spans: HTMLSpanElement[],
  snippet: string,
): HTMLSpanElement | null {
  const target = compact(snippet);
  if (!target) return null;

  const spanStarts: number[] = [];
  let pageText = "";

  for (const span of spans) {
    spanStarts.push(pageText.length);
    pageText += compact(span.textContent ?? "");
  }

  const matchStart = findPrefix(pageText, target);
  if (matchStart < 0) return null;

  return spans[spanIndexAt(spanStarts, matchStart)] ?? null;
}

function findPrefix(pageText: string, target: string): number {
  for (const length of PREFIX_LENGTHS) {
    const index = pageText.indexOf(target.slice(0, length));
    if (index >= 0) return index;
  }

  return -1;
}

function spanIndexAt(spanStarts: number[], offset: number): number {
  let index = 0;

  while (index + 1 < spanStarts.length && spanStarts[index + 1] <= offset) {
    index++;
  }

  return index;
}
