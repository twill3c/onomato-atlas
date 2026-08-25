"""用例データの生成(F-32 / N-05)。

data/raw の原文から語ごとの用例を切り出し、底本表記を付けて data/examples.json に書く。
**表示層は原文逐語**。分析層は語を見つけるためだけに使う。
"""
from __future__ import annotations

import json
from pathlib import Path

from pipeline import examples

ROOT = Path(__file__).resolve().parents[1]
PER_WORD = 6


def main(argv=None) -> int:
    manifest = json.loads((ROOT / "data" / "vocab_manifest.json").read_text(encoding="utf-8"))
    adopted = sorted(manifest["adopted"])
    corpus = json.loads((ROOT / "data" / "corpus_manifest.json").read_text(encoding="utf-8"))
    meta = {w["work_id"]: w for w in corpus["works"]}

    folded = {examples.kata_to_hira(w): w for w in adopted}
    out: dict[str, dict] = {w: {"word": w, "quotes": []} for w in adopted}
    files = sorted((ROOT / "data" / "raw").glob("*.txt"))
    for i, p in enumerate(files, 1):
        raw = p.read_text(encoding="utf-8")
        m = meta.get(p.stem, {})
        info = {"work_id": p.stem, "title": m.get("title", ""), "author": m.get("author", ""),
                "底本名": m.get("底本名", ""), "入力者": m.get("入力者", ""),
                "校正者": m.get("校正者", "")}
        low = examples.kata_to_hira(raw)
        for key, word in folded.items():
            if len(out[word]["quotes"]) >= PER_WORD or key not in low:
                continue
            rec = examples.build_record(word, raw, info, limit=2)
            out[word]["quotes"].extend(rec["quotes"][: PER_WORD - len(out[word]["quotes"])])
        if i % 400 == 0:
            done = sum(1 for r in out.values() if r["quotes"])
            print(f"  {i}/{len(files)} 作品  用例のある語 {done}/{len(adopted)}", flush=True)

    filled = {w: r for w, r in out.items() if r["quotes"]}
    (ROOT / "data" / "examples.json").write_text(
        json.dumps({"per_word_limit": PER_WORD, "words": filled}, ensure_ascii=False),
        encoding="utf-8")
    total = sum(len(r["quotes"]) for r in filled.values())
    print(f"用例 {total:,} 件 / 語 {len(filled)}/{len(adopted)}")
    empty = [w for w, r in out.items() if not r["quotes"]]
    if empty:
        print(f"用例が取れなかった語 {len(empty)}: {' '.join(empty[:20])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
