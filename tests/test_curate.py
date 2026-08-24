"""語彙 curation(F-05 / F-06 / F-07)。

期待値の出所: SPEC §4.2(curation 規範)と 2026-08-25 の実測
(docs/concept.md §2 実測 4 / §11 発見 A)。
"""
import pytest

from pipeline import curate


@pytest.mark.unit
def test_t008_除外リストの反復副詞は採用されない():
    # 実測 2026-08-25: これらは副詞 100%・高頻度で、品詞でも頻度でも切れない
    v = curate.build({"とうとう": 815, "なかなか": 698, "きらきら": 73})
    assert "とうとう" not in v.adopted
    assert "なかなか" not in v.adopted
    assert "きらきら" in v.adopted


@pytest.mark.unit
def test_t009_変化形は語幹がabab型として存在するときのみ採用される():
    # 実測 2026-08-25(§11 発見 A): この規則で 65 語すべてが偽陽性ゼロになった
    v = curate.build({"きらきら": 73, "きらり": 20, "ひとり": 500, "つもり": 400, "つまり": 300})
    assert "きらり" in v.adopted, "語幹 きらきら が語彙にある"
    for w in ("ひとり", "つもり", "つまり"):
        assert w not in v.adopted, f"{w} は語幹 ABAB が存在しない"


@pytest.mark.unit
def test_t010_全採否に理由が付き理由が空の語が無い():
    v = curate.build({"とうとう": 815, "きらきら": 73, "きらり": 20, "ひとり": 500})
    manifest = v.manifest()
    assert set(manifest) == {"とうとう", "きらきら", "きらり", "ひとり"}
    assert all(m["reason"] for m in manifest.values()), "理由が空の採否を残さない"
    assert all(m["decision"] in ("adopted", "rejected", "needs_review") for m in manifest.values())


@pytest.mark.unit
def test_t011_判定困難語は採用も除外もされず保留される():
    v = curate.build({"そろそろ": 234}, needs_review={"そろそろ"})
    assert "そろそろ" not in v.adopted
    assert "そろそろ" not in v.rejected
    assert "そろそろ" in v.needs_review


@pytest.mark.unit
def test_t012_エージェントは未知語を独断で採用しない():
    # 除外リストにも採用規則にも該当しない未知の ABAB 型は needs_review へ回る
    v = curate.build({"ぬめぬめ": 12})
    assert "ぬめぬめ" in v.needs_review
    assert "ぬめぬめ" not in v.adopted
