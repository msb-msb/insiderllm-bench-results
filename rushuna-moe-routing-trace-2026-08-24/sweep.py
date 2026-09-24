import os,sys,json
from collections import Counter,defaultdict
N=256; D=sys.argv[1]
WORK=['code','chat','longctx','odd']
def load(p):
    dec=defaultdict(list)
    for line in open(p):
        f=line.strip().split(',')
        if len(f)<3: continue
        try: pos=int(f[0]); lay=int(f[1]); ids=[int(x) for x in f[2:] if x!='']
        except ValueError: continue
        if pos>=0 and ids: dec[lay].append(ids)
    return dec
Ss=[8,16,24,32,48,64,80,96,112,128,160,192,224]
PERE=1.8125  # MiB per expert per layer
print("=== Static top-S oracle hit vs slots, and marginal return ===")
print(f"{'S':>4}{'VRAM(GiB)':>11}{'%experts':>10}"+"".join(f"{w:>10}" for w in WORK)+f"{'mean':>9}{'d(hit)/d(8 slots)':>19}")
tr={w:load(os.path.join(D,w+'.csv')) for w in WORK if os.path.exists(os.path.join(D,w+'.csv'))}
per={w:{l:Counter([e for ids in rows for e in ids]) for l,rows in d.items()} for w,d in tr.items()}
prev=None; out={}
for S in Ss:
    row=[]
    for w in tr:
        prof={l:set(e for e,_ in c.most_common(S)) for l,c in per[w].items()}
        h=t=0
        for l,rows in tr[w].items():
            s=prof[l]
            for ids in rows:
                for e in ids:
                    t+=1
                    if e in s: h+=1
        row.append(100*h/t)
    m=sum(row)/len(row)
    vram=S*40*PERE/1024
    marg="" if prev is None else f"{(m-prev)/((S-prevS)/8):>17.2f}pp"
    out[S]={'mean':m,'per':row,'vram':vram}
    print(f"{S:>4}{vram:>10.2f}{100*S/N:>9.1f}%"+"".join(f"{v:>9.1f}%" for v in row)+f"{m:>8.1f}%{marg:>19}")
    prev=m; prevS=S
json.dump(out,open(os.path.join(D,'slot_sweep.json'),'w'),indent=1)
