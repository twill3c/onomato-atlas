"""軸の採否記録と UI 配信データの隔離(F-22 / F-23)。

**F-22**: 検定を通っていない軸は UI に出さない。射影値も持たせない。
**F-23**: 採用軸・不採用軸とその検定結果を記録し、出典として参照できるようにする。

期待値の出所: SPEC F-22 / F-23。合成データで規則そのものを検査する。
"""
import pytest

from pipeline import axes_io


def stats(p_bin, p_emp):
    return {"n": 30, "same_direction": 25, "mean_cos": 0.1,
            "p_binomial": p_bin, "control_p_empirical": p_emp, "control_z_ratio": 3.0}


@pytest.mark.unit
def test_t210_基準を満たす軸は採用される():
    assert axes_io.decide(stats(0.01, 0.01), alpha=0.05) == "adopted"


@pytest.mark.unit
def test_t211_二項が有意でも対照を超えなければ不採用():
    assert axes_io.decide(stats(1e-9, 0.20), alpha=0.05) == "rejected"


@pytest.mark.unit
def test_t212_対照を超えても二項が有意でなければ不採用():
    assert axes_io.decide(stats(0.30, 0.01), alpha=0.05) == "rejected"


@pytest.mark.unit
def test_t213_不採用の軸には射影値を持たせない():
    doc = axes_io.build_document(
        [
            {"id": "a", "name": "採用軸", "stats": stats(0.01, 0.01),
             "vector": [1.0, 0.0], "projections": {"きらきら": 0.5}},
            {"id": "b", "name": "不採用軸", "stats": stats(0.30, 0.01),
             "vector": [0.0, 1.0], "projections": {"きらきら": 0.7}},
        ],
        alpha=0.05,
    )
    a = next(x for x in doc["axes"] if x["id"] == "a")
    b = next(x for x in doc["axes"] if x["id"] == "b")
    assert a["decision"] == "adopted" and "projections" in a
    assert b["decision"] == "rejected"
    assert "projections" not in b and "vector" not in b, "F-22 違反: 不採用軸のデータが残っている"


@pytest.mark.unit
def test_t214_不採用軸も検定結果は残る():
    doc = axes_io.build_document(
        [{"id": "b", "name": "不採用軸", "stats": stats(0.30, 0.01),
          "vector": [0.0, 1.0], "projections": {"きらきら": 0.7}}],
        alpha=0.05,
    )
    b = doc["axes"][0]
    assert b["stats"]["p_binomial"] == 0.30, "F-23: 不採用でも検定結果は記録する"


@pytest.mark.unit
def test_t215_採用基準が文書に明記される():
    doc = axes_io.build_document([], alpha=0.05)
    assert "criterion" in doc and doc["criterion"]["alpha"] == 0.05


# --- Q-02: 密度下限を満たさない語に軸スコアを持たせない ---

@pytest.mark.unit
def test_t216_密度下限未満の語には射影値を持たせない():
    doc = axes_io.build_document(
        [{"id": "a", "name": "軸", "stats": stats(0.01, 0.01), "vector": [1.0],
          "projections": {"あつい": 0.5, "うすい": 0.9},
          "density_floor": 50}],
        alpha=0.05,
        density={"あつい": 100, "うすい": 10},
    )
    proj = doc["axes"][0]["projections"]
    assert "あつい" in proj
    assert "うすい" not in proj, "Q-02 違反: 下限未満の語にスコアが残っている"


@pytest.mark.unit
def test_t217_下限と信頼性が軸ごとに記録される():
    doc = axes_io.build_document(
        [{"id": "a", "name": "軸", "stats": stats(0.01, 0.01), "vector": [1.0],
          "projections": {"あつい": 0.5}, "density_floor": 50, "reliability": 0.71}],
        alpha=0.05, density={"あつい": 100},
    )
    ax = doc["axes"][0]
    assert ax["density_floor"] == 50 and ax["reliability"] == 0.71
