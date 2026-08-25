"""作家ごとの使用傾向データの生成(F-40)。"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from pipeline import aozora_text, authors, extract

ROOT = Path(__file__).resolve().parents[1]
MIN_TOKENS = 60   # 総数がこれ未満の作家は傾向を語らない
TOP_N = 12


def main(argv=None) -> int:
    vocab = json.loads((ROOT / "data" / "vocab_manifest.json").read_text(encoding="utf-8"))
    adopted = set(vocab["adopted"])
    corpus = json.loads((ROOT / "data" / "corpus_manifest.json").read_text(encoding="utf-8"))
    meta = {w["work_id"]: w for w in corpus["works"]}

    per_author: dict[str, Counter] = defaultdict(Counter)
    works: dict[str, set] = defaultdict(set)
    files = sorted((ROOT / "data" / "raw").glob("*.txt"))
    for i, p in enumerate(files, 1):
        m = meta.get(p.stem)
        if not m:
            continue
        author = m.get("author") or "(不明)"
        text = aozora_text.normalize(p.read_text(encoding="utf-8"))
        for c in extract.candidates(text):
            if c.norm in adopted:
                per_author[author][c.norm] += 1
        works[author].add(p.stem)
        if i % 500 == 0:
            print(f"  {i}/{len(files)} 作品 / 作家 {len(per_author)}", flush=True)

    kept = {a: dict(c) for a, c in per_author.items() if sum(c.values()) >= MIN_TOKENS}
    print(f"作家 {len(per_author)} 中 {len(kept)} 名が総数 {MIN_TOKENS} 以上", flush=True)

    scored = authors.log_odds(kept)
    th = authors.bonferroni_z(len(kept), len({w for c in kept.values() for w in c}))
    out = {}
    for a, res in scored.items():
        top = sorted(res.items(), key=lambda kv: -kv[1]["z"])[:TOP_N]
        out[a] = {
            "author": a,
            "works": len(works[a]),
            "tokens": sum(kept[a].values()),
            "types": len(kept[a]),
            "top": [{"word": w, **v} for w, v in top],
            "n_significant": sum(1 for v in res.values() if v["z"] >= th),
        }
    doc = {"generated_on": "2026-08-25", "min_tokens": MIN_TOKENS,
           "prior_strength": authors.PRIOR_STRENGTH,
           "bonferroni_z": th, "n_authors": len(out), "authors": out}
    (ROOT / "data" / "authors.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    web = ROOT / "web" / "public" / "data"
    web.mkdir(parents=True, exist_ok=True)
    (web / "authors.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    sig = sum(v["n_significant"] for v in out.values())
    print(f"補正後の閾値 z >= {th} / 閾値を超えた作家×語 {sig} 件")
    rank = sorted(out.values(), key=lambda v: -v["tokens"])[:8]
    for r in rank:
        w = ", ".join(f"{t['word']}(z{t['z']:.1f})" for t in r["top"][:4])
        print(f"  {r['author']:<10} {r['works']:>2}作 延べ{r['tokens']:>5}  {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
