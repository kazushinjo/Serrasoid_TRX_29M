"""KiCad で手直しした回路図の部品の位置・向きを circuit.py の LAYOUT に取り込む

  python3 tools/import_layout.py [基準の回路図]

基準の回路図（省略時は git の HEAD の版）と、いまの kicad/Serrasoid_TRX.kicad_sch を比べ、
動いた部品だけを circuit.py の末尾の LAYOUT.update(...) に書き足す。
ブロックごとの座標のずれ（1 枚にまとめたときのずらし量）は、基準の回路図と LAYOUT から求める。
"""
import os, sys, subprocess, collections, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sx import parse, find, find1, unq
from circuit import parts, LAYOUT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = os.path.join(ROOT, 'kicad', 'Serrasoid_TRX.kicad_sch')

def syms(text):
    t = parse(text); r = {}
    for s in find(t, 'symbol'):
        ref = [unq(p[2]) for p in find(s, 'property') if unq(p[1]) == 'Reference'][0]
        if ref.startswith('#PWR'): continue
        u = int(find1(s, 'unit')[1]); at = find1(s, 'at')
        r['%s:%d' % (ref, u)] = (float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0)
    return r

def lay(key):
    ref, u = key.split(':')
    return LAYOUT.get(key) or (LAYOUT.get(ref) if u == '1' else None)

def main():
    base = open(sys.argv[1]).read() if len(sys.argv) > 1 else subprocess.run(
        ['git', 'show', 'HEAD:kicad/Serrasoid_TRX.kicad_sch'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    com, usr = syms(base), syms(open(SCH).read())
    blk = {p['ref']: p['block'] for p in parts}
    off = collections.defaultdict(collections.Counter)
    for k, v in com.items():
        l = lay(k)
        if l: off[blk[k.split(':')[0]]][(round(v[0] - l[0], 2), round(v[1] - l[1], 2))] += 1
    off = {b: c.most_common(1)[0][0] for b, c in off.items()}
    moved = [k for k in usr if k in com and usr[k] != com[k]]
    if not moved:
        print('動いた部品はない'); return
    order = ['%s:%d' % (p['ref'], u) for p in parts for u in range(1, 9) if '%s:%d' % (p['ref'], u) in moved]
    fmt = lambda v: ('%.2f' % v).rstrip('0').rstrip('.')
    lines = ['', '# KiCad で手直しした位置（%s に取り込み）' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'LAYOUT.update({']
    cur = None
    for k in order:
        b = blk[k.split(':')[0]]
        if b != cur: lines.append('    # ---- ' + b); cur = b
        x, y, r = usr[k]; dx, dy = off[b]
        lines.append("    '%s': (%s, %s, %d)," % (k, fmt(x - dx), fmt(y - dy), r))
    lines.append('})')
    open(os.path.join(ROOT, 'tools', 'circuit.py'), 'a').write('\n'.join(lines) + '\n')
    print('取り込み %d 個: %s' % (len(order), ' '.join(order)))

if __name__ == '__main__':
    main()
