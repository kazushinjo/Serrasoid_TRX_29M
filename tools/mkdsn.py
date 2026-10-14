"""KiCad が書き出した DSN を Freerouting 用に直す
- 内層 GND1/GND2 を power 層にする（信号を引かせない。GND は内層ベタでつながる）
- ネットごとの線幅クラスを作る
"""
import re, sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netclass import width_of
from circuit import parts
src, dst = sys.argv[1:3]
s = open(src).read()
# DSN のネット名（回路図の自動名）→ circuit.py のネット名
pinnet = {(p['ref'], k): n for p in parts for k, n in p['pins'].items() if n}
cname = {}
for m in re.finditer(r'\(net ("[^"]*"|\S+)\s+\(pins ([^)]*)\)', s):
    for pin in m.group(2).split():
        ref, num = pin.rsplit('-', 1)
        if (ref, num) in pinnet: cname[m.group(1).strip('"')] = pinnet[(ref, num)]; break
for L in ('GND1', 'GND2'):
    s = s.replace('(layer %s\n      (type signal)' % L, '(layer %s\n      (type power)' % L)
i = s.index('(class kicad_default'); j = s.index('(circuit', i)
names = re.findall(r'"[^"]*"|[^\s()]+', s[i + len('(class kicad_default'):j])
nm = lambda t: t[1:-1] if t.startswith('"') else t
cls = {}
for t in names:
    cls.setdefault(int(round(width_of(cname.get(nm(t), nm(t))) * 1000)), []).append(t)
def block(name, lst, w):
    return ('(class %s %s\n      (circuit\n        (use_via "Via[0-3]_800:400_um")\n      )\n      (rule\n        (width %d)\n'
            '        (clearance 250)\n      )\n    )') % (name, ' '.join(lst), w)
k = s.index('(rule', j); e = s.index(')\n    )', k) + len(')\n    )')
s = s[:i] + '\n    '.join(block('kicad_default' if n == 0 else 'w%d' % w, l, w) for n, (w, l) in enumerate(sorted(cls.items()))) + s[e:]
# 基板端から 0.8mm 内側までしか配線させない
def inset(mt):
    v = [int(t) for t in mt.group(2).split()]
    xs, ys = v[0::2], v[1::2]; x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); d = 800
    pts = [(x1 - d, y0 + d), (x0 + d, y0 + d), (x0 + d, y1 - d), (x1 - d, y1 - d), (x1 - d, y0 + d)]
    return mt.group(1) + '  '.join('%d %d' % p for p in pts) + ')'
s = re.sub(r'(\(boundary\s+\(path pcb 0\s+)([-\d\s]+)\)', inset, s, count=1)
open(dst, 'w').write(s)
print('classes', {w: len(l) for w, l in sorted(cls.items())})
