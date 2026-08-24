"""コーパス選定(F-01 / SPEC §4.1.1)。

期待値の出所: SPEC §4.1.1 の選定基準表(2026-08-25 確定)。
件数は合成フィクスチャに対する集合の一致で書き、実コーパスの件数を定数化しない。
"""
import csv
from pathlib import Path

import pytest

from pipeline import selection

FIX = Path(__file__).parent / "fixtures" / "index_mini.csv"


def rows():
    with FIX.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ids(sel):
    return {r["作品ID"] for r in sel}


@pytest.mark.unit
def test_t100_役割フラグが著者以外は落ちる():
    assert "000007" not in ids(selection.select(rows()))


@pytest.mark.unit
def test_t101_作品著作権ありは落ちる():
    assert "000002" not in ids(selection.select(rows()))


@pytest.mark.unit
def test_t102_テキストファイルurlが空なら落ちる():
    assert "000006" not in ids(selection.select(rows()))


@pytest.mark.unit
def test_t103_原題ありの翻訳は落ちる():
    assert "000003" not in ids(selection.select(rows()))


@pytest.mark.unit
def test_t104_新字新仮名以外は落ちる():
    assert "000004" not in ids(selection.select(rows()))


@pytest.mark.unit
def test_t105_分類が対象外のみなら落ち_一つでも該当すれば残る():
    got = ids(selection.select(rows()))
    assert "000005" not in got, "911 のみは対象外"
    assert "000010" in got, "911 913 の併記は 913 を含むので対象"


@pytest.mark.unit
def test_t106_採用される集合が選定基準と完全一致する():
    # SPEC §4.1.1 の段 1-6 をフィクスチャに適用した結果
    assert ids(selection.select(rows())) == {"000001", "000008", "000009", "000010"}


@pytest.mark.unit
def test_t107_著者あたり上限を超えない():
    src = rows()
    many = []
    for i in range(30):
        r = dict(src[0])
        r["作品ID"] = f"9{i:05d}"
        many.append(r)
    sel = selection.select(src + many, per_author_cap=20)
    from collections import Counter
    assert max(Counter(r["人物ID"] for r in sel).values()) <= 20


@pytest.mark.unit
def test_t108_選定は決定論である():
    a = [r["作品ID"] for r in selection.select(rows())]
    b = [r["作品ID"] for r in selection.select(rows())]
    assert a == b


@pytest.mark.unit
def test_t109_各段の残存件数が報告される():
    _, stages = selection.select_with_report(rows())
    # 段の名称は SPEC §4.1.1 の表に対応する。数はフィクスチャに対する実測
    assert [s["stage"] for s in stages] == [0, 1, 2, 3, 4, 5, 6, 7]
    assert stages[0]["remaining"] == len(rows())
    assert stages[-1]["remaining"] == 4


@pytest.mark.unit
def test_t110_底本表記が索引から取れる():
    for r in selection.select(rows()):
        meta = selection.source_note(r)
        assert meta["底本名"] and meta["入力者"]


@pytest.mark.unit
def test_t111_取得リストは作品idで一意化される():
    # SPEC §4.1.1: 共著は同一作品ID に著者行が複数立つ。実索引では段7で 2,212 行 / 2,200 作品
    src = rows()
    co = dict(src[0])
    co["人物ID"] = "000999"  # 同じ作品を別の著者行が持つ(共著)
    works = selection.unique_works(selection.select(src + [co]))
    assert len(works) == len({w["作品ID"] for w in works})
    assert "000001" in {w["作品ID"] for w in works}
