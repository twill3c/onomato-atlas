type Line = { a: number; b: number; from: string; to: string };

/** 具体例。**語の名前が見える**ことが目的なので、SVG ではなく文字で組む。 */
export default function PairExamples({ lines, rough = false, lo, hi }:
  { lines: Line[]; rough?: boolean; lo: number; hi: number }) {
  const pad = (hi - lo) * 0.02;
  const x = (v: number) => ((v - lo + pad) / (hi - lo + pad * 2)) * 100;
  // 端のラベルが切れないよう、軸そのものは中央 62% に収める
  const X = (v: number) => 19 + x(v) * 0.62;

  return (
    <div className="pairs">
      {lines.map((p) => {
        const a = X(p.a), b = X(p.b);
        return (
          <div className={rough ? "pair rough" : "pair"} key={p.from + p.to}>
            <div className="track">
              <span className="lab from" style={{ left: `${a}%` }}>{p.from}</span>
              <span className="dot from" style={{ left: `${a}%` }} />
              <span className="seg" style={{ left: `${Math.min(a, b)}%`,
                                             width: `${Math.abs(b - a)}%` }} />
              <span className="dot" style={{ left: `${b}%` }} />
              <span className="lab to" style={{ left: `${b}%` }}>{p.to}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
