"""0〜300MHz のスプリアス（計算値）の図 docs/images/spurious_calc_0-300MHz.png を作る

  python3 docs/tools/spur/make_spurious_plot.py [台数]

実測ではなく計算。中身:
- 搬送波 29.3MHz、10W（+40dBm）
- 逓倍のずれによる側帯波（±1〜15 × 1.83125MHz）: spur_v12.py の時間領域計算（部品のばらつき 200 通り）に
  PLL の閉ループ・送信 BPF・7 次 LPF を掛けたもの。周波数ごとに 200 通りの最悪値
- 高調波（2〜10 倍）: PA（MRF101AN）が出す高調波は実測していないので、AB 級の目安の値を仮定し、LPF を掛けた。
  LPF の阻止域は部品の寄生成分で実際には −70dB 程度で頭打ちになるとして、それより深い減衰は −70dB にした
- 入っていないもの: 基板上の逓倍の信号（1.83〜14.65MHz など）が直接出力側へ飛び込む分、VCO の位相雑音、電源からの混入
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spur_v11 as V11          # BPF・LPF のモデル

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(ROOT, 'docs', 'images', 'spurious_calc_0-300MHz.png')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
P0 = 40.0                       # 搬送波 dBm（10W）
LIMIT = P0 - 50                 # 50mW 以下かつ −50dBc → 10W では −10dBm
FLOOR = -110                    # 図の下限
LPF_FLOOR = -70                 # LPF の阻止域の頭打ち（仮定）
# PA の高調波（LPF の前、dBc）: 実測なし。AB 級シングルエンドの目安
PA_HARM = {2: -20, 3: -15, 4: -30, 5: -25, 6: -40, 7: -35, 8: -45, 9: -40, 10: -50}

FW3 = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'
FW6 = '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
if not os.path.exists(FW3):
    FW3, FW6 = 'C:/Windows/Fonts/YuGothM.ttc', 'C:/Windows/Fonts/YuGothB.ttc'
for f in (FW3, FW6): fm.fontManager.addfont(f)
plt.rcParams['font.family'] = fm.FontProperties(fname=FW3).get_name()
BOLD = fm.FontProperties(fname=FW6)
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
C_V12, C_HARM, C_LIM = '#2a78d6', '#1baf7a', '#d03b3b'


def bpf_tuned(model, Cc):
    best = None
    for c1 in np.arange(20, 34, 0.1):
        for c2 in np.arange(20, 34, 0.25):
            v = model.bpf(model.FC, c1 * 1e-12, c2 * 1e-12, Cc=Cc)
            if best is None or v > best[0]: best = (v, c1 * 1e-12, c2 * 1e-12)
    g0, c1, c2 = best
    return lambda f: model.bpf(f, c1, c2, Cc=Cc) / g0


def v12_sidebands():
    import spur_v12 as S          # spur_v11 の F0 などを書き換えるので、ここで読む
    rng = np.random.default_rng(7)
    bpf = bpf_tuned(S.S, 1e-12)
    l0g = S.S.lpf(S.FC)
    worst = {}
    for _ in range(N):
        ev, l0 = S.sim(S.rnd(rng), tanks=True)
        Ph = S.edge_sidebands(ev, l0)
        if Ph is None: continue
        for m in range(1, 16):
            for sgn in (+1, -1):
                amp = abs(Ph[m if sgn > 0 else 16 - m])
                f = S.FC + sgn * m * S.F0
                if f <= 0: continue
                g = abs(S.hcl(m * S.F0)) * bpf(f) * max(S.S.lpf(f) / l0g, 10 ** (LPF_FLOOR / 20))
                d = 20 * np.log10(amp * g + 1e-15)
                worst[f] = max(worst.get(f, -999), d)
    return S.FC, worst


fc12, sb12 = v12_sidebands()
lpf_rel = lambda f: max(20 * np.log10(V11.lpf(f) / V11.lpf(fc12)), LPF_FLOOR)
harm = {k * fc12: PA_HARM[k] + lpf_rel(k * fc12) for k in PA_HARM}

fig, ax = plt.subplots(figsize=(12, 6.4), dpi=170)
fig.patch.set_facecolor(SURF)


def stems(ax, data, color, label, lw=1.6, z=3):
    xs = np.array(sorted(data)); ys = np.array([P0 + data[x] for x in xs])
    keep = ys > FLOOR
    xs, ys = xs[keep] / 1e6, ys[keep]
    ax.vlines(xs, FLOOR, ys, color=color, lw=lw, zorder=z, label=label)
    ax.plot(xs, ys, 'o', ms=3.2, color=color, zorder=z + 1)
    return xs, ys


ax.set_facecolor(SURF)
for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
for sp in ('left', 'bottom'): ax.spines[sp].set_color(INK2)
ax.tick_params(colors=INK2, labelsize=9)
ax.grid(True, color=GRID, lw=0.7, zorder=0)
ax.set_xlim(0, 300); ax.set_xticks(np.arange(0, 301, 25))
ax.set_ylim(FLOOR, 50)
ax.set_xlabel('周波数（MHz）', color=INK2, fontsize=10)
ax.set_ylabel('電力（dBm）', color=INK2, fontsize=10)
ax.axhline(LIMIT, color=C_LIM, lw=1.4, ls=(0, (6, 3)), zorder=2)
stems(ax, sb12, C_V12, '逓倍のずれによる側帯波（200 通りの最悪値）', lw=2.0, z=4)
stems(ax, harm, C_HARM, '高調波（PA の高調波は仮定、LPF 後）')
ax.vlines([fc12 / 1e6], FLOOR, P0, color=INK, lw=2.4, zorder=6)
ax.plot([fc12 / 1e6], [P0], 'o', ms=5, color=INK, zorder=7)
ax.text(fc12 / 1e6 + 3, P0 + 2, '搬送波 29.3MHz　+40dBm（10W）', fontsize=9, color=INK, va='bottom')
ax.text(298, LIMIT + 2, '規格 −10dBm（50mW 以下かつ −50dBc）', fontsize=9, color=C_LIM, ha='right', va='bottom')
for k in (2, 3, 4, 5):
    f = k * fc12
    ax.text(f / 1e6, P0 + harm[f] + 3, '%d 倍\n%.0fdBm' % (k, P0 + harm[f]), fontsize=8, color=INK2, ha='center', va='bottom')
w12 = max(sb12.values()); w12f = max(sb12, key=sb12.get)
ax.annotate('側帯波の最悪: %.2fMHz %+.0fdBm（%+.0fdBc）' % (w12f / 1e6, P0 + w12, w12),
            xy=(w12f / 1e6, P0 + w12), xytext=(36, 12),
            fontsize=8.5, color=INK2, arrowprops=dict(arrowstyle='-', color=INK2, lw=0.7))
ax.legend(loc='upper right', bbox_to_anchor=(1.0, 0.94), fontsize=8.5, frameon=False, labelcolor=INK2)

fig.suptitle('Serrasoid TRX 29M　送信スプリアス 0〜300MHz（Ver 1.2、計算値・実測ではない）', x=0.012, ha='left', fontsize=13,
             color=INK, fontproperties=BOLD)
fig.text(0.012, 0.925,
         '10W・アンテナ端。側帯波は逓倍のずれ（部品のばらつき 200 通り）に PLL・送信 BPF・7 次 LPF を掛けたもの。'
         '高調波は PA の値を仮定（2 倍 −20、3 倍 −15dBc ほか）、LPF の阻止域は −70dB で頭打ちとした。\n'
         '入っていないもの: 基板上の逓倍の信号の飛び込み、VCO の位相雑音、電源からの混入。完成後はスペクトラムアナライザで実測すること。'
         '図の下限 %ddBm。' % FLOOR, fontsize=8, color=INK2, va='top')
fig.tight_layout(rect=(0, 0, 1, 0.88))
fig.savefig(OUT, facecolor=SURF)
print('saved', OUT)
print('Ver 1.2 側帯波 最悪 %.1f dBc（%.3f MHz）、高調波 最大 %.1f dBc' % (w12, w12f / 1e6, max(harm.values())))
