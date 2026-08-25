"""コーパス取得と青空文庫テキストの正規化(F-01 / N-02 / N-05)。

N-02: 実アクセスは手動実行のみ。テストはフィクスチャ駆動でネットワークを使わない。
期待値の出所: 実測 2026-08-25 — 選定 2,200 件はすべて .zip / ShiftJIS / JIS X 0208。
"""
import io
import zipfile

import pytest

from pipeline import aozora_text, fetch_corpus


def make_zip(name: str, body: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name, body.encode("cp932"))
    return buf.getvalue()


@pytest.mark.unit
def test_t120_zipからテキストを取り出しshiftjisを復号する():
    blob = make_zip("sample.txt", "星がきらきらと光る")
    assert fetch_corpus.extract_text(blob) == "星がきらきらと光る"


@pytest.mark.unit
def test_t121_zip内にテキストが無ければ例外():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.html", b"<html></html>")
    with pytest.raises(ValueError):
        fetch_corpus.extract_text(buf.getvalue())


@pytest.mark.unit
def test_t122_キャッシュがあればhttpを出さない(tmp_path):
    called = []

    def opener(url):  # 呼ばれたら失敗
        called.append(url)
        return b""

    cache = tmp_path / "000001.zip"
    cache.write_bytes(make_zip("a.txt", "ころころ転がる"))
    got = fetch_corpus.fetch_bytes("https://example.invalid/x.zip", cache, opener=opener)
    assert called == [], "キャッシュがあるのに HTTP を出した(N-02)"
    assert fetch_corpus.extract_text(got) == "ころころ転がる"


@pytest.mark.unit
def test_t123_キャッシュが無ければ取得して保存する(tmp_path):
    blob = make_zip("a.txt", "ばたばた走る")
    cache = tmp_path / "000002.zip"
    got = fetch_corpus.fetch_bytes("https://example.invalid/y.zip", cache, opener=lambda u: blob)
    assert cache.exists() and cache.read_bytes() == blob
    assert fetch_corpus.extract_text(got) == "ばたばた走る"


@pytest.mark.unit
def test_t124_manifestに取得元と底本表記が入る():
    row = {
        "作品ID": "000001", "作品名": "試作", "人物ID": "000100", "姓": "甲", "名": "一",
        "テキストファイルURL": "https://example.invalid/1.zip",
        "底本名1": "底本A", "入力者": "入力者A", "校正者": "校正者A",
        "文字遣い種別": "新字新仮名", "分類番号": "NDC 913", "公開日": "2000-01-01",
    }
    rec = fetch_corpus.manifest_record(row, fetched_on="2026-08-25", chars=12)
    assert rec["source_url"] == row["テキストファイルURL"]
    assert rec["fetched_on"] == "2026-08-25"
    # N-05: 底本表記を必ず付す
    assert rec["底本名"] == "底本A" and rec["入力者"] == "入力者A"
    assert rec["chars"] == 12


# --- 正規化(分析層)。表示層の原文は壊さない(N-05 二層原則) ---

RAW = """試作
甲一

-------------------------------------------------------
【テキスト中に現れる記号について】

《》：ルビ
-------------------------------------------------------

星《ほし》がきらきらと光った。
｜天《そら》には［＃「そら」に傍点］雲もない。


底本：「どこかの本」どこか書房
   2000（平成12）年1月1日第1刷発行
入力：入力者A
校正：校正者A
"""


@pytest.mark.unit
def test_t125_ルビと注記と傍点記号を除去する():
    got = aozora_text.normalize(RAW)
    assert "《ほし》" not in got and "［＃" not in got and "｜" not in got
    assert "星がきらきらと光った。" in got


@pytest.mark.unit
def test_t126_凡例ヘッダと底本フッタを落とす():
    got = aozora_text.normalize(RAW)
    assert "【テキスト中に現れる記号について】" not in got
    assert "底本：" not in got
    assert "入力：" not in got


@pytest.mark.unit
def test_t127_正規化は原文を変更しない():
    before = RAW
    aozora_text.normalize(RAW)
    assert RAW == before, "分析層の処理が表示層の原文を壊してはならない(N-05)"


@pytest.mark.unit
def test_t128_一時的な取得失敗はリトライされる(tmp_path):
    # 実測 2026-08-25: 本取得で DNS 断により 1,042 件が 1 回の失敗で脱落した
    calls = []
    blob = make_zip("a.txt", "きらきら光る")

    def flaky(url):
        calls.append(url)
        if len(calls) < 3:
            raise OSError("getaddrinfo failed")
        return blob

    got = fetch_corpus.fetch_bytes(
        "https://example.invalid/z.zip", tmp_path / "z.zip",
        opener=flaky, retries=3, backoff=0.0,
    )
    assert len(calls) == 3
    assert fetch_corpus.extract_text(got) == "きらきら光る"


@pytest.mark.unit
def test_t129_リトライを使い切ったら例外を上げる(tmp_path):
    def always_fail(url):
        raise OSError("getaddrinfo failed")

    with pytest.raises(OSError):
        fetch_corpus.fetch_bytes(
            "https://example.invalid/z.zip", tmp_path / "z.zip",
            opener=always_fail, retries=2, backoff=0.0,
        )
    assert not (tmp_path / "z.zip").exists(), "失敗した取得をキャッシュに残さない"
