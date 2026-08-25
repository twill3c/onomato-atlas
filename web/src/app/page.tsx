import { loadIndex } from "@/lib/data";
import PairChart from "./PairChart";

const fmtP = (p: number) =>
  p < 1e-4 ? p.toExponential(1).replace("e-", " × 10⁻") : p.toFixed(4);

export default function Home() {
  const ix = loadIndex();
  const duration = ix.axes.find((a) => a.id === "duration");
  const roughness = ix.axes.find((a) => a.id === "roughness");
  const dLines = ix.paradigms
    .filter((p) => p.axis === "duration")
    .map((p) => ({ a: p.stem_score, b: p.variant_score, delta: p.delta,
                   key: `${p.stem}-${p.variant}` }));
  const rLines = ix.voiced_pairs.map((p) => ({
    a: p.plain_score, b: p.voiced_score, delta: p.delta,
    key: `${p.plain}-${p.voiced}` }));

  return (
    <main>
      <h1>音象アトラス</h1>
      <p className="lede">
        オノマトペは音そのものが意味を運ぶと言われます。本当にそうなのかを、
        <strong>音の形</strong>と<strong>使われ方</strong>を別々に測って確かめました。
        音の形は表記から機械的に取り、使われ方は青空文庫
        {ix.corpus.works.toLocaleString()} 作品・{Math.round(ix.corpus.chars / 10000).toLocaleString()}
        万字の共起分布から取っています。片方をもう片方の材料にしていません。
      </p>

      <h2>語の形を変えると、意味は同じ向きに動く</h2>
      <p>
        <code>ころころ</code> と <code>ころり</code> は語幹が同じで、形だけが違います。
        この二つが文章の中で置かれる位置は、どれだけ違うのか。
        両方の位置が測れた {dLines.length} 組を線で結びました。
      </p>
      {duration && (
        <PairChart axis={duration} lines={dLines} color="var(--duration)"
                   testedN={duration.stats.n}
                   leftLabel="反復・持続(ころころ)" rightLabel="一回・瞬間(ころり)" />
      )}
      <p>
        線はほぼすべて右へ傾きます。<strong>音韻素性は一切使っていません。</strong>
        使ったのは「どんな語と一緒に現れるか」だけです。それでも、形を変えると
        意味が一定の向きへ動く。構想の段階で予想した「瞬間 ⇔ 持続」という軸が、
        コーパスの側から出てきました。
      </p>
      {duration && (
        <p className="note">
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
        {roughness ? roughness.stats.n : 0} 組選んで測りました。
        図に描けるのは両方の位置が測れた {rLines.length} 組だけです
        (この軸はスコアを出せる語が少なく、下限が厳しいためです)。
      </p>
      {roughness && (
        <PairChart axis={roughness} lines={rLines} color="var(--roughness)"
                   testedN={roughness.stats.n}
                   leftLabel="軽い・柔らかい" rightLabel="重い・粗い" />
      )}
      {roughness && (
        <p className="note">
          方向一致 {roughness.stats.same_direction}/{roughness.stats.n} 組・
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
        一方、上の二つの軸は 202 組・32 組の平均なので、語ごとのばらつきが打ち消し合って
        安定します。<strong>群として言えることは言い、語として言えないことは言わない</strong>
        —— それが載せるものと載せないものの境目です。
      </p>
      <p className="meta">
        <a href="/method/">方法と限界をくわしく</a>
      </p>
    </main>
  );
}
