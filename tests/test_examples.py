"""用例の抽出(F-32 / N-05 二層原則 / O-6)。

**表示層は青空文庫本文と逐語一致**しなければならない。分析層(ルビ・注記を除いた層)で
語を見つけ、文字オフセットで表示層へ戻して引用を切り出す。
分析層の文字列をそのまま引用として出してはならない。

期待値の出所: AGENTS.md §6、SPEC N-05。合成フィクスチャは青空文庫の記法を模した実例。
"""
import pytest

from pipeline import examples

RAW = (
    "　彼は星《ほし》がきらきらと光るのを見た。"
    "｜天《そら》には［＃「そら」に傍点］雲もない。"
    "　ばたばたと足音がした。"
)


@pytest.mark.unit
def test_t220_分析層はルビと注記を落とす():
    text, offsets = examples.strip_with_offsets(RAW)
    assert "《" not in text and "［＃" not in text and "｜" not in text
    assert "きらきら" in text
    assert len(offsets) == len(text)


@pytest.mark.unit
def test_t221_オフセットは原文の同じ文字を指す():
    text, offsets = examples.strip_with_offsets(RAW)
    for i, ch in enumerate(text):
        assert RAW[offsets[i]] == ch, f"{i} 文字目の対応が壊れている"


@pytest.mark.unit
def test_t222_引用は原文の部分文字列である():
    quotes = examples.collect("きらきら", RAW)
    assert quotes, "用例が取れていない"
    for q in quotes:
        assert q["quote"] in RAW, "引用が原文の部分文字列でない(N-05 違反)"


@pytest.mark.unit
def test_t223_引用にルビが残る():
    # 表示層は原文のまま。ルビを落としたら逐語一致でなくなる
    q = examples.collect("きらきら", RAW)[0]["quote"]
    assert "《ほし》" in q


@pytest.mark.unit
def test_t224_文の切れ目で切り出す():
    q = examples.collect("ばたばた", RAW)[0]["quote"]
    assert q.endswith("。")
    assert "きらきら" not in q, "隣の文を巻き込んでいる"


@pytest.mark.unit
def test_t225_カタカナ表記も見つける():
    raw = "　風がサラサラと鳴った。"
    quotes = examples.collect("さらさら", raw)
    assert quotes and "サラサラ" in quotes[0]["quote"]


@pytest.mark.unit
def test_t226_出典が付く():
    rec = examples.build_record(
        "きらきら", RAW,
        {"work_id": "000001", "title": "試作", "author": "甲一",
         "底本名": "底本A", "入力者": "入力者A", "校正者": "校正者A"},
    )
    assert rec["quotes"], "用例が空"
    src = rec["quotes"][0]["source"]
    for k in ("work_id", "title", "author", "底本名", "入力者"):
        assert src[k], f"{k} が空(N-05 違反)"


@pytest.mark.unit
def test_t227_注記を含む文は避けられる():
    raw = "　彼は［＃注記］きらきらと言った。　空がきらきらと光る。"
    q = examples.collect("きらきら", raw, prefer_clean=True)
    assert q and "［＃" not in q[0]["quote"]


@pytest.mark.validation
def test_t050_全用例が原文と逐語一致する():
    """O-6 / N-05。data/raw が無い環境では skip。"""
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    out = root / "data" / "examples.json"
    raw_dir = root / "data" / "raw"
    if not out.exists() or not raw_dir.exists():
        pytest.skip("用例データまたはコーパスが未生成")
    data = json.loads(out.read_text(encoding="utf-8"))
    cache = {}
    checked = 0
    for word, rec in data["words"].items():
        for q in rec["quotes"]:
            wid = q["source"]["work_id"]
            if wid not in cache:
                cache[wid] = (raw_dir / f"{wid}.txt").read_text(encoding="utf-8")
            assert q["quote"] in cache[wid], (
                f"{word} の引用が原文に無い(N-05 違反): {q['quote'][:30]}"
            )
            for k in ("底本名", "入力者"):
                assert q["source"][k], f"{word}: {k} が空(N-05 違反)"
            checked += 1
    assert checked > 0, "検査した引用が 0 件"


@pytest.mark.unit
def test_t228_引用は段落をまたがない():
    raw = "　空が光る" + chr(10) + chr(10) + "　私はざらざらの壁に触れた。"
    q = examples.collect("ざらざら", raw)[0]["quote"]
    assert chr(10) not in q, "引用が段落をまたいでいる"
    assert q.startswith("私は")
