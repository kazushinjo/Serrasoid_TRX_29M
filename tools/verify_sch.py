"""回路図から書き出したネットリストが circuit.py の接続と同じか確かめる（ネット名ではなく、つながり方で比べる）"""
import os, sys, re, subprocess, tempfile, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from circuit import parts
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
out = os.path.join(tempfile.mkdtemp(), 'n.net')
subprocess.run([K, 'sch', 'export', 'netlist', '-o', out, os.path.join(ROOT, 'kicad', 'Serrasoid_TRX.kicad_sch')], check=True, capture_output=True)
s = open(out).read()
got = {}
for m in re.finditer(r'\(net\s+\(code "\d+"\)\s+\(name "((?:[^"\\]|\\.)*)"\)(.*?)(?=\(net\s+\(code|\Z)', s, re.S):
    for r, p in re.findall(r'\(ref "([^"]*)"\)\s*\(pin "([^"]*)"\)', m.group(2)): got[(r, p)] = m.group(1)
want = {}
for p in parts:
    if p['ref'].startswith('#'): continue
    for k, n in p['pins'].items(): want[(p['ref'], k)] = n
bad = 0
g2w = collections.defaultdict(set); w2g = collections.defaultdict(set)
for k, n in want.items():
    g = got.get(k)
    if n is None:
        if g and not g.startswith('unconnected'): print('NC のはずがつながっている', k, g); bad += 1
        continue
    if g is None: print('回路図にない', k, n); bad += 1; continue
    g2w[g].add(n); w2g[n].add(g)
for g, ws in g2w.items():
    if len(ws) > 1: print('ショート:', g, sorted(ws)); bad += 1
for n, gs in w2g.items():
    if len(gs) > 1: print('切れている:', n, sorted(gs)); bad += 1
print('照合 %d ピン、不一致 %d' % (len(want), bad))
sys.exit(1 if bad else 0)
