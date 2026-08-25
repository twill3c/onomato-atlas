"""作家ごとの使用傾向(F-40)。

**カウントは正確、一般化は推論。** 収録作でのカウントに誤差は無いが、
著者あたり最大 20 作という標本から「この作家はこの語を好む」と言うのは推論である。

指標は**情報事前分布つき対数オッズ**(Monroe, Colaresi & Quinn 2008)。
単純な相対頻度は低頻度語で暴れ(総数 3 で 1 語なら 33%)、
328 作家 × 597 語の比較では偽の特徴語を大量に生む。この指標は
コーパス全体の分布を事前分布に使うので、少ないカウントは自動的に中央へ引き戻される。
"""
from __future__ import annotations

import math

PRIOR_STRENGTH = 500.0


def log_odds(counts: dict[str, dict[str, int]],
             prior_strength: float = PRIOR_STRENGTH) -> dict[str, dict[str, dict]]:
    """作家 → 語 → {z, delta, count, author_total} を返す。"""
    corpus: dict[str, int] = {}
    for row in counts.values():
        for w, c in row.items():
            corpus[w] = corpus.get(w, 0) + c
    total = sum(corpus.values())
    if total == 0:
        return {a: {} for a in counts}
    # 事前分布はコーパス全体の分布を prior_strength 個ぶんに縮めたもの
    alpha = {w: prior_strength * c / total for w, c in corpus.items()}
    a0 = sum(alpha.values())

    out: dict[str, dict[str, dict]] = {}
    for author, row in counts.items():
        n_i = sum(row.values())
        res: dict[str, dict] = {}
        for w in corpus:
            y_i = row.get(w, 0)
            aw = alpha[w]
            num_i = y_i + aw
            den_i = n_i + a0 - num_i
            num_all = corpus[w] + aw
            den_all = total + a0 - num_all
            if den_i <= 0 or den_all <= 0:
                continue
            delta = math.log(num_i / den_i) - math.log(num_all / den_all)
            var = 1.0 / num_i + 1.0 / num_all
            res[w] = {"z": round(delta / math.sqrt(var), 4),
                      "delta": round(delta, 4),
                      "count": y_i, "author_total": n_i}
        out[author] = res
    return out


def bonferroni_z(n_authors: int, n_words: int, alpha: float = 0.05) -> float:
    """多重比較の補正閾値(両側・正規近似)。328 × 597 の比較を素の 1.96 で見ない。"""
    m = max(1, n_authors * n_words)
    p = alpha / m / 2.0
    # 標準正規の上側 p 点を二分法で求める(scipy を使わない — N-01)
    lo, hi = 0.0, 12.0
    for _ in range(200):
        mid = (lo + hi) / 2
        tail = 0.5 * math.erfc(mid / math.sqrt(2))
        if tail > p:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)
