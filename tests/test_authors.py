"""作家ごとの使用傾向(F-40)。

**カウントは正確だが、一般化は推論である。** 収録作でのカウントは誤差ゼロだが、
「この作家はこの語を好む」と言うには標本(著者あたり最大 20 作)の限界がある。
指標は情報事前分布つき対数オッズ(Monroe et al. 2008)を使う。単純な相対頻度は
低頻度語で暴れ、328 作家 × 597 語の比較では偽の特徴語を大量に生む。

期待値の出所: 指標の定義そのもの。合成データで前提を assert して検算する。
"""
import pytest

from pipeline import authors


def toy():
    # A は「きらきら」に偏り、B は「ばたばた」に偏る
    return {
        "A": {"きらきら": 40, "ばたばた": 2, "ふわふわ": 8},
        "B": {"きらきら": 2, "ばたばた": 40, "ふわふわ": 8},
        "C": {"きらきら": 10, "ばたばた": 10, "ふわふわ": 10},
    }


@pytest.mark.unit
def test_t250_偏りのある語が上位に来る():
    out = authors.log_odds(toy())
    top_a = max(out["A"], key=lambda w: out["A"][w]["z"])
    top_b = max(out["B"], key=lambda w: out["B"][w]["z"])
    assert top_a == "きらきら" and top_b == "ばたばた"


@pytest.mark.unit
def test_t251_偏りのない作家は突出しない():
    out = authors.log_odds(toy())
    zs = [v["z"] for v in out["C"].values()]
    assert max(abs(z) for z in zs) < 2.0, "偏りが無いのに特徴語が出ている"


@pytest.mark.unit
def test_t252_低頻度語が暴れない():
    # D は総数 3 しかない。相対頻度なら 100% になるが z は小さいはず
    data = {**toy(), "D": {"きらきら": 3}}
    out = authors.log_odds(data)
    assert out["D"]["きらきら"]["z"] < out["A"]["きらきら"]["z"]


@pytest.mark.unit
def test_t253_カウントと総数を保持する():
    out = authors.log_odds(toy())
    assert out["A"]["きらきら"]["count"] == 40
    assert out["A"]["きらきら"]["author_total"] == 50


@pytest.mark.unit
def test_t254_zは符号を持ち少ない側は負になる():
    out = authors.log_odds(toy())
    assert out["A"]["ばたばた"]["z"] < 0


@pytest.mark.unit
def test_t255_多重比較の補正閾値を返す():
    out = authors.log_odds(toy())
    th = authors.bonferroni_z(len(out), max(len(v) for v in out.values()), alpha=0.05)
    assert th > 1.96, "比較数が増えれば閾値は厳しくなる"
