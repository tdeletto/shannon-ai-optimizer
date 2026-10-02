import sys; sys.path.insert(0,'.')
from harness import *
rnd=sys.argv[1]; split=sys.argv[2]; vs=sys.argv[3].split(','); S=int(sys.argv[4])
ids=[i for i,it in ITEMS.items() if it['split']==split]
agg={}
for v in vs:
  for s in range(1,S+1):
    d={}
    for p in glob.glob(f"{E}/gen/{rnd}_{v}_s{s}_*.txt"): d.update(parse_gen(p))
    miss=[i for i in ids if i not in d]
    if miss: print("MISSING",v,s,miss)
    for i in ids:
      if i in d:
        for k,x in auto_metrics(d[i]).items(): agg.setdefault(v,{}).setdefault(k,[]).append(x)
for v in vs:
  print(v, {k: round(st.mean(x),2) for k,x in agg[v].items()}, "median words", st.median(agg[v]['words']))
