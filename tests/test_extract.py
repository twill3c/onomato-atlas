"""擬態語候補の抽出(F-02 / F-03 / F-04 / F-06)。

期待値の出所: 2026-08-25 の実測(docs/concept.md §2 実測 2)。
正規表現のみの抽出が誤検出した実例をそのまま負例に据えている。
件数ではなく「返す / 返さない」の集合で書く(SPEC §7)。
"""
import pytest

from pipeline import extract


def surfaces(text):
    return {c.surface for c in extract.candidates(text)}


# --- 語境界の偽陽性(F-02)。実測 2026-08-25: 正規表現のみは延べの 10.4% が偽陽性 ---

@pytest.mark.unit
def test_t001_置いていて_から_いていて_を返さない():
    assert "いていて" not in surfaces("荷物をそこに置いていて下さい")


@pytest.mark.unit
def test_t002_彼らはらはらと_から_らはらは_を返さない():
    assert "らはらは" not in surfaces("彼らはらはらと涙をこぼした")


@pytest.mark.unit
def test_t003_わからん_から_からん_を返さない():
    got = surfaces("それは私にはわからん")
    assert "からん" not in got


@pytest.mark.unit
def test_t004_にやって_から_にやっ_を返さない():
    assert "にやっ" not in surfaces("彼は仕事を熱心にやって来た")


@pytest.mark.unit
def test_t005_擬態語は返す():
    assert "きらきら" in surfaces("星がきらきらと光っている")
    assert "ばたばた" in surfaces("廊下をばたばたと駆けて行った")


# --- 表記ゆれ統合(F-04)。実測 2026-08-25: 752 → 606 語 ---

@pytest.mark.unit
def test_t006_カタカナとひらがなが同一語に統合される():
    got = extract.tally(["星がキラキラ光る", "露がきらきら光る"])
    assert "キラキラ" not in got
    assert got["きらきら"] == 2, "統合後の頻度は両表記の和"


@pytest.mark.unit
def test_t007_統合は表記の差だけを畳み_別語を混ぜない():
    got = extract.tally(["ころころ転がる", "ごろごろ転がる"])
    assert set(got) >= {"ころころ", "ごろごろ"}, "濁音の差は別語である"


@pytest.mark.unit
def test_t013_品詞統計を頻度と一緒に取れる():
    # F-06 の名詞ガード(T-160)が語ごとの品詞分布を要求する
    freq, pos = extract.tally_with_pos(["星がきらきら光る", "きらきらしたもの"])
    assert freq["きらきら"] == 2
    assert sum(pos["きらきら"].values()) == 2
    assert set(pos) <= set(freq), "品詞統計のキーは頻度表のキーに含まれる"
