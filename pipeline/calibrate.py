"""Q-02(意味側ベクトルの最小密度)の較正。

**分割半信頼性**で測る: 作品を偶奇で二分し、各半分から独立に埋め込みを作って、
語ごとに近傍の一致率を見る。一致率が安定する密度が下限の目安になる。

作品単位で割るのは、同一作品内の共起が相関するため。出現を無作為に間引く方式は
その相関を無視して信頼性を過大評価する。
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from pipeline import aozora_text, build_vocab, sem

ROOT = Path(__file__).resolve().parents[1]


def split_cooccurrence(texts, targets, window=None):
    """作品を偶奇で二分し、それぞれの共起カウントを返す(トークン化は 1 回)。"""
    halves = [defaultdict(Counter), defaultdict(Counter)]
    for i, t in enumerate(texts):
        one = build_vocab.cooccurrence([t], targets)
        h = halves[i % 2]
        for w, c in one.items():
            h[w].update(c)
    return [{w: c for w, c in h.items()} for h in halves]


def neighbor_agreement(ctx_a, ctx_b, k: int, n_neighbors: int = 10) -> dict[str, float]:
    """両半分に現れる語について、近傍集合の一致率を返す。"""
    shared = sorted(set(ctx_a) & set(ctx_b))
    out = {}
    embs = []
    for ctx in (ctx_a, ctx_b):
        sub = {w: ctx[w] for w in shared}
        words, _, M = sem.build_matrix(sub, min_ctx_count=1)
        E, _ = sem.embed(sem.ppmi(M), k=k)
        embs.append((words, E))
    for w in shared:
        na = {x for x, _ in sem.neighbors(embs[0][0], embs[0][1], w, n_neighbors)}
        nb = {x for x, _ in sem.neighbors(embs[1][0], embs[1][1], w, n_neighbors)}
        out[w] = len(na & nb) / max(1, len(na))
    return out


def main(argv=None) -> int:
    manifest = json.loads((ROOT / "data" / "vocab_manifest.json").read_text(encoding="utf-8"))
    adopted = set(manifest["adopted"])
    texts = [aozora_text.normalize(p.read_text(encoding="utf-8"))
             for p in sorted((ROOT / "data" / "raw").glob("*.txt"))]
    print(f"読込 {len(texts)} 作品 / 採用 {len(adopted)} 語", flush=True)

    a, b = split_cooccurrence(texts, adopted)
    print(f"前半 {len(a)} 語 / 後半 {len(b)} 語", flush=True)
    # 分割データを保存する。k や近傍数の掃引で 46M 字を再トークン化しないため
    (ROOT / "data" / "cooc_halves.json").write_text(
        json.dumps([{w: dict(c) for w, c in h.items()} for h in (a, b)], ensure_ascii=False),
        encoding="utf-8")

    full = json.loads((ROOT / "data" / "cooc_counts.json").read_text(encoding="utf-8"))
    density = {w: len(c) for w, c in full.items()}

    K = 100
    agree = neighbor_agreement(a, b, k=K)
    buckets = [(0, 20), (20, 40), (40, 80), (80, 160), (160, 320), (320, 10 ** 9)]
    print(f"\n密度帯ごとの近傍一致率(k={K}・近傍 10 件・作品偶奇の分割半)")
    rows = []
    for lo, hi in buckets:
        ws = [w for w in agree if lo <= density.get(w, 0) < hi]
        if not ws:
            continue
        m = float(np.mean([agree[w] for w in ws]))
        rows.append({"lo": lo, "hi": None if hi > 10 ** 8 else hi, "n": len(ws), "agreement": m})
        label = f"{lo}-" + ("" if hi > 10 ** 8 else str(hi))
        print(f"  密度 {label:>9}: {len(ws):3} 語  一致率 {m:.3f}", flush=True)

    (ROOT / "data" / "q02_calibration.json").write_text(
        json.dumps({"k": K, "n_neighbors": 10, "buckets": rows,
                    "per_word": {w: round(v, 4) for w, v in agree.items()}},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("→ data/q02_calibration.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
