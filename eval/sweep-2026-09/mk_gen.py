import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *
rnd, split, variants, samples = sys.argv[1], sys.argv[2], sys.argv[3].split(','), int(sys.argv[4])
ids = [i for i,it in ITEMS.items() if it['split']==split]
if split=='dev':
    b1 = ids[0::2]; b2 = ids[1::2]; batches=[b1,b2]
else:
    batches=[ids]
os.makedirs(f"{E}/prompts/{rnd}", exist_ok=True)
for v in variants:
  for s in range(1,samples+1):
    for bi,b in enumerate(batches):
      p,out = gen_prompt(rnd,v,s,b)
      fn=f"{E}/prompts/{rnd}/gen_{v}_s{s}_b{bi}.txt"
      open(fn,'w').write(p)
      print(fn)
