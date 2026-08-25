"""音側素性の抽出(F-10)と循環の禁止(F-00)。

音側は**表記から決定論的に得る観測**であって主張ではない。人手介入なし。
期待値の出所: SPEC §2(用語)・§4.3。表記から一意に決まるので合成フィクスチャでよい。
"""
import ast
from pathlib import Path

import pytest

from pipeline import phon

PIPELINE = Path(__file__).resolve().parents[1] / "pipeline"
# 意味側を構成するモジュール。ここに音側(phon)を import してはならない(F-00)
SEMANTIC_MODULES = ("build_vocab.py", "sem.py")


@pytest.mark.unit
def test_t020_意味側は音側モジュールをimportしない():
    """F-00。**この検査に落ちたら他が全緑でも不合格**(AGENTS.md §1)。"""
    offenders = []
    for name in SEMANTIC_MODULES:
        p = PIPELINE / name
        if not p.exists():
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offenders += [(name, a.name) for a in node.names if "phon" in a.name]
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if "phon" in mod:
                    offenders.append((name, mod))
                if mod.startswith("pipeline") or mod == "":
                    offenders += [(name, a.name) for a in node.names if a.name == "phon"]
    assert offenders == [], f"意味側が音側を import している(F-00 違反): {offenders}"


@pytest.mark.unit
def test_t021_形態パラダイムは語幹と母音が一致し形態型だけが違う():
    fs = {w: phon.features(w) for w in ("ころころ", "ころっと", "ころり", "ころん")}
    assert len({f["stem"] for f in fs.values()}) == 1
    assert len({f["vowels"] for f in fs.values()}) == 1
    assert len({f["onset1"] for f in fs.values()}) == 1
    assert len({f["form"] for f in fs.values()}) == 4, "形態型は 4 通りに割れる"


@pytest.mark.unit
def test_t022_濁音半濁音促音撥音長音のフラグが表記と対応する():
    assert phon.features("からから")["voiced"] is False
    assert phon.features("がらがら")["voiced"] is True
    assert phon.features("ぱらぱら")["semivoiced"] is True
    assert phon.features("ころっと")["geminate"] is True
    assert phon.features("ころん")["moraic_n"] is True
    assert phon.features("すーっ")["long"] is True


@pytest.mark.unit
def test_t140_語頭子音と第2子音と母音列を取り出す():
    f = phon.features("きらきら")
    assert (f["onset1"], f["onset2"], f["vowels"]) == ("k", "r", "ia")
    g = phon.features("ぽつぽつ")
    assert (g["onset1"], g["onset2"], g["vowels"]) == ("p", "t", "ou")
    a = phon.features("うろうろ")
    assert a["onset1"] == "", "あ行は子音なし"


@pytest.mark.unit
def test_t141_濁音化は語幹の子音だけを変える():
    a, b = phon.features("きらきら"), phon.features("ぎらぎら")
    assert (a["onset1"], b["onset1"]) == ("k", "g")
    assert a["vowels"] == b["vowels"] and a["form"] == b["form"]


@pytest.mark.unit
def test_t142_抽出は決定論であり人手介入を持たない():
    assert phon.features("さらさら") == phon.features("さらさら")


@pytest.mark.unit
def test_t143_未対応の表記は例外にせず不明として返す():
    f = phon.features("しゃきしゃき")  # 拗音を含む 3 モーラ語幹は現行の語彙に無い
    assert f["form"] == "unknown" or f["stem"]
