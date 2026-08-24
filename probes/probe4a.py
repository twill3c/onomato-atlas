import re, glob, collections, json, sys
import fugashi
tagger=fugashi.Tagger()

PATS=[re.compile(r"([ぁ-ん]{2})\1"), re.compile(r"([ァ-ヴ]{2})\1"),
      re.compile(r"[ぁ-んァ-ヴ]{2}っと"), re.compile(r"[ぁ-んァ-ヴ]{2}り"),
      re.compile(r"[ぁ-んァ-ヴ]{2}ん"), re.compile(r"[ぁ-んァ-ヴ]{2}っ"),
      re.compile(r"[ぁ-んァ-ヴ]{2}ーっ"), re.compile(r"[ぁ-んァ-ヴ]{2}ー")]
OK_POS={"副詞","形状詞","感動詞","名詞"}
CONTENT={"動詞","形容詞","名詞","形状詞","副詞"}
LIGHT={"為る","成る","居る","有る","遣る","来る","行く","仕舞う","出来る","見る","言う","思う","成す","致す","下さる"}

def is_mimetic_form(s):
    return any(p.fullmatch(s) for p in PATS)

files=sorted(glob.glob(r"C:\_ClaudeCode\kokoro-graph\data\bronze\*.txt"))
freq=collections.Counter()
ctx=collections.defaultdict(collections.Counter)     # 窓±5 内容語
gov=collections.defaultdict(collections.Counter)     # 係り先用言(軽動詞除く)
pos_of=collections.defaultdict(collections.Counter)
examples=collections.defaultdict(list)
nchar=0
for fi,f in enumerate(files):
    t=open(f,encoding="utf-8").read()
    t=re.sub(r"《[^》]*》","",t);t=re.sub(r"［＃[^］]*］","",t);t=t.replace("｜","")
    nchar+=len(t)
    for line in t.split("\n"):
        if not line.strip(): continue
        ws=list(tagger(line))
        for i,w in enumerate(ws):
            s=w.surface
            if not (3<=len(s)<=4) or not is_mimetic_form(s): continue
            if w.feature.pos1 not in OK_POS: continue
            freq[s]+=1; pos_of[s][w.feature.pos1]+=1
            if len(examples[s])<3 and 8<len(line)<70: examples[s].append(line.strip())
            for k in range(1,6):
                if i+k>=len(ws): break
                p=ws[i+k].feature.pos1
                if p in ("動詞","形容詞"):
                    lem=ws[i+k].feature.lemma or ws[i+k].surface
                    if lem not in LIGHT: gov[s][lem]+=1
                    break
            for k in range(max(0,i-5),min(len(ws),i+6)):
                if k==i: continue
                if ws[k].feature.pos1 in CONTENT:
                    lem=ws[k].feature.lemma or ws[k].surface
                    if lem not in LIGHT: ctx[s][lem]+=1
    if fi%80==0: print(f"  ...{fi}/{len(files)}", file=sys.stderr)

keep={w:c for w,c in freq.items() if c>=5}
out={"nfiles":len(files),"nchar":nchar,
     "freq":keep,
     "pos":{w:dict(pos_of[w]) for w in keep},
     "ctx":{w:dict(ctx[w]) for w in keep},
     "gov":{w:dict(gov[w]) for w in keep},
     "ex":{w:examples[w] for w in keep}}
json.dump(out,open(r"C:\Users\TETRUR~1\AppData\Local\Temp\claude\c---ClaudeCode\aed437ee-8fa1-4d66-ada4-4fb8f9ad255d\scratchpad\cooc.json","w",encoding="utf-8"),ensure_ascii=False)
print(f"作品 {len(files)} / {nchar:,} 字")
print(f"擬態語候補(境界+POS+頻度>=5): {len(keep):,} 語 / 延べ {sum(keep.values()):,}")
byform=collections.Counter()
for w in keep:
    byform["ABAB" if PATS[0].fullmatch(w) or PATS[1].fullmatch(w) else
           "ABっと" if w.endswith("っと") else "ABり" if w.endswith("り") else
           "ABん" if w.endswith("ん") else "ABっ" if w.endswith("っ") else "ABー系"]+=1
print("形態別:", dict(byform))
