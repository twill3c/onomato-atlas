"""対比ベクトルによる軸推定と検定(F-20 / F-21)。

期待値の出所: 検定の定義そのもの。合成データで**前提を assert して検算**する
(VERIF-FALSE / HC-004 の予防)。実データの数値を定数で焼かない。

**F-00**: 軸の推定は意味側の座標だけで行う。音側は「どの語対を比べるか」の
群分けにしか使わない。
"""
import numpy as np
import pytest

from pipeline import axes

RNG = np.random.default_rng(0)


def aligned_pairs(n=30, dim=8, noise=0.15):
    """差分が同じ方向を向くよう作った対。前提をテスト内で検算する。"""
    direction = np.zeros(dim)
    direction[0] = 1.0
    a = RNG.normal(size=(n, dim))
    b = a + direction + noise * RNG.normal(size=(n, dim))
    diffs = b - a
    unit = diffs / np.linalg.norm(diffs, axis=1, keepdims=True)
    assert (unit @ direction > 0).mean() > 0.9, "合成データの前提(方向が揃う)が崩れている"
    return a, b


def random_pairs(n=30, dim=8):
    a = RNG.normal(size=(n, dim))
    b = RNG.normal(size=(n, dim))
    diffs = b - a
    unit = diffs / np.linalg.norm(diffs, axis=1, keepdims=True)
    assert abs((unit @ unit.mean(0)).mean()) < 0.5, "無作為対の前提が崩れている"
    return a, b


@pytest.mark.unit
def test_t190_方向が揃う対では検定が通る():
    a, b = aligned_pairs()
    r = axes.alignment_test(b - a)
    assert r["same_direction"] > r["n"] * 0.8
    assert r["p_binomial"] < 0.01


@pytest.mark.unit
def test_t191_無作為な対では検定が通らない():
    a, b = random_pairs()
    r = axes.alignment_test(b - a)
    assert r["p_binomial"] > 0.05, "偽陽性を出している"


@pytest.mark.unit
def test_t192_対応シャッフル対照が実装されている():
    a, b = aligned_pairs()
    obs = axes.alignment_test(b - a)
    null = axes.shuffle_control(a, b, n_iter=200, seed=1)
    assert null["mean_ratio"] < obs["same_direction"] / obs["n"]
    assert "z_ratio" in null and null["z_ratio"] > 2


@pytest.mark.unit
def test_t193_対比ベクトルは単位ベクトルで返る():
    a, b = aligned_pairs()
    v = axes.contrast_vector(b - a)
    assert np.isclose(np.linalg.norm(v), 1.0)


@pytest.mark.unit
def test_t194_射影は対比ベクトル方向のスカラーを返す():
    a, b = aligned_pairs()
    v = axes.contrast_vector(b - a)
    proj = axes.project(np.vstack([a, b]), v)
    assert proj.shape == (len(a) + len(b),)
    assert proj[len(a):].mean() > proj[:len(a)].mean(), "b 側が正の方向にあるはず"


@pytest.mark.unit
def test_t195_群間の並べ替え検定は差がある群で有意になる():
    g1 = RNG.normal(loc=1.0, size=40)
    g2 = RNG.normal(loc=0.0, size=40)
    r = axes.permutation_test(g1, g2, n_iter=2000, seed=2)
    assert r["diff"] > 0 and r["p"] < 0.01


@pytest.mark.unit
def test_t196_群間の並べ替え検定は差が無い群で有意にならない():
    g1 = RNG.normal(size=40)
    g2 = RNG.normal(size=40)
    r = axes.permutation_test(g1, g2, n_iter=2000, seed=3)
    assert r["p"] > 0.05


@pytest.mark.unit
def test_t197_holm補正は素のp値以上になる():
    raw = [0.04, 0.01, 0.2]
    got = axes.holm(raw)
    assert all(g >= r for g, r in zip(got, raw)), "補正後は素の p 以上"
    # 昇順に並べ替えたときに単調非減少(Holm の step-down 性)
    ordered = [got[i] for i in sorted(range(len(raw)), key=lambda i: raw[i])]
    assert ordered == sorted(ordered), "step-down が単調でない"


@pytest.mark.unit
def test_t198_検定は同じ種で再現する():
    a, b = aligned_pairs()
    r1 = axes.shuffle_control(a, b, n_iter=100, seed=7)
    r2 = axes.shuffle_control(a, b, n_iter=100, seed=7)
    assert r1 == r2
