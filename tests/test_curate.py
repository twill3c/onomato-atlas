"""語彙 curation(F-05 / F-06 / F-07)。

期待値の出所: SPEC §4.2(curation 規範)と 2026-08-25 の実測
(docs/concept.md §2 実測 4 / §11 発見 A)。
"""
from pathlib import Path

import pytest

from pipeline import curate

# 本番の判定表は curation の進行で正当に増える。テストは固定フィクスチャに依存させる
FIX = Path(__file__).parent / "fixtures" / "vocab_decisions_mini.tsv"


@pytest.mark.unit
def test_t008_除外リストの反復副詞は採用されない():
    # 実測 2026-08-25: これらは副詞 100%・高頻度で、品詞でも頻度でも切れない
    v = curate.build({"とうとう": 815, "なかなか": 698, "きらきら": 73}, decisions_path=FIX)
    assert "とうとう" not in v.adopted
    assert "なかなか" not in v.adopted
    assert "きらきら" in v.adopted


@pytest.mark.unit
def test_t009_変化形は語幹がabab型として存在するときのみ採用される():
    # 実測 2026-08-25(§11 発見 A): この規則で 65 語すべてが偽陽性ゼロになった
    v = curate.build({"きらきら": 73, "きらり": 20, "ひとり": 500, "つもり": 400, "つまり": 300}, decisions_path=FIX)
    assert "きらり" in v.adopted, "語幹 きらきら が語彙にある"
    for w in ("ひとり", "つもり", "つまり"):
        assert w not in v.adopted, f"{w} は語幹 ABAB が存在しない"


@pytest.mark.unit
def test_t010_全採否に理由が付き理由が空の語が無い():
    v = curate.build({"とうとう": 815, "きらきら": 73, "きらり": 20, "ひとり": 500}, decisions_path=FIX)
    manifest = v.manifest()
    assert set(manifest) == {"とうとう", "きらきら", "きらり", "ひとり"}
    assert all(m["reason"] for m in manifest.values()), "理由が空の採否を残さない"
    assert all(m["decision"] in ("adopted", "rejected", "needs_review") for m in manifest.values())


@pytest.mark.unit
def test_t011_判定困難語は採用も除外もされず保留される():
    v = curate.build({"そろそろ": 234}, needs_review={"そろそろ"}, decisions_path=FIX)
    assert "そろそろ" not in v.adopted
    assert "そろそろ" not in v.rejected
    assert "そろそろ" in v.needs_review


@pytest.mark.unit
def test_t012_エージェントは未知語を独断で採用しない():
    # 除外リストにも採用規則にも該当しない未知の ABAB 型は needs_review へ回る
    v = curate.build({"ぬめぬめ": 12}, decisions_path=FIX)
    assert "ぬめぬめ" in v.needs_review
    assert "ぬめぬめ" not in v.adopted


# --- F-06 の自動規則のガード(2026-08-25 の Q-01 判定で発見) ---

@pytest.mark.unit
def test_t160_名詞優勢の変化形は自動採用されず保留になる():
    """常用名詞と同音の変化形が語幹の採用に便乗して入るのを防ぐ。

    実測 2026-08-25: カタカナ外来語(バター/メリー/パリー)が ABー 型として、
    和語名詞(うねり/しおり/ぼたん)が ABり/ABん 型として語彙に混入していた。
    品詞では擬態語と切り分けられない(unidic は「ちろりと見る」も名詞にする)ので、
    自動採用の対象から外して人手判断に戻す。
    """
    freq = {"ばたばた": 100, "ばたー": 389, "ばたり": 27}
    pos = {"ばたー": {"名詞": 389}, "ばたり": {"副詞": 25, "名詞": 2}}
    v = curate.build(freq, pos_stats=pos, decisions_path=FIX)
    assert "ばたー" in v.needs_review, "名詞優勢の変化形は保留へ"
    assert "ばたー" not in v.adopted
    assert "ばたり" in v.adopted, "副詞優勢の変化形は従来どおり採用"


@pytest.mark.unit
def test_t161_保留理由に名詞優勢である旨が残る():
    freq = {"ばたばた": 100, "ばたー": 389}
    pos = {"ばたー": {"名詞": 389}}
    v = curate.build(freq, pos_stats=pos, decisions_path=FIX)
    assert "名詞" in v.reasons["ばたー"]


@pytest.mark.unit
def test_t162_abab型は名詞優勢でも判定表の決定に従う():
    # ABAB の名詞は正常(実測 2026-08-25: ABAB トークンの 2.5% が名詞)
    freq = {"きらきら": 50}
    pos = {"きらきら": {"名詞": 50}}
    v = curate.build(freq, pos_stats=pos, decisions_path=FIX)
    assert "きらきら" in v.adopted


@pytest.mark.unit
def test_t163_pos統計を渡さなければ従来どおり動く():
    freq = {"きらきら": 73, "きらり": 20}
    v = curate.build(freq, decisions_path=FIX)
    assert "きらり" in v.adopted
