"""擬態語候補の抽出(F-02 / F-03 / F-04)。

**正規表現のみの抽出を禁じる**(F-02)。形態素境界を必ず通す。
実測 2026-08-25(docs/concept.md §2 実測 2): 境界を通さないと延べの 10.4% が偽陽性になり、
変化形では `からん`(「わからん」由来)= 291、`にやっ`(「…にやって」由来)= 274 を拾う。

実測 2026-08-25(同 実測 3): ABAB トークンの品詞は副詞 90.6% / 形状詞 5.3% /
名詞 2.5% / 感動詞 1.3% で、解析器は品詞を散らさない。よって POS フィルタは有効。
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

# ひらがな 2 モーラ相当 2 文字の反復、およびカタカナ版
_REP_HIRA = re.compile(r"([ぁ-ん]{2})\1")
_REP_KATA = re.compile(r"([ァ-ヴ]{2})\1")
# 変化形。語幹の妥当性は curate 側が「語幹が ABAB として存在するか」で判定する(F-06)
_VARIANTS = [
    re.compile(r"[ぁ-んァ-ヴ]{2}っと"),
    re.compile(r"[ぁ-んァ-ヴ]{2}ーっ"),
    re.compile(r"[ぁ-んァ-ヴ]{2}っ"),
    re.compile(r"[ぁ-んァ-ヴ]{2}り"),
    re.compile(r"[ぁ-んァ-ヴ]{2}ん"),
    re.compile(r"[ぁ-んァ-ヴ]{2}ー"),
]
_ALL = [_REP_HIRA, _REP_KATA] + _VARIANTS

OK_POS = ("副詞", "形状詞", "感動詞", "名詞")


@dataclass(frozen=True)
class Candidate:
    surface: str
    pos: str
    norm: str


@lru_cache(maxsize=1)
def _tagger():
    import fugashi

    return fugashi.Tagger()


def is_mimetic_form(s: str) -> bool:
    """表記が擬態語の形をしているか。**語であることの保証ではない**(境界判定は別)。"""
    return 3 <= len(s) <= 4 and any(p.fullmatch(s) for p in _ALL)


def is_reduplication(s: str) -> bool:
    return bool(_REP_HIRA.fullmatch(s) or _REP_KATA.fullmatch(s))


def kata_to_hira(s: str) -> str:
    """表記ゆれ統合(F-04)。実測 2026-08-25: 752 → 606 語。"""
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヴ" else c for c in s)


def candidates(text: str) -> list[Candidate]:
    """1 つのテキストから候補を取り出す。形態素境界と品詞を必ず通す。"""
    out: list[Candidate] = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        for w in _tagger()(line):
            s = w.surface
            if not is_mimetic_form(s):
                continue
            pos = w.feature.pos1
            if pos not in OK_POS:
                continue
            out.append(Candidate(surface=s, pos=pos, norm=kata_to_hira(s)))
    return out


def tally(texts) -> Counter:
    """表記ゆれ統合後の頻度。キーはひらがな正規形。"""
    return tally_with_pos(texts)[0]


def tally_with_pos(texts) -> tuple[Counter, dict[str, Counter]]:
    """頻度と、語ごとの品詞分布を同時に返す。

    品詞分布は F-06 の名詞ガード(curate)が使う。実測 2026-08-25: このガードが無いと
    カタカナ外来語が変化形として語彙に混入する(バター 389 / メリー 192 / パリー 58)。
    """
    c: Counter = Counter()
    pos: dict[str, Counter] = {}
    for t in texts:
        for cand in candidates(t):
            c[cand.norm] += 1
            pos.setdefault(cand.norm, Counter())[cand.pos] += 1
    return c, pos
