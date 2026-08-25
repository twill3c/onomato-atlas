type Line = { a: number; b: number; delta: number; key: string };

/**
 * 全対をまとめて見る帯。**個々の語は読めなくてよい**。
 * 全部が同じ向きに傾いているかどうかが一目で入ることだけを狙う。
 * 縦横比は viewBox で固定する(引き伸ばすと丸が歪む)。
 */
export default function PairStrip({ lines, color, leftLabel, rightLabel, note }:
  { lines: Line[]; color: string; leftLabel: string; rightLabel: string; note: string }) {
  if (lines.length === 0) return null;
  const vals = lines.flatMap((p) => [p.a, p.b]);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.04 || 0.01;
  const W = 1000, ROW = 4.6, TOP = 8;
  const x = (v: number) => ((v - lo + pad) / (hi - lo + pad * 2)) * W;
  const sorted = [...lines].sort((p, q) => p.a - q.a);
  const H = TOP * 2 + sorted.length * ROW;

  return (
    <figure style={{ margin: "1rem 0 2rem" }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img"
           aria-label={`${lines.length} 組すべての向き`}>
        {sorted.map((p, i) => {
          const y = TOP + i * ROW;
          const back = p.delta <= 0;
          return (
            <g key={p.key}>
              <line x1={x(p.a)} y1={y} x2={x(p.b)} y2={y}
                    stroke={back ? "var(--ink-soft)" : color}
                    strokeWidth={back ? 2.2 : 1.6}
                    strokeDasharray={back ? "5 4" : undefined} opacity={back ? 0.9 : 0.75} />
              <circle cx={x(p.b)} cy={y} r="2.6" fill={back ? "var(--ink-soft)" : color} />
            </g>
          );
        })}
      </svg>
      <figcaption className="meta axisends">
        <span>← {leftLabel}</span><span>{note}</span><span>{rightLabel} →</span>
      </figcaption>
    </figure>
  );
}
