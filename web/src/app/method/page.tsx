import { loadIndex } from "@/lib/data";

export const metadata = { title: "方法と限界 — 音象アトラス" };

const fmtP = (p: number) =>
  p < 1e-4 ? p.toExponential(1).replace("e-", " × 10⁻") : p.toFixed(4);

export default function Method() {
  const ix = loadIndex();
  const rej = ix.rejected_axes;

  return (
    <main>
      <p className="meta"><a href="/">← 音象アトラス</a></p>
      <h1>方法と限界</h1>
      <p className="lede">
        何をどう測ったか、そして<strong>何が測れなかったか</strong>。
        このページは後者にも同じだけの分量を割いています。
      </p>

      <h2>音と意味を別々に測る</h2>
      <p>
        「音が意味を運ぶ」を確かめるには、音と意味を<strong>別の情報源から</strong>
        測らなければなりません。音の形から意味の座標を計算してしまうと、
        「形を変えると意味が動く」は計算の当たり前になり、何も確かめたことになりません。
      </p>
      <ul>
        <li><strong>音側</strong> — 語頭子音・第2子音・母音・形態・濁音。表記から機械的に取ります</li>
        <li><strong>意味側</strong> — その語がどんな語と一緒に現れるか。青空文庫
          {ix.corpus.works.toLocaleString()} 作品・
          {Math.round(ix.corpus.chars / 10000).toLocaleString()} 万字の共起分布から取ります</li>
      </ul>
      <p>
        意味側を組み立てるコードは音側のコードを読み込みません。これは
        <strong>テストで機械的に検査</strong>しています。落ちたら、ほかが全部通っていても不合格です。
      </p>

      <h2>調べたこと</h2>
      <div className="scroll">
        <table>
          <thead><tr><th>問い</th><th>対</th><th>方向一致</th><th>p</th><th>対照</th><th>判定</th></tr></thead>
          <tbody>
            {ix.axes.map((a) => (
              <tr key={a.id}>
                <td>{a.name}</td>
                <td className="mono">{a.stats.n}</td>
                <td className="mono">{a.stats.same_direction}/{a.stats.n}</td>
                <td className="mono">{fmtP(a.stats.p_binomial)}</td>
                <td className="mono">{a.stats.control_p_empirical.toFixed(3)}</td>
                <td>採用</td>
              </tr>
            ))}
            {rej.map((a) => (
              <tr key={a.id}>
                <td>{a.name}</td>
                <td className="mono">{a.stats.n}</td>
                <td className="mono">—</td>
                <td className="mono">{fmtP(a.stats.p_binomial)}</td>
                <td className="mono">{a.stats.control_p_empirical.toFixed(3)}</td>
                <td><strong>却下</strong></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">
        「対照」は、対の組み合わせだけを無作為に入れ替えたときの結果です。
        形そのものが持つ共通の傾きはそのまま残るので、<strong>これを超えた分だけが
        「語ごとの対応」の証拠</strong>になります。
      </p>
      <p>
        却下した「{rej[0]?.name}」を見てください。二項検定では{" "}
        p = {rej[0] && fmtP(rej[0].stats.p_binomial)} と極端に小さい。
        素朴に見れば確実に採用する数字です。しかし対照と比べると
        p = {rej[0]?.stats.control_p_empirical.toFixed(3)} で、
        <strong>形そのものの効果で説明され尽くしていました</strong>。
        だからこの軸のスコアは、このサイトのどこにも載っていません。
      </p>

      <h2>ブーバとキキ</h2>
      <p>
        破裂音は尖ったものを、共鳴音は丸いものを思わせる —— 1929 年の Köhler 以来
        知られている現象です。日本語のオノマトペでも同じ方向が出るかを、
        <strong>結果を見る前に予測を書き留めてから</strong>調べました。
        予測・調べ方・判定の基準を先に固定し、後から動かせないようにしてあります。
      </p>
      <ul>
        <li><strong>通った</strong> — 語頭が無声破裂音(k / t / p)の語は、共鳴音の語より
          「叩く・打つ・当たる・砕く」といった語と一緒に現れる(補正後 p = 0.0004)</li>
        <li><strong>通らなかった</strong> — 母音に i を含む語が「細い・鋭い・尖る」と
          一緒に現れる傾向は、向きは予測どおりでしたが有意になりませんでした(p = 0.065)。
          基準は 0.05 と先に決めていたので、<strong>0.065 は通らなかったということです</strong></li>
      </ul>

      <h2>出せなかったもの</h2>
      <p>
        当初は「意味の近い語」を並べる地図を作るつもりでした。作品を偶数番と奇数番に分けて
        別々に測り直したところ、こうなりました。
      </p>
      <div className="scroll">
        <table>
          <thead><tr><th>何を言うか</th><th>半分に分けたときの一致</th><th>出すか</th></tr></thead>
          <tbody>
            <tr><td>軸そのもの(群として)</td><td className="mono">対の平均差 +0.147 / +0.130</td><td>出す</td></tr>
            <tr><td>語ごとの軸スコア</td><td className="mono">相関 0.50 / 0.37</td><td>誤差の帯つきで出す</td></tr>
            <tr><td>語ごとの近傍語</td><td className="mono">最も近い語の一致 0.117</td><td><strong>出さない</strong></td></tr>
            <tr><td>語ごとの空間内の位置</td><td className="mono">順位相関 0.123</td><td><strong>出さない</strong></td></tr>
          </tbody>
        </table>
      </div>
      <p>
        意味の場そのものは保たれます。<code>きらきら</code>の近くには、どちらの半分でも
        光の語が並びます。しかし<strong>どの語が並ぶかは入れ替わります</strong>。
        だから「この語に意味が近いのはこれです」とは言いません。
      </p>
      <p>
        一方、軸は {ix.axes[0]?.stats.n} 組・{ix.axes[1]?.stats.n} 組の平均です。
        語ごとのばらつきが打ち消し合うので安定します。
        <strong>群として言えることは言い、語として言えないことは言わない</strong> ——
        それがこのサイトに載っているものと載っていないものの境目です。
      </p>

      <h2>この地図が扱えないこと</h2>
      <ul>
        <li><strong>近代語です。</strong>青空文庫は明治から昭和前期が中心で、
          著者の生年の中央値は 1890 年です。現代の語感とはずれます</li>
        <li><strong>抽出は完璧ではありません。</strong>人が 100 件を目で確かめて、
          2 件が誤りでした(「ごんごんごま」から<code>ごんごん</code>を切り出すような、
          複合語の内部を拾う誤りです)</li>
        <li><strong>まだ判断していない語が 77 語あります。</strong>
          <code>そろそろ</code>のように、様態を模す語なのか単なる副詞なのか、
          機械では決められないものです</li>
        <li><strong>頻度の低い語は位置を出せません。</strong>
          軸によって {ix.axes.map((a) => a.density_floor).join(" ないし ")} 種類以上の
          共起語が必要で、届かない語には出していません</li>
      </ul>

      <h2>データと出典</h2>
      <p className="meta">
        本文は青空文庫(パブリックドメイン)。引用はすべて原文の一部をそのまま切り出し、
        底本・入力者・校正者を各引用に付しています。ルビと傍点も原文どおりです。
        語の採否・軸の対・除外する軽動詞の一覧は、いずれも版を付けて記録し、
        変えたときは影響を測り直しています。
      </p>
      <p className="meta">生成日 {ix.generated_on}</p>
    </main>
  );
}
