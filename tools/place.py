"""配線長が短くなるように部品を置く（機能ブロックの区画の中で）

1. つながる相手の位置の平均へ寄せる計算を繰り返して、おおよその位置を決める
2. 大きい部品から順に、その位置に一番近い空き場所へ置く（向きも 4 通り試す）
3. 1 個ずつ外して置き直し、配線長（ネットごとのパッドの外接矩形の半周長）が減れば採用、を繰り返す

部品の大きさ・パッド位置は gen_pcb.py が向きごとに測って渡す。
"""
import math, random

G = 0.635          # 置き場所の刻み（mm）
GAP = 0.8          # 部品どうしのすき間

class Placer:
    def __init__(self, bw, bh, regions, grid=G, gap=GAP, edge=0.6):
        self.bw, self.bh, self.regions = bw, bh, regions
        self.G, self.GAP, self.edge = grid, gap, edge
        G = grid
        self.nx, self.ny = int(bw / G) + 2, int(bh / G) + 2
        self.occ = [bytearray(self.nx) for _ in range(self.ny)]
        self.parts = {}          # ref → dict(block, rots{rot: (box, pads{num: (dx, dy)})}, fixed, pos, rot)
        self.nets = {}           # name → (weight, [(ref, padnum)])
        self.part_nets = {}      # ref → set(net)
        r = int(45 / G) if G < 1 else int(120 / G)
        self.spiral = sorted(((dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)), key=lambda d: d[0] * d[0] + d[1] * d[1])

    # ---- データ
    def add_part(self, ref, block, rots, fixed=None):
        self.parts[ref] = dict(block=block, rots=rots, fixed=fixed is not None,
                               pos=(fixed[0], fixed[1]) if fixed else None, rot=fixed[2] if fixed else 0)
    def add_obstacle(self, rect):
        self._mark(rect, 1)
    def add_net(self, name, weight, pins):
        pins = [(r, n) for r, n in pins if r in self.parts]
        if len(pins) < 2 or weight <= 0: return
        self.nets[name] = (weight, pins)
        for r, _ in pins: self.part_nets.setdefault(r, set()).add(name)

    # ---- 占有
    def _cells(self, rect):
        G, GAP = self.G, self.GAP
        x0 = int(math.floor((rect[0] - GAP / 2) / G)); y0 = int(math.floor((rect[1] - GAP / 2) / G))
        x1 = int(math.ceil((rect[2] + GAP / 2) / G)); y1 = int(math.ceil((rect[3] + GAP / 2) / G))
        return x0, y0, x1, y1
    def _mark(self, rect, v):
        x0, y0, x1, y1 = self._cells(rect)
        for yy in range(max(0, y0), min(self.ny, y1)):
            row = self.occ[yy]
            for xx in range(max(0, x0), min(self.nx, x1)): row[xx] = max(0, row[xx] + v)
    def _free(self, rect, bound):
        if rect[0] < bound[0] or rect[1] < bound[1] or rect[2] > bound[2] or rect[3] > bound[3]: return False
        x0, y0, x1, y1 = self._cells(rect)
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(self.nx, x1), min(self.ny, y1)
        for yy in range(y0, y1):
            if any(self.occ[yy][x0:x1]): return False
        return True
    def rect(self, ref, pos=None, rot=None):
        p = self.parts[ref]; pos = pos or p['pos']; rot = p['rot'] if rot is None else rot
        b = p['rots'][rot][0]
        return (pos[0] + b[0], pos[1] + b[1], pos[0] + b[2], pos[1] + b[3])

    # ---- 配線長
    def pad_xy(self, ref, num, pos=None, rot=None):
        p = self.parts[ref]; pos = pos or p['pos']; rot = p['rot'] if rot is None else rot
        d = p['rots'][rot][1].get(num, (0, 0))
        return pos[0] + d[0], pos[1] + d[1]
    def net_len(self, name, override=None):
        w, pins = self.nets[name]
        xs, ys = [], []
        for r, n in pins:
            if override and r == override[0]: x, y = self.pad_xy(r, n, override[1], override[2])
            elif self.parts[r]['pos'] is None: continue
            else: x, y = self.pad_xy(r, n)
            xs.append(x); ys.append(y)
        if len(xs) < 2: return 0
        return w * (max(xs) - min(xs) + max(ys) - min(ys))
    def part_cost(self, ref, pos=None, rot=None):
        ov = (ref, pos, rot) if pos is not None else None
        c = sum(self.net_len(n, ov) for n in self.part_nets.get(ref, ()))
        a = getattr(self, 'anchor', {}).get(ref)
        if a is not None:                     # 決めておいた位置（列・行）から離れるほど損
            q = pos if pos is not None else self.parts[ref]['pos']
            if q is not None: c += self.anchor_w * (abs(q[0] - a[0]) + 2.0 * abs(q[1] - a[1]))
        return c
    def total(self):
        return sum(self.net_len(n) for n in self.nets)

    # ---- 1. おおよその位置
    def bound(self, ref, margin=0):
        x0, y0, x1, y1 = self.regions[self.parts[ref]['block']]
        e = self.edge
        return (max(e, x0 - margin), max(e, y0 - margin), min(self.bw - e, x1 + margin), min(self.bh - e, y1 + margin))
    def analytic(self, iters=80):
        est = {}
        for r, p in self.parts.items():
            if p['fixed']: est[r] = p['pos']
            else:
                b = self.bound(r); est[r] = ((b[0] + b[2]) / 2 + random.uniform(-3, 3), (b[1] + b[3]) / 2 + random.uniform(-3, 3))
        for _ in range(iters):
            new = {}
            for r, p in self.parts.items():
                if p['fixed']: continue
                sx = sy = sw = 0
                for n in self.part_nets.get(r, ()):
                    w, pins = self.nets[n]; k = w / max(1, len(pins) - 1)
                    for r2, _ in pins:
                        if r2 == r: continue
                        sx += k * est[r2][0]; sy += k * est[r2][1]; sw += k
                b = self.bound(r)
                if sw == 0: new[r] = est[r]; continue
                x = 0.5 * est[r][0] + 0.5 * sx / sw; y = 0.5 * est[r][1] + 0.5 * sy / sw
                new[r] = (min(max(x, b[0] + 2), b[2] - 2), min(max(y, b[1] + 2), b[3] - 2))
            est.update(new)
        return est

    # ---- 2・3. 空き場所探し
    def candidates(self, ref, target, bound, rots, limit=12):
        """target に近い空き場所を、向きごとに最大 limit 個"""
        out = []; G = self.G
        for rot in rots:
            b = self.parts[ref]['rots'][rot][0]
            cx, cy = target[0] - (b[0] + b[2]) / 2, target[1] - (b[1] + b[3]) / 2
            gx, gy = round(cx / G), round(cy / G); n = 0
            for dx, dy in self.spiral:
                pos = ((gx + dx) * G, (gy + dy) * G)
                if self._free((pos[0] + b[0], pos[1] + b[1], pos[0] + b[2], pos[1] + b[3]), bound):
                    out.append((pos, rot)); n += 1
                    if n >= limit: break
        return out
    def legalize(self, est):
        order = sorted([r for r, p in self.parts.items() if not p['fixed']],
                       key=lambda r: -max((b[2] - b[0]) * (b[3] - b[1]) for b, _ in self.parts[r]['rots'].values()))
        for r, p in self.parts.items():
            if p['fixed']: self._mark(self.rect(r), 1)
        # 未配置の部品はおおよその位置にあるものとして配線長を測る
        for r in order:
            self.parts[r]['pos'] = None
        tmp = dict(est)
        for r in order:
            best = None
            for margin in (0, 6, 200):
                cands = self.candidates(r, tmp[r], self.bound(r, margin), list(self.parts[r]['rots']), limit=6)
                if cands: break
            for pos, rot in cands:
                c = self.part_cost(r, pos, rot) + 0.05 * (abs(pos[0] - tmp[r][0]) + abs(pos[1] - tmp[r][1]))
                if best is None or c < best[0]: best = (c, pos, rot)
            self.parts[r]['pos'], self.parts[r]['rot'] = best[1], best[2]
            self._mark(self.rect(r), 1)
    def target_of(self, ref):
        xs, ys = [], []
        for n in self.part_nets.get(ref, ()):
            for r2, num in self.nets[n][1]:
                if r2 != ref and self.parts[r2]['pos'] is not None:
                    x, y = self.pad_xy(r2, num); xs.append(x); ys.append(y)
        if not xs: return self.parts[ref]['pos']
        xs.sort(); ys.sort()
        return xs[len(xs) // 2], ys[len(ys) // 2]
    def refine(self, passes=8, log=print):
        movable = [r for r, p in self.parts.items() if not p['fixed']]
        for it in range(passes):
            random.shuffle(movable); moved = 0
            for r in movable:
                p = self.parts[r]
                cur = self.part_cost(r)
                self._mark(self.rect(r), -1)
                best = (cur, p['pos'], p['rot'])
                tgt = self.target_of(r)
                for pos, rot in self.candidates(r, tgt, self.bound(r, 3), list(p['rots']), limit=8):
                    c = self.part_cost(r, pos, rot)
                    if c < best[0] - 0.05: best = (c, pos, rot)
                if best[1] != p['pos'] or best[2] != p['rot']: moved += 1
                p['pos'], p['rot'] = best[1], best[2]
                self._mark(self.rect(r), 1)
            log('  改善 %d 回目: 移動 %d 個、配線長の目安 %.0f mm' % (it + 1, moved, self.total()))
            if moved == 0: break
    def run(self, log=print, seed=1, init=None, passes=8):
        random.seed(seed)
        est = dict(init) if init else self.analytic()
        for r, p in self.parts.items():
            if p['fixed']: est[r] = p['pos']
        self.legalize(est)
        log('  初期配置: 配線長の目安 %.0f mm' % self.total())
        self.refine(passes=passes, log=log)
        return {r: (p['pos'], p['rot']) for r, p in self.parts.items()}
