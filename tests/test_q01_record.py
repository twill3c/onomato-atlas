"""Q-01 判定記録と SPEC の整合(Q-01 / HC-005)。

判定記録は測定の証拠。SPEC に書いた率が証拠と食い違ったら落ちる。
期待値の出所: gold/ の判定記録そのもの(実測)。SPEC 側の数字を写経しない。
"""
import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "gold"
SPEC = ROOT / "SPEC.md"


def _rate(path: Path) -> tuple[int, int]:
    with path.open(encoding="utf-8") as f:
        lines = [l for l in f if not l.startswith("#")]
    rows = list(csv.DictReader(lines, delimiter="\t"))
    fp = sum(1 for r in rows if r["is_false_positive"].strip() == "1")
    return fp, len(rows)


@pytest.mark.unit
def test_t173_判定記録が存在する():
    files = sorted(GOLD.glob("q01_judged_*.tsv"))
    assert files, "Q-01 の判定記録が gold/ に無い(HC-005)"
    for p in files:
        fp, n = _rate(p)
        assert n > 0, f"{p.name}: 標本が空"
        assert 0 <= fp <= n


@pytest.mark.unit
def test_t174_specに書いた偽陽性率が判定記録と一致する():
    fp, n = _rate(GOLD / "q01_judged_20260826.tsv")
    spec = SPEC.read_text(encoding="utf-8")
    pat = rf"偽陽性 {fp}/{n}"
    assert re.search(pat, spec), f"SPEC に『{pat}』が見当たらない(証拠と乖離)"


@pytest.mark.unit
def test_t175_判定記録は再生成で壊れない場所にある():
    # data/curated は build_vocab の出力先。判定記録がそこに無いことを確かめる
    assert not list((ROOT / "data" / "curated").glob("q01_judged_*.tsv"))
    assert list(GOLD.glob("q01_judged_*.tsv"))
