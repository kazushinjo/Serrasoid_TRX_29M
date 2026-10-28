"""circuit.py から KiCad の回路図 kicad/Serrasoid_TRX.kicad_sch（1 枚）を作る

- 機能ブロックごとに枠で囲んで並べる
- ブロックの中は、つながる部品が近くに来るように置き（place.py）、ピンの間を直角の線で結ぶ
- 電源・GND は電源記号、ブロックをまたぐ信号は同じ名前のグローバルラベル
"""
import os, sys, uuid, re, copy, datetime, heapq, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sx import parse, dump, find, find1, unq, q, Sym
import libload
from circuit import parts
try:
    from circuit import LAYOUT
except ImportError:
    LAYOUT = {}
from place import Placer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = 'Serrasoid_TRX'
LOCAL = os.path.join(ROOT, 'kicad', PROJ + '.kicad_sym')
S = Sym
NS = uuid.UUID('6a1c3f3e-29a0-4c55-9d1e-5e7a50000000')
ROOT_UUID = '6a1c3f3e-29a0-4c55-9d1e-5e7a50000001'
# GND だけは電源記号（GND 記号）でつなぐ。ほかの電源は線で結び、名前を示すため出どころに電源記号を 1 つ置く
POWER = {'GND'}
RAILS = {'+13V8', '+8V', '+5V', '+5VT', '+5VA', '+3V3S', '+3V3X', 'TX8V', 'RX8V'}
NAME_PIN = {}          # 電源の名前を示す電源記号を置くピン {net: (ref, pin)}
NAME_UP = set()
def pick_name_pins():
    """電源の名前を示す電源記号を置くピン: レギュレータの出力 → コネクタ → リレー → その他（PWR_FLAG は使わない）"""
    cand = {}
    for p in parts:
        if p['sym'] == 'power:PWR_FLAG': continue
        pins = libload.pins(libsym(p['sym']))
        for num, net in p['pins'].items():
            if net not in RAILS: continue
            # ピンが密に並ぶ IC（XIAO など）は横から線を入れにくいので後回し
            rank = 0 if (pins[num][5] == 'power_out' and len(pins) <= 3) else 1 if p['sym'].startswith('Connector') \
                else 2 if p['sym'].startswith('Relay') else 3
            if net not in cand or rank < cand[net][0]: cand[net] = (rank, p['ref'], num)
    for net, (rank, ref, num) in cand.items():
        NAME_PIN[net] = (ref, num)
        if rank == 0: NAME_UP.add(net)        # レギュレータの出力だけ記号を上に立てる（コネクタはピンが並ぶので外向きのまま）

# 機能ブロック → シートのファイル名（並び順 = ページ順）
SHEETS = [('電源', 'power'), ('制御', 'control'), ('セラゾイド変調', 'modulator'), ('逓倍', 'multiplier'), ('PLL', 'pll'),
          ('送信音声', 'txaudio'), ('送信RF', 'txrf'), ('受信', 'rx')]
PAPERS = [('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594)]
RG = 1.27            # 配線の格子
U = lambda: q(str(uuid.uuid4()))
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

def name_dir(o, net=None):
    """電源の名前を示す電源記号の向き: レギュレータの横向きの出力では上に立てる（右・左の線をふさがない）"""
    return (0, -1) if (o[1] == 0 and (net is None or net in NAME_UP)) else o

def sheet_uuid(block):
    return str(uuid.uuid5(NS, 'sheet:' + block))

def sym_uuid(ref, unit):
    return str(uuid.uuid5(NS, '%s:%d' % (ref, unit)))

def F(v):
    return S(('%.4f' % v).rstrip('0').rstrip('.'))

# ---------------------------------------------------------------- 記号の形
_lib = {}
def libsym(lib_id):
    if lib_id not in _lib:
        s = libload.get(lib_id, LOCAL if lib_id.startswith(PROJ + ':') else None)
        s[1] = q(lib_id); _lib[lib_id] = s
    return _lib[lib_id]

def rot(lx, ly, r):
    """ライブラリ座標（y 上向き）を角度 r で回し、回路図座標（y 下向き）のずれにする"""
    c, s = round(math.cos(math.radians(r))), round(math.sin(math.radians(r)))
    return (lx * c - ly * s, -(lx * s + ly * c))

DIRV = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}   # ライブラリ角度 → 回路図の単位ベクトル
ANG = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}

def body(sym, unit):
    """図形（ピンを除く）の外接矩形、ライブラリ座標"""
    xs, ys = [], []
    for c in find(sym, 'symbol'):
        u = int(re.search(r'_(\d+)_(\d+)$', unq(c[1])).group(1))
        if u not in (0, unit): continue
        for g in c[2:]:
            if not isinstance(g, list): continue
            if g[0] == 'rectangle':
                for k in ('start', 'end'): a = find1(g, k); xs.append(float(a[1])); ys.append(float(a[2]))
            elif g[0] == 'polyline':
                for xy in find(find1(g, 'pts'), 'xy'): xs.append(float(xy[1])); ys.append(float(xy[2]))
            elif g[0] == 'circle':
                a = find1(g, 'center'); r = float(find1(g, 'radius')[1])
                xs += [float(a[1]) - r, float(a[1]) + r]; ys += [float(a[2]) - r, float(a[2]) + r]
            elif g[0] == 'arc':
                for k in ('start', 'mid', 'end'): a = find1(g, k); xs.append(float(a[1])); ys.append(float(a[2]))
    if not xs: return (-1.27, -1.27, 1.27, 1.27)
    return (min(xs), min(ys), max(xs), max(ys))

class Unit:
    """回路図に置く 1 個分（多ユニット部品は 1 ユニット）"""
    def __init__(self, p, unit):
        self.p, self.unit = p, unit
        self.ref = p['ref']; self.key = '%s:%d' % (self.ref, unit)
        self.sym = libsym(p['sym'])
        allp = libload.pins(self.sym)
        self.pins = {k: v for k, v in allp.items() if v[6] in (0, unit)}
        self.body = body(self.sym, unit)
        self.two = len(allp) == 2
        self.pos, self.r = None, 0
    def n_pins_total(self):
        return len(libload.pins(self.sym))
    def pin_end(self, num, pos=None, r=None):
        pos = pos or self.pos; r = self.r if r is None else r
        v = self.pins[num]; dx, dy = rot(v[0], v[1], r)
        return (pos[0] + dx, pos[1] + dy)
    def pin_out(self, num, r=None):
        """ピン先から外へ向かう単位ベクトル（回路図座標）"""
        r = self.r if r is None else r
        return DIRV[int(self.pins[num][2] + 180 + r) % 360]
    def pin_line(self, num):
        """ピンの線上の点（先端を除く）"""
        v = self.pins[num]; e = self.pin_end(num); o = self.pin_out(num)
        n = int(round(v[3] / RG))
        return [(e[0] - o[0] * RG * i, e[1] - o[1] * RG * i) for i in range(1, n + 1)]
    def body_rect(self, pos=None, r=None):
        pos = pos or self.pos; r = self.r if r is None else r
        x0, y0, x1, y1 = self.body
        pts = [rot(x, y, r) for x, y in ((x0, y0), (x1, y1))]
        return (pos[0] + min(p[0] for p in pts), pos[1] + min(p[1] for p in pts),
                pos[0] + max(p[0] for p in pts), pos[1] + max(p[1] for p in pts))
    def footprint_box(self, r):
        """配置用の大きさ（ピン先・電源記号・文字の余白込み）、原点からの相対"""
        b = self.body_rect((0, 0), r)
        xs, ys = [b[0], b[2]], [b[1], b[3]]
        for num in self.pins:
            e = self.pin_end(num, (0, 0), r); o = self.pin_out(num, r)
            net = self.p['pins'][num]
            ext = 6.35 if (net in POWER or NAME_PIN.get(net) == (self.ref, num)) else 1.27
            xs += [e[0], e[0] + o[0] * ext]; ys += [e[1], e[1] + o[1] * ext]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        tw = max(len(self.p['value']), len(self.ref) + 1) * 1.05 + 1.5
        if self.two and r in (0, 180): x1 += tw
        elif self.two: y0 -= 3.0; y1 += 3.0
        else: y1 += 3.5; y0 -= 3.5; x1 += tw * 0.8
        return (x0, y0, x1, y1)

def units_of(p):
    sym = libsym(p['sym'])
    allp = libload.pins(sym)
    missing = set(allp) - set(p['pins'])
    if missing: raise SystemExit('%s (%s): 未定義のピン %s' % (p['ref'], p['sym'], sorted(missing)))
    extra = set(p['pins']) - set(allp)
    if extra: raise SystemExit('%s (%s): 記号にないピン %s' % (p['ref'], p['sym'], sorted(extra)))
    us = sorted({v[6] for v in allp.values() if v[6] != 0}) or [1]
    return [Unit(p, u) for u in us]

# ---------------------------------------------------------------- 1 枚分
class Sheet:
    def __init__(self, block, fname, page, units, global_nets):
        self.block, self.fname, self.page = block, fname, page
        self.units = units
        self.globals = global_nets
        self.items = []
        self.pwr = 0
        self.suuid = sheet_uuid(block)

    # ---- 配置
    TRIES = [(PAPERS[0], 7.62), (PAPERS[0], 6.35), (PAPERS[1], 7.62), (PAPERS[1], 10.16), (PAPERS[1], 6.35), (PAPERS[1], 5.08), (PAPERS[2], 7.62)]
    def place(self, start=0):
        """部品を置く。start 番目の条件（用紙・部品の間隔）から試し、区画に収まった条件の番号を返す"""
        for i in range(start, len(self.TRIES)):
            (name, w, h), gap = self.TRIES[i]
            self.paper, self.W, self.H = name, w, h
            region = (20, 22, w - 20, h - 45)
            res, pl = self._try_place(region, gap)
            if all(self._inside(pl.rect(k), region) for k in res): break
        self.gap, self.try_index = gap, i
        for u in self.units:
            (x, y), r = res[u.key]
            fixed = LAYOUT.get(u.key) or (LAYOUT.get(u.ref) if u.unit == 1 else None)
            gsn = RG if fixed else 2.54          # 手で決めた位置は 1.27mm 刻みのまま
            u.pos, u.r = (round(x / gsn) * gsn, round(y / gsn) * gsn), r

    def _inside(self, r, region):
        return r[0] >= region[0] - 0.01 and r[1] >= region[1] - 0.01 and r[2] <= region[2] + 0.01 and r[3] <= region[3] + 0.01

    def _roles(self):
        """2 端子部品の役割: 'shunt'（片側が GND か電源）か 'series'（信号の通り道）"""
        role = {}
        for u in self.units:
            if not u.two: role[u.key] = 'ic'; continue
            nets = [u.p['pins'][n] for n in sorted(u.pins)]
            pw = [n in POWER or n in RAILS for n in nets]
            role[u.key] = 'shunt' if any(pw) else 'series'
        return role

    def _shunt_rot(self, u):
        """GND を下、電源を上に向ける角度（ピン 1 が上になるのが 0°）"""
        n1, n2 = u.p['pins']['1'], u.p['pins']['2']
        def rank(n):
            return 0 if n in RAILS else 2 if n in POWER else 1
        return 0 if rank(n1) <= rank(n2) else 180

    def _levels(self):
        """信号の流れの順番（列）。回路一覧の先頭から、信号のネットをたどった段数"""
        sig = {}
        for u in self.units:
            for num in u.pins:
                n = u.p['pins'][num]
                if n and n not in POWER and n not in RAILS: sig.setdefault(n, set()).add(u.key)
        nb = {u.key: set() for u in self.units}
        for n, ks in sig.items():
            if len(ks) > 8: continue            # 多数の部品がつながるネット（VREF など）は流れに使わない
            for k in ks: nb[k] |= ks - {k}
        role = self._roles()
        lvl = {}
        order = [u.key for u in self.units]
        # 電源と GND だけにつながる部品（パスコンなど）は、回路一覧で直前の部品と同じ列に置く
        ponly = {u.key for u in self.units if all((u.p['pins'][n] in POWER or u.p['pins'][n] in RAILS or u.p['pins'][n] is None) for n in u.pins)}
        for start in order:
            if start in lvl or start in ponly: continue
            base = max(lvl.values()) + 1 if lvl else 0
            lvl[start] = base; q = [start]
            while q:
                k = q.pop(0)
                for k2 in sorted(nb[k], key=order.index):
                    if k2 in lvl: continue
                    # GND・電源に落ちる部品は、つながる相手と同じ列（その下に置く）
                    lvl[k2] = lvl[k] if role[k2] == 'shunt' else lvl[k] + 1
                    q.append(k2)
        last = 0
        units = {u.key: u for u in self.units}
        for k in order:
            if k in ponly and not units[k].two and units[k].p['sym'] != 'power:PWR_FLAG' and units[k].n_pins_total() >= 3 \
                    and units[k].unit == 1 and units[k].p['sym'].startswith(('Regulator', 'Converter')):
                last = (max(lvl.values()) + 1) if lvl else 0          # レギュレータは自分の列を持つ
                lvl[k] = last; role[k] = 'ic'
            elif k in ponly:
                lvl[k] = last; role[k] = 'shunt'
            else: last = lvl[k]
        return lvl, role

    def _try_place(self, region, gap):
        w, h = self.W, self.H
        pl = Placer(w, h, {self.block: region}, grid=2.54, gap=gap, edge=12)
        lvl, role = self._levels()
        ncol = max(lvl.values()) + 1
        colw = 22.86
        per_row = max(1, int((region[2] - region[0] - 16) / colw))       # 区画の幅を超える列は次の段へ折り返す
        nrow = (ncol + per_row - 1) // per_row
        rowh = max(60.0, (region[3] - region[1] - 10) / max(1, nrow))
        init, rows = {}, {}
        for u in self.units:
            if role[u.key] == 'shunt' and u.two: rr = [self._shunt_rot(u)]
            elif role[u.key] == 'series' and u.two: rr = [90, 270]
            else: rr = [0]
            fix = LAYOUT.get(u.key) or (LAYOUT.get(u.ref) if u.unit == 1 else None)
            if fix:                                 # 位置を手で決めた部品（circuit.py の LAYOUT）
                rr = [fix[2] if len(fix) > 2 else 0]
            rots = {r: (u.footprint_box(r), {num: u.pin_end(num, (0, 0), r) for num in u.pins}) for r in rr}
            pl.add_part(u.key, self.block, rots, (fix[0], fix[1], rr[0]) if fix else None)
            c = lvl[u.key]
            # 信号の通り道（IC・直列部品）は段の上側、GND・電源に落ちる部品はその下
            k = 'main' if role[u.key] != 'shunt' else 'shunt'
            i = rows.setdefault((c, k), 0); rows[(c, k)] += 1
            y0 = region[1] + 12 + (c // per_row) * rowh
            y = y0 + (i * 20 if k == 'main' else 20 + i * 14)
            init[u.key] = (region[0] + 8 + (c % per_row) * colw, y)
        nets = {}
        for u in self.units:
            for num in u.pins:
                net = u.p['pins'][num]
                if net and net not in POWER and net not in RAILS: nets.setdefault(net, []).append((u.key, num))
        for net, lst in nets.items():
            pl.add_net(net, 1.0, lst)
        pl.anchor, pl.anchor_w = init, 0.6
        return pl.run(log=lambda *a: None, init=init, passes=12), pl

    # ---- 結線
    def cell(self, p):
        return (int(round(p[0] / RG)), int(round(p[1] / RG)))
    def route(self):
        self.route_setup()
        nets = {}
        for u in self.units:
            for num in u.pins:
                net = u.p['pins'][num]
                if net and net not in POWER:
                    nets.setdefault(net, []).append((self.cell(u.pin_end(num)), u.pin_out(num)))
        self.pending = []
        for net in sorted(nets, key=lambda n: (self._span(nets[n]), n)):
            if len(nets[net]) < 2 and net not in self.globals: continue
            self._route_net(net, nets[net])
        for args in self.pending: self._global_label(*args)

    def route_setup(self):
        self.nx, self.ny = int(self.W / RG) + 1, int(self.H / RG) + 1
        blocked, pinend = set(), {}
        for u in self.units:
            x0, y0, x1, y1 = u.body_rect()
            for ix in range(int(math.floor(x0 / RG + 1e-6)), int(math.ceil(x1 / RG - 1e-6)) + 1):
                for iy in range(int(math.floor(y0 / RG + 1e-6)), int(math.ceil(y1 / RG - 1e-6)) + 1):
                    blocked.add((ix, iy))
            for num in u.pins:
                for pt in u.pin_line(num): blocked.add(self.cell(pt))
        for u in self.units:
            for num in u.pins:
                pinend[self.cell(u.pin_end(num))] = u.p['pins'][num] or '__nc__'
        for c in pinend: blocked.discard(c)
        # ピンの出口の 1 マスは、そのピンのネット専用
        self.escape = {}
        for u in self.units:
            for num in u.pins:
                net = u.p['pins'][num]
                if net and net not in POWER:
                    e = self.cell(u.pin_end(num)); o = u.pin_out(num)
                    self.escape[(e[0] + o[0], e[1] + o[1])] = net
        # 電源記号の置き場所
        for u in self.units:
            for num in u.pins:
                net = u.p['pins'][num]
                if net in POWER or NAME_PIN.get(net) == (u.ref, num):
                    e = self.cell(u.pin_end(num)); o = u.pin_out(num)
                    if net not in POWER: o = name_dir(o, net)
                    for k in range(1, 5):
                        for s in (-1, 0, 1):
                            blocked.add((e[0] + o[0] * k + (s if o[0] == 0 else 0), e[1] + o[1] * k + (s if o[1] == 0 else 0)))
        self.blocked, self.pinend = blocked, pinend
        # 電源記号を付けたピンには、線は横から入る
        self.side = {self.cell(u.pin_end(num)): (u.pin_out(num), name_dir(u.pin_out(num), u.p['pins'][num]))
                     for u in self.units for num in u.pins if NAME_PIN.get(u.p['pins'][num]) == (u.ref, num)}
        self.occ = {}                      # セル → {'h': ネット, 'v': ネット}
        self.ends = {}                     # 線の端・角（他のネットは通れない）
        self.wires, self.deg, self.wire_nets = [], {}, []
        self.failed = []

    def _span(self, pins):
        xs = [c[0] for c, _ in pins]; ys = [c[1] for c, _ in pins]
        return max(xs) - min(xs) + max(ys) - min(ys)

    def _route_net(self, net, pins, label=True):
        tree = {}                          # セル → 使っている向きの集合
        pin_of = {c: o for c, o in pins}
        start = min(pins, key=lambda pc: (pc[0][0], pc[0][1]))
        rest = [p for p in pins if p is not start]
        tree[start[0]] = set(); self._deg(net, start[0], 1)
        labeled = net in self.globals
        while rest:
            rest.sort(key=lambda pc: min(abs(pc[0][0] - t[0]) + abs(pc[0][1] - t[1]) for t in tree))
            tgt = rest.pop(0)
            if tgt[0] in tree:                 # ピンどうしが重なっている（線なしでつながっている）
                self._deg(net, tgt[0], 1); continue
            path = self._astar(tree, pin_of, tgt, net)
            if path is None:
                self.failed.append(net)
                if label:
                    self._label(net, tgt)
                    if not labeled: self._label(net, start); labeled = True
                continue
            self._commit(net, path, tree)
            self._deg(net, tgt[0], 1)
        if net in self.globals:            # ブロックをまたぐ信号の目印は、全部の線を引いた後で空いている所に置く
            self.pending.append((net, start, tree, pin_of))

    def _deg(self, net, c, d):
        self.deg[(net, c)] = self.deg.get((net, c), 0) + d

    def _astar(self, tree, pin_of, tgt, net=None):
        tc, tout = tgt
        inward = (-tout[0], -tout[1])
        flex = getattr(self, 'flex', set())      # ピン先でない端（ラベルの引き出し線の先）は横からも入れる
        okin = {d for d in DIRS if d != (tout[0], tout[1])} if tc in flex else {inward}
        if tc in getattr(self, 'side', {}):
            o_, sd = self.side[tc]; okin = {d for d in DIRS if d not in (o_, (-sd[0], -sd[1]))}
        heap, best, came = [], {}, {}
        for c, used in tree.items():
            if c in pin_of:
                if used: continue
                dirs = [pin_of[c]]                       # ピン先からは外向きにだけ出す
                if c in flex: dirs = [d for d in DIRS if d != (-pin_of[c][0], -pin_of[c][1])]
                if c in getattr(self, 'side', {}):
                    o_, sd = self.side[c]; dirs = [d for d in DIRS if d not in ((-o_[0], -o_[1]), sd)]
            else:
                # 線の端からは同じ向きにそのまま延ばしてもよい（延ばした先が線でなければ）
                dirs = [d for d in DIRS if ('h' if d[1] == 0 else 'v') not in used
                        or (c in self.ends and (c[0] + d[0], c[1] + d[1]) not in tree)]
                if c in self.ends and len(used) == 2 and not dirs: continue
            for d in dirs:
                heapq.heappush(heap, (abs(c[0] - tc[0]) + abs(c[1] - tc[1]), 0, c, d))
                best[(c, d)] = 0
        nexp = 0
        while heap:
            f, g, c, d = heapq.heappop(heap)
            if best.get((c, d), 1e9) < g: continue
            nexp += 1
            if nexp > getattr(self, 'max_exp', 300000): return None
            n = (c[0] + d[0], c[1] + d[1])
            if n == tc:
                if d not in okin: continue
                path = [n, c]; k = (c, d)
                while k in came:
                    k = came[k]; path.append(k[0])
                path.reverse()
                out = [path[0]]
                for p in path[1:]:
                    if p != out[-1]: out.append(p)
                return out
            if not (0 < n[0] < self.nx and 0 < n[1] < self.ny): continue
            if n in self.blocked or n in self.pinend or n in tree or n in self.ends: continue
            if self.escape.get(n, net) != net: continue
            o = self.occ.get(n, {})
            axis = 'h' if d[1] == 0 else 'v'
            if axis in o: continue
            crossing = bool(o)
            ng = g + 1 + (12 if crossing else 0)
            for nd in ([d] if crossing else [d, (d[1], d[0]), (-d[1], -d[0])]):
                g2 = ng + (0 if nd == d else 6)
                k2 = (n, nd)
                if best.get(k2, 1e9) <= g2: continue
                best[k2] = g2; came[k2] = (c, d)
                heapq.heappush(heap, (g2 + abs(n[0] - tc[0]) + abs(n[1] - tc[1]), g2, n, nd))
        return None

    def _commit(self, net, path, tree):
        # 既存の線の途中から枝分かれするときは、そこが T 字の接続点になる
        if tree.get(path[0]) and path[0] not in self.ends: self._deg(net, path[0], 2)
        for a, b in zip(path, path[1:]):
            axis = 'h' if a[1] == b[1] else 'v'
            for c in (a, b):
                self.occ.setdefault(c, {})[axis] = net
                tree.setdefault(c, set()).add(axis)
        pts = [path[0]]
        for i in range(1, len(path) - 1):
            a, b, c = path[i - 1], path[i], path[i + 1]
            if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]): pts.append(b)
        pts.append(path[-1])
        for p in pts: self.ends[p] = net
        self._deg(net, path[0], 1)
        for p in pts[1:-1]: self._deg(net, p, 2)
        for a, b in zip(pts, pts[1:]): self.wires.append((a, b)); self.wire_nets.append(net)

    def _global_label(self, net, start, tree, pin_of):
        tl = int(len(net) * 1.1 / RG) + 5
        def free(cells):
            return all(x not in self.blocked and x not in self.pinend and x not in self.ends and x not in self.occ
                       and self.escape.get(x, net) == net for x in cells)
        cands = []
        for c, used in tree.items():
            if c in pin_of:
                if not used: cands.append((c, pin_of[c]))       # まだ線のないピン（このブロックでは 1 本だけのネット）
            elif c not in self.ends:
                for d in DIRS:
                    if ('h' if d[1] == 0 else 'v') not in used: cands.append((c, d))
        cands.sort(key=lambda cd: (0 if cd[0] in pin_of else 1, abs(cd[0][0] - start[0][0]) + abs(cd[0][1] - start[0][1])))
        for c, o in cands:
            stub = [(c[0] + o[0] * k, c[1] + o[1] * k) for k in range(1, 3)]
            text = [(stub[-1][0] + o[0] * k, stub[-1][1] + o[1] * k) for k in range(1, tl)]
            if free(stub + text):
                self._commit(net, [c] + stub, tree)
                for x in text: self.blocked.add(x)
                self._glabel(net, stub[-1], o)
                return
        c, o = start
        self._glabel(net, c, o)

    def _glabel(self, net, c, o):
        ang = ANG[o]; x, y = c[0] * RG, c[1] * RG
        just = 'right' if ang in (180, 270) else 'left'
        self.items.append([S('global_label'), q(net), [S('shape'), S('passive')], [S('at'), F(x), F(y), S(str(ang))],
                           [S('fields_autoplaced'), S('yes')],
                           [S('effects'), [S('font'), [S('size'), S('1.27'), S('1.27')]], [S('justify'), S(just)]], [S('uuid'), U()],
                           [S('property'), q('Intersheetrefs'), q('${INTERSHEET_REFS}'), [S('at'), F(x), F(y), S('0')],
                            [S('effects'), [S('font'), [S('size'), S('1.27'), S('1.27')]], [S('justify'), S('left')], [S('hide'), S('yes')]]]])

    def _label(self, net, pc):
        """線を引けなかったピンは、ネット名のラベルで同じネットにする"""
        c, o = pc
        # ローカルラベルだとネット名にシート名（日本語）が付き、Freerouting が読めないのでグローバルラベルにする
        return self._glabel(net, c, o)
        ang = ANG[o]; just = 'right' if ang in (180, 270) else 'left'
        self.items.append([S('label'), q(net), [S('at'), F(c[0] * RG), F(c[1] * RG), S(str(ang))],
                           [S('effects'), [S('font'), [S('size'), S('1.27'), S('1.27')]], [S('justify'), S(just), S('bottom')]], [S('uuid'), U()]])

    # ---- 書き出し
    def instance(self, lib_id, ref, value, fp, x, y, unit, r, uid, hide_ref=False):
        sym = libsym(lib_id)
        props = {unq(p[1]): p for p in find(sym, 'property')}
        def pr(name, val, hide=False):
            p = props.get(name); ax = ay = aa = 0
            if p:
                a = find1(p, 'at'); ax, ay = float(a[1]), float(a[2]); aa = float(a[3]) if len(a) > 3 else 0
            dx, dy = rot(ax, ay, r)
            e = [S('effects'), [S('font'), [S('size'), S('1.27'), S('1.27')]]]
            if p:
                pe = find1(p, 'effects'); j = find1(pe, 'justify') if pe else None
                if j: e.append(copy.deepcopy(j))
            node = [S('property'), q(name), q(val), [S('at'), F(x + dx), F(y + dy), S(str(int((aa + r) % 180)))]]
            if hide: node.append([S('hide'), S('yes')])
            node.append(e)
            return node
        node = [S('symbol'), [S('lib_id'), q(lib_id)], [S('at'), F(x), F(y), S(str(r))], [S('unit'), S(str(unit))],
                [S('exclude_from_sim'), S('no')], [S('in_bom'), S('no' if ref.startswith('#') else 'yes')],
                [S('on_board'), S('no' if ref.startswith('#') else 'yes')], [S('dnp'), S('no')], [S('uuid'), q(uid)],
                pr('Reference', ref, hide_ref), pr('Value', value), pr('Footprint', fp, True), pr('Datasheet', '', True)]
        for num, v in libload.pins(sym).items():
            if v[6] in (0, unit): node.append([S('pin'), q(num), [S('uuid'), U()]])
        node.append([S('instances'), [S('project'), q(PROJ), [S('path'), q('/' + ROOT_UUID),
                                                              [S('reference'), q(ref)], [S('unit'), S(str(unit))]]]])
        self.items.append(node)

    def power(self, net, c, o):
        self.pwr += 1
        lib_id = 'power:GND' if net == 'GND' else PROJ + ':' + net
        native = 270 if net == 'GND' else 90
        self.instance(lib_id, '#PWR%d%03d' % (self.page, self.pwr), net, '', c[0], c[1], 1, (ANG[o] - native) % 360,
                      str(uuid.uuid4()), hide_ref=True)

    def emit(self):
        for u in self.units:
            x, y = u.pos
            self.instance(u.p['sym'], u.ref, u.p['value'], u.p['fp'], x, y, u.unit, u.r, sym_uuid(u.ref, u.unit))
            for num in u.pins:
                net = u.p['pins'][num]; e = u.pin_end(num); o = u.pin_out(num)
                if net is None:
                    self.items.append([S('no_connect'), [S('at'), F(e[0]), F(e[1])], [S('uuid'), U()]])
                elif net in POWER:
                    self.power(net, e, o)
                elif NAME_PIN.get(net) == (u.ref, num):
                    self.power(net, e, name_dir(o, net))
        for a, b in self.wires:
            self.items.append([S('wire'), [S('pts'), [S('xy'), F(a[0] * RG), F(a[1] * RG)], [S('xy'), F(b[0] * RG), F(b[1] * RG)]],
                               [S('stroke'), [S('width'), S('0')], [S('type'), S('default')]], [S('uuid'), U()]])
        for (net, c), d in self.deg.items():
            if d >= 3:
                self.items.append([S('junction'), [S('at'), F(c[0] * RG), F(c[1] * RG)], [S('diameter'), S('0')],
                                   [S('color'), S('0'), S('0'), S('0'), S('0')], [S('uuid'), U()]])
        # 中身の外接矩形（部品の配置枠・線・ラベル）
        xs, ys = [], []
        for u in self.units:
            for r in (u.footprint_box(u.r),):
                xs += [u.pos[0] + r[0], u.pos[0] + r[2]]; ys += [u.pos[1] + r[1], u.pos[1] + r[3]]
        for a2, b2 in self.wires:
            xs += [a2[0] * RG, b2[0] * RG]; ys += [a2[1] * RG, b2[1] * RG]
        for it in self.items:
            if it[0] in ('global_label', 'label'):
                at = find1(it, 'at'); x, y, ang = float(at[1]), float(at[2]), int(at[3])
                L = len(unq(it[1])) * 1.1 + 3
                dx, dy = {0: (L, 0), 180: (-L, 0), 90: (0, -L), 270: (0, L)}[ang]
                xs += [x, x + dx]; ys += [y, y + dy]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))

def shift(node, dx, dy):
    """S 式の中の座標（at・xy）をずらす"""
    if isinstance(node, list):
        if node and node[0] in ('at', 'xy') and len(node) >= 3:
            node[1] = F(float(node[1]) + dx); node[2] = F(float(node[2]) + dy)
        else:
            for c in node: shift(c, dx, dy)

def connect_labels(items, units, wires, PW, PH):
    """同じ名前のラベル（ブロックをまたぐ信号）どうしを線で結ぶ。結べたネットはラベルを消す"""
    g = Sheet('全体', '', 1, units, set())
    g.W, g.H = PW, PH
    g.route_setup()
    cells_of = {}                          # (ネット, ブロック) → そのブロック内の線のセル
    wdeg = {}                              # セル → ブロック内の線の本数（端で数える）
    for a, b, net, blk in wires:
        axis = 'h' if a[1] == b[1] else 'v'
        if axis == 'h': cs = [(x, a[1]) for x in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]
        else: cs = [(a[0], y) for y in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]
        for c in cs:
            g.occ.setdefault(c, {})[axis] = net
            cells_of.setdefault((net, blk), {}).setdefault(c, set()).add(axis)
        for c in (a, b):
            g.ends[c] = net; wdeg[c] = wdeg.get(c, 0) + 1
        for c in cs[1:-1]: wdeg[c] = wdeg.get(c, 0) + 2
    groups = {}
    blk_of = {}
    for u in units: blk_of[u.ref] = u.p['block']
    for it in items:
        if it[0] == 'global_label':
            at = find1(it, 'at'); c = g.cell((float(at[1]), float(at[2])))
            o = {0: (1, 0), 180: (-1, 0), 90: (0, -1), 270: (0, 1)}[int(at[3])]
            groups.setdefault(unq(it[1]), []).append((it, c, o))
    # ラベルがどのブロックのものか（近いブロックの線・ピン）
    # ネットごとに、つながっている線のかたまりに分ける
    segs = {}
    for a, b, net, blk in wires:
        axis = 'h' if a[1] == b[1] else 'v'
        if axis == 'h': cs = [(x, a[1]) for x in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]
        else: cs = [(a[0], y) for y in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]
        segs.setdefault(net, []).append(({c: {axis} for c in cs}, a, b))
    def comp(net, c, o):
        lst = segs.get(net, [])
        hit = [i for i, (cs, a, b) in enumerate(lst) if c in cs]
        group, todo = set(hit), list(hit)
        while todo:
            i = todo.pop(); cs, a, b = lst[i]
            for j, (cs2, a2, b2) in enumerate(lst):
                if j in group: continue
                if a2 in cs or b2 in cs or a in cs2 or b in cs2:
                    group.add(j); todo.append(j)
        d = {}
        for i in group:
            for cc, ax in lst[i][0].items(): d.setdefault(cc, set()).update(ax)
        d.setdefault(c, set())
        return d
    done, extra_w, extra_j, path_ends, path_ends_of = [], [], [], set(), {}
    for net in sorted(groups, key=lambda n: g._span([(c, o) for _, c, o in groups[n]])):
        lst = groups[net]
        if len(lst) < 2: continue
        comps = []
        for it, c, o in lst:
            cc = comp(net, c, o)
            if not any(c in x for x in comps): comps.append(cc)
        out = {c: o for _, c, o in lst}
        if os.environ.get('SCH_DEBUG') == net:
            print('DEBUG', net, [(c, o) for _, c, o in lst], [len(x) for x in comps])
        tree = dict(comps[0]); ok = True; paths = []
        for tgt in comps[1:]:
            path = route_between(g, net, tree, tgt, out)
            if path is None:
                if os.environ.get('SCH_DEBUG'):
                    for cc, used in list(tree.items())[:3] + list(tgt.items())[:3]:
                        print('  ', net, cc, used, [(d, (cc[0]+d[0], cc[1]+d[1]) in g.blocked, (cc[0]+d[0], cc[1]+d[1]) in g.pinend,
                              (cc[0]+d[0], cc[1]+d[1]) in g.ends, g.occ.get((cc[0]+d[0], cc[1]+d[1]))) for d in DIRS])
                    print('   src', len(tree), 'dst', len(tgt))
                ok = False; break
            paths.append(path)
            if os.environ.get('SCH_DEBUG') == net: print('  path', path[0], '->', path[-1], len(path))
            for x, y in zip(path, path[1:]):
                axis = 'h' if x[1] == y[1] else 'v'
                for c in (x, y): tree.setdefault(c, set()).add(axis)
            tree.update({c: tree.get(c, set()) | v for c, v in tgt.items()})
        if not ok: continue
        done.append(net)
        for path in paths:
            pts = [path[0]]
            for i in range(1, len(path) - 1):
                a, b, c = path[i - 1], path[i], path[i + 1]
                if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]): pts.append(b)
            pts.append(path[-1])
            for x, y in zip(pts, pts[1:]): extra_w.append((x, y))
            for c in pts: g.ends[c] = net
            for x, y in zip(path, path[1:]):
                axis = 'h' if x[1] == y[1] else 'v'
                for c in (x, y): g.occ.setdefault(c, {})[axis] = net
            for c in (path[0], path[-1]):
                path_ends.add(c); path_ends_of.setdefault(net, set()).add(c)
                exist = wdeg.get(c, 0) + (1 if c in g.pinend else 0)
                if exist >= 2: extra_j.append(c)
                wdeg[c] = wdeg.get(c, 0) + 1
            for c in path[1:-1]:                  # 後から引く線がこの線の途中につながるときのため
                wdeg[c] = wdeg.get(c, 0) + 2
    print('ブロック間を線で結んだ信号 %d / %d（残りはラベル: %s）' % (len(done), len([n for n in groups if len(groups[n]) > 1]),
          sorted({n for n in groups if len(groups[n]) > 1} - set(done)) or 'なし'))
    keep = [it for it in items if not (it[0] == 'global_label' and unq(it[1]) in done)]
    # ラベルを外した引き出し線の先が余ったら、分岐点まで切り詰める
    for net in (done if not os.environ.get('NO_TRIM') else []):
        for _, c, o in groups[net]:
            if c in g.pinend or c in path_ends or wdeg.get(c, 0) > 2: continue
            for it in list(keep):
                if it[0] != 'wire': continue
                pts = find(find1(it, 'pts'), 'xy')
                ends = [g.cell((float(q_[1]), float(q_[2]))) for q_ in pts]
                if c not in ends: continue
                other = ends[1] if ends[0] == c else ends[0]
                if sum(1 for a2, b2, *_ in wires if c in (a2, b2)) > 1: break
                same = [(a2, b2) for a2, b2, n2, _ in wires if n2 == net and (a2, b2) not in ((c, other), (other, c))]
                attach = path_ends_of.get(net, set()) | {a2 for a2, b2 in same} | {b2 for a2, b2 in same} | \
                         {u for a2, b2 in same for u in seg_cells(a2, b2)}
                on = [e for e in attach if e != other and min(other[0], c[0]) <= e[0] <= max(other[0], c[0])
                      and min(other[1], c[1]) <= e[1] <= max(other[1], c[1]) and (e[0] == c[0] or e[1] == c[1])]
                if on:
                    nearest = min(on, key=lambda e: abs(e[0] - c[0]) + abs(e[1] - c[1]))
                    k = 0 if ends[0] == c else 1
                    pts[k][1] = F(nearest[0] * RG); pts[k][2] = F(nearest[1] * RG)
                    if not any(nearest in (a2, b2) for a2, b2 in same) and nearest not in path_ends_of.get(net, set()):
                        extra_j.append(nearest)       # 線の途中につながるので接続点
                else:
                    keep.remove(it)
    for a, b in extra_w:
        keep.append([S('wire'), [S('pts'), [S('xy'), F(a[0] * RG), F(a[1] * RG)], [S('xy'), F(b[0] * RG), F(b[1] * RG)]],
                     [S('stroke'), [S('width'), S('0')], [S('type'), S('default')]], [S('uuid'), U()]])
    for c in set(extra_j):
        keep.append([S('junction'), [S('at'), F(c[0] * RG), F(c[1] * RG)], [S('diameter'), S('0')],
                     [S('color'), S('0'), S('0'), S('0'), S('0')], [S('uuid'), U()]])
    return keep

def seg_cells(a, b):
    if a[1] == b[1]: return [(x, a[1]) for x in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]
    return [(a[0], y) for y in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]

def route_between(g, net, src, dst, out):
    """src（セル → 使っている向き）から dst のどこかへ、直角の線を引く"""
    def dirs_from(c, used):
        if not used:
            if c in g.side:
                o, sd = g.side[c]; return [d for d in DIRS if d not in ((-o[0], -o[1]), sd)]
            if c in g.pinend: return [out.get(c) or g_pin_out(g, c)]
            return list(DIRS)
        return [d for d in DIRS if ('h' if d[1] == 0 else 'v') not in used]
    goal = {}
    for c, used in dst.items():
        if used: goal[c] = {d for d in DIRS if ('h' if d[1] == 0 else 'v') not in used}
        elif c in g.side:
            o, sd = g.side[c]; goal[c] = {d for d in DIRS if d not in (o, (-sd[0], -sd[1]))}
        elif c in g.pinend: goal[c] = {(-o[0], -o[1]) for o in [out.get(c) or g_pin_out(g, c)]}
        else: goal[c] = set(DIRS)
    gx = [c[0] for c in goal]; gy = [c[1] for c in goal]
    def h(c):
        return max(0, min(gx) - c[0], c[0] - max(gx)) + max(0, min(gy) - c[1], c[1] - max(gy))
    heap, best, came = [], {}, {}
    for c, used in src.items():
        for d in dirs_from(c, used):
            if d is None: continue
            heapq.heappush(heap, (h(c), 0, c, d)); best[(c, d)] = 0
    nexp = 0
    while heap:
        f, gg, c, d = heapq.heappop(heap)
        if best.get((c, d), 1e9) < gg: continue
        nexp += 1
        if nexp > 3000000: return None
        n = (c[0] + d[0], c[1] + d[1])
        if n in goal:
            if d not in goal[n]: continue
            path = [n, c]; k = (c, d)
            while k in came:
                k = came[k]; path.append(k[0])
            path.reverse()
            o2 = [path[0]]
            for p in path[1:]:
                if p != o2[-1]: o2.append(p)
            return o2
        if not (0 < n[0] < g.nx and 0 < n[1] < g.ny): continue
        if n in g.blocked or n in g.pinend or n in src or n in g.ends: continue
        if g.escape.get(n, net) != net: continue
        o = g.occ.get(n, {})
        axis = 'h' if d[1] == 0 else 'v'
        if axis in o: continue
        crossing = bool(o)
        ng = gg + 1 + (8 if crossing else 0)
        for nd in ([d] if crossing else [d, (d[1], d[0]), (-d[1], -d[0])]):
            g2 = ng + (0 if nd == d else 6)
            k2 = (n, nd)
            if best.get(k2, 1e9) <= g2: continue
            best[k2] = g2; came[k2] = (c, d)
            heapq.heappush(heap, (g2 + h(n), g2, n, nd))
    return None

def g_pin_out(g, c):
    for u in g.units:
        for num in u.pins:
            if g.cell(u.pin_end(num)) == c: return u.pin_out(num)
    return None

def write_merged(sheets, out=None):
    """ブロックごとに作った回路を、枠で囲んで 1 枚に並べる"""
    M = 8.0          # 枠の内側の余白
    sizes = [('A1', 841, 594), ('A0', 1189, 841)] + [('User', 1189 + 100 * k, 841 + 100 * k) for k in range(1, 8)]
    for name, PW, PH in sizes:
        x, y, rowh, ok, pos = 25.4, 30.48, 0, True, []
        for sh in sheets:
            w = sh.bbox[2] - sh.bbox[0] + 2 * M; h = sh.bbox[3] - sh.bbox[1] + 2 * M + 6
            if x + w > PW - 20: x = 25.4; y += rowh + 22.86; rowh = 0
            pos.append((x, y, w, h)); x += w + 22.86; rowh = max(rowh, h)
        if y + rowh < PH - 60 and all(px + pw < PW - 20 for px, py, pw, ph in pos): break
    items, libs = [], {}
    allunits, allwires = [], []
    for sh, (x, y, w, h) in zip(sheets, pos):
        dx = round((x + M - sh.bbox[0]) / 2.54) * 2.54; dy = round((y + M + 6 - sh.bbox[1]) / 2.54) * 2.54
        for it in sh.items:
            shift(it, dx, dy); items.append(it)
            if it[0] == 'symbol':
                lid = unq(find1(it, 'lib_id')[1]); libs[lid] = libsym(lid)
        for u in sh.units:
            u.pos = (u.pos[0] + dx, u.pos[1] + dy); allunits.append(u)
        ci, cj = int(round(dx / RG)), int(round(dy / RG))
        allwires += [((a[0] + ci, a[1] + cj), (b[0] + ci, b[1] + cj), n, sh.block) for (a, b), n in zip(sh.wires, sh.wire_nets)]
    for sh, (x, y, w, h) in zip(sheets, pos):
        items.append([S('rectangle'), [S('start'), F(x), F(y)], [S('end'), F(x + w), F(y + h)],
                      [S('stroke'), [S('width'), S('0.3')], [S('type'), S('dash')]], [S('fill'), [S('type'), S('none')]], [S('uuid'), U()]])
        items.append([S('text'), q(sh.block), [S('exclude_from_sim'), S('no')], [S('at'), F(x + 3), F(y + 6), S('0')],
                      [S('effects'), [S('font'), [S('size'), S('4'), S('4')], [S('bold'), S('yes')]], [S('justify'), S('left'), S('bottom')]], [S('uuid'), U()]])
    items = connect_labels(items, allunits, allwires, PW, PH)
    note = ('送信: マイク → 送信音声 → セラゾイド変調（1.83125MHz で PM）→ 逓倍 ×16（段間同調）→ PLL（VCO 29.3MHz）→ 送信RF（10W）→ ANT\\n'
            '受信: ANT → 受信（2N3819 → NJM2594 → 10.7MHz 増幅 → 10.7MHz → MC3361 → LM386）→ SP\\n'
            '制御: XIAO ESP32C3 ＋ Si5351（CLK0 = 変調基準 18.3125MHz、CLK1 = 受信局発 18.6MHz）\\n'
            'ブロックの中もブロックの間も線で結線（電源も線。電源の名前は出どころの電源記号で示す。GND だけ GND 記号）')
    items.append([S('text'), q(note), [S('exclude_from_sim'), S('no')], [S('at'), F(25.4), F(max(py + ph for px, py, pw, ph in pos) + 20), S('0')],
                  [S('effects'), [S('font'), [S('size'), S('2.5'), S('2.5')]], [S('justify'), S('left'), S('bottom')]], [S('uuid'), U()]])
    sch = [S('kicad_sch'), [S('version'), S('20260306')], [S('generator'), q('eeschema')], [S('generator_version'), q('10.0')],
           [S('uuid'), q(ROOT_UUID)], ([S('paper'), q(name)] if name != 'User' else [S('paper'), q('User'), F(PW), F(PH)]),
           [S('title_block'), [S('title'), q('Serrasoid TRX 29M（セラゾイド変調 29MHz FM 10W トランシーバ）')],
            [S('date'), q(datetime.date.today().isoformat())], [S('rev'), q('1.2')], [S('company'), q('JA6FUF')]],
           [S('lib_symbols')] + list(libs.values())] + items + [
           [S('sheet_instances'), [S('path'), q('/'), [S('page'), q('1')]]], [S('embedded_fonts'), S('no')]]
    open(out or os.path.join(ROOT, 'kicad', PROJ + '.kicad_sch'), 'w').write(dump(sch) + '\n')
    if out: return name
    # ブロック別に分けていたころのファイルは消す
    for sh in sheets:
        f = os.path.join(ROOT, 'kicad', sh.fname + '.kicad_sch')
        if os.path.exists(f): os.remove(f)
    return name

def main():
    blocks = {}
    for p in parts: blocks.setdefault(p['block'], []).append(p)
    where = {}
    for blk, ps in blocks.items():
        for p in ps:
            for n in p['pins'].values():
                if n and n not in POWER: where.setdefault(n, set()).add(blk)
    global_nets = {n for n, b in where.items() if len(b) > 1}
    pick_name_pins()
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    preview = next((a[len('--preview='):] for a in sys.argv[1:] if a.startswith('--preview=')), None)
    sheets = []
    for i, (blk, fname) in enumerate(SHEETS):
        if only and blk not in only: continue
        us = [u for p in blocks[blk] for u in units_of(p)]
        sh = Sheet(blk, fname, i + 2, us, global_nets)
        k = 0
        while True:                       # 線を引けないネットがあれば、条件を変えて置き直す
            sh.place(k); sh.route()
            if not sh.failed or sh.try_index >= len(Sheet.TRIES) - 1: break
            k = sh.try_index + 1
            sh.items = []
        sh.emit()
        print('%-10s 部品 %3d 線 %4d ラベルで代用 %s' % (blk, len(us), len(sh.wires), sorted(set(sh.failed)) or 'なし'))
        sheets.append(sh)
    print('用紙', write_merged(sheets, preview))

if __name__ == '__main__':
    main()
