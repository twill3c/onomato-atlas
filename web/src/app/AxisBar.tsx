import type { AxisMeta } from "@/lib/data";

/**
 * 語ごとの軸スコアを**帯**で描く。点で描くと精度を過大に見せる。
 * 帯の幅は測定の標準誤差 SEM = σ√(1-r)。信頼性は 0.70 前後しかない。
 */
export default function AxisBar({ axis, value, color, left, right }:
  { axis: AxisMeta; value: number; color: string; left: string; right: string }) {
  const span = axis.sd * 3;
  const pos = (v: number) => Math.min(100, Math.max(0, ((v + span) / (span * 2)) * 100));
  const sem = axis.sem ?? 0;
  const x1 = pos(value - sem), x2 = pos(value + sem);

  return (
    <div style={{ margin: "0 0 1.4rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between",
                    fontSize: "0.8rem", color: "var(--ink-soft)" }}>
        <span>{left}</span>
        <span>{axis.name}</span>
        <span>{right}</span>
      </div>
      <svg viewBox="0 0 100 8" width="100%" height="34" preserveAspectRatio="none"
           role="img" aria-label={`${axis.name}: ${value.toFixed(3)} ± ${sem.toFixed(3)}`}>
        <line x1="0" y1="4" x2="100" y2="4" stroke="var(--rule)" strokeWidth="0.4"
              vectorEffect="non-scaling-stroke" />
        <line x1="50" y1="1.5" x2="50" y2="6.5" stroke="var(--rule)" strokeWidth="0.4"
              vectorEffect="non-scaling-stroke" />
        <rect x={x1} y="2.4" width={Math.max(0.6, x2 - x1)} height="3.2"
              fill={color} opacity="0.32" />
        <line x1={pos(value)} y1="1.2" x2={pos(value)} y2="6.8" stroke={color}
              strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
      </svg>
      <p className="meta" style={{ margin: 0 }}>
        {value.toFixed(3)} ± {sem.toFixed(3)}(測定の標準誤差)・
        この軸の信頼性 {axis.reliability?.toFixed(2)}
      </p>
    </div>
  );
}
