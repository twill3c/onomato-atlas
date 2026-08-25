"""用例の抽出(F-32 / N-05 二層原則 / O-6)。

**表示層(原文逐語)と分析層(ルビ・注記を除いた層)を文字オフセットで対応させる。**
語は分析層で探し、引用は表示層から切り出す。分析層の文字列を引用として出してはならない。

青空文庫の記法(実測 2026-08-25):
- ルビ `《…》`、ルビ開始記号 `｜`、入力者注記 `［＃…］`
- 段落が 1 行に収まっているため、文の切り出しは句点で行う
"""
from __future__ import annotations

import re

_SENT_END = "。！？" + chr(10)  # 改行も文の境界とする(段落をまたいだ引用を防ぐ)
_RUBY_OPEN, _RUBY_CLOSE = "《", "》"
_ANNOT_OPEN, _ANNOT_CLOSE = "［＃", "］"


def kata_to_hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヴ" else c for c in s)


def strip_with_offsets(raw: str) -> tuple[str, list[int]]:
    """分析層の文字列と、各文字が原文のどこかを指すオフセット列を返す。"""
    out, offsets = [], []
    i = 0
    n = len(raw)
    while i < n:
        if raw.startswith(_ANNOT_OPEN, i):
            j = raw.find(_ANNOT_CLOSE, i)
            i = n if j < 0 else j + 1
            continue
        ch = raw[i]
        if ch == _RUBY_OPEN:
            j = raw.find(_RUBY_CLOSE, i)
            i = n if j < 0 else j + 1
            continue
        if ch == "｜":
            i += 1
            continue
        out.append(ch)
        offsets.append(i)
        i += 1
    return "".join(out), offsets


def _sentence_span(display: str, pos: int) -> tuple[int, int]:
    """表示層の pos を含む文の範囲。句点の直後から次の句点までを取る。"""
    start = 0
    for k in range(pos - 1, -1, -1):
        if display[k] in _SENT_END:
            start = k + 1
            break
    end = len(display)
    for k in range(pos, len(display)):
        if display[k] in _SENT_END:
            end = k + 1
            break
    return start, end


def collect(word: str, raw: str, prefer_clean: bool = False, limit: int = 5) -> list[dict]:
    """語の用例を原文から切り出す。戻り値の quote は**原文の部分文字列**。"""
    analysis, offsets = strip_with_offsets(raw)
    folded = kata_to_hira(analysis)
    target = kata_to_hira(word)
    found, seen = [], set()
    for m in re.finditer(re.escape(target), folded):
        a, b = m.start(), m.end() - 1
        if a >= len(offsets) or b >= len(offsets):
            continue
        s, e = _sentence_span(raw, offsets[a])
        quote = raw[s:e].strip("　 " + chr(10))
        if not quote or quote in seen:
            continue
        seen.add(quote)
        found.append({"quote": quote, "surface": analysis[m.start():m.end()],
                      "has_annotation": _ANNOT_OPEN in quote})
    if prefer_clean:
        clean = [q for q in found if not q["has_annotation"]]
        if clean:
            found = clean
    return found[:limit]


def build_record(word: str, raw: str, meta: dict, limit: int = 5) -> dict:
    """1 作品からの用例に出典を付す。**底本表記は必須**(N-05)。"""
    quotes = []
    for q in collect(word, raw, prefer_clean=True, limit=limit):
        quotes.append({
            "quote": q["quote"],
            "surface": q["surface"],
            "source": {
                "work_id": meta.get("work_id", ""),
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "底本名": meta.get("底本名", ""),
                "入力者": meta.get("入力者", ""),
                "校正者": meta.get("校正者", ""),
            },
        })
    return {"word": word, "quotes": quotes}
