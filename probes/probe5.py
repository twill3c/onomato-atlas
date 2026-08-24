# -*- coding: utf-8 -*-
import json,re,collections,math
import numpy as np
P=r"C:\Users\TETRUR~1\AppData\Local\Temp\claude\c---ClaudeCode\aed437ee-8fa1-4d66-ada4-4fb8f9ad255d\scratchpad"
d=json.load(open(P+r"\cooc.json",encoding="utf-8"))

# ---- 1. 表記ゆれ統合(カタカナ→ひらがな)
def kata2hira(s): return "".join(chr(ord(c)-0x60) if "ァ"<=c<="ヴ" else c for c in s)
freq=collections.Counter(); ctx=collections.defaultdict(collections.Counter); gov=collections.defaultdict(collections.Counter)
for w,c in d["freq"].items():
    h=kata2hira(w); freq[h]+=c
    for k,v in d["ctx"][w].items(): ctx[h][k]+=v
    for k,v in d["gov"][w].items(): gov[h][k]+=v
print(f"表記ゆれ統合: {len(d['freq'])} → {len(freq)} 語(延べ {sum(freq.values()):,})")

# ---- 2. curation(暫定・要人手承認)
EXCLUDE=set("""いろいろ だんだん とうとう いよいよ なかなか わざわざ ますます しばしば たびたび
まだまだ おりおり ようよう よくよく いやいや もともと そうそう めいめい たまたま いちいち
そもそも そこそこ ろくろく おのおの もしもし みるみる つぎつぎ ただただ もろもろ まあまあ
うすうす ついつい かずかず やすやす またまた あらあら むざむざ おちおち ゆくゆく ながなが
とびとび つらつら こうこう みちみち あとあと みすみす ゆめゆめ おうおう きちきち よいよい
へいへい はいはい ありあり まざまざ しげしげ ほとほと いきいき のびのび まるまる しずしず
おいおい つぶつぶ みずみず ふきふき うまうま おめおめ のめのめ ぜひぜひ""".split())
KANJI_HINT="""色々 段々 到頭 愈々 中々 態々 益々 屡々 度々 未々 折々 漸々 能々 否々 元々 銘々 偶々 一々
其々 碌々 各々 見る見る 次々 唯々 諸々 数々 易々 又々 無慙々 落々 行々 長々 飛々 倩々 道々 後々
見す見す 努々 生々 伸々 丸々 静々 有り有り 目々 繁々 殆々"""
vocab=[w for w in freq if w not in EXCLUDE and freq[w]>=10]
print(f"暫定 curation 後(頻度>=10): {len(vocab)} 語  ※除外 {len(EXCLUDE)} 語は要人手承認")

# ---- 3. PPMI 行列
cvocab=collections.Counter()
for w in vocab:
    for k,v in ctx[w].items(): cvocab[k]+=v
cols=[c for c,n in cvocab.items() if n>=5]
ci={c:i for i,c in enumerate(cols)}
M=np.zeros((len(vocab),len(cols)))
for i,w in enumerate(vocab):
    for k,v in ctx[w].items():
        if k in ci: M[i,ci[k]]=v
tot=M.sum(); rs=M.sum(1,keepdims=True); cs=M.sum(0,keepdims=True)
with np.errstate(divide="ignore",invalid="ignore"):
    PPMI=np.log((M*tot)/(rs*cs)); PPMI[~np.isfinite(PPMI)]=0; PPMI[PPMI<0]=0
print(f"行列: {M.shape[0]} 語 × {M.shape[1]} 文脈語  非零率 {(M>0).mean():.2%}")

U,Sv,Vt=np.linalg.svd(PPMI,full_matrices=False)
ev=(Sv**2)/ (Sv**2).sum()
print("\n[寄与率] "+"  ".join(f"d{i+1}:{ev[i]:.1%}" for i in range(10)))
print(f"  累積 d1-5 {ev[:5].sum():.1%} / d1-10 {ev[:10].sum():.1%} / d1-30 {ev[:30].sum():.1%}")

K=30
E=U[:,:K]*Sv[:K]
En=E/np.linalg.norm(E,axis=1,keepdims=True)

print("\n[各次元の両極(語)と主要文脈語] — 事後解釈できるか")
for k in range(6):
    ordv=np.argsort(E[:,k])
    lo=[vocab[i] for i in ordv[:8]]; hi=[vocab[i] for i in ordv[-8:]][::-1]
    cordv=np.argsort(Vt[k]); clo=[cols[i] for i in cordv[:6]]; chi=[cols[i] for i in cordv[-6:]][::-1]
    print(f"  d{k+1} ({ev[k]:.1%})")
    print(f"    +: {' '.join(hi)}    | 文脈 {' '.join(chi)}")
    print(f"    -: {' '.join(lo)}    | 文脈 {' '.join(clo)}")

print("\n[最近傍(健全性チェック)]")
vi={w:i for i,w in enumerate(vocab)}
for w in ["きらきら","ぐるぐる","ざらざら","そわそわ","ばたばた","ふわふわ","どきどき","ぼろぼろ"]:
    if w not in vi: continue
    sim=En@En[vi[w]]; o=np.argsort(-sim)[1:7]
    print(f"  {w:6} → "+" ".join(f"{vocab[i]}({sim[i]:.2f})" for i in o))

# ---- 4. O-2' 濁音ペアの分布差ベクトルは揃うか
VOICE=str.maketrans("かきくけこさしすせそたちつてとはひふへほ","がぎぐげござじずぜぞだぢづでどばびぶべぼ")
pairs=[]
for w in vocab:
    if len(w)==4 and w[:2]==w[2:]:
        v=w[:2].translate(VOICE)*2
        if v!=w and v in vi: pairs.append((w,v))
print(f"\n[O-2' 濁音ペア] 語彙内で成立 {len(pairs)} 組: "+" ".join(f"{a}/{b}" for a,b in pairs))
def loo_test(diffs,label):
    D=np.array(diffs); D=D/np.linalg.norm(D,axis=1,keepdims=True)
    n=len(D); pos=0; sims=[]
    for i in range(n):
        others=np.delete(D,i,axis=0).mean(0)
        others/=np.linalg.norm(others)
        s=float(D[i]@others); sims.append(s); pos+= s>0
    p=sum(math.comb(n,k) for k in range(pos,n+1))/2**n
    print(f"  {label}: n={n}  同方向 {pos}/{n}  平均cos {np.mean(sims):+.3f}  片側二項p={p:.4g}")
    return pos,n,np.mean(sims)
if len(pairs)>=8:
    loo_test([En[vi[b]]-En[vi[a]] for a,b in pairs],"濁音化の差分ベクトル")
    rng=np.random.default_rng(0); idx=np.arange(len(vocab))
    rs_=[]
    for t in range(200):
        a=rng.choice(idx,len(pairs)); b=rng.choice(idx,len(pairs))
        D=En[b]-En[a]; D=D/np.linalg.norm(D,axis=1,keepdims=True)
        m=D.mean(0); rs_.append(float(np.linalg.norm(m)))
    obs=np.linalg.norm(np.array([ (En[vi[b]]-En[vi[a]])/np.linalg.norm(En[vi[b]]-En[vi[a]]) for a,b in pairs]).mean(0))
    print(f"  平均差分ベクトルの長さ 実測 {obs:.3f} vs ランダム対 {np.mean(rs_):.3f}±{np.std(rs_):.3f}  → z={(obs-np.mean(rs_))/np.std(rs_):+.2f}")

# ---- 5. O-1' 形態パラダイム
fam=collections.defaultdict(dict)
for w in vocab:
    if len(w)==4 and w[:2]==w[2:]: fam[w[:2]]["ABAB"]=w
for w in freq:
    if freq[w]>=10 and len(w)==3 and w[2] in "りん": fam[w[:2]]["AB"+w[2]]=w
par=[(v["ABAB"],v["ABり"]) for v in fam.values() if "ABAB" in v and "ABり" in v and v["ABり"] in freq]
par=[(a,b) for a,b in par if a in vi]
print(f"\n[O-1' ABAB→ABり パラダイム] {len(par)} 組: "+" ".join(f"{a}/{b}" for a,b in par))
