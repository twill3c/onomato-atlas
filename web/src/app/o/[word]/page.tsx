import { loadIndex, loadQuotes } from "@/lib/data";
import { nearest } from "@/lib/phonDist";
import AxisBar from "../../AxisBar";
import Quote from "../../Quote";

const COLOR: Record<string, string> = {
  duration: "var(--duration)", roughness: "var(--roughness)",
};
const ENDS: Record<string, [string, string]> = {
  duration: ["反復・持続", "一回・瞬間"], roughness: ["軽い・柔らかい", "重い・粗い"],
};
const FORM_JA: Record<string, string> = {
  ABAB: "反復形", "ABり": "一回完了形", "ABん": "撥音形", "ABっ": "促音形",
  "ABっと": "促音+と形", "ABー": "長音形", "ABーっ": "長音+促音形", unknown: "その他",
};

export function generateStaticParams() {
  return Object.keys(loadIndex().words).map((word) => ({ word: word.normalize("NFC") }));
}

export default async function WordPage({ params }: { params: Promise<{ word: string }> }) {
  const { word: raw } = await params;
  const word = decodeURIComponent(raw).normalize("NFC");
  const ix = loadIndex();
  const w = ix.words[word];
  if (!w) return <main><h1>{word}</h1><p>この語は収録していません。</p></main>;
  const quotes = loadQuotes(w.id);
  const p = w.phon;
  const phons = Object.fromEntries(Object.entries(ix.words).map(([k, v]) => [k, v.phon]));
  const sound = nearest(word, phons, 8);

  return (
    <main>
      <p className="meta"><a href="/words/">← 語一覧</a></p>
      <h1 style={{ fontSize: "2.6rem", letterSpacing: "0.12em" }}>{word}</h1>
      <p className="lede">
        青空文庫 {ix.corpus.works.toLocaleString()} 作品に {w.freq.toLocaleString()} 回。
        形は{FORM_JA[p.form] ?? p.form}。
      </p>

      <h2>用例</h2>
      <p className="meta" style={{ marginTop: "-0.4rem" }}>
        引用は青空文庫の本文をそのまま切り出したものです。ルビと傍点も原文どおりです。
      </p>
      {quotes.length === 0 && <p>用例が取れませんでした。</p>}
      {quotes.map((q, i) => <Quote key={i} q={q} mark={q.surface} />)}

      <h2>音の形</h2>
      <div className="scroll">
        <table>
          <tbody>
            <tr><th>語幹</th><td className="mono">{p.stem}</td>
                <th>形態</th><td>{FORM_JA[p.form] ?? p.form}</td></tr>
            <tr><th>語頭子音</th><td className="mono">{p.onset1 || "(なし)"}</td>
                <th>第2子音</th><td className="mono">{p.onset2 || "(なし)"}</td></tr>
            <tr><th>母音</th><td className="mono">{p.vowels}</td>
                <th>濁音</th><td>{p.voiced ? "あり" : "なし"}
                  {p.semivoiced ? " / 半濁音あり" : ""}</td></tr>
          </tbody>
        </table>
      </div>
      <p className="meta">
        音の形は表記から機械的に取っています。意味の測定には一切使っていません。
      </p>

      <h2>音が似ている語</h2>
      <p className="meta" style={{ marginTop: "-0.4rem" }}>
        <strong>音の形が似ているだけで、意味が近いとは限りません。</strong>
        語頭子音・第2子音・母音・形態・濁音などの一致で並べています。表記だけから
        機械的に出るので、コーパスを変えても結果は変わりません。
      </p>
      <p style={{ lineHeight: 2.2 }}>
        {sound.map((s) => (
          <a key={s.word} href={`/o/${encodeURIComponent(s.word)}/`}
             style={{ marginRight: "1.1rem", whiteSpace: "nowrap" }}>
            {s.word}<span className="meta" style={{ fontSize: "0.75em" }}> {s.distance}</span>
          </a>
        ))}
      </p>
      <p className="note">
        意味が近い語は出していません。作品を半分に分けて測り直すと、最も近い語が一致するのは
        100 回中 12 回しかありませんでした。再現しないものは載せません。
      </p>

      <h2>軸の上の位置</h2>
      {ix.axes.filter((a) => w.axes[a.id] !== undefined).map((a) => (
        <AxisBar key={a.id} axis={a} value={w.axes[a.id]}
                 color={COLOR[a.id] ?? "var(--accent)"}
                 left={ENDS[a.id]?.[0] ?? ""} right={ENDS[a.id]?.[1] ?? ""} />
      ))}
      {ix.axes.filter((a) => w.axes[a.id] === undefined).map((a) => (
        <p key={a.id} className="note">
          {a.name}: この語は用例が少なく、位置を出せる基準
          (異なり共起語 {a.density_floor} 以上)に届きません。だから出していません。
        </p>
      ))}
      <p className="note">
        帯は測定の標準誤差です。作品を半分に分けて測り直したときのぶれから求めています。
        帯が広いのは、この方法の精度がその程度だということです。
      </p>
    </main>
  );
}
