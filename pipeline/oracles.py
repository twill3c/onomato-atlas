"""事前登録オラクルの実行(O-3 / F-21)。

**手続きの唯一の出所は `gold/o3_preregistration.json`。**
プローブ語・群定義・検定法・反復数・種・片側/両側・α・多重比較補正・最小群サイズを
コード側に書かない(T-201 が静的に検査する)。結果を見てから手続きを変えないための仕掛け。

音側素性(`phon`)は**群分けにのみ**使う。測定そのものは意味側の共起だけで行う
(事前登録 §procedure・SPEC F-00)。本モジュールは意味側の構成には関与しないので、
T-020 の SEMANTIC_MODULES には含めない。
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from pipeline import axes, phon


def load_preregistration(path: Path | str) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    if spec.get("status") != "registered":
        raise ValueError("登録済みでない事前登録は実行しない")
    return spec


def probe_scores(ctx: dict[str, Counter], probes: list[str]) -> dict[str, float]:
    """語ごとの、プローブ語との PPMI 合計。意味側の共起だけから計算する。"""
    words = sorted(ctx)
    cols = sorted({k for c in ctx.values() for k in c})
    ci = {c: i for i, c in enumerate(cols)}
    M = np.zeros((len(words), len(cols)))
    for i, w in enumerate(words):
        for k, v in ctx[w].items():
            M[i, ci[k]] = v
    X = axes.ppmi(M) if hasattr(axes, "ppmi") else _ppmi(M)
    idx = [ci[p] for p in probes if p in ci]
    if not idx:
        return {w: 0.0 for w in words}
    return {w: float(X[i, idx].sum()) for i, w in enumerate(words)}


def _ppmi(M: np.ndarray) -> np.ndarray:
    from pipeline import sem

    return sem.ppmi(M)


def _matches(word: str, cond: dict) -> bool:
    f = phon.features(word)
    if "onset1" in cond:
        return f["onset1"] in cond["onset1"]
    if "vowels_contain" in cond:
        return bool(f["vowels"]) and cond["vowels_contain"] in f["vowels"]
    if "vowels_not_contain" in cond:
        return bool(f["vowels"]) and cond["vowels_not_contain"] not in f["vowels"]
    raise ValueError(f"未知の群条件: {cond}")


def split_groups(words, cond_a: dict, cond_b: dict):
    """音側素性で 2 群に分ける。**群分けにしか音側を使わない。**"""
    a = [w for w in words if _matches(w, cond_a)]
    b = [w for w in words if _matches(w, cond_b)]
    return a, b


def verdict(diff: float, p_adj: float, alpha: float) -> str:
    """事前登録の方向と一致し、補正後 p が α 未満なら pass。"""
    return "pass" if (diff > 0 and p_adj < alpha) else "fail"


def run_hypothesis(hyp: dict, ctx: dict[str, Counter], procedure: dict) -> dict:
    scores = probe_scores(ctx, hyp["probes"])
    a, b = split_groups(sorted(ctx), hyp["group_a"], hyp["group_b"])
    if min(len(a), len(b)) < procedure["min_group_size"]:
        return {
            "id": hyp["id"], "verdict": "underpowered",
            "n_a": len(a), "n_b": len(b),
            "note": "群サイズが事前登録の下限未満。通過とも不通過とも書かない",
        }
    r = axes.permutation_test(
        [scores[w] for w in a], [scores[w] for w in b],
        n_iter=procedure["permutations"], seed=procedure["seed"],
        alternative="greater" if procedure["alternative"] == "one-sided" else "two-sided",
    )
    return {
        "id": hyp["id"], "claim": hyp["claim"], "n_a": len(a), "n_b": len(b),
        "mean_a": float(np.mean([scores[w] for w in a])),
        "mean_b": float(np.mean([scores[w] for w in b])),
        "diff": r["diff"], "p_raw": r["p"], "verdict": None,
    }


def run_all(spec: dict, ctx: dict[str, Counter]) -> dict:
    proc = spec["procedure"]
    results = [run_hypothesis(h, ctx, proc) for h in spec["hypotheses"]]
    testable = [r for r in results if r["verdict"] != "underpowered"]
    if testable:
        adj = axes.holm([r["p_raw"] for r in testable])
        for r, pa in zip(testable, adj):
            r["p_adj"] = pa
            r["verdict"] = verdict(r["diff"], pa, proc["alpha"])
    return {
        "preregistration": spec["id"],
        "procedure": proc,
        "results": results,
        # 総合ラベルは事前登録に無い(決定規則は仮説ごと)。集計として出すだけで、
        # 判定そのものは results の verdict が正本。
        "summary": {
            "pass": sum(1 for r in results if r["verdict"] == "pass"),
            "fail": sum(1 for r in results if r["verdict"] == "fail"),
            "underpowered": sum(1 for r in results if r["verdict"] == "underpowered"),
        },
    }
