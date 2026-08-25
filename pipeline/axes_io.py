"""軸の採否記録と UI 配信データの生成(F-22 / F-23)。

**F-22(較正ファーストの UI 版)**: 検定を通っていない軸は UI に出さない。
不採用の軸からは**ベクトルも射影値も落とす**。UI 側の実装ミスで出てしまう余地を
データ側で断つ。

**F-23**: 採用・不採用のいずれも、検定結果と対比語対を記録して出典として参照できるようにする。
"""
from __future__ import annotations

CRITERION = {
    "description": "方向一致の二項検定と、対応シャッフル対照の経験 p の両方が α 未満",
    "requires": ["p_binomial < alpha", "control_p_empirical < alpha"],
}


def decide(stats: dict, alpha: float) -> str:
    """軸の採否(Q-03)。**両方**を満たさなければ採用しない。"""
    ok = stats.get("p_binomial", 1.0) < alpha and stats.get("control_p_empirical", 1.0) < alpha
    return "adopted" if ok else "rejected"


def build_document(axis_specs, alpha: float, generated_on: str = "",
                   density: dict | None = None) -> dict:
    """axes.json の中身を組む。

    不採用の軸は検定結果だけを残す(F-22)。採用軸でも、**密度下限を満たさない語には
    射影値を持たせない**(Q-02)。軸ごとに下限が違うのは、軸によって必要な密度が
    違うことが分割半較正で分かったため。
    """
    out = []
    for spec in axis_specs:
        decision = decide(spec["stats"], alpha)
        rec = {
            "id": spec["id"],
            "name": spec["name"],
            "source": spec.get("source", ""),
            "pairs": spec.get("pairs", []),
            "stats": spec["stats"],
            "decision": decision,
        }
        for key in ("density_floor", "reliability"):
            if key in spec:
                rec[key] = spec[key]
        if decision == "adopted":
            rec["vector"] = spec["vector"]
            floor = spec.get("density_floor")
            proj = spec["projections"]
            if floor is not None and density is not None:
                proj = {w: v for w, v in proj.items() if density.get(w, 0) >= floor}
            rec["projections"] = proj
        out.append(rec)
    doc = {"criterion": {**CRITERION, "alpha": alpha}, "axes": out}
    if generated_on:
        doc["generated_on"] = generated_on
    return doc
