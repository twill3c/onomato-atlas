import { parseRuby, type Quote as Q } from "@/lib/data";

/** 引用は原文の部分文字列そのもの。ルビと傍点注記を表示用に描き分けるだけ(N-05)。 */
export default function Quote({ q, mark }: { q: Q; mark: string }) {
  const frags = parseRuby(q.quote);
  return (
    <figure style={{ margin: "0 0 1.6rem" }}>
      <blockquote style={{ margin: 0, fontSize: "1.02rem", lineHeight: 2 }}>
        {frags.map((f, i) => {
          if (f.t === "ruby") return <ruby key={i}>{f.base}<rt>{f.rt}</rt></ruby>;
          if (f.t === "note") return (
            <span key={i} className="meta" style={{ fontSize: "0.72em" }}>［{f.s}］</span>
          );
          const parts = f.s.split(mark);
          return (
            <span key={i}>
              {parts.map((p, j) => (
                <span key={j}>
                  {p}
                  {j < parts.length - 1 && (
                    <mark style={{ background: "transparent", color: "var(--accent)",
                                   fontWeight: 600 }}>{mark}</mark>
                  )}
                </span>
              ))}
            </span>
          );
        })}
      </blockquote>
      <figcaption className="meta">
        {q.source.author}『{q.source.title}』/ 底本『{q.source.底本名}』/
        入力 {q.source.入力者}{q.source.校正者 && ` / 校正 ${q.source.校正者}`}
      </figcaption>
    </figure>
  );
}
