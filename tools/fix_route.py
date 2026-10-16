"""Freerouting で残った未接続を、表・裏 2 層の格子で探して線を引く（KiCad 付属の Python で実行）

  python3 tools/fix_route.py [基板ファイル]

ネットごとに、つながっている銅（パッド・線・ビア）のかたまりを求め、かたまりが 2 つ以上あるネットについて、
いちばん大きいかたまりへ、ほかのかたまりを順につなぐ。線幅は netclass.py、間隔は 0.25mm（mkdsn.py と同じ）。
外層の GND ベタはよけずに引き、引いたあとで塗り直す。
"""
import sys, os, heapq, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from netclass import width_of

M, mm = pcbnew.FromMM, pcbnew.ToMM
G = 0.2            # 格子（mm）
CLR = 0.25         # 間隔（mm）
VIA_D, VIA_H = 0.8, 0.4
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


class Grid:
    def __init__(self, b, x0, y0, x1, y1):
        self.b = b; self.x0, self.y0 = x0, y0
        self.nx, self.ny = int((x1 - x0) / G) + 1, int((y1 - y0) / G) + 1
    def xy(self, i, j): return self.x0 + i * G, self.y0 + j * G
    def ij(self, x, y): return int(round((x - self.x0) / G)), int(round((y - self.y0) / G))


def items_of(b):
    """銅の図形を (ネット, 層の集合, 種類, データ) で返す。データは線: (ax, ay, bx, by, 半幅)、円: (x, y, 半径)、矩形: (x0, y0, x1, y1)"""
    out = []
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition(); out.append((t.GetNetname(), set(LAYERS), 'c', (mm(p.x), mm(p.y), mm(t.GetWidth(pcbnew.F_Cu)) / 2), t))
        else:
            a, e = t.GetStart(), t.GetEnd()
            out.append((t.GetNetname(), {t.GetLayer()}, 's', (mm(a.x), mm(a.y), mm(e.x), mm(e.y), mm(t.GetWidth()) / 2), t))
    for f in b.GetFootprints():
        for p in f.Pads():
            ls = {L for L in LAYERS if p.IsOnLayer(L)}
            if not ls: continue
            bb = p.GetBoundingBox()
            out.append((p.GetNetname(), ls, 'r', (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())), p))
    return out


def dist_to(it, x, y):
    k, d = it[2], it[3]
    if k == 's': return seg_dist(x, y, d[0], d[1], d[2], d[3]) - d[4]
    if k == 'c': return math.hypot(x - d[0], y - d[1]) - d[2]
    dx = max(d[0] - x, 0, x - d[2]); dy = max(d[1] - y, 0, y - d[3]); return math.hypot(dx, dy)


def components(items, net):
    """そのネットの銅のかたまり（触れ合っているもの）"""
    own = [it for it in items if it[0] == net]
    par = list(range(len(own)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    def pts(it):
        k, d = it[2], it[3]
        if k == 's': return [(d[0], d[1]), (d[2], d[3])]
        if k == 'c': return [(d[0], d[1])]
        return [((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)]
    for i, a in enumerate(own):
        for j in range(i + 1, len(own)):
            c = own[j]
            if not (a[1] & c[1]): continue
            if any(dist_to(c, x, y) <= 0.01 + (a[3][4] if a[2] == 's' else a[3][2] if a[2] == 'c' else 0) for x, y in pts(a)) or \
               any(dist_to(a, x, y) <= 0.01 + (c[3][4] if c[2] == 's' else c[3][2] if c[2] == 'c' else 0) for x, y in pts(c)):
                par[find(i)] = find(j)
    groups = {}
    for i, it in enumerate(own): groups.setdefault(find(i), []).append(it)
    return sorted(groups.values(), key=len, reverse=True)


def route(b, net, src, dst, items, margin=12):
    w = width_of(net); hw = w / 2
    xs = [v for it in src + dst for v in ((it[3][0], it[3][2]) if it[2] != 'c' else (it[3][0],))]
    ys = [v for it in src + dst for v in ((it[3][1], it[3][3]) if it[2] != 'c' else (it[3][1],))]
    bb = b.GetBoardEdgesBoundingBox()
    x0, y0 = max(mm(bb.GetX()) + 0.5, min(xs) - margin), max(mm(bb.GetY()) + 0.5, min(ys) - margin)
    x1, y1 = min(mm(bb.GetRight()) - 0.5, max(xs) + margin), min(mm(bb.GetBottom()) - 0.5, max(ys) + margin)
    g = Grid(b, x0, y0, x1, y1)
    others = [it for it in items if it[0] != net]
    # 層ごとの通れないセル（線の中心がそこに来ると、ほかのネットに近すぎる）
    block = {L: set() for L in LAYERS}; vblock = set()
    for it in others:
        k, d = it[2], it[3]
        if k == 's': bx0, by0, bx1, by1, r = min(d[0], d[2]), min(d[1], d[3]), max(d[0], d[2]), max(d[1], d[3]), d[4]
        elif k == 'c': bx0, by0, bx1, by1, r = d[0], d[1], d[0], d[1], d[2]
        else: bx0, by0, bx1, by1, r = d[0], d[1], d[2], d[3], 0
        reach = max(hw, VIA_D / 2) + CLR + r + G
        i0, j0 = g.ij(bx0 - reach, by0 - reach); i1, j1 = g.ij(bx1 + reach, by1 + reach)
        for i in range(max(0, i0), min(g.nx, i1 + 1)):
            for j in range(max(0, j0), min(g.ny, j1 + 1)):
                x, y = g.xy(i, j); dd = dist_to(it, x, y)
                for L in it[1]:
                    if dd < hw + CLR: block[L].add((i, j))
                if dd < VIA_D / 2 + CLR: vblock.add((i, j))
    def cells_of(group):
        out = set()
        for it in group:
            k, d = it[2], it[3]
            if k == 's':
                n = max(1, int(math.hypot(d[2] - d[0], d[3] - d[1]) / G))
                for s in range(n + 1):
                    x, y = d[0] + (d[2] - d[0]) * s / n, d[1] + (d[3] - d[1]) * s / n
                    for L in it[1]: out.add((L,) + g.ij(x, y))
            else:
                x, y = (d[0], d[1]) if k == 'c' else ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
                for L in it[1]: out.add((L,) + g.ij(x, y))
        return {c for c in out if 0 <= c[1] < g.nx and 0 <= c[2] < g.ny}
    S, T = cells_of(src), cells_of(dst)
    if not S or not T: return None
    tx = [c[1] for c in T]; ty = [c[2] for c in T]
    def h(c): return G * (max(0, min(tx) - c[1], c[1] - max(tx)) + max(0, min(ty) - c[2], c[2] - max(ty)))
    VIA_COST = 3.0
    dist = {c: 0 for c in S}; prev = {}; pq = [(h(c), 0, c) for c in S]; heapq.heapify(pq)
    end = None
    while pq:
        f, d0, c = heapq.heappop(pq)
        if d0 > dist.get(c, 1e9): continue
        if c in T: end = c; break
        L, i, j = c
        nbr = [((L, i + di, j + dj), G * math.hypot(di, dj)) for di in (-1, 0, 1) for dj in (-1, 0, 1) if di or dj]
        if (i, j) not in vblock: nbr.append(((LAYERS[1] if L == LAYERS[0] else LAYERS[0], i, j), VIA_COST))
        for n, cost in nbr:
            if not (0 <= n[1] < g.nx and 0 <= n[2] < g.ny): continue
            if (n[1], n[2]) in block[n[0]] and n not in T and n not in S: continue
            nd = d0 + cost
            if nd < dist.get(n, 1e9):
                dist[n] = nd; prev[n] = c; heapq.heappush(pq, (nd + h(n), nd, n))
    if end is None: return None
    path = [end]
    while path[-1] in prev: path.append(prev[path[-1]])
    path.reverse()
    # 直線ごとにまとめて線とビアを置く
    ni = b.FindNet(net); added = 0
    def pos(c): x, y = g.xy(c[1], c[2]); return pcbnew.VECTOR2I(M(x), M(y))
    k = 0
    while k < len(path) - 1:
        a = path[k]
        if path[k + 1][0] != a[0]:
            v = pcbnew.PCB_VIA(b); v.SetPosition(pos(a)); v.SetWidth(M(VIA_D)); v.SetDrill(M(VIA_H)); v.SetNet(ni); b.Add(v)
            k += 1; added += 1; continue
        d = (path[k + 1][1] - a[1], path[k + 1][2] - a[2]); m = k + 1
        while m + 1 < len(path) and path[m + 1][0] == a[0] and (path[m + 1][1] - path[m][1], path[m + 1][2] - path[m][2]) == d: m += 1
        t = pcbnew.PCB_TRACK(b); t.SetStart(pos(a)); t.SetEnd(pos(path[m])); t.SetWidth(M(w)); t.SetLayer(a[0]); t.SetNet(ni); b.Add(t)
        k = m; added += 1
    return added


def main(path):
    b = pcbnew.LoadBoard(path)
    nets = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            if n and n != 'GND' and not n.startswith('unconnected'): nets[n] = 1
    fixed = 0
    for net in nets:
        items = items_of(b)
        comps = components(items, net)
        while len(comps) > 1:
            n = route(b, net, comps[0], comps[1], items)
            if n is None:
                print('引けない:', net); break
            print('引いた: %s（線・ビア %d）' % (net, n)); fixed += 1
            items = items_of(b); comps = components(items, net)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(path)
    print('完了', fixed)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kicad', 'Serrasoid_TRX.kicad_pcb'))
