import { useEffect, useRef, useState } from "react";
import { formatDay } from "./format";

const HEIGHT = 180;
const MARGIN = { top: 12, right: 8, bottom: 24, left: 36 };
const MAX_BAR_WIDTH = 24;
const BAR_RADIUS = 4;
// Dates shown under the axis, at most; the rest are in the tooltip.
const MAX_X_LABELS = 7;

export interface DailyBarPoint {
  date: string;
  value: number;
}

/** A clean axis maximum (1, 2, 5 × 10^n) with its tick step. */
function niceScale(max: number): { top: number; step: number } {
  if (max <= 4) return { top: 4, step: 1 };

  const rough = max / 4;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const step =
    [1, 2, 5, 10].map((factor) => factor * magnitude).find((s) => s >= rough) ??
    10 * magnitude;

  return { top: Math.ceil(max / step) * step, step };
}

function compact(value: number): string {
  return value >= 1000 ? `${+(value / 1000).toFixed(1)}K` : String(value);
}

/** Column with a rounded data end and a square base on the baseline. */
function columnPath(x: number, y: number, width: number, height: number) {
  const r = Math.min(BAR_RADIUS, width / 2, height);
  const bottom = y + height;

  return [
    `M${x},${bottom}`,
    `V${y + r}`,
    `Q${x},${y} ${x + r},${y}`,
    `H${x + width - r}`,
    `Q${x + width},${y} ${x + width},${y + r}`,
    `V${bottom}`,
    "Z",
  ].join(" ");
}

export function DailyBarChart({
  title,
  unit,
  points,
  color,
}: {
  title: string;
  /** Noun shown after the value in the tooltip, e.g. "câu hỏi". */
  unit: string;
  points: DailyBarPoint[];
  color: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    const observer = new ResizeObserver(([entry]) =>
      setWidth(entry.contentRect.width),
    );
    observer.observe(element);

    return () => observer.disconnect();
  }, []);

  const total = points.reduce((sum, point) => sum + point.value, 0);
  const { top, step } = niceScale(Math.max(0, ...points.map((p) => p.value)));

  const plotWidth = Math.max(0, width - MARGIN.left - MARGIN.right);
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const slot = points.length > 0 ? plotWidth / points.length : 0;
  // Leave at least a 2px gap between neighbouring columns.
  const barWidth = Math.max(1, Math.min(MAX_BAR_WIDTH, slot * 0.7, slot - 2));

  const y = (value: number) => MARGIN.top + plotHeight * (1 - value / top);

  const ticks: number[] = [];
  for (let tick = 0; tick <= top; tick += step) ticks.push(tick);

  const labelEvery = Math.max(1, Math.ceil(points.length / MAX_X_LABELS));

  const hovered = hoverIndex !== null ? points[hoverIndex] : null;
  const hoveredCenter =
    hoverIndex !== null ? MARGIN.left + slot * (hoverIndex + 0.5) : 0;

  return (
    <figure className="rounded-lg border border-slate-200 bg-white p-4">
      <figcaption className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-medium text-slate-900">{title}</span>
        <span className="text-xs text-slate-500">
          Tổng: <span className="font-medium text-slate-900">{total}</span>
        </span>
      </figcaption>

      <div ref={containerRef} className="relative mt-3">
        {width > 0 && (
          <svg
            width={width}
            height={HEIGHT}
            role="img"
            aria-label={`${title}: tổng ${total} ${unit}`}
            onMouseLeave={() => setHoverIndex(null)}
          >
            {ticks.map((tick) => (
              <g key={tick}>
                <line
                  x1={MARGIN.left}
                  x2={width - MARGIN.right}
                  y1={y(tick)}
                  y2={y(tick)}
                  stroke={tick === 0 ? "#cbd5e1" : "#f1f5f9"}
                />
                <text
                  x={MARGIN.left - 6}
                  y={y(tick)}
                  dy="0.32em"
                  textAnchor="end"
                  className="fill-slate-500 text-[10px]"
                >
                  {compact(tick)}
                </text>
              </g>
            ))}

            {hoverIndex !== null && (
              <rect
                x={MARGIN.left + slot * hoverIndex}
                y={MARGIN.top}
                width={slot}
                height={plotHeight}
                fill="#f1f5f9"
              />
            )}

            {points.map((point, index) => {
              const height = (plotHeight * point.value) / top;
              if (height <= 0) return null;

              return (
                <path
                  key={point.date}
                  d={columnPath(
                    MARGIN.left + slot * index + (slot - barWidth) / 2,
                    y(point.value),
                    barWidth,
                    height,
                  )}
                  fill={color}
                />
              );
            })}

            {points.map((point, index) =>
              index % labelEvery === 0 ? (
                <text
                  key={point.date}
                  x={MARGIN.left + slot * (index + 0.5)}
                  y={HEIGHT - 6}
                  textAnchor="middle"
                  className="fill-slate-500 text-[10px]"
                >
                  {formatDay(point.date)}
                </text>
              ) : null,
            )}

            {/* Hit targets span the whole day, not just the column. */}
            {points.map((point, index) => (
              <rect
                key={point.date}
                x={MARGIN.left + slot * index}
                y={MARGIN.top}
                width={slot}
                height={plotHeight}
                fill="transparent"
                onMouseEnter={() => setHoverIndex(index)}
              />
            ))}
          </svg>
        )}

        {hovered && (
          <div
            className="pointer-events-none absolute top-0 z-10 -translate-x-1/2 whitespace-nowrap rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs shadow-md"
            style={{
              left: Math.min(Math.max(hoveredCenter, 60), width - 60),
            }}
          >
            <div className="text-slate-500">{formatDay(hovered.date, true)}</div>
            <div className="mt-0.5 flex items-center gap-1.5 text-slate-900">
              <span
                className="h-2 w-2 rounded-sm"
                style={{ backgroundColor: color }}
              />
              <span className="font-medium">{hovered.value}</span> {unit}
            </div>
          </div>
        )}
      </div>
    </figure>
  );
}
