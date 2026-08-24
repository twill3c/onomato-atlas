# -*- coding: utf-8 -*-
exec(open(r"C:\Users\TETRUR~1\AppData\Local\Temp\claude\c---ClaudeCode\aed437ee-8fa1-4d66-ada4-4fb8f9ad255d\scratchpad\probe6.py",encoding="utf-8").read().split("print(\"\n[O-1'")[0])
import numpy as np, math
def loo_stats(D):
    D=np.array(D); nz=np.linalg.norm(D,axis=1)>1e-9; D=D[nz]/np.linalg.norm(D[nz],axis=1,keepdims=True)
    n=len(D); pos=0; sims=[]
    for i in range(n):
        m=np.delete(D,i,axis=0).mean(0); m/=np.linalg.norm(m); s=float(D[i]@m); sims.append(s); pos+=s>0
    return pos,n,float(np.mean(sims)),float(np.linalg.norm(D.mean(0)))
par=[(s,w) for w,s in VAR.items() if w.endswith("り")]
pos,n,mc,L=loo_stats([En[vi[b]]-En[vi[a]] for a,b in par])
print(f"[実測] ABAB→ABり  n={n} 同方向 {pos}/{n} ({pos/n:.0%}) 平均cos {mc:+.3f} 平均差分長 {L:.3f}")

# 対照1: 頻度比をマッチさせた無関係対
rng=np.random.default_rng(11)
ratios=[(freq[b]+1)/(freq[a]+1) for a,b in par]
fr=np.array([freq[w] for w in vocab],dtype=float)
res=[]
for t in range(300):
    D=[]
    for r,(a0,b0) in zip(ratios,par):
        for _ in range(40):
            i=rng.integers(len(vocab)); j=rng.integers(len(vocab))
            if i==j: continue
            rr=(fr[j]+1)/(fr[i]+1)
            if 0.6*r<rr<1.7*r and abs(math.log((fr[i]+1)/(freq[a0]+1)))<1.2: break
        D.append(En[j]-En[i])
    res.append(loo_stats(D))
p_=np.array([r[0]/r[1] for r in res]); m_=np.array([r[2] for r in res]); l_=np.array([r[3] for r in res])
print(f"[対照1 頻度比マッチ無関係対] 同方向率 {p_.mean():.0%}±{p_.std():.0%}  平均cos {m_.mean():+.3f}±{m_.std():.3f}  差分長 {l_.mean():.3f}±{l_.std():.3f}")
print(f"  → 実測の z: 同方向率 {(pos/n-p_.mean())/p_.std():+.2f} / 平均cos {(mc-m_.mean())/m_.std():+.2f} / 差分長 {(L-l_.mean())/l_.std():+.2f}")

# 対照2: ペアをシャッフル(ABAB と ABり の対応をランダム化・頻度分布は完全保存)
res2=[]
for t in range(300):
    bs=[b for a,b in par]; rng.shuffle(bs)
    D=[En[vi[b]]-En[vi[a]] for (a,_),b in zip(par,bs)]
    res2.append(loo_stats(D))
p2=np.array([r[0]/r[1] for r in res2]); m2=np.array([r[2] for r in res2]); l2=np.array([r[3] for r in res2])
print(f"[対照2 対応シャッフル(頻度分布保存)] 同方向率 {p2.mean():.0%}±{p2.std():.0%}  平均cos {m2.mean():+.3f}±{m2.std():.3f}  差分長 {l2.mean():.3f}±{l2.std():.3f}")
print(f"  → 実測の z: 同方向率 {(pos/n-p2.mean())/p2.std():+.2f} / 平均cos {(mc-m2.mean())/m2.std():+.2f} / 差分長 {(L-l2.mean())/l2.std():+.2f}")
print("\n※対照2 が高めに出るのは ABり 全体に共通の成分(形態そのものの効果)を含むため。")
print("  対照2 を上回る分だけが「語ごとに対応した」効果。")

# 追加: ABAB→ABん / ABAB→ABっと でも同方向か
for suf in ("ん","っ"):
    pp=[(s,w) for w,s in VAR.items() if w.endswith(suf) and not w.endswith("っと")]
    if len(pp)>=6:
        p3,n3,m3,l3=loo_stats([En[vi[b]]-En[vi[a]] for a,b in pp])
        # 「り」方向との一致
        Dr=np.array([En[vi[b]]-En[vi[a]] for a,b in par]); Dr=Dr/np.linalg.norm(Dr,axis=1,keepdims=True); dirr=Dr.mean(0); dirr/=np.linalg.norm(dirr)
        Ds=np.array([En[vi[b]]-En[vi[a]] for a,b in pp]); Ds=Ds/np.linalg.norm(Ds,axis=1,keepdims=True)
        agree=(Ds@dirr>0).sum()
        print(f"[汎化] ABAB→AB{suf}  n={n3} 同方向 {p3}/{n3}  「り」方向との一致 {agree}/{len(Ds)}  対: "+" ".join(f"{a}/{b}" for a,b in pp[:10]))
