"""青空文庫テキストの正規化(分析層)。

**N-05 二層原則**: ここで作るのは分析層。表示層(原文逐語)は `data/raw` の生テキストが持ち、
本モジュールは入力文字列を変更しない(純関数)。用例の引用は分析層の出力から作ってはならない。

除去するもの(実測 2026-08-25 の青空文庫テキスト形式):
- 冒頭の凡例ブロック(`----` で挟まれた【テキスト中に現れる記号について】)
- 末尾の `底本：` 以降(底本・入力・校正の奥付)
- ルビ `《…》`、ルビ開始記号 `｜`、入力者注記 `［＃…］`
"""
from __future__ import annotations

import re

_RUBY = re.compile(r"《[^》]*》")
_ANNOT = re.compile(r"［＃[^］]*］")
_RULE = re.compile(r"^-{10,}$", re.M)
_FOOTER = re.compile(r"^底本[：:]", re.M)


def strip_header(text: str) -> str:
    """凡例ブロックを落とす。`----` 行が 2 本あるときのみ、その間を除去する。"""
    marks = [m.start() for m in _RULE.finditer(text)]
    if len(marks) < 2:
        return text
    end = _RULE.search(text, marks[1]).end()
    return text[:marks[0]] + text[end:]


def strip_footer(text: str) -> str:
    m = _FOOTER.search(text)
    return text[: m.start()] if m else text


def normalize(text: str) -> str:
    """分析層のテキストを返す。引数は変更しない。"""
    t = strip_header(text)
    t = strip_footer(t)
    t = _RUBY.sub("", t)
    t = _ANNOT.sub("", t)
    t = t.replace("｜", "")
    return t.strip()
