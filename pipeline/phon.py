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


# 音側の距離(N-04)。**TypeScript 側 web/src/lib/phonDist.ts と同一の定義**。
# 変えるときは両方を同時に変え、gold/phon_cross.json を作り直して O-4 を通すこと。
WEIGHTS = {
    "onset1": 3.0, "onset2": 2.0, "vowels": 3.0, "form": 2.0,
    "voiced": 1.0, "semivoiced": 1.0, "geminate": 0.5, "moraic_n": 0.5, "long": 0.5,
}


def distance(a: str, b: str) -> float:
    """音側素性のハミング距離(重み付き)。**意味の距離ではない。**"""
    fa, fb = features(a), features(b)
    total = 0.0
    for key, w in WEIGHTS.items():
        va, vb = fa.get(key), fb.get(key)
        if va is None or vb is None:
            total += w if va != vb else 0.0
        elif va != vb:
            total += w
    return round(total, 4)


def nearest(word: str, candidates, n: int = 8) -> list[tuple[str, float]]:
    """音が似た語を返す。同語は含めない。同点は表記順で決める(決定論)。"""
    scored = [(c, distance(word, c)) for c in candidates if c != word]
    scored.sort(key=lambda x: (x[1], x[0]))
    return scored[:n]


def table(words) -> dict[str, dict]:
    """語のリストから音側素性表を作る。"""
    return {w: features(w) for w in words}
