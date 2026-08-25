"""語彙構築と品質指標の測定(F-05 / F-07 / Q-01 / Q-02)。

期待値の出所: SPEC §4.2・§6、および 2026-08-25 の実測。
件数は定数で書かず、不変量(集合の一致・欠落の不在・単調性)で書く。
"""
from pathlib import Path

import pytest

from pipeline import build_vocab

FIX = Path(__file__).parent / "fixtures" / "vocab_decisions_mini.tsv"


TEXTS = [
    "星がきらきらと光り、露がきらきら落ちた。",
    "廊下をばたばたと駆け、扉をばたばた叩いた。",
    "彼はきらりと目を光らせた。",
    "とうとう夜が明けた。なかなか眠れない。",
    "ぬめぬめした岩に足を取られた。",
]


@pytest.mark.unit
def test_t130_共起密度は異なり共起語数として測れる():
    ctx = build_vocab.cooccurrence(TEXTS, {"きらきら", "ばたばた"}, window=5)
    assert set(ctx) == {"きらきら", "ばたばた"}
    assert all(len(v) > 0 for v in ctx.values())


@pytest.mark.unit
def test_t131_共起は自分自身を数えない():
    ctx = build_vocab.cooccurrence(["きらきら きらきら 光る"], {"きらきら"}, window=5)
    assert "きらきら" not in ctx["きらきら"]


@pytest.mark.unit
def test_t132_軽動詞は共起から除かれる():
    ctx = build_vocab.cooccurrence(["きらきらする"], {"きらきら"}, window=5)
    assert "為る" not in ctx["きらきら"]


@pytest.mark.unit
def test_t133_密度レポートは語ごとの異なり共起語数を返す():
    ctx = build_vocab.cooccurrence(TEXTS, {"きらきら", "ばたばた"}, window=5)
    d = build_vocab.density_report(ctx)
    assert set(d["per_word"]) == {"きらきら", "ばたばた"}
    assert d["min"] <= d["median"] <= d["max"]


@pytest.mark.unit
def test_t134_成果物に採否と理由と表版が揃う():
    out = build_vocab.build(TEXTS, min_freq=1, decisions_path=FIX)
    m = out["vocab"]
    assert all(r["reason"] for r in m.values()), "理由が空の採否を残さない(F-07)"
    assert all(r["table_version"] for r in m.values())
    assert m["きらきら"]["decision"] == "adopted"
    assert m["とうとう"]["decision"] == "rejected"
    assert m["ぬめぬめ"]["decision"] == "needs_review"


@pytest.mark.unit
def test_t135_変化形は語幹が採用されているときだけ採用される():
    out = build_vocab.build(TEXTS, min_freq=1, decisions_path=FIX)
    assert out["vocab"]["きらり"]["decision"] == "adopted"


@pytest.mark.unit
def test_t136_q01の検査標本は決定論的に抽出される():
    a = build_vocab.false_positive_sample(TEXTS, n=3, seed=7)
    b = build_vocab.false_positive_sample(TEXTS, n=3, seed=7)
    assert a == b, "同じ種なら同じ標本(再現可能な人手検査のため)"
    assert all(s["surface"] in s["context"] for s in a)


@pytest.mark.unit
def test_t137_q01標本は指定した語の出現だけから引かれる():
    # Q-01 は「抽出の誤分割」を測る指標。curation で除外済みの語を混ぜると
    # 抽出の誤りと採否の判断が混ざる(2026-08-25 に実際に混ざった)
    s = build_vocab.false_positive_sample(TEXTS, n=10, seed=1, targets={"きらきら"})
    assert s, "標本が空"
    assert {x["surface"] for x in s} == {"きらきら"}


# --- 人手判定の保護(HC-005・2026-08-25 に判定を失った事故を受けて) ---

@pytest.mark.unit
def test_t170_判定済みの標本を上書きしない(tmp_path):
    p = tmp_path / "q01_sample.tsv"
    p.write_text(
        "# 既存の標本\nsurface\tpos\tis_false_positive\tcontext\n"
        "きらきら\t副詞\t1\t文脈\n", encoding="utf-8")
    with pytest.raises(build_vocab.JudgedSampleExists):
        build_vocab.write_sample(p, [{"surface": "ばたばた", "pos": "副詞", "context": "文脈"}])
    assert "1" in p.read_text(encoding="utf-8"), "判定が残っている"


@pytest.mark.unit
def test_t171_判定が無ければ上書きしてよい(tmp_path):
    p = tmp_path / "q01_sample.tsv"
    p.write_text(
        "# 既存の標本\nsurface\tpos\tis_false_positive\tcontext\n"
        "きらきら\t副詞\t\t文脈\n", encoding="utf-8")
    build_vocab.write_sample(p, [{"surface": "ばたばた", "pos": "副詞", "context": "新しい文脈"}])
    assert "ばたばた" in p.read_text(encoding="utf-8")


@pytest.mark.unit
def test_t172_ファイルが無ければ新規作成する(tmp_path):
    p = tmp_path / "q01_sample.tsv"
    build_vocab.write_sample(p, [{"surface": "きらきら", "pos": "副詞", "context": "文脈"}])
    assert p.exists() and "きらきら" in p.read_text(encoding="utf-8")


@pytest.mark.unit
def test_t176_軽動詞リストは版付きファイルから読まれる():
    # F-13: 測定器を無記名で差し替えられないようにする(AGENTS §3)
    assert build_vocab.LIGHT_VERBS_VERSION != "hardcoded"
    assert "為る" in build_vocab.LIGHT_VERBS
    assert len(build_vocab.LIGHT_VERBS) >= 10
