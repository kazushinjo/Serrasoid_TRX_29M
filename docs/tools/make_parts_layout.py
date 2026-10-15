# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 JA6FUF (kazushinjo)
"""
部品実装図（docs/Serrasoid_TRX_部品実装図.pdf）と配置図 PNG を作る。PSN_TRX の docs/tools/make_parts_layout.py が元。

  1) KiCad 付属の Python で基板データを書き出す
       /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
           docs/tools/export_board.py kicad/Serrasoid_TRX.kicad_pcb board.json
  2) matplotlib のある Python で作図する
       python3 docs/tools/make_parts_layout.py board.json docs/Serrasoid_TRX_部品実装図.pdf [PNG の出力先フォルダ]

部品表（ブロック・値・種類・注意）は tools/circuit.py から作る。区画は tools/gen_pcb.py の REGIONS。
ブロックの順（BLOCKS）が組立順の目安。
"""
import ast, json, math, os, re, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, Circle, Ellipse, Polygon
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.transforms as mtrans

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import circuit

FW3 = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'
FW6 = '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
if not os.path.exists(FW3):   # Windows: 游ゴシック（PSN_TRX と同じ）
    FW3, FW6 = 'C:/Windows/Fonts/YuGothM.ttc', 'C:/Windows/Fonts/YuGothB.ttc'
for f in (FW3, FW6):
    fm.fontManager.addfont(f)
plt.rcParams['font.family'] = fm.FontProperties(fname=FW3).get_name()
BOLD = fm.FontProperties(fname=FW6)

board = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
PNGDIR = sys.argv[3] if len(sys.argv) > 3 else None

TITLE = 'Serrasoid TRX 29M　部品実装図'
SUB = '基板 170 × 130 mm / 4 層 / すべてリード部品（表面実装なし）　Ver 1.0　2026-10-16'
COPPER = '#c8762f'
FAB = '#333333'
FAINT = '#c8c8c8'
NAVY = '#1f2d6b'
# 組立順の目安: 電源を先に付けて電圧を確かめ、制御（XIAO・Si5351）→ 変調 → 逓倍 → 送信音声 → 送信RF → 受信
BLOCKS = [
    ('電源', '#f6c27a', ['ヒューズ（5A）は後面パネル側。U2 L7808 には小型放熱器を付ける',
                        '付け終わったら 13.8V を入れ、+8V・+5V（2 系統）・+3.3V を確認してから次へ']),
    ('制御', '#b9b2ec', ['XIAO（U5）はソケット、Si5351 モジュール（U6 AE-Si5351A）はピンヘッダで実装',
                        'XIAO の D0（PTT）・D9（エンコーダ SW）は起動設定ピン: PTT・つまみを押したまま電源を入れない']),
    ('セラゾイド変調', '#f0b8d8', ['C19（100p）は C0G（NP0）必須。のこぎり波の直線性に直結',
                                 'TP1（RAMP）・TP2（THRESH）・TP3（PM）で波形を確認できる']),
    ('逓倍', '#a9c8ef', ['U10・U11・U12 は必ず AC 品（74AC14・74AC86）。HC・HCT 品では 29MHz まで上がらない',
                        '遅延の C（C23〜C27）は NP0。TP4 で 29.3MHz を確認']),
    ('送信音声', '#d6e6a4', ['VR3 マイク利得、VR4 周波数偏移（±5kHz）、VR5 しきい値の中心']),
    ('送信RF', '#f2aaa8', ['Q5 RD06HHF1 は放熱器 HS1 に固定。Q6 RD16HHF1 は基板端に立て、ケースの放熱器にねじ止め（絶縁不要）',
                          'C58 は積層セラミック（X7R・100V）。LPF の C59〜C62 は NP0 500V。コイルの巻数は表のとおり']),
    ('受信', '#a8dcb4', ['FL1（10.7MHz 水晶フィルタ 10M15A）・FL2（455kHz セラミックフィルタ）は 3 ピンで中央が GND',
                        'TC3・TC4 は 29.3MHz に同調']),
]
BCOL = {n: c for n, c, _ in BLOCKS}

# 区画（tools/gen_pcb.py の REGIONS）
src = open(os.path.join(ROOT, 'tools', 'gen_pcb.py')).read()
REGIONS = ast.literal_eval(re.search(r'REGIONS = (\{.*?\})', src, re.S).group(1))

FP = {f['ref']: f for f in board['fps']}
xs = [p[0] for e in board['edge'] for p in (e.get('p') or [e.get('a'), e.get('b')]) if p]
ys = [p[1] for e in board['edge'] for p in (e.get('p') or [e.get('a'), e.get('b')]) if p]
BX0, BX1, BY0, BY1 = min(xs), max(xs), min(ys), max(ys)


# ---------------------------------------------------------------- 部品表（circuit.py から）
def kind(p):
    s, fp, r = p['sym'], p['fp'], p['ref']
    if s == 'Device:R': return '抵抗'
    if s == 'Device:C': return '積層セラミックC' if '積層' in p['note'] else 'セラミックコンデンサ'
    if s == 'Device:C_Polarized': return '電解コンデンサ'
    if s == 'Device:C_Trim': return 'トリマコンデンサ'
    if s == 'Device:R_Potentiometer_Trim': return '半固定抵抗'
    if s == 'Connector:TestPoint': return 'テストポイント'
    if s.startswith('Connector_Generic'): return '線材' if 'SolderWire' in fp else 'ピンヘッダ'
    if r.startswith('D'): return 'ダイオード'
    if r.startswith('Q'): return 'トランジスタ/FET'
    if r.startswith('K'): return 'リレー'
    if r.startswith('X') or r.startswith('FL'): return '水晶/フィルタ'
    if r.startswith('T') or r.startswith('L'): return 'トロイダル' if ('T3' in fp or 'T5' in fp or 'BN43' in fp or 'FT' in p['value']) else 'コイル'
    if 'XIAO' in s: return 'マイコン(ソケット)'
    if 'Si5351' in s: return 'モジュール'
    if 'Regulator' in s or 'Converter' in s: return 'レギュレータ'
    return 'IC(ソケット)' if 'Socket' in fp else 'IC'


def caution(p):
    k, n, fp = kind(p), p['note'], p['fp']
    out = []
    if k == '電解コンデンサ': out.append('極性: □パッドが＋')
    if k == 'ダイオード': out.append('極性: □パッドが K')
    if k == 'トランジスタ/FET' or (k == 'レギュレータ' and 'TO-92' in fp): out.append('□パッドが 1 番ピン')
    if k in ('IC', 'IC(ソケット)'): out.append('1 番ピン（□）の向き')
    if k == 'トロイダル' and n:
        out.append(re.sub(r'（[^）]*）', '', n.split('。')[-1 if 'BN43' in fp else 0]).strip())
        return '、'.join(out)
    for key in ('NP0', 'C0G', '500V', 'AC 品', 'HCT', '25V', '放熱', 'ソケット', '積層', '0.8mm'):
        if key in n:
            # 注記のうち、その言葉を含む区切り（「。」「、」）を 1 つ採る
            seg = [s for s in re.split('[。]', n) if key in s][0]
            seg = re.sub(r'（[^）]*）', '', seg).strip('、 ')
            if seg and seg not in out: out.append(seg)
            break
    return '、'.join(out)


ROWS = {n: [] for n, _, _ in BLOCKS}
for p in circuit.parts:
    if p['ref'].startswith('#'): continue
    ROWS[p['block']].append([p['ref'], p['value'], kind(p), caution(p)])
ROWS['送信RF'].append(['HS1', FP['HS1']['val'], '放熱器', 'Q5 をねじ止めしてからはんだ付け'])
BLOCK_OF = {r[0]: n for n, rows in ROWS.items() for r in rows}


# ---------------------------------------------------------------- 描画
def draw_shape(ax, s, col, lw):
    t = s['t']
    if t == 'seg':
        ax.plot([s['a'][0], s['b'][0]], [s['a'][1], s['b'][1]], color=col, lw=lw, solid_capstyle='round')
    elif t == 'poly':
        ax.add_patch(Polygon(s['p'], closed=True, fill=bool(s.get('fill')), fc=col if s.get('fill') else 'none', ec=col, lw=lw))
    elif t == 'circ':
        ax.add_patch(Circle(s['c'], s['r'], fill=bool(s.get('fill')), fc=col if s.get('fill') else 'none', ec=col, lw=lw))
    elif t == 'arc3':
        (x1, y1), (x2, y2), (x3, y3) = s['a'], s['m'], s['b']
        d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        if abs(d) < 1e-9:
            return
        ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
        uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
        r = math.hypot(x1 - ux, y1 - uy)
        a1, a2, am = (math.atan2(y - uy, x - ux) for x, y in ((x1, y1), (x3, y3), (x2, y2)))
        def norm(a, ref):
            while a < ref:
                a += 2 * math.pi
            return a
        e1 = norm(a2, a1); m1 = norm(am, a1)
        if m1 > e1:
            e1 -= 2 * math.pi
        n = 30
        pts = [(ux + r * math.cos(a1 + (e1 - a1) * k / n), uy + r * math.sin(a1 + (e1 - a1) * k / n)) for k in range(n + 1)]
        ax.plot([x for x, y in pts], [y for x, y in pts], color=col, lw=lw)


def draw_pad(ax, p, fc, ec):
    x, y = p['c']
    w, h = p['sz']
    tr = mtrans.Affine2D().rotate_deg_around(x, y, -p['ang']) + ax.transData
    if p['sh'] == 'circle':
        ax.add_patch(Circle((x, y), w / 2, fc=fc, ec=ec, lw=0.3))
    elif p['sh'] == 'oval':
        ax.add_patch(Ellipse((x, y), w, h, fc=fc, ec=ec, lw=0.3, transform=tr))
    else:
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=fc, ec=ec, lw=0.3, transform=tr))
    if p['drill'] > 0:
        ax.add_patch(Circle((x, y), p['drill'] / 2, fc='white', ec='none'))


def draw_fp(ax, f, mode, small=False):
    """mode: 'normal' / 'faint'"""
    col = FAB if mode != 'faint' else FAINT
    for s in f['fab']:
        draw_shape(ax, s, col, 0.5 if mode != 'faint' else 0.4)
    for p in f['pads']:
        if mode == 'faint':
            draw_pad(ax, p, 'white', FAINT)
        else:
            draw_pad(ax, p, COPPER, '#7a4a1c')
    if mode != 'faint':
        (x0, y0), (x1, y1) = f['bbox']
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ax.text(cx, cy, 'U5 (XIAO)' if f['ref'] == 'U5' else f['ref'], ha='center', va='center', fontsize=4.0 if small else 5.2, color=NAVY, fontproperties=BOLD,
                zorder=20, bbox=dict(fc='white', ec='none', alpha=0.65, pad=0.15))
        if not small and f['val'] and not f['ref'].startswith(('H', 'J', 'TP')):
            ax.text(cx, cy + 1.6, f['val'][:14], ha='center', va='center', fontsize=3.2, color='#555555', zorder=20)


def board_axes(fig, rect):
    ax = fig.add_axes(rect)
    ax.set_xlim(BX0 - 2, BX1 + 2)
    ax.set_ylim(BY1 + 5, BY0 - 5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.add_patch(Rectangle((BX0, BY0), BX1 - BX0, BY1 - BY0, fill=False, ec='black', lw=1.4, zorder=30))
    ax.text((BX0 + BX1) / 2, BY0 - 1.2, '↑ 後面（DC 入力・RD16HHF1・ANT）', ha='center', va='bottom', fontsize=6.5, color='#555555')
    ax.text((BX0 + BX1) / 2, BY1 + 1.2, '↓ 前面', ha='center', va='top', fontsize=6.5, color='#555555')
    return ax


def header(fig, sub_title, page, total):
    fig.text(0.015, 0.965, f'{TITLE}（部品面）', fontsize=13, fontproperties=BOLD, va='top')
    fig.text(0.015, 0.932, SUB, fontsize=7.5, color='#444444', va='top')
    if sub_title:
        fig.text(0.015, 0.905, sub_title, fontsize=11, fontproperties=BOLD, va='top', color=NAVY)
    fig.text(0.985, 0.012, f'{page} / {total}', fontsize=7, ha='right', color='#666666')


def draw_blocks(ax, only=None, alpha=0.32):
    for name, (x0, y0, x1, y1) in REGIONS.items():
        a = alpha if (only is None or name == only) else 0.06
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=BCOL.get(name, '#dddddd'), ec='none', alpha=a, zorder=0))


SHORT_TYPE = {'セラミックコンデンサ': 'セラC', '積層セラミックC': '積層C', '電解コンデンサ': '電解C', 'トランジスタ/FET': 'Tr/FET', 'トリマコンデンサ': 'トリマC',
              '半固定抵抗': '半固定VR', 'IC(ソケット)': 'IC(ｿｹｯﾄ)', 'マイコン(ソケット)': 'マイコン', 'テストポイント': 'TP', '水晶/フィルタ': '水晶/FL', 'トロイダル': 'ﾄﾛｲﾀﾞﾙ', 'ダイオード': 'ﾀﾞｲｵｰﾄﾞ', 'レギュレータ': 'ﾚｷﾞｭﾚｰﾀ'}


def fit(v, width_pt, fs):
    """列幅（pt）に収まるよう末尾を「…」で切る（全角 1.0、半角 0.55 文字幅で概算）"""
    import unicodedata
    w = lambda c: 1.0 if unicodedata.east_asian_width(c) in 'WF' else 0.62
    if sum(w(c) for c in v) * fs <= width_pt:
        return v
    out = ''
    for c in v:
        if (sum(w(x) for x in out) + w(c) + 1.0) * fs > width_pt:
            return out + '…'
        out += c
    return out


A4 = (11.69, 8.27)


def table(fig, rect, rows, color):
    """rows: [[部品番号, 値, 種類, 注意]]。40 行を超えたら 2 段組み。"""
    cols = ['部品番号', '値/型番', '種類', '注意']
    n = len(rows)
    per = n if n <= 40 else math.ceil(n / 2)
    chunks = [rows[i:i + per] for i in range(0, n, per)]
    x0, y0, w, h = rect
    cw = w / len(chunks)
    for ci, ch in enumerate(chunks):
        ax = fig.add_axes([x0 + ci * cw, y0, cw - 0.005, h])
        ax.axis('off')
        rh = min(0.034 / h, 1.0 / (len(ch) + 1))
        widths = [0.13, 0.24, 0.21, 0.42] if len(chunks) == 1 else [0.14, 0.25, 0.17, 0.44]
        xs_ = [sum(widths[:i]) for i in range(4)]
        fs = 6.2 if len(chunks) == 1 else 5.2
        ax.add_patch(Rectangle((0, 1 - rh), 1, rh, fc=color, ec='#888888', lw=0.4))
        for i, c in enumerate(cols):
            ax.text(xs_[i] + 0.01, 1 - rh / 2, c, fontsize=fs, va='center', color='white', fontproperties=BOLD)
        for r, row in enumerate(ch):
            yy = 1 - rh * (r + 2)
            ax.add_patch(Rectangle((0, yy), 1, rh, fc='#f3f3f3' if r % 2 else 'white', ec='#bbbbbb', lw=0.3))
            for i, v in enumerate(row):
                v = str(v)
                if i == 2:
                    v = SHORT_TYPE.get(v, v) if len(chunks) > 1 else {'セラミックコンデンサ': 'セラミックC'}.get(v, v)
                f_i = fs if i < 3 else fs - 0.6
                v = fit(v, widths[i] * cw * A4[0] * 72 - 3, f_i)
                ax.text(xs_[i] + 0.01, yy + rh / 2, v, fontsize=f_i, va='center',
                        fontproperties=BOLD if i == 0 else None, color=NAVY if i == 0 else 'black', clip_on=True)
        for xv in xs_[1:]:
            ax.plot([xv, xv], [1 - rh * (len(ch) + 1), 1], color='#bbbbbb', lw=0.3)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)


pages_total = 1 + len(BLOCKS)
pdf = PdfPages(OUT, metadata={'Title': 'Serrasoid TRX 29M 部品実装図 Ver1.0', 'Author': 'JA6FUF'})
n_parts = sum(len(r) for r in ROWS.values())

# ---- 1. 全体図
fig = plt.figure(figsize=A4)
header(fig, f'全体図（{n_parts} 点、取付穴 H1〜H4 を除く）', 1, pages_total)
ax = board_axes(fig, [0.03, 0.10, 0.94, 0.78])
draw_blocks(ax)
for f in board['fps']:
    draw_fp(ax, f, 'normal', small=True)
fig.text(0.03, 0.075, '□（四角）パッド = 1 番ピン / 電解コンデンサの＋ / ダイオードの K（カソード）。H1〜H4 = M3 取付穴（GND）。', fontsize=7)
fig.text(0.03, 0.055, '抵抗・ダイオードはすべて縦置き。IC はすべて DIP ソケット。上辺がケースの後面側。', fontsize=7)
fig.text(0.03, 0.035, 'ブロック別の詳細と部品表は次ページ以降（組立順の目安: 1→%d）。' % len(BLOCKS), fontsize=7)
lx = 0.60
for i, (name, col, _) in enumerate(BLOCKS):
    yy = 0.075 - (i % 3) * 0.02; xx = lx + (i // 3) * 0.13
    fig.patches.append(Rectangle((xx, yy - 0.006), 0.015, 0.012, transform=fig.transFigure, fc=col, ec='#888888', lw=0.4, alpha=0.8))
    fig.text(xx + 0.02, yy, f'{i + 1} {name}', fontsize=6.5, va='center')
pdf.savefig(fig)
if PNGDIR:
    fig.savefig(os.path.join(PNGDIR, 'layout_overview.png'), dpi=200)
plt.close(fig)

# ---- ブロック別
for bi, (name, col, memo) in enumerate(BLOCKS):
    rows = ROWS[name]
    fig = plt.figure(figsize=A4)
    header(fig, f'{bi + 1}. {name}（{len(rows)}点）', bi + 2, pages_total)
    ax = board_axes(fig, [0.01, 0.06, 0.60, 0.76])
    draw_blocks(ax, only=name)
    refs = set(r[0] for r in rows)
    for f in board['fps']:
        draw_fp(ax, f, 'normal' if f['ref'] in refs else 'faint')
    # 区画の外に置かれた部品は紫の枠で示す
    x0, y0, x1, y1 = REGIONS[name]
    for f in board['fps']:
        if f['ref'] in refs:
            (a, b), (c, d) = f['bbox']
            if a < x0 - 0.5 or c > x1 + 0.5 or b < y0 - 0.5 or d > y1 + 0.5:
                ax.add_patch(Rectangle((a, b), c - a, d - b, fill=False, ec='#7b3fbf', ls=':', lw=0.8, zorder=25))
    tcol = {'#f6c27a': '#d9922f', '#b9b2ec': '#7d73c9', '#f0b8d8': '#c96f9f', '#a9c8ef': '#5b8fd0',
            '#d6e6a4': '#8aa63e', '#f2aaa8': '#d0605c', '#a8dcb4': '#4fa766'}.get(col, col)
    table(fig, [0.625, 0.06, 0.365, 0.82], rows, tcol)
    for k, line in enumerate(memo):
        fig.text(0.015, 0.878 - k * 0.018, line, fontsize=7, va='top', color='#333333')
    pdf.savefig(fig); plt.close(fig)
pdf.close()
print('pages', pages_total, 'parts', n_parts, OUT)

# ---- 配置図 PNG（全体、部品番号・値入り）
if PNGDIR:
    W_MM, H_MM = (BX1 - BX0) + 4, (BY1 - BY0) + 4
    fig = plt.figure(figsize=(W_MM / 25.4 * 1.6, H_MM / 25.4 * 1.6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(BX0 - 2, BX1 + 2); ax.set_ylim(BY1 + 2, BY0 - 2); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((BX0, BY0), BX1 - BX0, BY1 - BY0, fill=False, ec='black', lw=1.2, zorder=30))
    draw_blocks(ax, alpha=0.35)
    for f in board['fps']:
        draw_fp(ax, f, 'normal')
    fig.savefig(os.path.join(PNGDIR, 'layout_full.png'), dpi=330); plt.close(fig)
    print('png', PNGDIR)
