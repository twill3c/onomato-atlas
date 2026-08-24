"""青空文庫索引からのコーパス選定(F-01 / SPEC §4.1.1)。

選定基準は 2026-08-25 に escalation を経て確定した。段の順序と条件を変えるときは
SPEC §4.1.1 を先に改訂すること(規則をコード側で先に動かさない)。

段 7(著者あたり上限)の作品選択は **系統抽出**で行う: 作品ID の昇順に並べ、
等間隔で cap 件を取る。乱数を使わないので種が要らず、再実行で完全に同じ集合になる。
先頭 cap 件を取ると作品ID の若い(登録の早い)作品に偏るため、この方式を採る。
"""
from __future__ import annotations

TARGET_NDC = ("913", "914", "K91")
KANA_TYPE = "新字新仮名"
DEFAULT_CAP = 20
SAMPLING_METHOD = "systematic_by_work_id"  # 乱数不使用(seed なし)


def _ndc_tokens(row: dict) -> list[str]:
    return [t for t in (row.get("分類番号") or "").split() if t != "NDC"]


def _is_target_ndc(row: dict) -> bool:
    return any(t.startswith(TARGET_NDC) for t in _ndc_tokens(row))


# SPEC §4.1.1 の段。(段番号, 名称, 述語)。段 0 は母集団、段 7 は cap で別扱い。
FILTERS = [
    (1, "役割フラグ = 著者", lambda r: (r.get("役割フラグ") or "") == "著者"),
    (2, "作品著作権フラグ = なし", lambda r: (r.get("作品著作権フラグ") or "") == "なし"),
    (3, "テキストファイルURL あり", lambda r: bool((r.get("テキストファイルURL") or "").strip())),
    (4, "原題なし(翻訳を除く)", lambda r: not (r.get("原題") or "").strip()),
    (5, f"文字遣い種別 = {KANA_TYPE}", lambda r: (r.get("文字遣い種別") or "") == KANA_TYPE),
    (6, f"分類番号が {'/'.join(TARGET_NDC)} を含む", _is_target_ndc),
]


def _cap_by_author(rows: list[dict], cap: int) -> list[dict]:
    """著者あたり cap 件へ系統抽出で間引く。入力順は保存する。"""
    by_author: dict[str, list[dict]] = {}
    for r in rows:
        by_author.setdefault(r.get("人物ID") or "", []).append(r)
    keep: set[int] = set()
    for works in by_author.values():
        if len(works) <= cap:
            keep.update(id(w) for w in works)
            continue
        ordered = sorted(works, key=lambda w: w.get("作品ID") or "")
        step = len(ordered) / cap
        keep.update(id(ordered[int(i * step)]) for i in range(cap))
    return [r for r in rows if id(r) in keep]


def select_with_report(rows: list[dict], per_author_cap: int = DEFAULT_CAP):
    """選定結果と、各段の残存件数レポートを返す。"""
    stages = [{"stage": 0, "name": "索引全行", "remaining": len(rows)}]
    cur = list(rows)
    for num, name, pred in FILTERS:
        cur = [r for r in cur if pred(r)]
        stages.append({"stage": num, "name": name, "remaining": len(cur)})
    cur = _cap_by_author(cur, per_author_cap)
    stages.append(
        {
            "stage": 7,
            "name": f"著者あたり {per_author_cap} 作品上限",
            "remaining": len(cur),
            "method": SAMPLING_METHOD,
            "seed": None,
        }
    )
    return cur, stages


def select(rows: list[dict], per_author_cap: int = DEFAULT_CAP) -> list[dict]:
    return select_with_report(rows, per_author_cap)[0]


def source_note(row: dict) -> dict:
    """底本表記(N-05)。索引 CSV から直接取れるので本文フッタを解析しない。

    実測 2026-08-25: 底本名1・入力者は 100%、校正者は 99.7% 充足。
    """
    return {
        "底本名": (row.get("底本名1") or "").strip(),
        "入力者": (row.get("入力者") or "").strip(),
        "校正者": (row.get("校正者") or "").strip(),
    }


def unique_works(rows: list[dict]) -> list[dict]:
    """取得リスト用に作品ID で一意化する(SPEC §4.1.1)。

    共著は同一作品ID に著者行が複数立つ。実索引では段 7 が 2,212 行 / 異なり作品 2,200 で、
    差 12 件がこれにあたる。先に現れた行を残し、入力順を保存する。
    """
    seen: set[str] = set()
    out = []
    for r in rows:
        wid = r.get("作品ID") or ""
        if wid in seen:
            continue
        seen.add(wid)
        out.append(r)
    return out
