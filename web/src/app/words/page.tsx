import { loadIndex } from "@/lib/data";

export const metadata = { title: "語一覧 — 音象アトラス" };

export default function Words() {
  const ix = loadIndex();
  const words = Object.values(ix.words).sort((a, b) => b.freq - a.freq);
  const scored = (id: string) => words.filter((w) => w.axes[id] !== undefined).length;
  return (
    <main>
      <p className="meta"><a href="/">← 音象アトラス</a></p>
      <h1>語一覧</h1>
      <p className="lede">
        青空文庫 {ix.corpus.works.toLocaleString()} 作品から抽出し、人手で採否を判断した{" "}
        {words.length} 語。頻度順です。軸の位置を出せるのは
        {ix.axes.map((a) => ` ${a.name} が ${scored(a.id)} 語`).join(" ・")}
        で、残りは用例が足りません。
      </p>
      <div className="scroll">
        <table>
          <thead>
            <tr><th>語</th><th>頻度</th><th>形</th><th>用例</th>
              {ix.axes.map((a) => <th key={a.id}>{a.name}</th>)}</tr>
          </thead>
          <tbody>
            {words.map((w) => (
              <tr key={w.word}>
                <td style={{ fontSize: "1.05rem" }}>
                  <a href={`/o/${encodeURIComponent(w.word)}/`}>{w.word}</a></td>
                <td className="mono">{w.freq}</td>
                <td className="meta">{w.phon.form}</td>
                <td className="mono">{w.n_quotes}</td>
                {ix.axes.map((a) => (
                  <td key={a.id} className="mono">
                    {w.axes[a.id] !== undefined ? w.axes[a.id].toFixed(2) : "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
