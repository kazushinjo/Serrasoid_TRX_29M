"""circuit.py から KiCad 回路図 kicad/Serrasoid_TRX.kicad_sch を作る

部品はブロックごとの枠の中に信号の順で並べ、各ピンの先にネットラベル（電源は電源記号）を付ける。
"""
import os, sys, uuid, re, copy, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sx import parse, dump, find, find1, unq, q, Sym
import libload
from circuit import parts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = 'Serrasoid_TRX'
LOCAL = os.path.join(ROOT, 'kicad', PROJ + '.kicad_sym')
S = Sym
U = lambda: q(str(uuid.uuid4()))
ROOT_UUID = '6a1c3f3e-29a0-4c55-9d1e-5e7a50000001'
POWER = {'GND', '+13V8', '+8V', '+5V', '+5VT', '+5VA', '+3V3S', '+3V3X', 'TX8V', 'RX8V'}
GRID = 2.54

def F(v):
    return S(('%.4f' % v).rstrip('0').rstrip('.'))

def snap(v):
    return round(v / GRID) * GRID

def libsym(lib_id):
    path = LOCAL if lib_id.startswith(PROJ + ':') else None
    s = libload.get(lib_id, path)
    s[1] = q(lib_id)
    return s

def bbox(sym, unit):
    """記号（unit）の外形 (xmin, ymin, xmax, ymax)、回路図座標（y 下向き）"""
    xs, ys = [], []
    for c in find(sym, 'symbol'):
        m = re.search(r'_(\d+)_(\d+)$', unq(c[1])); u = int(m.group(1))
        if u not in (0, unit): continue
        for g in c[2:]:
            if not isinstance(g, list): continue
            if g[0] == 'rectangle':
                for k in ('start', 'end'):
                    a = find1(g, k); xs.append(float(a[1])); ys.append(-float(a[2]))
            elif g[0] == 'polyline':
                for xy in find(find1(g, 'pts'), 'xy'): xs.append(float(xy[1])); ys.append(-float(xy[2]))
            elif g[0] == 'circle':
                a = find1(g, 'center'); r = float(find1(g, 'radius')[1])
                xs += [float(a[1]) - r, float(a[1]) + r]; ys += [-float(a[2]) - r, -float(a[2]) + r]
            elif g[0] == 'arc':
                for k in ('start', 'mid', 'end'):
                    a = find1(g, k); xs.append(float(a[1])); ys.append(-float(a[2]))
            elif g[0] == 'pin':
                at = find1(g, 'at'); xs.append(float(at[1])); ys.append(-float(at[2]))
    if not xs: return (-2.54, -2.54, 2.54, 2.54)
    return (min(xs), min(ys), max(xs), max(ys))

def text_w(s, size=1.27):
    return len(s) * size * 0.75 + 1.5

FREE = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # ピンの向き → ピンの外側（回路図座標）

items = []        # 回路図の要素（S 式）
lib_used = {}
pwr_n = [0]

def instance(lib_id, ref, value, fp, x, y, unit=1, rot=0, hide_ref=False):
    sym = lib_used.setdefault(lib_id, libsym(lib_id))
    props = {unq(p[1]): p for p in find(sym, 'property')}
    def pr(name, val, hide=False):
        p = props.get(name)
        ax, ay, aa = 0, 0, '0'
        if p:
            a = find1(p, 'at'); ax, ay = float(a[1]), float(a[2]); aa = str(a[3]) if len(a) > 3 else '0'
        e = [S('effects'), [S('font'), [S('size'), S('1.27'), S('1.27')]]]
        if p:
            pe = find1(p, 'effects'); j = find1(pe, 'justify') if pe else None
            if j: e.append(copy.deepcopy(j))
        r = [S('property'), q(name), q(val), [S('at'), F(x + ax), F(y - ay), S(aa)]]
        if hide: r.append([S('hide'), S('yes')])
        r.append(e)
        return r
    pins = libload.pins(sym)
    node = [S('symbol'), [S('lib_id'), q(lib_id)], [S('at'), F(x), F(y), S(str(rot))], [S('unit'), S(str(unit))],
            [S('exclude_from_sim'), S('no')], [S('in_bom'), S('no' if ref.startswith('#') else 'yes')],
            [S('on_board'), S('no' if ref.startswith('#') else 'yes')], [S('dnp'), S('no')], [S('uuid'), U()],
            pr('Reference', ref, hide_ref), pr('Value', value), pr('Footprint', fp, True), pr('Datasheet', '', True)]
    for num, v in pins.items():
        if v[6] in (0, unit): node.append([S('pin'), q(num), [S('uuid'), U()]])
    node.append([S('instances'), [S('project'), q(PROJ), [S('path'), q('/' + ROOT_UUID), [S('reference'), q(ref)], [S('unit'), S(str(unit))]]]])
    items.append(node)

def power(net, x, y, free):
    pwr_n[0] += 1
    ref = '#PWR%03d' % pwr_n[0]
    lib_id = 'power:GND' if net == 'GND' else PROJ + ':' + net
    native = 270 if net == 'GND' else 90           # 記号の本体がある向き（ライブラリ座標、y 上向き）
    want = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[free]   # 回路図の外側方向をライブラリ角度に
    rot = (want - native) % 360
    instance(lib_id, ref, net, '', x, y, 1, rot, hide_ref=True)

def label(net, x, y, free):
    ang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[free]
    just = [S('justify'), S('right' if ang in (180, 270) else 'left'), S('bottom')]
    items.append([S('label'), q(net), [S('at'), F(x), F(y), S(str(ang))],
                  [S('effects'), [S('font'), [S('size'), S('1.27'), S('1.27')]], just], [S('uuid'), U()]])

def noconn(x, y):
    items.append([S('no_connect'), [S('at'), F(x), F(y)], [S('uuid'), U()]])

def rect(x0, y0, x1, y1):
    items.append([S('rectangle'), [S('start'), F(x0), F(y0)], [S('end'), F(x1), F(y1)],
                  [S('stroke'), [S('width'), S('0.3')], [S('type'), S('dash')]], [S('fill'), [S('type'), S('none')]], [S('uuid'), U()]])

def text(t, x, y, size=3.0):
    items.append([S('text'), q(t), [S('exclude_from_sim'), S('no')], [S('at'), F(x), F(y), S('0')],
                  [S('effects'), [S('font'), [S('size'), F(size), F(size)], [S('bold'), S('yes')]], [S('justify'), S('left'), S('bottom')]], [S('uuid'), U()]])

def units_of(p):
    sym = lib_used.setdefault(p['sym'], libsym(p['sym']))
    pins = libload.pins(sym)
    missing = set(pins) - set(p['pins'])
    if missing: raise SystemExit('%s (%s): 未定義のピン %s' % (p['ref'], p['sym'], sorted(missing)))
    extra = set(p['pins']) - set(pins)
    if extra: raise SystemExit('%s (%s): 記号にないピン %s' % (p['ref'], p['sym'], sorted(extra)))
    us = sorted({v[6] for v in pins.values() if v[6] != 0}) or [1]
    return sym, pins, us

def cell(p, unit):
    """配置用の大きさ（ラベル込み）と、原点からのずれ"""
    sym, pins, _ = units_of(p)
    x0, y0, x1, y1 = bbox(sym, unit)
    l = r = t = b = 0
    for num, v in pins.items():
        if v[6] not in (0, unit): continue
        net = p['pins'][num]
        w = 3.0 if (net is None or net in POWER) else text_w(net)
        fx, fy = FREE[int(v[2]) % 360]
        if fx < 0: l = max(l, w)
        if fx > 0: r = max(r, w)
        if fy < 0: t = max(t, w if net not in POWER and net else 4)
        if fy > 0: b = max(b, w if net not in POWER and net else 4)
    # 値の文字ぶん右に余白
    r = max(r, text_w(p['value']) - (x1 - x0) / 2 + 2) if p['sym'].startswith('Device:') else r
    if p['sym'] == 'power:PWR_FLAG': r = max(r, 10)
    return (x0 - l - 2, y0 - t - 3, x1 + r + 2, y1 + b + 3)

def place_part(p, unit, x, y):
    sym, pins, _ = units_of(p)
    instance(p['sym'], p['ref'], p['value'], p['fp'], x, y, unit)
    for num, v in pins.items():
        if v[6] not in (0, unit): continue
        px, py = x + v[0], y - v[1]
        net = p['pins'][num]
        free = FREE[int(v[2]) % 360]
        if net is None: noconn(px, py)
        elif net in POWER: power(net, px, py, free)
        else: label(net, px, py, free)

def main():
    blocks = []
    for p in parts:
        if not blocks or blocks[-1][0] != p['block']: blocks.append((p['block'], []))
        blocks[-1][1].append(p)
    PAPER, PW, PH = 'A1', 841, 594
    MX, TOP = 20, 25
    colw = (PW - 2 * MX - 10) / 2
    # 2 列に積む（左: 電源・制御・受信、右: 変調・逓倍・送信音声・送信RF）
    cols = {0: ['電源', '制御', '受信'], 1: ['セラゾイド変調', '逓倍', '送信音声', '送信RF']}
    order = {b: (c, i) for c, bs in cols.items() for i, b in enumerate(bs)}
    ycur = {0: TOP, 1: TOP}
    for name, ps in sorted(blocks, key=lambda b: order[b[0]]):
        c = order[name][0]
        bx0 = MX + c * (colw + 10); by0 = ycur[c]
        x = bx0 + 4; y = by0 + 10; rowh = 0
        placed = []
        for p in ps:
            _, _, us = units_of(p)
            for u in us:
                cx0, cy0, cx1, cy1 = cell(p, u)
                w, h = cx1 - cx0, cy1 - cy0
                if x + w > bx0 + colw - 4:
                    x = bx0 + 4; y += rowh; rowh = 0
                ox, oy = snap(x - cx0), snap(y - cy0)
                placed.append((p, u, ox, oy))
                x += w; rowh = max(rowh, h)
        y += rowh
        rect(bx0, by0, bx0 + colw, y + 4)
        text(name, bx0 + 3, by0 + 7)
        for p, u, ox, oy in placed: place_part(p, u, ox, oy)
        ycur[c] = y + 12
    if max(ycur.values()) > PH - 15:
        print('警告: 用紙に収まらない', ycur)
    today = datetime.date.today().isoformat()
    sch = [S('kicad_sch'), [S('version'), S('20260306')], [S('generator'), q('eeschema')], [S('generator_version'), q('10.0')],
           [S('uuid'), q(ROOT_UUID)], [S('paper'), q(PAPER)],
           [S('title_block'), [S('title'), q('Serrasoid TRX 29M（セラゾイド変調 29MHz FM 10W トランシーバ）')], [S('date'), q(today)],
            [S('rev'), q('1.0')], [S('company'), q('JA6FUF')]],
           [S('lib_symbols')] + list(lib_used.values())] + items + [
           [S('sheet_instances'), [S('path'), q('/'), [S('page'), q('1')]]], [S('embedded_fonts'), S('no')]]
    out = os.path.join(ROOT, 'kicad', PROJ + '.kicad_sch')
    open(out, 'w').write(dump(sch) + '\n')
    print('wrote', out, len(items), 'items', ycur)

if __name__ == '__main__':
    main()
