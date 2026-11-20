import json, statistics as st, sys
for A in sys.argv[1:]:
    c=json.load(open(f"{A}/results-{A}.json"))["cells"]
    for L,reps in c.items():
        reqs=[r[k] for r in reps for k in ("prime","measured")]
        pn=[q["timings"]["prompt_n"] for q in reqs]; cn=[q["timings"]["cache_n"] for q in reqs]
        so=[q["swapout_kib"] for q in reqs]; links=set(tuple(l) for q in reqs for l in q["prefill_pcie_links"])
        err=[q["error"] for q in reqs if q["error"]]
        void=[]
        if max(pn)-min(pn)>3: void.append("prompt_n spread %d"%(max(pn)-min(pn)))
        if max(cn)>16: void.append("cache_n %d"%max(cn))
        if max(so)>0: void.append("swapout")
        if any(l!=("3","16") for l in links): void.append("pcie %s"%links)
        if err: void.append("errors")
        empty=sum(1 for q in reqs if not q["answer_head"].strip())
        m=[r["measured"]["timings"] for r in reps]
        pp=[x["prompt_per_second"] for x in m]; tg=[x["predicted_per_second"] for x in m]
        acc=sum(x["draft_n_accepted"] for x in m)/max(1,sum(x["draft_n"] for x in m))
        print(f"{A} {L:>5}: prefill {st.mean(pp):6.1f} ({min(pp)}..{max(pp)})  decode {st.mean(tg):5.2f} ({min(tg)}..{max(tg)})  accept {acc:.2f}  pn {min(pn)}-{max(pn)} links {sorted(links)} empty {empty} void={void or 'no'}")
