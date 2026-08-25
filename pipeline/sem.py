"""意味側チャネル(F-11 / F-12 / F-13 / F-14)。

**F-00(循環の禁止・最重要)**: このモジュールは音側(`pipeline.phon`)を import しない。
意味側の座標は音韻素性から一切影響を受けてはならない。T-020 が AST で静的に検査し、
落ちたら他が全緑でも不合格とする(AGENTS.md §1)。

構成: 窓共起カウント → PPMI → 打ち切り SVD。
SVD の次元数は**較正で決める**(F-15)。既定値をコードに焼かない。
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import numpy as np

_VERSION_RE = re.compile(r"^#\s*light_verbs\s+v(?P<v>[\w.\-]+)")


def load_stoplist(path: Path | str) -> tuple[str, frozenset[str]]:
    """軽動詞ストップリストを版付きファイルから読む(F-13)。

    version 行が無ければ例外。測定器を無記名で差し替えられないようにするため
    (AGENTS.md §3)。
    """
    p = Path(path)
    version = None
    lemmas: set[str] = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            m = _VERSION_RE.match(line)
            if m:
                version = m.group("v")
            continue
        if not line.strip() or line.startswith("lemma"):
            continue
        lemmas.add(line.split("\t", 1)[0].strip())
    if version is None:
        raise ValueError(f"version 行の無いストップリストは読まない: {p}")
    return version, frozenset(lemmas)


def build_matrix(ctx: dict[str, Counter], min_ctx_count: int = 5):
    """共起カウント行列を組む。戻り値は (語リスト, 文脈語リスト, 行列)。"""
    total: Counter = Counter()
    for c in ctx.values():
        total.update(c)
    cols = sorted(w for w, n in total.items() if n >= min_ctx_count)
    ci = {w: i for i, w in enumerate(cols)}
    words = sorted(ctx)
    M = np.zeros((len(words), len(cols)))
    for i, w in enumerate(words):
        for k, v in ctx[w].items():
            j = ci.get(k)
            if j is not None:
                M[i, j] = v
    return words, cols, M


def ppmi(M: np.ndarray) -> np.ndarray:
    """正の相互情報量。行と列が独立なら 0 になる(T-181 が解析的に検算する)。"""
    total = M.sum()
    if total == 0:
        return np.zeros_like(M)
    rows = M.sum(1, keepdims=True)
    colsum = M.sum(0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        X = np.log((M * total) / (rows * colsum))
    X[~np.isfinite(X)] = 0.0
    X[X < 0] = 0.0
    return X


def embed(X: np.ndarray, k: int):
    """打ち切り SVD。戻り値は (埋め込み, 寄与率)。k は較正で決める(F-15)。"""
    U, S, _ = np.linalg.svd(X, full_matrices=False)
    k = min(k, len(S))
    ev = (S ** 2) / (S ** 2).sum() if (S ** 2).sum() else np.zeros_like(S)
    return U[:, :k] * S[:k], ev[:k]


def _unit(E: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(E, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    return E / norm


def neighbors(words: list[str], E: np.ndarray, word: str, n: int = 10):
    """コサイン近傍。自分自身は返さない。"""
    i = words.index(word)
    sim = _unit(E) @ _unit(E)[i]
    order = np.argsort(-sim)
    return [(words[j], float(sim[j])) for j in order if j != i][:n]


def sensitivity(words: list[str], before: np.ndarray, after: np.ndarray, n: int = 10) -> dict:
    """測定器を変えたときの変位(F-14)。

    座標そのものは SVD の符号・回転で変わりうるので、**近傍の入れ替わり**を主指標にする。
    """
    b, a = _unit(before), _unit(after)
    shift = float(np.mean(np.linalg.norm(a - b, axis=1)))
    churn = []
    for i, w in enumerate(words):
        nb_b = {x for x, _ in neighbors(words, before, w, n)}
        nb_a = {x for x, _ in neighbors(words, after, w, n)}
        churn.append(1.0 - len(nb_b & nb_a) / max(1, len(nb_b)))
    return {"mean_shift": shift, "neighbor_churn": float(np.mean(churn)), "n_words": len(words)}


def governor_features(gov: dict[str, Counter], top_n: int = 10) -> dict[str, list]:
    """係り先用言を別特徴として保持する(F-12)。共起行列とは混ぜない。"""
    return {w: c.most_common(top_n) for w, c in gov.items()}
