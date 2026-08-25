"""O-3 事前登録の封印(T-035)。

事前登録は**結果を見る前に方向を固定する**ためのものなので、登録後の変更を検出する。
期待値の出所: 2026-08-25 に登録した gold/o3_preregistration.json の実測ハッシュ。
このテストが落ちたら、登録を書き換えたか、新しい登録 ID を切るべき場面である。
"""
import hashlib
import json
from pathlib import Path

import pytest

PREREG = Path(__file__).resolve().parents[1] / "gold" / "o3_preregistration.json"
# 実測 2026-08-25(L2 loop_005 で登録)
REGISTERED_SHA256 = "723ba803b5f0864acd43c7241464de8ee48ffb710db9fd828a4a605e706a699c"


@pytest.mark.unit
def test_t035_事前登録は登録後に変更されていない():
    got = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    assert got == REGISTERED_SHA256, (
        "事前登録が変更された。O-3 は結果を見る前に方向を固定する仕組みなので、"
        "内容を変えるなら新しい登録 ID を切り、旧登録を残すこと"
    )


@pytest.mark.unit
def test_t036_事前登録に必要な項目が揃っている():
    d = json.loads(PREREG.read_text(encoding="utf-8"))
    assert d["status"] == "registered"
    assert len(d["hypotheses"]) >= 2
    for h in d["hypotheses"]:
        assert h["probes"] and h["direction"] and h["group_a"] and h["group_b"]
    p = d["procedure"]
    # 検定手続きは結果を見る前に決まっていなければならない
    for k in ("test", "permutations", "seed", "alternative", "alpha",
              "multiple_comparison", "min_group_size"):
        assert p.get(k) is not None, f"手続きの {k} が未定"
    assert d["decision_rule"]["fail"], "不通過時の扱いが書かれていない(F-22)"


@pytest.mark.unit
def test_t037_事前登録は音側素性を群分けにしか使わない():
    d = json.loads(PREREG.read_text(encoding="utf-8"))
    # F-00: 測定そのものは意味側だけで行う
    assert "意味側チャネルのみから計算する" in d["procedure"]["measure"]
    for h in d["hypotheses"]:
        assert set(h["group_a"]) <= {"onset1", "vowels_contain", "vowels_not_contain"}
