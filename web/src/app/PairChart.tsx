import type { AxisMeta } from "@/lib/data";

type Line = { a: number; b: number; delta: number; key: string };
type Props = { axis: AxisMeta; lines: Line[]; color: string;
               leftLabel: string; rightLabel: string; testedN: number };

/**
 * 対が動く図。各対を軸上の短い矢印として重ねる。
 * 見せたいのは個々の語の位置ではなく「対が同じ向きに動くこと」なので、
 * 位置は点で描く(誤差の帯は語ページ側で示す — Q-02 の信頼性は 0.70 前後)。
 */
export default function PairChart({ axis, lines: pairs, color, leftLabel, rightLabel,
                                    testedN }: Props) {
  if (pairs.length === 0) return null;
  const vals = pairs.flatMap((p) => [p.a, p.b]);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.06 || 0.01;
  const x = (v: number) => ((v - lo + pad) / (hi - lo + pad * 2)) * 100;

  const sorted = [...pairs].sort((x, y) => x.a - y.a);
  const same = pairs.filter((p) => p.delta > 0).length;
  const row = 4.2, top = 26, h = top + sorted.length * row + 14;

  return (
    <figure style={{ margin: "1.5rem 0 2.5rem" }}>
      <div className="scroll">
        <svg viewBox={`0 0 100 ${h}`} width="100%" height={h * 7}
             preserveAspectRatio="none" role="img"
             aria-label={`${axis.name} の軸上で ${pairs.length} 組の対がどちらへ動くかを示す図`}>
          <line x1="0" y1={top - 9} x2="100" y2={top - 9}
                stroke="var(--rule)" strokeWidth="0.25" vectorEffect="non-scaling-stroke" />
          {sorted.map((p, i) => {
            const y = top + i * row;
            const back = p.delta <= 0;
            return (
              <g key={p.key} opacity={back ? 0.85 : 1}>
                <line x1={x(p.a)} y1={y} x2={x(p.b)} y2={y}
                      stroke={back ? "var(--ink-soft)" : color}
                      strokeWidth={back ? 1.1 : 1.4}
                      strokeDasharray={back ? "1.6 1.4" : undefined}
                      vectorEffect="non-scaling-stroke" />
                <circle cx={x(p.a)} cy={y} r="0.55" fill="var(--paper)"
                        stroke={back ? "var(--ink-soft)" : color} strokeWidth="0.3"
                        vectorEffect="non-scaling-stroke" />
                <circle cx={x(p.b)} cy={y} r="0.8"
                        fill={back ? "var(--ink-soft)" : color} />
              </g>
            );
          })}
        </svg>
      </div>
      <figcaption className="meta" style={{ display: "flex", justifyContent: "space-between",
                                            marginTop: "0.25rem" }}>
        <span>← {leftLabel}</span>
        <span>
          図に描けた {pairs.length} 組中 <strong style={{ color }}>{same} 組</strong>が同じ向き
          {testedN > pairs.length && `(検定は ${testedN} 組すべてで実施)`}
        </span>
        <span>{rightLabel} →</span>
      </figcaption>
    </figure>
  );
}
