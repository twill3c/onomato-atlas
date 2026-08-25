"""配信データの生成(F-30〜F-33 / N-03)。

配信データは**検定を通った軸の、密度下限を満たす語のスコアだけ**を運ぶ。
音側素性は決定論なので全語に付ける。近傍語は運ばない(F-32b)。

期待値の出所: SPEC F-30/F-32/F-32b、axes.json の採否。
"""
import pytest

from pipeline import webdata


AXES = {
    "criterion": {"alpha": 0.05},
    "axes": [
        {"id": "duration", "name": "瞬間 ⇔ 持続", "decision": "adopted",
         "density_floor": 40, "reliability": 0.704,
         "stats": {"n": 202, "p_binomial": 1e-30, "control_p_empirical": 0.01},
         "projections": {"ころころ": -0.4, "ころり": 0.5}},
        {"id": "moraic_n", "name": "却下軸", "decision": "rejected",
         "stats": {"n": 45, "p_binomial": 1e-6, "control_p_empirical": 0.52}},
    ],
}
VOCAB = {"adopted": ["ころころ", "ころり", "きらきら"],
         "vocab": {"ころころ": {"freq": 144}, "ころり": {"freq": 30}, "きらきら": {"freq": 413}}}


@pytest.mark.unit
def test_t230_採用軸のスコアだけを運ぶ():
    doc = webdata.build(AXES, VOCAB, {})
    w = doc["words"]["ころころ"]
    assert "duration" in w["axes"]
    assert "moraic_n" not in w["axes"], "却下軸のスコアが配信データに混じっている(F-22)"


@pytest.mark.unit
def test_t231_下限未満の語にはスコアを付けない():
    doc = webdata.build(AXES, VOCAB, {})
    assert doc["words"]["きらきら"]["axes"] == {}, "axes.json に射影が無い語にスコアが付いた"


@pytest.mark.unit
def test_t232_音側素性は全語に付く():
    doc = webdata.build(AXES, VOCAB, {})
    for w in VOCAB["adopted"]:
        f = doc["words"][w]["phon"]
        assert f["onset1"] is not None and f["form"]


@pytest.mark.unit
def test_t233_近傍語を運ばない():
    doc = webdata.build(AXES, VOCAB, {})
    for w in doc["words"].values():
        assert "neighbors" not in w, "F-32b 違反: 近傍語が配信データに入っている"


@pytest.mark.unit
def test_t234_パラダイム線は両端にスコアがある組だけ():
    doc = webdata.build(AXES, VOCAB, {})
    lines = doc["paradigms"]
    assert lines and all(
        l["stem_score"] is not None and l["variant_score"] is not None for l in lines)
    assert any(l["stem"] == "ころころ" and l["variant"] == "ころり" for l in lines)


@pytest.mark.unit
def test_t235_軸のメタに検定結果と信頼性が入る():
    doc = webdata.build(AXES, VOCAB, {})
    ax = doc["axes"][0]
    assert ax["reliability"] == 0.704 and ax["stats"]["n"] == 202
    assert ax["density_floor"] == 40


@pytest.mark.unit
def test_t236_用例は語ごとに分割して運ぶ():
    ex = {"words": {"ころころ": {"quotes": [{"quote": "ころころ転がる", "source": {"title": "作"}}]}}}
    doc = webdata.build(AXES, VOCAB, ex)
    assert doc["words"]["ころころ"]["n_quotes"] == 1
    assert "quotes" not in doc["words"]["ころころ"], "用例は本体に埋めず別ファイルへ"
