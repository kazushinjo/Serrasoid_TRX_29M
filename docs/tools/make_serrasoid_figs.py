"""セラゾイド変調部の説明図（docs/images/*.png）を作る。matplotlib とヒラギノを使う"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images')
os.makedirs(OUT, exist_ok=True)
FW3 = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'
FW6 = '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
for f in (FW3, FW6): fm.fontManager.addfont(f)
plt.rcParams['font.family'] = fm.FontProperties(fname=FW3).get_name()
BOLD = fm.FontProperties(fname=FW6)
INK, QUIET, LINE, ACC, ACC2 = '#222222', '#666666', '#444444', '#1f6fb2', '#c0392b'

# ---------------------------------------------------------------- 1. 信号の流れ
def flow():
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=200)
    ax.set_xlim(0, 100); ax.set_ylim(0, 42); ax.axis('off')
    def box(x, y, w, h, name, sub, accent=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3,rounding_size=1.2',
                                    fc='#e8f1fa' if accent else 'white', ec=ACC if accent else LINE, lw=1.6 if accent else 1.0))
        ax.text(x + w / 2, y + h - 2.3, name, ha='center', va='center', fontsize=9.5, fontproperties=BOLD, color=INK)
        for i, s in enumerate(sub):
            ax.text(x + w / 2, y + h - 5.4 - i * 2.6, s, ha='center', va='center', fontsize=7.6, color=QUIET)
    def arrow(x1, y1, x2, y2, label=None, dy=1.2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color=LINE, lw=1.0))
        if label: ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, label, ha='center', fontsize=7.2, color=ACC2)
    # 上段: クロック → 4017 → 放電、定電流源 → のこぎり波
    box(1, 29, 15, 10, 'Si5351 CLK0', ['1.83125MHz', '送信中だけ出力'])
    box(20, 29, 15, 10, '74HCT123（2）', ['立ち上がりで', '約 70ns パルス'])
    box(39, 29, 15, 10, '2N7000', ['放電スイッチ', '546ns ごと'])
    box(58, 29, 18, 10, '2SA1015 定電流源', ['約 300µA', 'VR2 で傾き調整'])
    box(42, 15, 22, 10, 'C79 68pF', ['のこぎり波 RAMP', '0〜約 1.7V（TP3）'], accent=True)
    arrow(16, 34, 20, 34); ax.text(18, 40.2, '18.3MHz', ha='center', fontsize=7.2, color=ACC2)
    arrow(35, 34, 39, 34); ax.text(37, 40.2, 'RST', ha='center', fontsize=7.2, color=ACC2)
    arrow(46.5, 29, 50, 25)
    arrow(67, 29, 58, 25)
    box(1, 1, 22, 10, '送信音声', ['マイク → ×22 → ×11', 'クリップ → 3kHz LPF'])
    box(27, 1, 15, 10, 'VR3・VR4', ['偏移・中心', 'THRESH（TP4）'])
    arrow(23, 6, 27, 6)
    box(70, 15, 13, 10, '2SA1015 差動対', ['RAMP と', 'THRESH を比較'], accent=True)
    box(70, 1, 13, 10, '74HCT123（1）', ['幅 273ns', 'PM_OUT（TP6）'])
    box(86, 1, 13, 10, '逓倍 ×16・PLL', ['段間同調 → VCO', '29.3MHz（TP2）'])
    box(86, 15, 13, 10, '送信RF', ['BPF → 2N2222A', '→ IRF510 → MRF101AN'])
    arrow(64, 22, 70, 22); ax.text(67, 23.2, '+ RAMP', ha='center', fontsize=7.2, color=ACC2)
    ax.plot([42, 66, 66], [6, 6, 18], color=LINE, lw=1.0); arrow(66, 18, 70, 18)
    ax.text(54, 7.2, 'THRESH', ha='center', fontsize=7.2, color=ACC2); ax.text(67.6, 15.6, '−', ha='center', fontsize=8, color=ACC2)
    arrow(76.5, 15, 76.5, 11); ax.text(77.4, 13, 'COMP_N', ha='left', fontsize=7.2, color=ACC2)
    arrow(83, 6, 86, 6)
    arrow(92.5, 11, 92.5, 15); ax.text(93.4, 13, 'TXDRV', ha='left', fontsize=7.2, color=ACC2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'serrasoid_flow.png')); plt.close(fig)

# ---------------------------------------------------------------- 2. のこぎり波としきい値
def waves():
    T, tr = 0.546, 0.07                   # µs
    slope = 3.4                           # V/µs
    t = np.linspace(0, 3 * T, 6000)
    ph = np.mod(t, T)
    ramp = np.where(ph < tr, 0.0, (ph - tr) * slope)
    v0 = 0.85
    dv = 0.22 * np.sin(2 * np.pi * t / (3 * T) - np.pi / 2)    # 音声の変化（見やすく誇張）
    th = v0 + dv
    comp = (ramp > th).astype(float)
    # ワンショット: comp の立ち上がりから半周期（0.273µs）
    rise = np.where(np.diff(comp) > 0)[0]
    pm = np.zeros_like(t)
    for i in rise: pm[(t >= t[i]) & (t < t[i] + T / 2)] = 1
    q0 = (ph < tr).astype(float)
    fig, axs = plt.subplots(4, 1, figsize=(10, 6.2), dpi=200, sharex=True, gridspec_kw=dict(height_ratios=[1, 2.6, 1, 1]))
    for a in axs:
        for s in ('top', 'right'): a.spines[s].set_visible(False)
        a.tick_params(labelsize=8)
    axs[0].plot(t, q0, color=LINE, lw=1.1); axs[0].set_ylim(-0.2, 1.4); axs[0].set_yticks([])
    axs[0].set_ylabel('Q0\n(RST)', rotation=0, ha='right', va='center', fontsize=8.5)
    axs[1].plot(t, ramp, color=ACC, lw=1.3, label='RAMP（のこぎり波）')
    axs[1].plot(t, th, color=ACC2, lw=1.2, ls='--', label='THRESH（しきい値 = 中心 ＋ 音声）')
    for i in rise:
        axs[1].plot([t[i], t[i]], [0, th[i]], color=QUIET, lw=0.6, ls=':')
        axs[1].plot(t[i], th[i], 'o', ms=3.2, color=ACC2)
    axs[1].set_ylim(0, 2.1); axs[1].set_ylabel('V', rotation=0, fontsize=8.5)
    axs[1].legend(fontsize=7.8, loc='upper left', frameon=False, ncol=2)
    axs[1].text(t[rise[0]] + 0.03, 0.15, '交点のタイミングが\n音声で前後する', fontsize=7.6, color=QUIET)
    axs[2].plot(t, comp, color=LINE, lw=1.1); axs[2].set_ylim(-0.2, 1.4); axs[2].set_yticks([])
    axs[2].set_ylabel('比較の出力\n（反転して表示）', rotation=0, ha='right', va='center', fontsize=8.5)
    axs[3].plot(t, pm, color=ACC, lw=1.3); axs[3].set_ylim(-0.2, 1.4); axs[3].set_yticks([])
    axs[3].set_ylabel('PM_OUT\n(74HCT123)', rotation=0, ha='right', va='center', fontsize=8.5)
    axs[3].set_xlabel('時間（µs）　1 周期 = 0.546µs（1.83125MHz）', fontsize=8.5)
    fig.suptitle('しきい値が上がると交点（立ち上がり）が遅れ、下がると早まる（音声の振れは見やすく誇張）', fontsize=9.5, fontproperties=BOLD, x=0.02, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(os.path.join(OUT, 'serrasoid_waves.png')); plt.close(fig)

# ---------------------------------------------------------------- 3. XOR による 2 逓倍
def doubler():
    T = 1.0
    t = np.linspace(0, 2.2 * T, 4000)
    x = (np.mod(t, T) < T / 2).astype(float)
    tau = T / 4
    xd = (np.mod(t - tau, T) < T / 2).astype(float)
    # RC（0.69RC = T/4）を数周期まわして定常状態にし、74AC14（しきい値 0.6 / 0.4）で整形・反転
    RC = tau / 0.69; dt = t[1] - t[0]
    tt = np.arange(-6 * T, 2.2 * T, dt); xx = (np.mod(tt, T) < T / 2).astype(float)
    a = 0.0; out = 1.0; rcs = []; invs = []
    for v in xx:
        a += (v - a) * dt / RC
        if a > 0.6: out = 0.0
        elif a < 0.4: out = 1.0
        rcs.append(a); invs.append(out)
    n = len(t); rc = np.array(rcs[-n:]); inv = np.array(invs[-n:])
    y = np.logical_xor(x > 0.5, inv > 0.5).astype(float)
    fig, axs = plt.subplots(4, 1, figsize=(10, 4.8), dpi=200, sharex=True)
    rows = [(x, 'x（入力）', LINE), (rc, 'RC の後', QUIET), (inv, '74AC14\n（整形・反転）', LINE), (y, 'XOR 出力\n（2 倍の周波数）', ACC)]
    for a_, (v, name, c) in zip(axs, rows):
        a_.plot(t, v, color=c, lw=1.3); a_.set_ylim(-0.2, 1.3); a_.set_yticks([])
        a_.set_ylabel(name, rotation=0, ha='right', va='center', fontsize=8.5)
        for s in ('top', 'right'): a_.spines[s].set_visible(False)
        a_.tick_params(labelsize=8)
    for lv in (0.4, 0.6): axs[1].axhline(lv, color=QUIET, lw=0.6, ls=':')
    axs[1].text(2.21 * T, 0.6, 'VT+ 0.6', fontsize=7, color=QUIET, va='center'); axs[1].text(2.21 * T, 0.4, 'VT− 0.4', fontsize=7, color=QUIET, va='center')
    axs[2].annotate('', xy=(T + tau, 1.12), xytext=(T, 1.12), arrowprops=dict(arrowstyle='<->', color=ACC2, lw=1))
    axs[2].text(T + tau / 2, 1.2, 'τ = 入力周期の 1/4', ha='center', fontsize=7.8, color=ACC2)
    axs[3].set_xlabel('時間（入力周期 = 1）', fontsize=8.5)
    fig.suptitle('入力の両方のエッジで τ 幅のパルスが出るので、周波数は 2 倍、タイミングのズレ（位相）も 2 倍になる', fontsize=9.5, fontproperties=BOLD, x=0.02, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(os.path.join(OUT, 'serrasoid_doubler.png')); plt.close(fig)

if __name__ == '__main__':
    flow(); waves(); doubler()
    print('ok', OUT)
