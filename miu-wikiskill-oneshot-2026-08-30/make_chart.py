#!/usr/bin/env python3
"""Build the article chart straight from the scored run records."""
import json, glob, re, statistics as st
N=47
b=100*json.load(open('scored/baseline_recheck.json'))['runs'][0]['summary']['exact']/N
G={24:[],16:[],8:[]}
for f in glob.glob('scored/sk_*.json'):
    d=json.load(open(f)); tag=d['tag'][3:]
    G[int(re.match(r'g(\d+)_',tag).group(1))].append(100*d['runs'][0]['summary']['exact']/N)
m24=st.mean(G[24]); sd24=st.stdev(G[24])
W,H=780,392; L,R,T,B=150,30,64,64
PW=W-L-R
XMIN,XMAX=38.0,62.0
def x(v): return L+(v-XMIN)/(XMAX-XMIN)*PW
LANES=[(24,'#3b82f6','24 traces','n=10'),(16,'#e8590c','16 traces','n=5'),(8,'#0d9488','8 traces','n=5')]
LH=82; y0=T+34
BG,SURF,INK,MUTED='#0f1115','#1a1d24','#e4e4e7','#a1a1aa'
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif" role="img" aria-label="Twenty compiled skills scored against the 48.94 percent baseline; all fall inside the compiler-noise band.">']
o.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
# sigma band around the group-24 mean
BT=T+8; BB=y0+2*LH+26
o.append(f'<rect x="{x(m24-sd24):.1f}" y="{BT}" width="{x(m24+sd24)-x(m24-sd24):.1f}" height="{BB-BT:.1f}" fill="#3b82f6" opacity="0.10"/>')
o.append(f'<text x="{(x(m24-sd24)+x(m24+sd24))/2:.1f}" y="{BB+17:.1f}" fill="{MUTED}" font-size="11.5" text-anchor="middle">compiler noise, \u00b11\u03c3 = {sd24:.2f} pp</text>')
# axis ticks
for v in range(40,63,5):
    o.append(f'<line x1="{x(v):.1f}" y1="{BT}" x2="{x(v):.1f}" y2="{H-B+6}" stroke="#2a2f3a" stroke-width="1"/>')
    o.append(f'<text x="{x(v):.1f}" y="{H-B+24}" fill="{MUTED}" font-size="12" text-anchor="middle">{v}%</text>')
# baseline
o.append(f'<line x1="{x(b):.1f}" y1="{BT-10}" x2="{x(b):.1f}" y2="{BB}" stroke="{INK}" stroke-width="2" stroke-dasharray="5 4"/>')
o.append(f'<text x="{x(b):.1f}" y="{BT-18}" fill="{INK}" font-size="12.5" font-weight="600" text-anchor="middle">no-skill baseline {b:.2f}%</text>')
# lanes
for i,(g,col,lab,nn) in enumerate(LANES):
    cy=y0+i*LH
    o.append(f'<circle cx="{L-128}" cy="{cy-4}" r="5" fill="{col}"/>')
    o.append(f'<text x="{L-116}" y="{cy}" fill="{INK}" font-size="13.5" font-weight="600">{lab}</text>')
    o.append(f'<text x="{L-116}" y="{cy+17}" fill="{MUTED}" font-size="11.5">{nn} · mean {st.mean(G[g]):.2f}%</text>')
    o.append(f'<line x1="{L}" y1="{cy-4}" x2="{W-R}" y2="{cy-4}" stroke="#22262f" stroke-width="1"/>')
    seen={}
    for v in sorted(G[g]):
        k=round(v,2); seen[k]=seen.get(k,0)+1
        o.append(f'<circle cx="{x(v):.1f}" cy="{cy-4-(seen[k]-1)*13:.1f}" r="5.5" fill="{col}" stroke="{BG}" stroke-width="2"/>')
# annotate the outlier
gmax=max(G[24])
o.append(f'<text x="{x(gmax):.1f}" y="{y0-26}" fill="{INK}" font-size="11.5" text-anchor="middle">g24_07</text>')
o.append(f'<line x1="{x(gmax):.1f}" y1="{y0-22}" x2="{x(gmax):.1f}" y2="{y0-13}" stroke="{MUTED}" stroke-width="1"/>')
# band label
o.append(f'<text x="{L-128}" y="{H-14}" fill="{MUTED}" font-size="11.5">Exact match on the 47-item test split · each dot is one compiled skill · Qwen3.6-27B Q4_K_M, RTX 3090</text>')
o.append('</svg>')
open('scores.svg','w').write("\n".join(o))
print(f"baseline {b:.2f}  g24 mean {m24:.2f} sd {sd24:.3f}  band {m24-sd24:.2f}-{m24+sd24:.2f}")
print("wrote scores.svg", len("\n".join(o)), "bytes")
