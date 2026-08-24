# -*- coding: utf-8 -*-
import json,collections,math
import numpy as np
P=r"C:\Users\TETRUR~1\AppData\Local\Temp\claude\c---ClaudeCode\aed437ee-8fa1-4d66-ada4-4fb8f9ad255d\scratchpad"
d=json.load(open(P+r"\cooc.json",encoding="utf-8"))
def k2h(s): return "".join(chr(ord(c)-0x60) if "ァ"<=c<="ヴ" else c for c in s)
freq=collections.Counter(); ctx=collections.defaultdict(collections.Counter)
for w,c in d["freq"].items():
    h=k2h(w); freq[h]+=c
    for k,v in d["ctx"][w].items(): ctx[h][k]+=v
EXCLUDE=set("""いろいろ だんだん とうとう いよいよ なかなか わざわざ ますます しばしば たびたび まだまだ
おりおり ようよう よくよく いやいや もともと そうそう めいめい たまたま いちいち そもそも そこそこ
ろくろく おのおの もしもし みるみる つぎつぎ ただただ もろもろ まあまあ うすうす ついつい かずかず
やすやす またまた あらあら むざむざ おちおち ゆくゆく ながなが とびとび つらつら こうこう みちみち
あとあと みすみす ゆめゆめ おうおう きちきち よいよい へいへい はいはい ありあり まざまざ しげしげ
ほとほと いきいき のびのび まるまる しずしず おいおい つぶつぶ みずみず ふきふき うまうま おめおめ
あかあか つくつく""".split())
# ABAB(擬態語)
AB={w for w in freq if len(w)==4 and w[:2]==w[2:] and w not in EXCLUDE and freq[w]>=10}
# 変化形: 語幹が ABAB として独立に存在することを要件にする(自動 curation 規則)
VAR={}
for w in freq:
    if freq[w]>=8 and len(w) in (3,4) and w[:2]*2 in AB and w!=w[:2]*2:
        if w[2:] in ("り","ん","っ","っと","ーっ","ー"): VAR[w]=w[:2]*2
vocab=sorted(AB|set(VAR))
print(f"語彙: ABAB {len(AB)} + 変化形 {len(VAR)} = {len(vocab)}")
print(f"  変化形サンプル: {' '.join(list(VAR)[:24])}")

cv=collections.Counter()
for w in vocab:
    for k,v in ctx[w].items(): cv[k]+=v
cols=[c for c,n in cv.items() if n>=5]; ci={c:i for i,c in enumerate(cols)}
M=np.zeros((len(vocab),len(cols)))
for i,w in enumerate(vocab):
    for k,v in ctx[w].items():
        if k in ci: M[i,ci[k]]=v
tot=M.sum(); rs=M.sum(1,keepdims=True); cs=M.sum(0,keepdims=True)
with np.errstate(divide="ignore",invalid="ignore"):
    X=np.log((M*tot)/(rs*cs)); X[~np.isfinite(X)]=0; X[X<0]=0
U,Sv,Vt=np.linalg.svd(X,full_matrices=False); ev=(Sv**2)/(Sv**2).sum()
K=30; E=U[:,:K]*Sv[:K]; En=E/np.linalg.norm(E,axis=1,keepdims=True)
vi={w:i for i,w in enumerate(vocab)}
print(f"行列 {M.shape}  寄与率 d1-5 {ev[:5].sum():.1%} / d1-30 {ev[:30].sum():.1%}")
print("\n[次元の両極]")
for k in range(5):
    o=np.argsort(E[:,k])
    print(f"  d{k+1}({ev[k]:.1%}) +: {' '.join(vocab[i] for i in o[-7:][::-1])}")
    print(f"           -: {' '.join(vocab[i] for i in o[:7])}")

def loo(diffs,label):
    D=np.array(diffs); n=len(D)
    nz=np.linalg.norm(D,axis=1)>1e-9; D=D[nz]/np.linalg.norm(D[nz],axis=1,keepdims=True); n=len(D)
    pos=0; sims=[]
    for i in range(n):
        m=np.delete(D,i,axis=0).mean(0); m/=np.linalg.norm(m)
        s=float(D[i]@m); sims.append(s); pos+=s>0
    p=sum(math.comb(n,k) for k in range(pos,n+1))/2**n
    print(f"  {label}: n={n} 同方向 {pos}/{n} ({pos/n:.0%})  平均cos {np.mean(sims):+.3f}  片側二項 p={p:.4g}")
    return np.array(sims)

print("\n[O-1' 形態パラダイム ABAB → ABり]")
par=[(s,w) for w,s in VAR.items() if w.endswith("り")]
print("  対: "+" ".join(f"{a}/{b}" for a,b in par))
s1=loo([En[vi[b]]-En[vi[a]] for a,b in par],"ABAB→ABり の差分")
rng=np.random.default_rng(7); null=[]
for t in range(300):
    ia=rng.choice(len(vocab),len(par)); ib=rng.choice(len(vocab),len(par))
    D=En[ib]-En[ia]; nz=np.linalg.norm(D,axis=1)>1e-9; D=D[nz]/np.linalg.norm(D[nz],axis=1,keepdims=True)
    null.append(float(np.linalg.norm(D.mean(0))))
obs=None
D=np.array([En[vi[b]]-En[vi[a]] for a,b in par]); D=D/np.linalg.norm(D,axis=1,keepdims=True)
obs=float(np.linalg.norm(D.mean(0)))
print(f"  平均差分ベクトル長 実測 {obs:.3f} vs ランダム対 {np.mean(null):.3f}±{np.std(null):.3f} → z={(obs-np.mean(null))/np.std(null):+.2f}")
mean_dir=D.mean(0); mean_dir/=np.linalg.norm(mean_dir)
proj=X.shape and (En@mean_dir)
o=np.argsort(proj)
print(f"  この方向の +極: {' '.join(vocab[i] for i in o[-10:][::-1])}")
print(f"  この方向の -極: {' '.join(vocab[i] for i in o[:10])}")

print("\n[O-2' 濁音ミニマルペア(意味的に対応する対のみ人手選別)]")
CUR=[("きらきら","ぎらぎら"),("さらさら","ざらざら"),("からから","がらがら"),("ころころ","ごろごろ"),
     ("するする","ずるずる"),("くるくる","ぐるぐる"),("たらたら","だらだら"),("とろとろ","どろどろ"),
     ("とんとん","どんどん"),("はらはら","ばらばら"),("くらくら","ぐらぐら"),("きりきり","ぎりぎり")]
CUR=[(a,b) for a,b in CUR if a in vi and b in vi]
print("  対: "+" ".join(f"{a}/{b}" for a,b in CUR))
loo([En[vi[b]]-En[vi[a]] for a,b in CUR],"濁音化の差分")
