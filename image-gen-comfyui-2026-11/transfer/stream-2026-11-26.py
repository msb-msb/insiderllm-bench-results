#!/usr/bin/env python3
"""Stream the image-gen lock's file table through Tamanna into LLM_repo (lock eaf6324d, G4 transfer rule).
curl runs on Tamanna and its output comes over ssh to Miu; nothing is written to Tamanna's disk. Tamanna hashes the
stream (tee -> sha256sum), Miu hashes the file from disk; both must equal the table's sha256 or the file is fetched
again (one retry). The HF token goes over ssh stdin as the curl header (-H @-), never in argv or on Tamanna's disk.
Stop: kill this process group (stop-stream.sh); remote curls die on the broken pipe."""
import json,os,subprocess,sys,hashlib,time,threading,queue,re
D=os.path.dirname(os.path.abspath(__file__))
M=json.load(open(os.path.join(D,'manifest-2026-11-26.json')))
ORDER=[5,6,7,8,9,10,11,12,13,16,15,14,17,18,19,20,21,22,35,36,37]+[1,2,3,4]+list(range(23,35))
TOK=open(os.path.expanduser('~/.cache/huggingface/token')).read().strip()
LOG=open(os.path.join(D,'stream-2026-11-26.log'),'a',buffering=1)
lk=threading.Lock()
def log(*a):
    with lk: LOG.write(time.strftime('%F %T ')+' '.join(map(str,a))+'\n')
def disk_sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<24),b''): h.update(b)
    return h.hexdigest()
def one(i):
    r=M[i-1]; pub,repo=r['repo'].split('/')
    dst=os.path.join(D,pub,repo,r['path']); ok=dst+'.sha256-verified'
    if os.path.exists(ok): log(f'#{i} skip (already verified)'); return True
    os.makedirs(os.path.dirname(dst),exist_ok=True)
    url=f"https://huggingface.co/{r['repo']}/resolve/{r['commit']}/{r['path']}"
    want=r['sha256']; assert want and re.fullmatch('[0-9a-f]{64}',want)
    for attempt in (1,2):
        t0=time.time(); part=dst+'.part'
        remote=f"bash -c 'set -o pipefail; curl -sSfL --retry 5 --retry-delay 10 -H @- \"{url}\" | tee >(sha256sum >&2)'"
        with open(part,'wb') as out:
            p=subprocess.run(['ssh','-o','ServerAliveInterval=30','tamanna',remote],input=f'Authorization: Bearer {TOK}\n'.encode(),stdout=out,stderr=subprocess.PIPE)
        err=p.stderr.decode(errors='replace'); hs=re.findall(r'\b[0-9a-f]{64}\b',err); th=hs[-1] if hs else None
        size=os.path.getsize(part); dt=time.time()-t0
        mh=disk_sha(part) if size==r['size'] else None
        good = p.returncode==0 and th==want and mh==want and size==r['size']
        log(f"#{i} try{attempt} rc={p.returncode} bytes={size}/{r['size']} {size/max(dt,1)/2**20:.1f}MiB/s tamanna={th} miu={mh} want={want} {'OK' if good else 'FAIL'} {r['repo']}/{r['path']}"+('' if good else ' err='+err.strip()[-300:].replace('\n',' | ')))
        if good:
            os.replace(part,dst)
            open(ok,'w').write(f"{want}  {os.path.basename(dst)}\ntamanna_stream={th}\nmiu_disk={mh}\nrepo={r['repo']}@{r['commit']}\nverified={time.strftime('%FT%T%z')}\n")
            return True
        if p.returncode<0 or p.returncode==255: break   # killed or ssh gone: don't retry
    return False
q=queue.Queue(); [q.put(i) for i in ORDER]
res={}
def w():
    while True:
        try: i=q.get_nowait()
        except queue.Empty: return
        res[i]=one(i)
log('START', len(ORDER),'files, workers', sys.argv[1] if len(sys.argv)>1 else 4)
ts=[threading.Thread(target=w) for _ in range(int(sys.argv[1]) if len(sys.argv)>1 else 4)]
[t.start() for t in ts]; [t.join() for t in ts]
bad=[i for i in ORDER if not res.get(i)]
log('DONE ok=',len(ORDER)-len(bad),'fail=',bad)
