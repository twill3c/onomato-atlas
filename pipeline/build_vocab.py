"""語彙構築と品質指標の測定(F-05 / F-07 / Q-01 / Q-02)。

Q-01(抽出の偽陽性率)は**人手検査を要する**。本モジュールは決定論的な検査標本を出すだけで、
偽陽性率そのものを自動で算出しない。人手検査の結果は SPEC §6 に実測日つきで記録する。

Q-02(意味側ベクトルの最小密度)は異なり共起語数として測る。SVD は不要(L2 の仕事)。

軽動詞ストップリストは**測定器の設計**であり、変更は専用コミット + 感度分析を要する(F-13/F-14)。
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict

from pipeline import curate, extract

# 軽動詞ストップリスト v1.0.0(2026-08-25)
# 実測: これを除かないと きらきら→為る(16)、そわそわ→為る(30) のように
# 意味を持たない軽動詞が係り先を支配する(docs/concept.md §2 実測 7)
LIGHT_VERBS_VERSION = "1.0.0"
LIGHT_VERBS = frozenset(
    "為る 成る 居る 有る 遣る 来る 行く 仕舞う 出来る 見る 言う 思う 成す 致す 下さる".split()
)
CONTENT_POS = ("動詞", "形容詞", "名詞", "形状詞", "副詞")


def _kata(s: str) -> str:
    """ひらがな → カタカナ(行の粗い前フィルタ用)。"""
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ん" else c for c in s)
WINDOW = 5


def _tagger():
    return extract._tagger()


def cooccurrence(texts, targets: set[str], window: int = WINDOW) -> dict[str, Counter]:
    """対象語ごとの窓共起(内容語 lemma)。自分自身と軽動詞は数えない。"""
    ctx: dict[str, Counter] = defaultdict(Counter)
    seen: set[str] = set()  # 出現はしたが有効な共起語が 0 の語も密度 0 として残す(Q-02)
    for text in texts:
        for line in text.split("\n"):
            if not line.strip():
                continue
            ws = list(_tagger()(line))
            for i, w in enumerate(ws):
                norm = extract.kata_to_hira(w.surface)
                if norm not in targets:
                    continue
                seen.add(norm)
                lo, hi = max(0, i - window), min(len(ws), i + window + 1)
                for k in range(lo, hi):
                    if k == i or ws[k].feature.pos1 not in CONTENT_POS:
                        continue
                    lem = ws[k].feature.lemma or ws[k].surface
                    if lem in LIGHT_VERBS or extract.kata_to_hira(lem) == norm:
                        continue
                    ctx[norm][lem] += 1
    return {t: ctx.get(t, Counter()) for t in sorted(seen)}


def density_report(ctx: dict[str, Counter]) -> dict:
    """Q-02 の材料。語ごとの異なり共起語数とその分布。"""
    per = {w: len(c) for w, c in ctx.items()}
    vals = sorted(per.values())
    if not vals:
        return {"per_word": {}, "min": 0, "median": 0, "max": 0, "n": 0}
    return {
        "per_word": per,
        "min": vals[0],
        "median": vals[len(vals) // 2],
        "max": vals[-1],
        "n": len(vals),
    }


def false_positive_sample(texts, n: int = 100, seed: int = 0, window: int = 20,
                          targets: set[str] | None = None) -> list[dict]:
    """Q-01 用の検査標本。抽出された語とその文脈を決定論的に n 件返す。

    **偽陽性かどうかは人間が判断する。**本関数は判定しない。

    `targets` を渡すとその語の出現だけを標本にする。Q-01 は**抽出の誤分割**を測る指標なので、
    curation で除外済みの語を混ぜてはならない。混ぜると抽出の誤りと採否の判断が混ざる
    (2026-08-25 に実際に混ざり、200 件中 146 件が非擬態語になった)。
    """
    hits = []
    for ti, text in enumerate(texts):
        for line in text.split("\n"):
            s = line.strip()
            if not s:
                continue
            # 高速化: 対象語を含まない行は形態素解析にかけない
            if targets is not None and not any(t in s or _kata(t) in s for t in targets):
                continue
            for c in extract.candidates(s):
                if targets is not None and c.norm not in targets:
                    continue
                i = s.find(c.surface)
                hits.append(
                    {
                        "surface": c.surface,
                        "pos": c.pos,
                        "text_index": ti,
                        "context": s[max(0, i - window) : i + len(c.surface) + window],
                    }
                )
    rng = random.Random(seed)
    hits.sort(key=lambda h: (h["surface"], h["text_index"], h["context"]))
    return rng.sample(hits, min(n, len(hits)))


def build(texts, min_freq: int = 5, decisions_path=None) -> dict:
    """語彙を確定し、成果物一式を返す(F-07)。

    `decisions_path` はテストが本番の判定表に結合しないための注入口。本番表は curation の
    進行で正当に増えるので、テストが直接読むと正しい変更で落ちる(2026-08-25 に実際に落ちた)。
    """
    tal = extract.tally(texts)
    kept = {w: c for w, c in tal.items() if c >= min_freq}
    v = curate.build(kept, decisions_path=decisions_path)
    manifest = v.manifest()
    for w, rec in manifest.items():
        rec["freq"] = kept.get(w, 0)
    return {
        "vocab": manifest,
        "adopted": sorted(v.adopted),
        "needs_review": sorted(v.needs_review, key=lambda w: -kept.get(w, 0)),
        "table_version": v.version,
        "light_verbs_version": LIGHT_VERBS_VERSION,
        "min_freq": min_freq,
        "types_all": len(tal),
        "types_kept": len(kept),
        "tokens_all": sum(tal.values()),
    }


def _load_raw(raw_dir):
    from pipeline import aozora_text

    out = []
    for p in sorted(raw_dir.glob("*.txt")):
        out.append(aozora_text.normalize(p.read_text(encoding="utf-8")))
    return out


def main(argv=None) -> int:
    import argparse
    import csv
    import json
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-freq", type=int, default=5)
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260825)
    args = ap.parse_args(argv)

    texts = _load_raw(root / "data" / "raw")
    print(f"読込 {len(texts):,} 作品 / {sum(len(t) for t in texts):,} 字(正規化後)", flush=True)

    out = build(texts, min_freq=args.min_freq)
    print(f"抽出: 異なり {out['types_all']:,} / 延べ {out['tokens_all']:,} / "
          f"頻度>={args.min_freq} が {out['types_kept']:,}", flush=True)
    adopted = set(out["adopted"])
    print(f"curation: 採用 {len(adopted):,} / 保留 {len(out['needs_review']):,}", flush=True)

    ctx = cooccurrence(texts, adopted)
    dens = density_report(ctx)
    out["density"] = {k: v for k, v in dens.items() if k != "per_word"}
    for w, rec in out["vocab"].items():
        if w in dens["per_word"]:
            rec["ctx_types"] = dens["per_word"][w]
    print(f"共起密度(採用語 {dens['n']:,}): 最小 {dens['min']} / 中央値 {dens['median']} / 最大 {dens['max']}", flush=True)

    (root / "data" / "vocab_manifest.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    sample = false_positive_sample(texts, n=args.sample, seed=args.seed, targets=adopted)
    with (root / "data" / "curated" / "q01_sample.tsv").open("w", encoding="utf-8", newline="") as f:
        f.write(f"# Q-01 検査標本 {len(sample)} 件(seed={args.seed})。"
                "偽陽性なら is_false_positive 列に 1 を書く。判定は人間が行う\n")
        w = csv.writer(f, delimiter="\t")
        w.writerow(["surface", "pos", "is_false_positive", "context"])
        for s in sample:
            w.writerow([s["surface"], s["pos"], "", s["context"]])

    with (root / "data" / "curated" / "needs_review_worksheet.tsv").open("w", encoding="utf-8", newline="") as f:
        f.write(f"# needs_review ワークシート({len(out['needs_review'])} 語・頻度順)\n")
        f.write("# decision 列に adopted / rejected を書き、vocab_decisions.tsv へ反映する(SPEC §4.2)\n")
        w = csv.writer(f, delimiter="\t")
        w.writerow(["word", "freq", "ctx_types", "decision", "reason"])
        for x in out["needs_review"]:
            w.writerow([x, out["vocab"][x]["freq"], out["vocab"][x].get("ctx_types", ""), "", ""])

    print("成果物 → data/vocab_manifest.json / data/curated/q01_sample.tsv / needs_review_worksheet.tsv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
