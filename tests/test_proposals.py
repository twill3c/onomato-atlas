"""採否提案シートの不変量(F-05 / F-07)。

提案は**決定ではない**。人間が承認して vocab_decisions.tsv に反映されるまで
パイプラインに効いてはならない。T-152 がその隔離を静的に検査する。

期待値の出所: SPEC §4.2、AGENTS.md §2、および 2026-08-25 に生成したシートの構造。
"""
import ast
import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROPOSALS = ROOT / "data" / "curated" / "vocab_proposals.tsv"
MANIFEST = ROOT / "data" / "vocab_manifest.json"
VALID = {"adopted", "rejected", "hold"}


def _rows():
    with PROPOSALS.open(encoding="utf-8") as f:
        lines = [l for l in f if not l.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


@pytest.mark.unit
def test_t150_提案は現在の保留語を全件覆う():
    """シートは curation 1 巡分の記録であり、承認が進むと保留側だけが減る。

    等号で書くと承認した瞬間に落ちる(2026-08-25 に実際に落ちた)。
    正しい不変量は「現在の保留語がシートに含まれる」という包含関係。
    """
    nr = set(json.loads(MANIFEST.read_text(encoding="utf-8"))["needs_review"])
    words = {r["word"] for r in _rows()}
    missing = nr - words
    assert missing == set(), f"提案シートに無い保留語がある: {sorted(missing)[:10]}"


@pytest.mark.unit
def test_t151_全行に提案と理由がある():
    for r in _rows():
        assert r["proposed"] in VALID, f"{r['word']}: 提案値が不正 {r['proposed']}"
        assert r["reason"].strip(), f"{r['word']}: 理由が空"


@pytest.mark.unit
def test_t152_パイプラインは提案シートを読まない():
    """提案が人間の承認を経ずに採用へ化けないことを保証する(AGENTS.md §2)。"""
    offenders = []
    for p in (ROOT / "pipeline").glob("*.py"):
        src = p.read_text(encoding="utf-8")
        if "vocab_proposals" in src:
            offenders.append(p.name)
        tree = ast.parse(src, filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "proposal" in node.value.lower():
                    offenders.append(f"{p.name}:{node.value[:40]}")
    assert offenders == [], f"パイプラインが提案シートを参照している: {offenders}"


@pytest.mark.unit
def test_t153_hold_は採用にも除外にもしない():
    holds = [r for r in _rows() if r["proposed"] == "hold"]
    assert holds, "hold が 1 件も無いのは判断を丸めた疑いがある"
    for r in holds:
        assert r["approved"].strip() in ("", *VALID)
