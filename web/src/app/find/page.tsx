import { loadIndex } from "@/lib/data";
import FindClient from "./FindClient";

export const metadata = { title: "探す — 音象アトラス" };

export default function Find() {
  const ix = loadIndex();
  return (
    <main>
      <p className="meta"><a href="/">← 音象アトラス</a></p>
      <h1>探す</h1>
      <p className="lede">
        音の形と、検定を通った軸の位置で絞り込めます。ブラウザの中だけで動くので、
        入力した内容はどこにも送られません。
      </p>
      <p className="note">
        <strong>「意味が近い語」では絞れません。</strong>
        当初は文を入れて場面に合う語を出すつもりでしたが、語ごとの意味の位置は
        コーパスを半分に分けると再現しませんでした。ここで絞れるのは、
        表記から機械的に決まる音の形と、群として検定を通った軸だけです。
      </p>
      <FindClient words={Object.values(ix.words)} axes={ix.axes} />
    </main>
  );
}
