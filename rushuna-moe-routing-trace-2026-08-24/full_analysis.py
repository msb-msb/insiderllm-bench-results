#!/usr/bin/env python3
import os,sys,json
from collections import Counter,defaultdict,OrderedDict
N_EXP=256; TOPK=8
D=sys.argv[1]
WORK=['code','chat','longctx','odd']; HELD=['heldout_code','heldout_chat']

def load(p):
    dec=defaultdict(list); pre=defaultdict(Counter)
    for line in open(p):
        s=line.strip()
        if not s: continue
        f=s.split(',')
        try:
            pos=int(f[0]); lay=int(f[1]); ids=[int(x) for x in f[2:] if x!='']
        except ValueError: continue
        if not ids: continue
        if pos<0: pre[lay].update(ids)
        else: dec[lay].append(ids)
    return dec,pre

T={}
for w in WORK+HELD:
    p=os.path.join(D,w+'.csv')
    if os.path.exists(p):
        dec,pre=load(p); T[w]=(dec,pre)
        print(f"{w}: {len(dec[0])} tokens x {len(dec)} layers",flush=True)

def counts(dec):
    per={}; agg=Counter()
    for l,rows in dec.items():
        c=Counter()
        for ids in rows: c.update(ids)
        per[l]=c; agg.update(c)
    return per,agg

def share(c,frac):
    tot=sum(c.values());  k=max(1,int(round(N_EXP*frac)))
    return 100.0*sum(v for _,v in c.most_common(k))/tot if tot else 0.0

def static_hit(dec,prof):     # prof: layer->set
    h=t=0
    for l,rows in dec.items():
        s=prof.get(l,set())
        for ids in rows:
            for e in ids:
                t+=1
                if e in s: h+=1
    return 100.0*h/t if t else 0.0

def topS_profile(per,S): return {l:set(e for e,_ in c.most_common(S)) for l,c in per.items()}

def lru(rows,S):
    od=OrderedDict(); h=t=ins=0
    for ids in rows:
        for e in ids:
            t+=1
            if e in od: h+=1; od.move_to_end(e)
            else:
                ins+=1
                if len(od)>=S: od.popitem(last=False)
                od[e]=1
    return h,t,ins

def lfu_decay(rows,S,alpha=0.98):
    sc={}; cache=set(); h=t=ins=0; scale=1.0
    for step,ids in enumerate(rows):
        scale*=alpha
        if scale<1e-12:
            for k in sc: sc[k]/=scale
            scale=1.0
        inc=1.0/scale
        for e in ids:
            t+=1; sc[e]=sc.get(e,0.0)+inc
            if e in cache: h+=1
            elif len(cache)<S: cache.add(e); ins+=1
            else:
                v=min(cache,key=lambda x:sc.get(x,0.0))
                if sc[e]>sc.get(v,0.0): cache.discard(v); cache.add(e); ins+=1
    return h,t,ins

def reelect(rows,S,warm,K=32,alpha=0.98):
    sc={e:float(c) for e,c in warm.items()}
    cache=set(e for e,_ in sorted(sc.items(),key=lambda kv:-kv[1])[:S])
    h=t=ins=0; scale=1.0
    for step,ids in enumerate(rows,1):
        scale*=alpha
        if scale<1e-12:
            for k in sc: sc[k]/=scale
            scale=1.0
        inc=1.0/scale
        for e in ids:
            t+=1; sc[e]=sc.get(e,0.0)+inc
            if e in cache: h+=1
        if step%K==0:
            new=set(e for e,_ in sorted(sc.items(),key=lambda kv:-kv[1])[:S])
            ins+=len(new-cache); cache=new
    return h,t,ins

R={}
PER={}; AGG={}; PRE={}
for w,(dec,pre) in T.items():
    per,agg=counts(dec); PER[w]=per; AGG[w]=agg; PRE[w]=pre

print("\n=== (a) LONG-RUN DISTRIBUTION (decode, aggregate over 40 layers) ===")
print(f"{'workload':<14}{'top10%':>9}{'top25%':>9}{'top50%':>9}{'flat=':>8}")
R['dist']={}
for w in WORK+HELD:
    if w not in AGG: continue
    a=[share(AGG[w],f) for f in (0.10,0.25,0.50)]
    R['dist'][w]=a
    print(f"{w:<14}{a[0]:>8.1f}%{a[1]:>8.1f}%{a[2]:>8.1f}%{'10/25/50':>8}")

print("\n  per-layer top10% share, aggregated across the 4 trace workloads:")
pl=defaultdict(list)
for w in WORK:
    if w not in PER: continue
    for l,c in PER[w].items(): pl[l].append(share(c,0.10))
lay_sorted=sorted(pl)
R['perlayer_top10']={l:sum(v)/len(v) for l,v in pl.items()}
line=""
for l in lay_sorted:
    m=sum(pl[l])/len(pl[l])
    line+=f"L{l:02d}:{m:.0f}% "
    if (l+1)%8==0: print("   "+line); line=""
if line: print("   "+line)

print("\n=== (b) STATIC TOP-S ORACLE HIT RATE (per-layer profile from same trace) ===")
Ss=[16,32,64,112,128]
print(f"{'workload':<14}"+"".join(f"S={s:<8}" for s in Ss))
R['oracle']={}
for w in WORK+HELD:
    if w not in T: continue
    row=[]
    for S in Ss:
        row.append(static_hit(T[w][0], topS_profile(PER[w],S)))
    R['oracle'][w]=row
    print(f"{w:<14}"+"".join(f"{v:>6.1f}%   " for v in row))

print("\n=== (c) DISTINCT EXPERTS IN A SLIDING WINDOW (mean over layers+workloads) ===")
R['window']={}
for W in (10,50,200):
    vals=[]
    for w in WORK:
        if w not in T: continue
        for l,rows in T[w][0].items():
            if len(rows)<W: continue
            step=max(1,len(rows)//60)
            for i in range(0,len(rows)-W+1,step):
                s=set()
                for ids in rows[i:i+W]: s.update(ids)
                vals.append(len(s))
    m=sum(vals)/len(vals)
    R['window'][W]=m
    print(f"  window {W:>3} tokens ({W*TOPK:>5} activations): {m:6.1f} distinct experts of 256  ({100*m/N_EXP:.1f}%)")

print("\n=== (d) POLICY COMPARISON (mean hit % over 40 layers, trace workloads) ===")
R['policy']={}
for S in (64,112):
    print(f"\n  --- S={S} slots/layer ---")
    print(f"  {'workload':<14}{'oracle':>9}{'prefill':>9}{'LRU':>9}{'LFU-dec':>9}{'reelect32':>11}")
    for w in WORK:
        if w not in T: continue
        dec,pre=T[w]
        o=static_hit(dec, topS_profile(PER[w],S))
        pf=static_hit(dec, {l:set(e for e,_ in pre[l].most_common(S)) for l in dec})
        hs=ts=0; hs2=ts2=0; hs3=ts3=0
        for l,rows in dec.items():
            a,b,_=lru(rows,S); hs+=a; ts+=b
            a,b,_=lfu_decay(rows,S); hs2+=a; ts2+=b
            a,b,_=reelect(rows,S,pre[l]); hs3+=a; ts3+=b
        vals=[o,pf,100*hs/ts,100*hs2/ts2,100*hs3/ts3]
        R['policy'][f"{w}_S{S}"]=vals
        print(f"  {w:<14}{vals[0]:>8.1f}%{vals[1]:>8.1f}%{vals[2]:>8.1f}%{vals[3]:>8.1f}%{vals[4]:>10.1f}%")

print("\n=== (e) CROSS-WORKLOAD TRANSFER (S=112) ===")
S=112
profs={w:topS_profile(PER[w],S) for w in WORK if w in PER}
print("  top-112 set overlap (mean over layers, % of 112 shared):")
ws=[w for w in WORK if w in profs]
print("            "+"".join(f"{x:>12}" for x in ws))
R['overlap']={}
for a in ws:
    line=f"  {a:<10}"
    for b in ws:
        ov=sum(len(profs[a][l]&profs[b][l]) for l in profs[a])/len(profs[a])
        R['overlap'][f"{a}->{b}"]=100*ov/S
        line+=f"{100*ov/S:>11.1f}%"
    print(line)
print("\n  hit rate of profile(row) applied to workload(col), and merged/held-out:")
merged={}
for l in PER[ws[0]]:
    m=Counter()
    for w in ws: m.update(PER[w][l])
    merged[l]=set(e for e,_ in m.most_common(S))
print("            "+"".join(f"{x:>12}" for x in ws+HELD))
R['transfer']={}
for a in ws+['MERGED']:
    prof=merged if a=='MERGED' else profs[a]
    line=f"  {a:<10}"
    for b in ws+HELD:
        if b not in T: line+=f"{'-':>12}"; continue
        v=static_hit(T[b][0],prof); R['transfer'][f"{a}->{b}"]=v
        line+=f"{v:>11.1f}%"
    print(line)

print("\n=== (f) PER-LAYER STRUCTURE: oracle hit @S=112, early/mid/late ===")
R['layerband']={}
for w in WORK:
    if w not in T: continue
    bands={'L0-12':range(0,13),'L13-26':range(13,27),'L27-39':range(27,40)}
    out=[]
    for bn,rng in bands.items():
        h=t=0
        prof=topS_profile(PER[w],112)
        for l in rng:
            if l not in T[w][0]: continue
            for ids in T[w][0][l]:
                for e in ids:
                    t+=1
                    if e in prof[l]: h+=1
        out.append(100*h/t if t else 0)
    R['layerband'][w]=out
    print(f"  {w:<14} early {out[0]:5.1f}%   mid {out[1]:5.1f}%   late {out[2]:5.1f}%")

print("\n=== (g) IS -n 512 ENOUGH? oracle@112 from first N tokens, evaluated on full trace ===")
R['ntok']={}
for w in ['code','chat']:
    if w not in T: continue
    row=[]
    for N in (256,512,1024,2048):
        per_n={}
        for l,rows in T[w][0].items():
            c=Counter()
            for ids in rows[:N]: c.update(ids)
            per_n[l]=c
        row.append(static_hit(T[w][0], topS_profile(per_n,112)))
    R['ntok'][w]=row
    print(f"  {w:<14}"+"".join(f"n={n}:{v:5.1f}%  " for n,v in zip((256,512,1024,2048),row)))

print("\n=== (h) DEGENERACY CHECK: repeated expert-tuple rate (layer 20) ===")
R['degen']={}
for w in WORK+HELD:
    if w not in T: continue
    rows=[tuple(x) for x in T[w][0][20]]
    c=Counter(rows)
    rep=100.0*(1-len(c)/len(rows))
    R['degen'][w]=rep
    print(f"  {w:<14} distinct tuples {len(c):>5}/{len(rows)}  repeat rate {rep:5.1f}%")

json.dump(R,open(os.path.join(D,'analysis.json'),'w'),indent=1)
print("\nwrote analysis.json")
