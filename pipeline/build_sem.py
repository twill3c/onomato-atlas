"""意味側チャネルを本コーパスに適用して sem.json を生成する(F-11/F-12)。

SVD 次元数は較正で決めるため、ここでは複数の k について寄与率を記録するだけにする。
"""
import json
from pathlib import Path

import numpy as np

from pipeline import aozora_text, build_vocab, sem

ROOT = Path(__file__).resolve().parents[1]
K_MAX = 100

def main():
    manifest = json.loads((ROOT / "data" / "vocab_manifest.json").read_text(encoding="utf-8"))
    adopted = set(manifest["adopted"])
    print(f"採用語 {len(adopted)} / ストップリスト v{build_vocab.LIGHT_VERBS_VERSION}", flush=True)

    texts = [aozora_text.normalize(p.read_text(encoding="utf-8"))
             for p in sorted((ROOT / "data" / "raw").glob("*.txt"))]
    print(f"読込 {len(texts)} 作品 / {sum(len(t) for t in texts):,} 字", flush=True)

    ctx = build_vocab.cooccurrence(texts, adopted)
    words, cols, M = sem.build_matrix(ctx, min_ctx_count=5)
    print(f"行列 {M.shape[0]} 語 x {M.shape[1]} 文脈語 / 非零率 {(M > 0).mean():.2%}", flush=True)

    X = sem.ppmi(M)
    E, ev = sem.embed(X, k=K_MAX)
    cum = np.cumsum(ev)
    print("寄与率: " + "  ".join(f"d{i+1}:{ev[i]:.1%}" for i in range(5)), flush=True)
    for k in (10, 30, 50, 100):
        if k <= len(cum):
            print(f"  累積 d1-{k}: {cum[k-1]:.1%}", flush=True)

    out = {
        "n_words": len(words),
        "n_contexts": len(cols),
        "nonzero_rate": float((M > 0).mean()),
        "stoplist_version": build_vocab.LIGHT_VERBS_VERSION,
        "k_max": K_MAX,
        "explained_variance": [float(x) for x in ev],
        "words": words,
        "embedding": [[round(float(x), 5) for x in row] for row in E],
    }
    (ROOT / "data" / "sem.json").write_text(
        json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"sem.json → {len(words)} 語 x {K_MAX} 次元", flush=True)

    for w in ("きらきら", "ぐるぐる", "そわそわ", "ばたばた", "どきどき", "ざらざら"):
        if w in words:
            nb = sem.neighbors(words, E, w, n=5)
            print(f"  {w:6} → " + " ".join(f"{a}({b:.2f})" for a, b in nb), flush=True)

if __name__ == "__main__":
    raise SystemExit(main())
