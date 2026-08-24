import re, glob, collections
import fugashi
tagger=fugashi.Tagger()
SEED="きらきら ぎらぎら さらさら ざらざら ころころ ごろごろ からから がらがら するする ずるずる とんとん どんどん ふらふら ぶらぶら くるくる ぐるぐる ばたばた ぱたぱた ちらちら にやにや ぞろぞろ すたすた よろよろ じろじろ そわそわ だらだら ぶるぶる はらはら うとうと ぶつぶつ もじもじ にこにこ じりじり ずんずん ばらばら ぐずぐず ちくちく ひらひら ぽかぽか ぴかぴか".split()
SEEDS=set(SEED)
files=sorted(glob.glob(r"C:\_ClaudeCode\kokoro-graph\data\bronze\*.txt"))[:200]
docs=[]
for f in files:
    t=open(f,encoding="utf-8").read()
    t=re.sub(r"《[^》]*》","",t);t=re.sub(r"［＃[^］]*］","",t);t=t.replace("｜","")
    docs.append(t)
print(f"標本 {len(docs)} 作品 / {sum(len(d) for d in docs):,} 字")

nxt=collections.Counter(); hit=collections.Counter()
verbwin=collections.Counter(); verbs_of=collections.defaultdict(collections.Counter)
ctx_of=collections.defaultdict(collections.Counter)
CONTENT={"動詞","形容詞","名詞","形状詞","副詞"}
for d in docs:
    for line in d.split("\n"):
        if not line.strip(): continue
        ws=list(tagger(line))
        surf=[w.surface for w in ws]
        for i,w in enumerate(ws):
            if w.surface in SEEDS:
                hit[w.surface]+=1
                if i+1<len(ws): nxt[surf[i+1]]+=1
                # 後方窓で最初の動詞/形容詞を探す
                found=None
                for k in range(1,6):
                    if i+k>=len(ws): break
                    p=ws[i+k].feature.pos1
                    if p in ("動詞","形容詞"):
                        found=k; verbs_of[w.surface][ws[i+k].feature.lemma or surf[i+k]]+=1; break
                verbwin[found if found else "なし"]+=1
                # 窓±5 の内容語(意味ベクトル素材)
                for k in range(max(0,i-5),min(len(ws),i+6)):
                    if k==i: continue
                    if ws[k].feature.pos1 in CONTENT:
                        ctx_of[w.surface][ws[k].feature.lemma or surf[k]]+=1
tot=sum(hit.values())
print(f"\nシード {len(SEEDS)} 語 / 出現延べ {tot:,}")
print(f"\n[直後の形態素] 上位15: " + "  ".join(f"{k}({v})" for k,v in nxt.most_common(15)))
print(f"\n[後方窓で最初の用言までの距離]")
for k in [1,2,3,4,5,"なし"]:
    v=verbwin.get(k,0); print(f"  {k}形態素: {v:5}  {v/tot:5.1%}")
cum=sum(verbwin.get(k,0) for k in (1,2,3))
print(f"  → 窓3以内で用言に到達: {cum:,} / {tot:,} = {cum/tot:.1%}")
print(f"\n[意味ベクトルの密度(窓±5 内容語)]")
rows=[(w,hit[w],len(ctx_of[w]),sum(ctx_of[w].values())) for w in sorted(hit,key=lambda x:-hit[x])]
print("  語        出現  異なり共起語  延べ")
for w,h,d,s in rows[:12]: print(f"  {w:8} {h:5} {d:8} {s:8}")
import statistics
print(f"  異なり共起語の中央値: {statistics.median([r[2] for r in rows])}  最小 {min(r[2] for r in rows)}")
print(f"\n[係り先用言の例]")
for w in ["きらきら","ばたばた","そわそわ","ざらざら","ぐるぐる"]:
    if verbs_of[w]: print(f"  {w}: " + " ".join(f"{k}({v})" for k,v in verbs_of[w].most_common(6)))
