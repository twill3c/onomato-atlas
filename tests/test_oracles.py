"""事前登録オラクル O-3 の実行手続き(O-3 / F-21)。

**事前登録に書いた手続きだけを実行する。**プローブ語・群定義・検定法・反復数・種・
片側/両側・α・多重比較補正は `gold/o3_preregistration.json` が唯一の出所であり、
コード側に別の値を書かない(書いたら T-201 が落ちる)。

音側素性は**群分けにのみ**使う(事前登録 §procedure・F-00)。
"""
import json
from collections import Counter
from pathlib import Path

import pytest

from pipeline import oracles

PREREG = Path(__file__).resolve().parents[1] / "gold" / "o3_preregistration.json"


@pytest.mark.unit
def test_t200_事前登録から手続きを読む():
    spec = oracles.load_preregistration(PREREG)
    assert spec["procedure"]["permutations"] == 10000
    assert spec["procedure"]["seed"] == 20260825
    assert len(spec["hypotheses"]) == 2


@pytest.mark.unit
def test_t201_コードに手続きの定数を持たない():
    src = (Path(__file__).resolve().parents[1] / "pipeline" / "oracles.py").read_text(
        encoding="utf-8")
    for forbidden in ("10000", "20260825", "0.05"):
        assert forbidden not in src, (
            f"手続きの値 {forbidden} がコードに焼かれている。事前登録が唯一の出所"
        )


@pytest.mark.unit
def test_t202_プローブ語のppmi合計を語ごとに出す():
    ctx = {
        "かちかち": Counter({"叩く": 10, "光る": 1}),
        "むにゃむにゃ": Counter({"叩く": 1, "光る": 10}),
    }
    got = oracles.probe_scores(ctx, ["叩く"])
    assert got["かちかち"] > got["むにゃむにゃ"]


@pytest.mark.unit
def test_t203_群分けは音側素性で行う():
    words = ["かちかち", "むにゃむにゃ", "きらきら"]
    a, b = oracles.split_groups(words, {"onset1": ["k", "t", "p"]},
                                {"onset1": ["m", "n", "r", "w", ""]})
    assert "かちかち" in a and "きらきら" in a
    assert "むにゃむにゃ" in b


@pytest.mark.unit
def test_t204_母音条件で群分けできる():
    words = ["きらきら", "ころころ"]
    a, b = oracles.split_groups(words, {"vowels_contain": "i"},
                                {"vowels_not_contain": "i"})
    assert a == ["きらきら"] and b == ["ころころ"]


@pytest.mark.unit
def test_t205_群サイズが下限未満なら検出力不足として返す():
    spec = oracles.load_preregistration(PREREG)
    r = oracles.run_hypothesis(
        spec["hypotheses"][0], {"きらきら": Counter({"叩く": 1})}, spec["procedure"])
    assert r["verdict"] == "underpowered", "小さい群で通過/不通過を書いてはならない"


@pytest.mark.unit
def test_t206_判定は方向と補正後pの両方を見る():
    assert oracles.verdict(diff=1.0, p_adj=0.01, alpha=0.05) == "pass"
    assert oracles.verdict(diff=-1.0, p_adj=0.01, alpha=0.05) == "fail"
    assert oracles.verdict(diff=1.0, p_adj=0.20, alpha=0.05) == "fail"
