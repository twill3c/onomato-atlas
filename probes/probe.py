import re, glob, collections, sys, json
files = sorted(glob.glob(r"C:\_ClaudeCode\kokoro-graph\data\bronze\*.txt"))
text_all = []
for f in files:
    try:
        t = open(f, encoding="utf-8").read()
    except Exception as e:
        continue
    # 青空文庫ヘッダ/フッタとルビ・注記を粗く除去
    t = re.sub(r"《[^》]*》", "", t)
    t = re.sub(r"［＃[^］]*］", "", t)
    t = re.sub(r"｜", "", t)
    text_all.append(t)
T = "\n".join(text_all)
print(f"作品数 {len(text_all)}  総文字数 {len(T):,}")

# ---- ABAB 反復型(ひらがな2モーラ反復)
rep = collections.Counter(re.findall(r"([ぁ-ん]{2})\1", T))
print(f"\n[ABAB型] 異なり語 {len(rep):,}  延べ {sum(rep.values()):,}")
for th in (1,3,10,30,100,300):
    print(f"  頻度>={th:<4}: {sum(1 for v in rep.values() if v>=th):,} 語")
print("\n  上位40:", "  ".join(f"{s*2}({c})" for s,c in rep.most_common(40)))

# ---- 語幹ごとの形態パラダイム(O-1 候補)
VOICED = str.maketrans("かきくけこさしすせそたちつてとはひふへほ","がぎぐげござじずぜぞだぢづでどばびぶべぼ")
stems = [s for s,c in rep.items() if c>=3]
forms = {}
for s in stems:
    v = {}
    for name,pat in [("ABAB",s+s),("ABっと",s+"っと"),("ABっ",s+"っ"),("ABり",s+"り"),("ABん",s+"ん"),("ABーっ",s+"ーっ")]:
        n = len(re.findall(re.escape(pat), T))
        if name=="ABっ": n -= len(re.findall(re.escape(s+"っと"), T))
        if n>0: v[name]=n
    if len(v)>=2: forms[s]=v
print(f"\n[O-1 形態パラダイム] 2形態以上を持つ語幹 {len(forms):,} 件(語幹頻度>=3 の {len(stems):,} 件中)")
for th in (3,4):
    print(f"  {th}形態以上: {sum(1 for v in forms.values() if len(v)>=th):,} 件")
rich = sorted(forms.items(), key=lambda kv:-len(kv[1]))[:12]
for s,v in rich:
    print(f"    {s}: " + " / ".join(f"{k.replace('AB',s)}={n}" for k,n in v.items()))

# ---- 濁音ミニマルペア(O-2 候補)
pairs=[]
for s,c in rep.items():
    d = s.translate(VOICED)
    if d!=s and d in rep:
        pairs.append((s,c,d,rep[d]))
pairs.sort(key=lambda p:-(p[1]+p[3]))
print(f"\n[O-2 濁音ミニマルペア] {len(pairs):,} 組(両側とも ABAB で出現)")
print("  上位20:", "  ".join(f"{a*2}({ac})/{b*2}({bc})" for a,ac,b,bc in pairs[:20]))
print(f"  両側とも頻度>=5: {sum(1 for a,ac,b,bc in pairs if ac>=5 and bc>=5):,} 組")
