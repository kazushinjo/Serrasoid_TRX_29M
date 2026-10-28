"""基板の確認用: ネットごとの配線長（circuit.py の名前で）と主要部品の位置。KiCad 付属の Python で実行"""
import pcbnew, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from circuit import parts
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pin = {(p['ref'], k): n for p in parts for k, n in p['pins'].items() if n}
b = pcbnew.LoadBoard(os.path.join(ROOT, 'kicad', 'Serrasoid_TRX.kicad_pcb'))
cn = {}
for f in b.GetFootprints():
    for pd in f.Pads():
        k = (f.GetReference(), pd.GetNumber())
        if k in pin: cn[pd.GetNetname()] = pin[k]
L, W = {}, {}
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK':
        n = cn.get(t.GetNetname(), t.GetNetname()); L[n] = L.get(n, 0) + pcbnew.ToMM(t.GetLength())
        W[n] = min(W.get(n, 9), pcbnew.ToMM(t.GetWidth()))
vias = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
print('配線 合計 %.0f mm、ビア %d' % (sum(L.values()), vias))
groups = [('送信RF', ['TXDRV', 'TXBPF_IN', 'TB1', 'TB2', 'TXBPF_OUT', 'Q_BUF_B', 'Q_BUF_C', 'DRV_IN', 'DRV_G', 'DRV_D', 'PA_IN', 'PA_GA', 'PA_GB', 'PA_DA', 'PA_DB', 'LPF_IN', 'LPF2', 'LPF3', 'TX_OUT', 'ANT']),
          ('受信RF', ['RX_ANT', 'RB1', 'RB2', 'RFA_D', 'MIX_IN', 'LO_IN', 'LO_DIV', 'CLK1', 'MIX_OUT', 'IF1', 'MIX3', 'LIM_IN', 'OSC_B', 'OSC_E', 'QUAD']),
          ('変調・逓倍', ['CLK0', 'CLK0_IN', 'RST_P', 'RST_G', 'RAMP', 'THRESH', 'COMP_OUT', 'PM_OUT', 'X2', 'X4', 'X8', 'X16', 'TK1', 'TK2', 'TK3', 'X2S', 'X4S', 'X8S']),
          ('PLL', ['PFD_UP', 'PFD_DN', 'PFD_RST', 'VCO_CK', 'VT', 'VAR_K', 'VCO_IN', 'VCO_OA', 'VCO_O', 'VCO_L', 'TXOSC']),
          ('電源（太線）', ['+13V8', 'DCDC_IN', '+8V', 'TX8V', 'RX8V', '+5V', '+5VT', '+5VA'])]
for g, ns in groups:
    print('[%s]' % g, '  '.join('%s %.0f mm（%.1f）' % (n, L.get(n, 0), W.get(n, 0)) for n in ns))
fp = {f.GetReference(): f for f in b.GetFootprints()}
for r in sys.argv[1:]:
    p = fp[r].GetPosition(); print(r, fp[r].GetValue(), '(%.1f, %.1f) %d°' % (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y), fp[r].GetOrientationDegrees()))
