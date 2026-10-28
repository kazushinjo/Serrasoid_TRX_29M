# 対策後の構成: 基準 1.83125MHz（CLK0 18.3125MHz ÷10）→ ×2 ×4 段（×16）、
# 段 1〜3 の後に LC 同調（Q 約 5）＋ 74HCU04 自己バイアスで矩形に戻す、最後に PLL 追従（74AC74 PFD・VCO）
import numpy as np, sys
import spur_v11 as S

F0 = 18.3125e6/10; T0 = 1/F0; FC = 16*F0; VCC = 5.0
S.F0, S.T0, S.FC = F0, T0, FC
STAGES = [(1.8e3, 100e-12), (910, 100e-12), (510, 82e-12), (330, 47e-12)]
# 同調回路: (L, C, 直列抵抗 Rs, インダクタ Qu) 3.66 / 7.33 / 14.65MHz
TANKS = [(10e-6, 180e-12, 1e3, 40), (4.7e-6, 100e-12, 1e3, 40), (1.0e-6, 120e-12, 470, 40)]
CSTRAY = 7e-12      # HCU04 入力・結合 C・配線
NH = 600            # 再構成に使う高調波数（F0 の倍数）

def coeffs(ev, l0, nmax=NH):
    n = np.arange(1, nmax+1); w = 2*np.pi*n/T0; c = np.zeros(nmax, complex)
    pts = [0.0] + [t for t, _ in ev] + [T0]; lv = l0
    for i in range(len(pts)-1):
        if lv: c += (np.exp(-1j*w*pts[i]) - np.exp(-1j*w*pts[i+1]))/(1j*w*T0)
        if i < len(ev): lv = ev[i][1]
    return n, c          # x(t) = c0 + sum 2 Re(c_n e^{j n w0 t})

def tank_square(ev, l0, Lt, Ct, Rs, Qu, dC, dL, t_lh, t_hl):
    n, c = coeffs(ev, l0)
    w = 2*np.pi*n*F0
    Lv = Lt*(1+dL); Cv = Ct*(1+dC) + CSTRAY
    Zl = 1j*w*Lv + w*Lv/Qu; Zc = 1/(1j*w*Cv)
    Zp = Zl*Zc/(Zl+Zc)
    h = Zp/(Rs+10+Zp)             # 74AC86 出力抵抗 約 10Ω
    # 1MΩ 帰還のバイアスで、しきい値 = 入力の平均（DC 成分は結合 C で除く）
    N = 1 << 15; t = np.arange(N)/N*T0
    X = np.zeros(N, complex); X[1:NH+1] = c*h; X[-NH:] = np.conj((c*h)[::-1])
    v = np.real(np.fft.ifft(X))*N
    s = v > 0; out = []
    for i in np.nonzero(s != np.roll(s, -1))[0]:
        j = (i+1) % N
        frac = v[i]/(v[i]-v[j]); tc = (i+frac)/N*T0
        rising = not s[i]
        # 反転出力: 入力の立ち上がり → 出力の立ち下がり
        out.append(((tc + (t_hl if rising else t_lh)) % T0, 0 if rising else 1))
    out.sort()
    return out, 1-out[0][1]

def sim(p, tanks=True):
    ev = [(1e-15, 1), ((0.5+p['d0'])*T0, 0)]; l0 = 0
    for k, (R, C) in enumerate(STAGES):
        R *= 1+p['dr'][k]; C = C*(1+p['dc'][k]) + p['cs'][k]
        cr = S.rc_hyst(ev, l0, R, C, p['vtp'][k], p['vtm'][k])
        b = [(t + (p['inv_hl'][k] if s else p['inv_lh'][k]), 1-s) for t, s in cr]
        b = S.fold(S.expand(b))[0]
        a = S.fold(S.expand([(t + p['pin'][k], l) for t, l in ev]))[0]
        ev = S.xor(a, b, p['x_lh'][k], p['x_hl'][k]); l0 = 1-ev[0][1]
        if tanks and k < 3:
            Lt, Ct, Rs, Qu = TANKS[k]
            ev, l0 = tank_square(ev, l0, Lt, Ct, Rs, Qu, p['tc'][k], p['tl'][k], p['u_lh'][k], p['u_hl'][k])
    return ev, l0

# ---- PLL（PFD 74AC74、能動ループフィルタ、VCO）。立ち上がりエッジの時刻ずれを位相とみて閉ループ伝達で絞る
KD = VCC/(2*np.pi)            # V/rad（UP−DN の差動）
KV = 2*np.pi*0.2e6            # rad/s/V（1N4007 可変容量、約 0.2MHz/V）
R1, R2, CI = 11.2e3, 1.5e3, 10e-9
P1 = 1/(2*np.pi*2.8e3*220e-12); P2 = 1/(2*np.pi*1e3*470e-12)
def hcl(f, kv=KV):
    s = 2j*np.pi*f
    G = KD*kv*(1+s*R2*CI)/(s*R1*CI)/s/(1+s/(2*np.pi*P1))/(1+s/(2*np.pi*P2))/(1+s/(2*np.pi*1e6))   # MCP6002 の GBW 1MHz
    return G/(1+G)

def edge_sidebands(ev, l0):
    """立ち上がりエッジ（16 個/周期）の理想位置からのずれ → 搬送波 FC 周りの側帯波（複素振幅）"""
    r = sorted(t for t, l in ev if l == 1)
    if len(r) != 16: return None
    r = np.array(r); k = np.arange(16)
    off = np.angle(np.mean(np.exp(2j*np.pi*(r/T0*16 - k))))   # 平均位相を除く
    ph = 2*np.pi*(r/T0*16 - k) - off
    ph = (ph + np.pi) % (2*np.pi) - np.pi
    Ph = np.fft.fft(ph)/16                       # m = 0..15 → 側帯波 ±m F0
    return Ph

def rnd(rng):
    p = S.rnd(rng)
    p = {k: (v[:4] if isinstance(v, np.ndarray) else v) for k, v in p.items()}
    U = lambda a, b, n=3: rng.uniform(a, b, n)
    p.update(tc=U(-.05, .05), tl=U(-.10, .10), u_lh=6e-9+U(-1.5e-9, 1.5e-9), u_hl=6e-9+U(-1.5e-9, 1.5e-9))
    return p

if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    Cc = float(sys.argv[2])*1e-12 if len(sys.argv) > 2 else 1e-12
    rng = np.random.default_rng(7)
    bpf = lambda f, c1, c2: S.bpf(f, c1, c2, Cc=Cc)
    best = None
    for c1 in np.arange(20, 34, 0.05):
        for c2 in np.arange(20, 34, 0.25):
            v = bpf(FC, c1*1e-12, c2*1e-12)
            if best is None or v > best[0]: best = (v, c1, c2)
    C1, C2 = best[1]*1e-12, best[2]*1e-12
    g0 = bpf(FC, C1, C2); l0g = S.lpf(FC)
    print('BPF 上部結合 %.1fp: 同調 C1=%.1fp C2=%.1fp  挿入損 %.1f dB' % (Cc*1e12, C1*1e12, C2*1e12, 20*np.log10(g0)))
    for d in [-3.66, -1.83, -0.5, -0.1, 0.1, 0.5, 1.83, 3.66, 14.65, 29.3]:
        f = FC+d*1e6
        print('  %+6.2f MHz: BPF %6.1f dB  PLL %6.1f dB  LPF %6.1f dB' % (d, 20*np.log10(bpf(f, C1, C2)/g0),
              20*np.log10(abs(hcl(abs(d)*1e6))), 20*np.log10(S.lpf(f)/l0g)))
    for kv in [0.1e6, 0.2e6, 0.4e6]:
        fs = np.logspace(2, 6.5, 400); h = abs(hcl(fs, 2*np.pi*kv))
        print('  KV %.1fMHz/V: 閉ループ −3dB %.0f kHz、ピーク %+.1f dB、3kHz で %+.2f dB' % (kv/1e6, fs[np.argmax(h < 0.707)]/1e3, 20*np.log10(h.max()), 20*np.log10(abs(hcl(3e3, 2*np.pi*kv)))))
    rows = {}
    for mode in ['old', 'tank']:
        r16 = []; ant = []
        for i in range(N):
            p = rnd(rng)
            ev, l0 = sim(p, tanks=(mode == 'tank'))
            n, a = S.spectrum(ev, l0, 60)
            car = a[15]
            raw = 20*np.log10(np.delete(a, 15)/car + 1e-15)
            Ph = edge_sidebands(ev, l0)
            if Ph is None:
                r16.append(raw.max()); ant.append(np.nan); continue
            sb = []
            for m in range(1, 9):
                for sgn in (+1, -1):
                    amp = abs(Ph[m if sgn > 0 else 16-m])
                    f = FC + sgn*m*F0
                    g = abs(hcl(m*F0)) * bpf(f, C1, C2)/g0 * S.lpf(f)/l0g
                    sb.append(20*np.log10(amp*g + 1e-15))
            r16.append(raw.max()); ant.append(max(sb))
        rows[mode] = (np.array(r16), np.array(ant))
        print('\n[%s] ×16 出力の最大スプリアス（16 次以外、搬送波比）: 中央 %.1f / 悪い5%% %.1f dBc' %
              ('同調なし' if mode == 'old' else '段間同調あり', np.median(r16), np.percentile(r16, 95)))
        bad = np.isnan(ant); a2 = np.array(ant)[~bad]
        print('      ×16 のエッジが欠ける（PLL がロックできない）: %d / %d 台' % (bad.sum(), len(ant)))
        if len(a2): print('      PLL・BPF・LPF 後（ANT、±1〜8 F0 の側帯波）: 中央 %.1f / 悪い5%% %.1f / 最悪 %.1f dBc' %
              (np.median(a2), np.percentile(a2, 95), np.max(a2)))
