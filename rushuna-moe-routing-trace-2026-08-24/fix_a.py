import os,sys,json
from collections import Counter,defaultdict
N_EXP=256; D=sys.argv[1]
WORK=['code','chat','longctx','odd']; HELD=['heldout_code','heldout_chat']
def load(p):
    dec=defaultdict(list)
    for line in open(p):
        f=line.strip().split(',')
        if len(f)<3: continue
        try: pos=int(f[0]); lay=int(f[1]); ids=[int(x) for x in f[2:] if x!='']
        except ValueError: continue
        if pos>=0 and ids: dec[lay].append(ids)
    return dec
def share(c,frac):
    tot=sum(c.values()); k=max(1,int(round(N_EXP*frac)))
    return 100.0*sum(v for _,v in c.most_common(k))/tot if tot else 0.0
print("=== (a) CORRECTED: per-layer concentration, then averaged over layers ===")
print("    (experts are layer-specific; pooling IDs across layers conflates them)")
print(f"{'workload':<14}{'top10%':>9}{'top25%':>9}{'top50%':>9}   | pooled-across-layers top10%")
res={}
for w in WORK+HELD:
    p=os.path.join(D,w+'.csv')
    if not os.path.exists(p): continue
    dec=load(p)
    pooled=Counter()
    per=[]
    for l,rows in dec.items():
        c=Counter()
        for ids in rows: c.update(ids)
        pooled.update(c)
        per.append((share(c,0.10),share(c,0.25),share(c,0.50)))
    m=[sum(x[i] for x in per)/len(per) for i in range(3)]
    res[w]={'perlayer':m,'pooled10':share(pooled,0.10)}
    print(f"{w:<14}{m[0]:>8.1f}%{m[1]:>8.1f}%{m[2]:>8.1f}%   | {share(pooled,0.10):>8.1f}%")
print("\n  uniform/flat reference: top10%=10.0%  top25%=25.0%  top50%=50.0%")
json.dump(res,open(os.path.join(D,'analysis_a_corrected.json'),'w'),indent=1)
