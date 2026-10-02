import sys; sys.path.insert(0,'.')
from harness import *
rnd, split, vs, S, tags = sys.argv[1], sys.argv[2], sys.argv[3].split(','), int(sys.argv[4]), sys.argv[5].split(',')
ids=[i for i,it in ITEMS.items() if it['split']==split]
batches=[ids[0::2], ids[1::2]] if split=='dev' else [ids]
for t in tags:
  for s in range(1,S+1):
    for bi,b in enumerate(batches):
      p,out=judge_prompt(rnd,s,b,vs,t)
      fn=f"{E}/prompts/{rnd}/judge_{t}_s{s}_b{bi}.txt"; open(fn,'w').write(p); print(fn, len(p.split()))
