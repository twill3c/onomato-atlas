import { loadIndex } from "@/lib/data";
import PairExamples from "./PairExamples";
import PairStrip from "./PairStrip";

const fmtP = (p: number) =>
  p < 1e-4 ? p.toExponential(1).replace("e-", " × 10⁻") : p.toFixed(4);

const PICK_D = ["ばたばた", "きらきら", "にこにこ", "くるくる", "ぐるぐる", "ふわふわ",
  "ちらちら", "さらさら", "ひらひら", "するする", "ゆらゆら", "ぽつぽつ", "ころころ",
  "じろじろ", "ほろほろ"];

export default function Home() {
  const ix = loadIndex();
  const duration = ix.axes.find((a) => a.id === "duration");
  const roughness = ix.axes.find((a) => a.id === "roughness");

  const dAll = ix.paradigms.filter((p) => p.axis === "duration");
  const dLines = dAll.map((p) => ({ a: p.stem_score, b: p.variant_score,
    delta: p.delta, key: `${p.stem}-${p.variant}` }));
  const dPick = PICK_D
    .map((s) => dAll.find((p) => p.stem === s && p.variant.endsWith("り")))
    .filter((p): p is NonNullable<typeof p> => !!p)
    .map((p) => ({ a: p.stem_score, b: p.variant_score, from: p.stem, to: p.variant }));
  const dv = dAll.flatMap((p) => [p.stem_score, p.variant_score]);

  const rAll = ix.voiced_pairs;
  const rLines = rAll.map((p) => ({ a: p.plain_score, b: p.voiced_score,
    delta: p.delta, key: `${p.plain}-${p.voiced}` }));
  const rPick = [...rAll].sort((a, b) => b.delta - a.delta).slice(0, 10)
    .map((p) => ({ a: p.plain_score, b: p.voiced_score, from: p.plain, to: p.voiced }));
  const rv = rAll.flatMap((p) => [p.plain_score, p.voiced_score]);

  const dSame = dLines.filter((p) => p.delta > 0).length;
  const rSame = rLines.filter((p) => p.delta > 0).length;

  return (
    <main>
      <h1>音象アトラス</h1>
      <p className="lede">
        オノマトペは音そのものが意味を運ぶと言われます。本当にそうなのかを、
        <strong>音の形</strong>と<strong>使われ方</strong>を別々に測って確かめました。
        音の形は表記から機械的に取り、使われ方は青空文庫
        {ix.corpus.works.toLocaleString()} 作品・
        {Math.round(ix.corpus.chars / 10000).toLocaleString()} 万字の共起分布から
        取っています。片方をもう片方の材料にしていません。
      </p>

      <h2>語の形を変えると、意味は同じ向きに動く</h2>
      <p>
        <code>ころころ</code> と <code>ころり</code> は語幹が同じで、形だけが違います。
        この二つが文章の中で置かれる位置は、どれだけ違うのか。
        左の白丸が <code>〜〜</code> の形、右の黒丸が <code>〜り</code> の形です。
      </p>
      <div className="axisline" />
      <div className="meta axisends" style={{ marginBottom: "0.3rem" }}>
        <span>← 反復・持続</span><span>一回・瞬間 →</span>
      </div>
      <PairExamples lines={dPick} lo={Math.min(...dv)} hi={Math.max(...dv)} />
      <p className="meta">
        いずれも右へ動きます。<code>ばたばた</code> が <code>ばたり</code> になると
        最も大きく動き、<code>ほろほろ</code> と <code>ほろり</code> の差は小さい。
      </p>

      <h3>同じことを {dLines.length} 組すべてで</h3>
      <p>
        上の 15 組は分かりやすいものを選びました。恣意的に見えないよう、
        位置を測れた組を全部並べます。1 本が 1 組で、点が <code>〜り</code> 側です。
      </p>
      <PairStrip lines={dLines} color="var(--duration)"
                 leftLabel="反復・持続" rightLabel="一回・瞬間"
                 note={`${dLines.length} 組中 ${dSame} 組が右へ(破線が逆向きの ${
                   dLines.length - dSame} 組)`} />
      <p>
        線はほぼすべて右へ傾きます。<strong>音韻素性は一切使っていません。</strong>
        使ったのは「どんな語と一緒に現れるか」だけです。それでも、形を変えると
        意味が一定の向きへ動く。構想の段階で予想した「瞬間 ⇔ 持続」という軸が、
        コーパスの側から出てきました。
      </p>
      {duration && (
        <p className="note">
          検定は位置を測れなかった組も含む {duration.stats.n} 組で実施。
          方向一致 {duration.stats.same_direction}/{duration.stats.n} 組・
          二項検定 p = {fmtP(duration.stats.p_binomial)}。
          対の組み合わせだけを無作為化した対照と比べても有意です
          (経験 p = {duration.stats.control_p_empirical.toFixed(3)})。
        </p>
      )}

      <h2>濁点を打つと、意味は重く粗くなる</h2>
      <p>
        <code>きらきら</code> と <code>ぎらぎら</code>、<code>さらさら</code> と{" "}
        <code>ざらざら</code>。清音と濁音だけが違う対を{" "}
        {roughness ? roughness.stats.n : 0} 組選びました。
        左の白丸が清音、右の黒丸が濁音です。
      </p>
      <div className="axisline" />
      <div className="meta axisends" style={{ marginBottom: "0.3rem" }}>
        <span>← 軽い・柔らかい</span><span>重い・粗い →</span>
      </div>
      <PairExamples lines={rPick} rough lo={Math.min(...rv)} hi={Math.max(...rv)} />
      <PairStrip lines={rLines} color="var(--roughness)"
                 leftLabel="軽い・柔らかい" rightLabel="重い・粗い"
                 note={`位置を測れた ${rLines.length} 組中 ${rSame} 組が右へ`} />
      {roughness && (
        <p className="note">
          検定は {roughness.stats.n} 組で実施。方向一致{" "}
          {roughness.stats.same_direction}/{roughness.stats.n} 組・
          二項検定 p = {fmtP(roughness.stats.p_binomial)}・
          対照の経験 p = {roughness.stats.control_p_empirical.toFixed(3)}。
          この軸を作るのに使っていない 533 語でも、濁音を含む語のほうが
          「重い・粗い」側に寄ります(並べ替え検定 p = 0.0001)。
        </p>
      )}

      <h2>出せなかったもの</h2>
      <p>
        当初は「意味の近い語」を並べる地図を作るつもりでした。作品を半分に分けて
        測り直したところ、<strong>最も近い語が一致するのは 100 回中 12 回</strong>しか
        ありませんでした。個々の語の近傍は、コーパスを変えると入れ替わります。
        だからこの地図には近傍語を載せていません。
      </p>
      <p>
        一方、上の二つの軸は {duration?.stats.n} 組・{roughness?.stats.n} 組の平均なので、
        語ごとのばらつきが打ち消し合って安定します。
        <strong>群として言えることは言い、語として言えないことは言わない</strong>
        —— それが載せるものと載せないものの境目です。
      </p>
      <p className="meta">
        <a href="/method/">方法と限界をくわしく</a> ・{" "}
        <a href="/words/">語を見る({Object.keys(ix.words).length} 語)</a> ・{" "}
        <a href="/authors/">作家ごとの傾向</a> ・{" "}
        <a href="/find/">探す</a>
      </p>
    </main>
  );
}
