import sys; sys.path.insert(0,'.')
from harness import *
from collections import defaultdict
rnd=sys.argv[1]; base=sys.argv[2] if len(sys.argv)>2 else 'V0'
rows=[]
for p in glob.glob(f"{E}/judge/{rnd}_s*_*.txt"):
    if p.endswith('.map.json'): continue
    s=int(re.search(r"_s(\d+)_",p).group(1)); jt=re.search(r"_s\d+_([a-z]+)_",p).group(1)
    for r in parse_judge(p): r.update(sample=s, judge=jt); rows.append(r)
# drop missing generations
missing=set()
for r in rows:
    if 'MISSING' in r['reason'].upper(): missing.add((r['item'],r['sample']))
for v in {r['variant'] for r in rows}:
    for smp in {r['sample'] for r in rows}:
        d={}
        for p in glob.glob(f"{E}/gen/{rnd}_{v}_s{smp}_*.txt"): d.update(parse_gen(p))
        for r in rows:
            if r['variant']==v and r['sample']==smp and r['item'] not in d: missing.add((r['item'],smp))
rows=[r for r in rows if (r['item'],r['sample']) not in missing]
vs=sorted({r['variant'] for r in rows})
print("rows",len(rows),"dropped",missing)
cell=defaultdict(list)
for r in rows: cell[(r['variant'],r['item'],r['sample'])].append(r)
def m(v,key,judge=None):
    x=[r[key] for r in rows if r['variant']==v and (judge is None or r['judge']==judge)]
    return round(st.mean(x),2)
print(f"{'var':6}{'overall':>8}{'opus':>7}{'sonnet':>7}{'correct':>8}{'concise':>8}{'fail%':>7}")
for v in vs:
    fr=100*st.mean([r['fail'] for r in rows if r['variant']==v])
    print(f"{v:6}{m(v,'overall'):>8}{m(v,'overall','opus'):>7}{m(v,'overall','sonnet'):>7}{m(v,'correct'):>8}{m(v,'concise'):>8}{fr:>7.1f}")
# paired vs base: unit = item (avg over samples & judges), bootstrap over items
items=sorted({r['item'] for r in rows})
def itemscore(v,i): 
    x=[r['overall'] for r in rows if r['variant']==v and r['item']==i]
    return st.mean(x) if x else None
rng=random.Random(0)
for v in vs:
    if v==base: continue
    d=[itemscore(v,i)-itemscore(base,i) for i in items if itemscore(v,i) is not None and itemscore(base,i) is not None]
    boots=sorted(st.mean(rng.choices(d,k=len(d))) for _ in range(4000))
    wins=sum(x>0.25 for x in d); losses=sum(x<-0.25 for x in d)
    print(f"{v} - {base}: mean {st.mean(d):+.2f}  95%CI [{boots[100]:+.2f},{boots[3900]:+.2f}]  items W/L {wins}/{losses} of {len(d)}")
# per category
cats=sorted({ITEMS[i]['cat'] for i in items})
print("\nper-category overall:")
print(f"{'cat':16}"+"".join(f"{v:>7}" for v in vs))
for c in cats:
    print(f"{c:16}"+"".join(f"{st.mean([r['overall'] for r in rows if r['variant']==v and ITEMS[r['item']]['cat']==c]):>7.2f}" for v in vs))
print("\nper-item overall:")
print(f"{'item':6}"+"".join(f"{v:>7}" for v in vs))
for i in items:
    print(f"{i:6}"+"".join(f"{itemscore(v,i):>7.2f}" for v in vs))
