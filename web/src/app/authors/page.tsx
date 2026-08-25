import { loadAuthors } from "@/lib/data";

export const metadata = { title: "作家ごとの傾向 — 音象アトラス" };

export default function Authors() {
  const d = loadAuthors();
  const list = Object.values(d.authors)
    .filter((a) => a.n_significant > 0)
    .sort((a, b) => b.n_significant - a.n_significant || b.tokens - a.tokens);
  const quiet = d.n_authors - list.length;

  return (
    <main>
      <p className="meta"><a href="/">← 音象アトラス</a></p>
      <h1>作家ごとの傾向</h1>
      <p className="lede">
        誰がどのオノマトペを人より多く使うか。数え上げそのものに誤差はありませんが、
        {d.n_authors} 人 × 数百語を一度に比べると、偶然の偏りが山ほど「特徴」に見えます。
        そこで比較の数だけ基準を厳しくしました
        (通常の <span className="mono">z ≥ 1.96</span> ではなく{" "}
        <span className="mono">z ≥ {d.bonferroni_z.toFixed(2)}</span>)。
        それでも残ったものだけを並べています。
      </p>
      <p className="note">
        指標は情報事前分布つき対数オッズです。単純な割合だと、総数が少ない作家で
        たまたま出た語が 100% になってしまいます。この指標はコーパス全体の分布を
        下敷きにするので、少ない数は自動的に中央へ引き戻されます。
        延べ {d.min_tokens} 未満の作家は載せていません。
      </p>

      {list.map((a) => (
        <section key={a.author} style={{ margin: "2.2rem 0" }}>
          <h3 style={{ margin: "0 0 0.2rem" }}>{a.author}</h3>
          <p className="meta" style={{ margin: "0 0 0.5rem" }}>
            収録 {a.works} 作・延べ {a.tokens.toLocaleString()} 回・
            異なり {a.types} 語 / 基準を超えた語 {a.n_significant}
          </p>
          <p style={{ margin: 0, lineHeight: 2.1 }}>
            {a.top.filter((t) => t.z >= d.bonferroni_z).map((t) => (
              <a key={t.word} href={`/o/${encodeURIComponent(t.word)}/`}
                 style={{ marginRight: "1.2rem", whiteSpace: "nowrap" }}>
                {t.word}
                <span className="meta" style={{ fontSize: "0.75em" }}> {t.count}回</span>
              </a>
            ))}
          </p>
        </section>
      ))}

      <h2>基準を超えた語が無かった作家</h2>
      <p>
        {quiet} 人には、この基準を超える語がありませんでした。
        使っていないという意味ではありません。<strong>収録した作品の量では、
        他の作家との差を言い切れなかった</strong>ということです。
        著者ごとの収録は最大 20 作に抑えてあるので、その範囲での判断になります。
      </p>
      <p className="meta">
        ここで言えるのは「収録作でこの語が目立つ」までです。
        「この作家はこの語を好む」は、全作品を見ないと言えません。
      </p>
    </main>
  );
}
