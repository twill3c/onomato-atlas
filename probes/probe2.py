import re, glob, collections
import fugashi
tagger = fugashi.Tagger()
files = sorted(glob.glob(r"C:\_ClaudeCode\kokoro-graph\data\bronze\*.txt"))[:100]
docs=[]
for f in files:
    t=open(f,encoding="utf-8").read()
    t=re.sub(r"《[^》]*》","",t); t=re.sub(r"［＃[^］]*］","",t); t=t.replace("｜","")
    docs.append(t)
T="\n".join(docs)
print(f"標本 {len(docs)} 作品 / {len(T):,} 字")

REP=re.compile(r"([ぁ-ん]{2})\1")
regex_types=collections.Counter(m.group(0) for m in REP.finditer(T))
print(f"\n正規表現のみ: 異なり {len(regex_types):,} / 延べ {sum(regex_types.values()):,}")

tok_types=collections.Counter(); pos_of=collections.defaultdict(collections.Counter)
for line in T.split("\n"):
    if not line.strip(): continue
    for w in tagger(line):
        s=w.surface
        if len(s)==4 and REP.fullmatch(s):
            tok_types[s]+=1
            pos_of[s][w.feature.pos1]+=1
print(f"語境界一致  : 異なり {len(tok_types):,} / 延べ {sum(tok_types.values()):,}")
lost=sum(regex_types.values())-sum(tok_types.values())
print(f"→ 語境界で落ちた延べ {lost:,} 件 = 正規表現ヒットの {lost/sum(regex_types.values()):.1%}")

print("\n[語境界で消える語(部分文字列の偽陽性)] 上位:")
gone=[(w,c-tok_types.get(w,0)) for w,c in regex_types.items()]
gone.sort(key=lambda x:-x[1])
print("  "+"  ".join(f"{w}({regex_types[w]}→{tok_types.get(w,0)})" for w,_ in gone[:18]))

print("\n[語境界一致の上位40 と 品詞]")
for w,c in tok_types.most_common(40):
    p=pos_of[w].most_common(1)[0]
    print(f"  {w:6} {c:5}  {p[0]}({p[1]/c:.0%})", end="\n" if list(tok_types).index(w)%2 else "")
print("\n[ABAB トークンの品詞分布(延べ)]")
allpos=collections.Counter()
for w in tok_types:
    for p,n in pos_of[w].items(): allpos[p]+=n
for p,n in allpos.most_common(): print(f"  {p:8} {n:6}  {n/sum(allpos.values()):.1%}")
