"""意味側チャネル(F-11 / F-12 / F-13 / F-14)。

**F-00**: このモジュールは音側(phon)を import しない。T-020 が静的に検査する。
期待値の出所: PPMI・SVD の定義そのもの(合成データで解析的に検算する)と、
SPEC §4.3。SVD 次元数は較正で決めるので定数を焼かない(F-15)。
"""
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from pipeline import sem

FIXTURE_STOPLIST = Path(__file__).parent / "fixtures" / "light_verbs_mini.tsv"


def toy():
    # ひかり群 と おと群 が別々の文脈語を持つ合成データ
    return {
        "きらきら": Counter({"光る": 10, "輝く": 8, "星": 6}),
        "ぴかぴか": Counter({"光る": 9, "輝く": 7, "星": 5}),
        "ばたばた": Counter({"叩く": 10, "音": 8, "走る": 6}),
        "とんとん": Counter({"叩く": 9, "音": 7, "走る": 5}),
    }


@pytest.mark.unit
def test_t180_ppmiは非負である():
    words, cols, M = sem.build_matrix(toy(), min_ctx_count=1)
    X = sem.ppmi(M)
    assert (X >= 0).all()


@pytest.mark.unit
def test_t181_独立な共起はppmiが0になる():
    # 行と列が独立(外積)なら PMI は 0。解析的に検算できる合成データ
    M = np.outer([2.0, 4.0], [3.0, 6.0, 1.0])
    X = sem.ppmi(M)
    assert np.allclose(X, 0.0), "独立なのに PPMI が立っている"


@pytest.mark.unit
def test_t182_svdの次元数は引数で決まる():
    words, cols, M = sem.build_matrix(toy(), min_ctx_count=1)
    E2 = sem.embed(sem.ppmi(M), k=2)[0]
    E3 = sem.embed(sem.ppmi(M), k=3)[0]
    assert E2.shape[1] == 2 and E3.shape[1] == 3


@pytest.mark.unit
def test_t183_寄与率が返り合計が1以下():
    words, cols, M = sem.build_matrix(toy(), min_ctx_count=1)
    _, ev = sem.embed(sem.ppmi(M), k=3)
    assert len(ev) == 3 and 0 < ev.sum() <= 1.0 + 1e-9


@pytest.mark.unit
def test_t184_近傍は自分自身を返さず意味の近い語を返す():
    words, cols, M = sem.build_matrix(toy(), min_ctx_count=1)
    E, _ = sem.embed(sem.ppmi(M), k=3)
    nb = sem.neighbors(words, E, "きらきら", n=1)
    assert nb[0][0] != "きらきら"
    assert nb[0][0] == "ぴかぴか", "光の語同士が近いはず"


@pytest.mark.unit
def test_t185_ストップリストは版付きファイルから読む():
    version, lemmas = sem.load_stoplist(FIXTURE_STOPLIST)
    assert version and lemmas


@pytest.mark.unit
def test_t186_版行の無い辞書は例外にする():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bad.tsv"
        p.write_text("lemma" + chr(9) + "理由" + chr(10) + "為る" + chr(9) + "x" + chr(10),
                     encoding="utf-8")
        with pytest.raises(ValueError):
            sem.load_stoplist(p)


@pytest.mark.unit
def test_t187_感度分析は座標変位と近傍の入れ替わりを返す():
    words, cols, M = sem.build_matrix(toy(), min_ctx_count=1)
    E, _ = sem.embed(sem.ppmi(M), k=3)
    rep = sem.sensitivity(words, E, E)
    assert rep["mean_shift"] == pytest.approx(0.0)
    assert rep["neighbor_churn"] == pytest.approx(0.0)


@pytest.mark.unit
def test_t188_係り先用言を別特徴として保持する():
    gov = {"きらきら": Counter({"光る": 5}), "ばたばた": Counter({"叩く": 4})}
    out = sem.governor_features(gov, top_n=3)
    assert out["きらきら"][0][0] == "光る"
    assert set(out) == set(gov)
