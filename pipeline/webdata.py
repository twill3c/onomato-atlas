"""配信データの生成(F-30〜F-33 / N-03)。

**運ぶもの**: 語の音側素性(決定論・全語)、採用軸のスコア(密度下限を満たす語のみ)、
パラダイム線(両端にスコアがある組)、用例の件数。

**運ばないもの**: 却下された軸のスコア(F-22)、近傍語(F-32b)。
近傍語は分割半で再現しないため UI に出さない。音側素性の近傍はクライアントが
素性から計算する(F-33)。用例本体は語ごとに分割して別ファイルで配る。
"""
from __future__ import annotations

from pipeline import extract, phon


def build(axes_doc: dict, vocab: dict, examples_doc: dict) -> dict:
    adopted_axes = [a for a in axes_doc["axes"] if a["decision"] == "adopted"]
    words: dict[str, dict] = {}
    for w in vocab["adopted"]:
        scores = {}
        for a in adopted_axes:
            v = a.get("projections", {}).get(w)
            if v is not None:
                scores[a["id"]] = v
        rec = {
            "word": w,
            "freq": vocab["vocab"].get(w, {}).get("freq", 0),
            "phon": phon.features(w),
            "axes": scores,
            "n_quotes": len(examples_doc.get("words", {}).get(w, {}).get("quotes", [])),
        }
        words[w] = rec

    paradigms = []
    ab = {w for w in vocab["adopted"] if extract.is_reduplication(w)}
    for w in vocab["adopted"]:
        if w in ab or len(w) != 3 or w[2] not in "りっんー":
            continue
        stem = w[:2] * 2
        if stem not in ab:
            continue
        for a in adopted_axes:
            p = a.get("projections", {})
            if stem in p and w in p:
                paradigms.append({
                    "axis": a["id"], "stem": stem, "variant": w,
                    "stem_score": p[stem], "variant_score": p[w],
                    "delta": round(p[w] - p[stem], 4),
                })
    axes_meta = [{
        "id": a["id"], "name": a["name"], "source": a.get("source", ""),
        "density_floor": a.get("density_floor"), "reliability": a.get("reliability"),
        "stats": a["stats"], "n_scored": len(a.get("projections", {})),
    } for a in adopted_axes]
    rejected = [{
        "id": a["id"], "name": a["name"], "stats": a["stats"], "decision": "rejected",
    } for a in axes_doc["axes"] if a["decision"] != "adopted"]
    return {"axes": axes_meta, "rejected_axes": rejected,
            "words": words, "paradigms": paradigms}


def main(argv=None) -> int:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    axes_doc = json.loads((root / "data" / "axes.json").read_text(encoding="utf-8"))
    vocab = json.loads((root / "data" / "vocab_manifest.json").read_text(encoding="utf-8"))
    ex = json.loads((root / "data" / "examples.json").read_text(encoding="utf-8"))
    doc = build(axes_doc, vocab, ex)

    out = root / "web" / "public" / "data"
    (out / "quotes").mkdir(parents=True, exist_ok=True)
    # 用例は語ごとに分割する。ファイル名に日本語を使うと符号化で壊れうるので通し番号にする
    ids = {w: i for i, w in enumerate(sorted(doc["words"]))}
    for w, i in ids.items():
        q = ex.get("words", {}).get(w, {}).get("quotes", [])
        (out / "quotes" / f"{i}.json").write_text(
            json.dumps({"word": w, "quotes": q}, ensure_ascii=False), encoding="utf-8")
        doc["words"][w]["id"] = i
    doc["generated_on"] = "2026-08-25"
    doc["corpus"] = {"works": 2200, "chars": 46687923, "authors": 328}
    (out / "index.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    size = (out / "index.json").stat().st_size
    qtotal = sum(p.stat().st_size for p in (out / "quotes").glob("*.json"))
    print(f"index.json {size / 1024:.0f} KB / 語 {len(doc['words'])} / "
          f"軸 {len(doc['axes'])} 採用・{len(doc['rejected_axes'])} 却下")
    print(f"パラダイム線 {len(doc['paradigms'])} 本")
    for a in doc["axes"]:
        print(f"  {a['id']:<10} スコア {a['n_scored']:>3} 語 / 下限 {a['density_floor']} / "
              f"信頼性 {a['reliability']}")
    print(f"quotes/ {len(ids)} ファイル 計 {qtotal / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
