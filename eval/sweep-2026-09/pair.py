# Paired item-level comparisons between non-baseline arms (ablation checks).
import sys; sys.path.insert(0,'.')
from harness import *
def load(rnd):
    rows=[]
    for p in glob.glob(f"{E}/judge/{rnd}_s*_*.txt"):
        if p.endswith('.map.json'): continue
        for r in parse_judge(p): rows.append(r)
    return rows
def item(rows,v,i,k='overall'):
    x=[r[k] for r in rows if r['variant']==v and r['item']==i]; return st.mean(x) if x else None
for rnd,a,b in [("R4","V8","V7"),("R4","V8","V6"),("R4","V7","V6"),("R5","V8","V9"),("R5","V8","V10"),("R5","V9","V10")]:
    rows=load(rnd); items=sorted({r['item'] for r in rows})
    d=[item(rows,a,i)-item(rows,b,i) for i in items if item(rows,a,i) is not None and item(rows,b,i) is not None]
    rng=random.Random(0); bs=sorted(st.mean(rng.choices(d,k=len(d))) for _ in range(4000))
    print(rnd,a,"-",b,f"{st.mean(d):+.2f} [{bs[100]:+.2f},{bs[3900]:+.2f}] n={len(d)}")
