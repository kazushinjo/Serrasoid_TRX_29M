# Serrasoid TRX 29M 送信スプリアス推定（逓倍部のばらつき → BPF → LPF）
import numpy as np, sys
F0 = 9.15625e6/10; T0 = 1/F0; FC = 32*F0; VCC = 5.0
STAGES = [(3.9e3,100e-12),(1.8e3,100e-12),(910,100e-12),(510,82e-12),(330,47e-12)]

def expand(ev, k=3):
    return [(t+m*T0, l) for m in range(-k, k+1) for (t, l) in ev]

def fold(evx):
    """expanded events -> one-period events (t in [0,T0)) and level at 0"""
    evx = sorted(evx)
    one = [(t, l) for t, l in evx if 0 <= t < T0]
    before = [l for t, l in evx if t < 0]
    return one, before[-1]

def rc_hyst(ev, l0, R, C, vtp, vtm):
    tau = R*C; v = VCC/2; s = 0; out = []
    for per in range(80):
        lvl = l0; t = 0.0
        for te, nl in ev + [(T0, None)]:
            tgt = VCC*lvl
            if s == 0 and tgt > vtp and v < vtp:
                tc = t + tau*np.log((tgt-v)/(tgt-vtp))
                if tc < te: s = 1; out.append((per, tc, 1))
            elif s == 1 and tgt < vtm and v > vtm:
                tc = t + tau*np.log(v/vtm)
                if tc < te: s = 0; out.append((per, tc, 0))
            v = tgt + (v-tgt)*np.exp(-(te-t)/tau); t = te
            if nl is not None: lvl = nl
    return [(t, l) for per, t, l in out if per == 79]

def xor(a, b, d_lh, d_hl):
    ea = expand(a); eb = expand(b)
    allev = sorted([(t, 'a', l) for t, l in ea] + [(t, 'b', l) for t, l in eb])
    la = ea[-1][1] ^ 0; lb = eb[-1][1]
    # initial levels: before the first event, level = opposite of first event's new level
    la = 1 - ea[0][1] if ea[0][0] == min(t for t,_ in ea) else la
    la = 1 - sorted(ea)[0][1]; lb = 1 - sorted(eb)[0][1]
    out = []
    for t, w, l in allev:
        if w == 'a': la = l
        else: lb = l
        y = la ^ lb
        out.append((t + (d_lh if y else d_hl), y))
    return fold(out)[0]

def sim(p):
    ev = [(1e-15, 1), ((0.5+p['d0'])*T0, 0)]; l0 = 0
    for k, (R, C) in enumerate(STAGES):
        R *= 1+p['dr'][k]; C = C*(1+p['dc'][k]) + p['cs'][k]
        cr = rc_hyst(ev, l0, R, C, p['vtp'][k], p['vtm'][k])
        b = [(t + (p['inv_hl'][k] if s else p['inv_lh'][k]), 1-s) for t, s in cr]
        b = fold(expand(b))[0]
        a = [(t + p['pin'][k], l) for t, l in ev]
        a = fold(expand(a))[0]
        ev = xor(a, b, p['x_lh'][k], p['x_hl'][k])
        l0 = 1 - ev[0][1]
    return ev, l0

def spectrum(ev, l0, nmax=110):
    n = np.arange(1, nmax+1); w = 2*np.pi*n/T0; c = np.zeros(nmax, complex)
    pts = [0.0] + [t for t, _ in ev] + [T0]; lv = l0
    for i in range(len(pts)-1):
        if lv: c += (np.exp(-1j*w*pts[i]) - np.exp(-1j*w*pts[i+1]))/(1j*w*T0)
        if i < len(ev): lv = ev[i][1]
    return n, 2*np.abs(c)

# ---- 送信 BPF: T30-6 17T（タップ 2T）× 2、上部結合 2pF ----
L = 3.6e-9*17**2; QU = 150; NT = 17/2
def bpf(f, C1, C2, Rs=110.0, Rl=56.0, Cc=2e-12):
    w = 2*np.pi*f; jw = 1j*w; GL = 1/(w*L*QU)
    Y = np.array([[1/(NT**2*Rs)+GL+1/(jw*L)+jw*(C1+Cc), -jw*Cc],
                  [-jw*Cc, 1/(NT**2*Rl)+GL+1/(jw*L)+jw*(C2+Cc)]])
    V = np.linalg.solve(Y, np.array([1/(NT*Rs), 0]))
    return abs(V[1]/NT)
def tune():
    best = None
    for c1 in np.arange(20, 32, 0.05):
        for c2 in np.arange(20, 32, 0.25):
            v = bpf(FC, c1*1e-12, c2*1e-12)
            if best is None or v > best[0]: best = (v, c1, c2)
    c2s = np.arange(best[2]-0.3, best[2]+0.3, 0.01)
    c2 = max(c2s, key=lambda c: bpf(FC, best[1]*1e-12, c*1e-12))
    return np.array([best[1], c2])*1e-12

# ---- 7 次チェビシェフ LPF（120p / 0.35µH / 220p / 0.39µH / 220p / 0.35µH / 120p）、T50-6 Q 200 ----
def lpf(f, R=50.0, Q=200):
    w = 2*np.pi*f; jw = 1j*w
    def Lz(Lv): return jw*Lv + w*Lv/Q
    Al = 3.6e-9*1.2  # unused
    A = np.eye(2, dtype=complex)
    def sh(C): return np.array([[1, 0], [jw*C, 1]])
    def se(Z): return np.array([[1, Z], [0, 1]])
    for m in [sh(120e-12), se(Lz(0.35e-6)), sh(220e-12), se(Lz(0.39e-6)), sh(220e-12), se(Lz(0.35e-6)), sh(120e-12)]:
        A = A @ m
    Vs = 1.0; vout = 2*R/(A[0,0]*R + A[0,1] + A[1,0]*R*R + A[1,1]*R)
    return abs(vout)

def rnd(rng, adjusted=True):
    vtp0 = rng.uniform(2.5, 3.1); vtm0 = rng.uniform(1.6, 2.1)
    U = lambda a, b: rng.uniform(a, b, 5)
    return dict(d0=rng.uniform(-0.01, 0.01) if adjusted else rng.uniform(-0.03, 0.03),
                dr=U(-.05, .05), dc=U(-.05, .05), cs=U(4e-12, 8e-12),
                vtp=vtp0+U(-.1, .1), vtm=vtm0+U(-.1, .1),
                inv_lh=5e-9+U(-1e-9, 1e-9), inv_hl=5e-9+U(-1e-9, 1e-9),
                x_lh=5e-9+U(-1e-9, 1e-9), x_hl=5e-9+U(-1e-9, 1e-9), pin=U(-.3e-9, .3e-9))

if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    rng = np.random.default_rng(7)
    C1, C2 = tune()
    print('BPF tuned C1=%.1fp C2=%.1fp' % (C1*1e12, C2*1e12))
    for d in [-5, -3.66, -2.75, -1.83, -0.92, 0, 0.92, 1.83, 2.75, 3.66, 5, 14.65, 29.3, 58.6]:
        f = FC + d*1e6
        print('  %+6.2f MHz (%6.2f): BPF %6.1f dB  LPF %6.1f dB' % (d, f/1e6, 20*np.log10(bpf(f, C1, C2)/bpf(FC, C1, C2)), 20*np.log10(lpf(f)/lpf(FC))))
    res = []
    for i in range(N):
        n, a = spectrum(*sim(rnd(rng)))
        car = a[31]
        f = n*F0
        g = np.array([bpf(x, C1, C2) for x in f])/bpf(FC, C1, C2) * np.array([lpf(x) for x in f])/lpf(FC)
        raw = 20*np.log10(a/car + 1e-12); out = 20*np.log10(a*g/car + 1e-12)
        res.append((raw, out))
    raw = np.array([r[0] for r in res]); out = np.array([r[1] for r in res])
    print('\nharm  f(MHz)   逓倍出力(中央/悪い5%)   ANT(中央/悪い5%)  dBc')
    for h in [16, 24, 28, 29, 30, 31, 33, 34, 35, 36, 40, 48, 64, 96]:
        i = h-1
        print('%3d %8.3f   %7.1f / %7.1f      %7.1f / %7.1f' % (h, h*F0/1e6, np.median(raw[:, i]), np.percentile(raw[:, i], 95), np.median(out[:, i]), np.percentile(out[:, i], 95)))
    m = np.delete(out, 31, axis=1)
    worst = m.max(axis=1); idx = np.delete(np.arange(1, 111), 31)[m.argmax(axis=1)]
    print('\n最大スプリアス(ANT, 高調波を除く PA 非線形なし): 中央 %.1f dBc / 悪い5%% %.1f dBc / 最悪 %.1f dBc' % (np.median(worst), np.percentile(worst, 95), worst.max()))
    vals, cnt = np.unique(idx, return_counts=True)
    print('最大になる次数:', dict(zip((vals*F0/1e6).round(2), cnt)))
