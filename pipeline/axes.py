"""対比ベクトルによる軸推定と検定(F-20 / F-21 / F-22)。

**軸は手で定義しない。** 語対の集合(例 ABAB ↔ ABり)の意味側差分の平均方向として推定し、
検定を通ったものだけを軸として採用する。通っていない軸は UI に出さない(F-22)。

**F-00**: 推定も検定も意味側の座標だけで行う。音側素性は「どの語対を比べるか」の
群分けにしか使わない。このモジュールは phon を import しない。

検定の構成(docs/concept.md §11 発見C の手続きを踏襲):
- 方向一致検定: leave-one-out で各差分と他の平均方向のコサインを取り、正の数を二項検定
- 対照(対応シャッフル): 対の組み合わせだけを無作為化する。形態そのものが持つ共通方向を
  保存したまま「語ごとの対応」の寄与だけを取り出せる。**素の無作為対より厳しい対照**
"""
from __future__ import annotations

import math

import numpy as np


def _unit(V: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(V, axis=-1, keepdims=True)
    n = np.where(n == 0, 1.0, n)
    return V / n


def contrast_vector(diffs: np.ndarray) -> np.ndarray:
    """差分群の平均方向(単位ベクトル)。これが軸になる。"""
    return _unit(_unit(diffs).mean(0))


def project(E: np.ndarray, axis: np.ndarray) -> np.ndarray:
    """全語を軸方向へ射影する。検定を通った軸だけに使うこと(F-22)。"""
    return _unit(E) @ axis


def alignment_test(diffs: np.ndarray) -> dict:
    """leave-one-out 方向一致検定。"""
    D = _unit(diffs[np.linalg.norm(diffs, axis=1) > 1e-12])
    n = len(D)
    if n < 2:
        return {"n": n, "same_direction": 0, "mean_cos": 0.0, "p_binomial": 1.0,
                "mean_diff_len": 0.0}
    sims, pos = [], 0
    for i in range(n):
        m = np.delete(D, i, axis=0).mean(0)
        m = m / (np.linalg.norm(m) or 1.0)
        s = float(D[i] @ m)
        sims.append(s)
        pos += s > 0
    p = sum(math.comb(n, k) for k in range(pos, n + 1)) / (2 ** n)
    return {
        "n": n,
        "same_direction": int(pos),
        "mean_cos": float(np.mean(sims)),
        "p_binomial": float(p),
        "mean_diff_len": float(np.linalg.norm(D.mean(0))),
    }


def shuffle_control(A: np.ndarray, B: np.ndarray, n_iter: int = 1000, seed: int = 0) -> dict:
    """対応シャッフル対照。B 側の割り当てだけを無作為化する。

    形態そのものが持つ共通方向は保存されるので、これを上回った分だけが
    「語ごとの対応」の寄与になる。
    """
    rng = np.random.default_rng(seed)
    obs = alignment_test(B - A)
    ratios, cosines = [], []
    idx = np.arange(len(B))
    for _ in range(n_iter):
        rng.shuffle(idx)
        r = alignment_test(B[idx] - A)
        ratios.append(r["same_direction"] / max(1, r["n"]))
        cosines.append(r["mean_cos"])
    ratios = np.array(ratios)
    cosines = np.array(cosines)
    obs_ratio = obs["same_direction"] / max(1, obs["n"])
    return {
        "n_iter": n_iter,
        "seed": seed,
        "mean_ratio": float(ratios.mean()),
        "sd_ratio": float(ratios.std()),
        "mean_cos": float(cosines.mean()),
        "sd_cos": float(cosines.std()),
        "z_ratio": float((obs_ratio - ratios.mean()) / (ratios.std() or 1e-12)),
        "z_cos": float((obs["mean_cos"] - cosines.mean()) / (cosines.std() or 1e-12)),
        "p_empirical": float((ratios >= obs_ratio).mean()),
    }


def permutation_test(g1, g2, n_iter: int = 10000, seed: int = 0, alternative: str = "greater") -> dict:
    """2 群の平均差の並べ替え検定(O-3 の手続き)。scipy を使わない(N-01)。"""
    g1 = np.asarray(g1, dtype=float)
    g2 = np.asarray(g2, dtype=float)
    obs = float(g1.mean() - g2.mean())
    pool = np.concatenate([g1, g2])
    n1 = len(g1)
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_iter):
        rng.shuffle(pool)
        d = pool[:n1].mean() - pool[n1:].mean()
        count += (d >= obs) if alternative == "greater" else (abs(d) >= abs(obs))
    return {
        "diff": obs,
        "n1": n1,
        "n2": len(g2),
        "n_iter": n_iter,
        "seed": seed,
        "alternative": alternative,
        "p": float((count + 1) / (n_iter + 1)),
    }


def holm(pvalues) -> list[float]:
    """Holm 補正。戻り値は入力と同じ並び。"""
    p = list(pvalues)
    order = sorted(range(len(p)), key=lambda i: p[i])
    out = [0.0] * len(p)
    prev = 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, (len(p) - rank) * p[i])
        prev = max(prev, adj)
        out[i] = prev
    return out
