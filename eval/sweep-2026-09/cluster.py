# Re-test V8-V0 with the generation BATCH as the unit. One agent wrote every
# answer in a batch in a single pass, so items within a batch are not
# independent; an item-level bootstrap understates the variance.
import sys; sys.path.insert(0,'.')
from harness import *
def batches(rnd,split):
    ids=[i for i,it in ITEMS.items() if it['split']==split]
    return [ids[0::2], ids[1::2]] if split=='dev' else [ids]
def rows(rnd):
    out=[]
    for p in glob.glob(f"{E}/judge/{rnd}_s*_*.txt"):
        if p.endswith('.map.json'): continue
        s=int(re.search(r"_s(\d+)_",p).group(1))
        for r in parse_judge(p):
            if 'MISSING' in r['reason'].upper(): continue
            r['sample']=s; out.append(r)
    return out
def run(rnd,split,a,b):
    R=rows(rnd); d=[]
    for s in sorted({r['sample'] for r in R}):
        for bt in batches(rnd,split):
            bt=set(bt)
            xa=[r['overall'] for r in R if r['variant']==a and r['sample']==s and r['item'] in bt]
            xb=[r['overall'] for r in R if r['variant']==b and r['sample']==s and r['item'] in bt]
            if xa and xb: d.append(st.mean(xa)-st.mean(xb))
    m=st.mean(d); se=st.stdev(d)/len(d)**.5
    print(f"{rnd} {a}-{b}: batches={len(d)} diffs={[round(x,2) for x in d]} mean {m:+.2f} t={m/se:+.2f}")
    return d
allr=[]
for rnd in ("R4","R5"): allr+=run(rnd,'dev','V8','V0')
for rnd in ("HO","HS"): allr+=run(rnd,'heldout','V8','V0')
run("R4",'dev','V8','V7'); run("R5",'dev','V8','V9'); run("R5",'dev','V8','V10')
m=st.mean(allr); print("pooled V8-V0 batch units", len(allr), f"mean {m:+.2f}", "positive", sum(x>0 for x in allr))
