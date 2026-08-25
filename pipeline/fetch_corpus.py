"""青空文庫コーパスの取得(F-01 / N-02 / N-05)。

N-02: **実アクセスは手動実行のみ**。再実行はキャッシュ優先で HTTP を出さない。
取得間隔 1 秒以上・User-Agent 明示。テストは `opener` 注入でネットワークを使わない。
N-05: 全レコードに取得元 URL・取得日・底本表記(底本名 / 入力者 / 校正者)を残す。

使い方:
    python -m pipeline.fetch_corpus              # 選定全件(キャッシュ優先)
    python -m pipeline.fetch_corpus --limit 10   # 先頭 10 件だけ
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

from pipeline import selection

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "index_cache" / "list_person_all_extended_utf8.csv"
CACHE = ROOT / "data" / "cache"
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "corpus_manifest.json"

UA = "onomato-atlas corpus builder (personal research; contact: twill3c@gmail.com)"
MIN_INTERVAL = 1.0  # 秒(N-02)
_last = 0.0


def today() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat()


def _http(url: str) -> bytes:
    global _last
    wait = MIN_INTERVAL - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    _last = time.monotonic()
    return body


RETRIES = 3
BACKOFF = 2.0  # 秒(指数バックオフの基数)


def fetch_bytes(url: str, cache_path: Path, opener=_http,
                retries: int = RETRIES, backoff: float = BACKOFF) -> bytes:
    """キャッシュ優先の取得。キャッシュがあれば opener を呼ばない(N-02)。

    一時的なネットワーク障害でリトライする。実測 2026-08-25: 本取得の途中で DNS が落ち、
    リトライが無かったため 2,200 件中 1,042 件が 1 回の失敗で脱落した。
    失敗した取得はキャッシュに残さない(壊れた zip を再利用しないため)。
    """
    if cache_path.exists():
        return cache_path.read_bytes()
    last = None
    for attempt in range(retries):
        try:
            body = opener(url)
            break
        except Exception as e:  # noqa: BLE001 — 種別を問わず所定回数だけ再試行する
            last = e
            if attempt + 1 < retries and backoff:
                time.sleep(backoff * (2 ** attempt))
    else:
        raise last
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(body)
    return body


def extract_text(blob: bytes) -> str:
    """zip から本文テキストを取り出して復号する。選定分は全件 ShiftJIS(実測 2026-08-25)。"""
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".txt")]
        if not names:
            raise ValueError(f"zip にテキストが無い: {zf.namelist()}")
        data = zf.read(names[0])
    for enc in ("cp932", "shift_jis_2004", "utf-8", "euc_jp"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("本文の文字コードを判定できない")


def manifest_record(row: dict, fetched_on: str, chars: int) -> dict:
    note = selection.source_note(row)
    return {
        "work_id": row["作品ID"],
        "title": row["作品名"],
        "person_id": row["人物ID"],
        "author": f"{row.get('姓','')}{row.get('名','')}",
        "kana_type": row.get("文字遣い種別", ""),
        "ndc": row.get("分類番号", ""),
        "published": row.get("公開日", ""),
        "source_url": row["テキストファイルURL"],
        "fetched_on": fetched_on,
        "chars": chars,
        **note,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    with INDEX.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    sel, stages = selection.select_with_report(rows)
    works = selection.unique_works(sel)
    if args.limit:
        works = works[: args.limit]

    RAW.mkdir(parents=True, exist_ok=True)
    records, failures = [], []
    on = today()
    for i, row in enumerate(works, 1):
        wid = row["作品ID"]
        try:
            blob = fetch_bytes(row["テキストファイルURL"], CACHE / f"{wid}.zip")
            text = extract_text(blob)
        except Exception as e:  # 個別失敗で全体を止めない。manifest に列挙する
            failures.append({"work_id": wid, "url": row["テキストファイルURL"], "error": repr(e)})
            continue
        (RAW / f"{wid}.txt").write_text(text, encoding="utf-8")
        records.append(manifest_record(row, on, len(text)))
        if i % 100 == 0:
            print(f"  {i}/{len(works)}  取得 {len(records)} / 失敗 {len(failures)}", flush=True)

    MANIFEST.write_text(
        json.dumps(
            {
                "fetched_on": on,
                "index_fetched_on": "2026-08-17",
                "selection_stages": stages,
                "requested": len(works),
                "fetched": len(records),
                "failures": failures,
                "works": records,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    total = sum(r["chars"] for r in records)
    print(f"完了: {len(records)}/{len(works)} 件 / {total:,} 字 / 失敗 {len(failures)} 件")
    print(f"manifest → {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
