"""語彙 curation(F-05 / F-06 / F-07)。

**エージェントは未知語の採否を独断で決めない**(AGENTS.md §2)。
判定は版管理された `data/curated/vocab_decisions.tsv` にのみ従い、
表に無い ABAB 型は `needs_review` へ回してエスカレーションの対象にする。

変化形(ABり/ABん/ABっ 等)だけは自動規則で足りる(F-06):
**語幹が ABAB 型として語彙内に採用されていること**を要件とする。
実測 2026-08-25(docs/concept.md §11 発見 A): この規則で 65 語すべてが偽陽性ゼロになった。
規則を緩めると `ひとり` `つもり` `つまり` `かなり` `やはり` が混入し、SVD 第 1 次元を占領する。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.extract import is_reduplication, kata_to_hira

DECISIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "curated" / "vocab_decisions.tsv"
_VERSION_RE = re.compile(r"^#\s*vocab_decisions\s+v(?P<v>\d+\.\d+\.\d+)")

REASON_NO_STEM = "語幹が ABAB 型として語彙に存在しない(F-06)"
REASON_UNKNOWN = "curation 表に無い未知語。人手の採否判断が必要(AGENTS.md §2)"
REASON_FORCED_REVIEW = "判定困難として明示的に保留された"


def load_decisions(path: Path | None = None) -> tuple[str, dict[str, tuple[str, str]]]:
    """版付き判定表を読む。version 行が無ければ例外(AGENTS.md §3)。"""
    p = path or DECISIONS_PATH
    version = None
    table: dict[str, tuple[str, str]] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            m = _VERSION_RE.match(line)
            if m:
                version = m.group("v")
            continue
        if not line.strip() or line.startswith("word\t"):
            continue
        word, decision, reason = line.split("\t", 2)
        table[word] = (decision, reason)
    if version is None:
        raise ValueError(f"version 行の無い判定表は読まない: {p}")
    return version, table


@dataclass
class Vocab:
    version: str
    adopted: set[str] = field(default_factory=set)
    rejected: set[str] = field(default_factory=set)
    needs_review: set[str] = field(default_factory=set)
    reasons: dict[str, str] = field(default_factory=dict)

    def manifest(self) -> dict[str, dict]:
        out = {}
        for w in self.adopted | self.rejected | self.needs_review:
            decision = (
                "adopted" if w in self.adopted
                else "rejected" if w in self.rejected
                else "needs_review"
            )
            out[w] = {"decision": decision, "reason": self.reasons[w], "table_version": self.version}
        return out


def build(freq: dict[str, int], needs_review: set[str] | None = None,
          decisions_path: Path | None = None) -> Vocab:
    """頻度表から語彙を確定する。freq のキーは表記ゆれ統合済みであること(F-04)。"""
    version, table = load_decisions(decisions_path)
    forced = set(needs_review or ())
    v = Vocab(version=version)

    # 第 1 段: ABAB 型を判定表に照らす
    for word in freq:
        norm = kata_to_hira(word)
        if not is_reduplication(norm):
            continue
        if norm in forced:
            v.needs_review.add(norm); v.reasons[norm] = REASON_FORCED_REVIEW
        elif norm in table:
            decision, reason = table[norm]
            (v.adopted if decision == "adopted" else v.rejected).add(norm)
            v.reasons[norm] = reason
        else:
            v.needs_review.add(norm); v.reasons[norm] = REASON_UNKNOWN

    # 第 2 段: 変化形は語幹の採否に従う(F-06)
    for word in freq:
        norm = kata_to_hira(word)
        if is_reduplication(norm) or norm in v.reasons:
            continue
        stem = norm[:2] * 2
        if stem in v.adopted:
            v.adopted.add(norm)
            v.reasons[norm] = f"語幹 {stem} が採用済み(F-06 自動規則)"
        else:
            v.rejected.add(norm)
            v.reasons[norm] = REASON_NO_STEM
    return v
