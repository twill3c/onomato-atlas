"""音側素性の抽出(F-10)。

**表記から決定論的に得る観測**であって主張ではない。人手介入を持たない。

**F-00(循環の禁止)**: このモジュールを意味側の構成に使ってはならない。
音側は検証・色分け・逆引きにのみ用いる。T-020 が静的に検査する。

対象は 2 モーラ語幹の擬態語(`ころころ` `ころり` 等)。拗音を含む 3 モーラ語幹
(`しゃきしゃき`)は現行の抽出器が拾わないため、form=unknown として返す。
"""
from __future__ import annotations

# かな → (子音, 母音)。あ行は子音なし。
_KANA = {}
for _row, _cons in [
    ("あいうえお", ""), ("かきくけこ", "k"), ("がぎぐげご", "g"),
    ("さしすせそ", "s"), ("ざじずぜぞ", "z"), ("たちつてと", "t"),
    ("だぢづでど", "d"), ("なにぬねの", "n"), ("はひふへほ", "h"),
    ("ばびぶべぼ", "b"), ("ぱぴぷぺぽ", "p"), ("まみむめも", "m"),
    ("らりるれろ", "r"),
]:
    for _k, _v in zip(_row, "aiueo"):
        _KANA[_k] = (_cons, _v)
_KANA.update({"や": ("y", "a"), "ゆ": ("y", "u"), "よ": ("y", "o"),
              "わ": ("w", "a"), "を": ("w", "o")})

VOICED = set("がぎぐげござじずぜぞだぢづでどばびぶべぼ")
SEMIVOICED = set("ぱぴぷぺぽ")

FORMS = ("ABAB", "ABっと", "ABーっ", "ABっ", "ABり", "ABん", "ABー")


def _form(word: str) -> str:
    if len(word) == 4 and word[:2] == word[2:]:
        return "ABAB"
    for suffix in ("っと", "ーっ", "っ", "り", "ん", "ー"):
        if word.endswith(suffix) and len(word) == 2 + len(suffix):
            return "AB" + suffix
    return "unknown"


def features(word: str) -> dict:
    """音側素性を返す。未対応の表記でも例外にせず form=unknown で返す。"""
    form = _form(word)
    stem = word[:2]
    onsets, vowels = [], []
    for ch in stem:
        if ch == "ー" and vowels:
            # 長音符は直前の母音の引き伸ばし。子音は持たない
            onsets.append("")
            vowels.append(vowels[-1])
            continue
        c, v = _KANA.get(ch, (None, None))
        if c is None:
            return {
                "word": word, "stem": stem, "form": "unknown",
                "onset1": None, "onset2": None, "vowels": None,
                "voiced": None, "semivoiced": None,
                "geminate": None, "moraic_n": None, "long": None,
            }
        onsets.append(c)
        vowels.append(v)
    return {
        "word": word,
        "stem": stem,
        "form": form,
        "onset1": onsets[0],
        "onset2": onsets[1],
        "vowels": "".join(vowels),
        "voiced": any(ch in VOICED for ch in stem),
        "semivoiced": any(ch in SEMIVOICED for ch in stem),
        "geminate": "っ" in word,
        "moraic_n": word.endswith("ん"),
        "long": "ー" in word,
    }


def table(words) -> dict[str, dict]:
    """語のリストから音側素性表を作る。"""
    return {w: features(w) for w in words}
