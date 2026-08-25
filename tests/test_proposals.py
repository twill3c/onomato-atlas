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
DECISIONS = ROOT / "data" / "curated" / "vocab_decisions.tsv"
VALID = {"adopted", "rejected", "hold"}


def _rows():
    with PROPOSALS.open(encoding="utf-8") as f:
        lines = [l for l in f if not l.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


@pytest.mark.unit
def test_t150_承認した採用が判定表に反映されている():
    """シートと live manifest を結合させない(HC-004)。

    保留語は curation の承認で減り、新しい規則(F-06b 名詞ガード等)で増える。
    どちらの向きにも動くので、シートと manifest の集合関係を不変量にしてはならない
    (等号でも包含でも落ちた。2026-08-25 に 2 度)。
    ここで確かめるのは「承認したものが判定表に届いているか」という一方向の整合だけ。
    """
    approved = {r["word"] for r in _rows() if r["approved"].strip() == "adopted"}
    if not approved:
        pytest.skip("まだ承認された語が無い")
    decided = {}
    for line in DECISIONS.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or line.startswith("word	") or not line.strip():
            continue
        w, dec, _ = line.split("	", 2)
        decided[w] = dec
    missing = {w for w in approved if decided.get(w) != "adopted"}
    assert missing == set(), f"承認したのに判定表へ届いていない語: {sorted(missing)[:10]}"


@pytest.mark.unit
def test_t154_シートに同じ語が二度出ない():
    words = [r["word"] for r in _rows()]
    dupes = {w for w in words if words.count(w) > 1}
    assert dupes == set(), f"重複: {sorted(dupes)[:10]}"


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
