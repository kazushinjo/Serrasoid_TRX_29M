"""circuit.py から基板 kicad/Serrasoid_TRX.kicad_pcb を作る（部品配置・ネット割り当て・GND 内層）

KiCad 付属の Python で実行する:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 tools/gen_pcb.py
配線は route.sh（Freerouting）で行う。
"""
import os, sys, json, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew, subprocess, re, tempfile
from circuit import parts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = 'Serrasoid_TRX'
SYSFP = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
LOCALFP = os.path.join(ROOT, 'kicad', PROJ + '.pretty')
NS = uuid.UUID('6a1c3f3e-29a0-4c55-9d1e-5e7a50000000')
M = pcbnew.FromMM
mm = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))

# 基板外形（上辺 = 後面、下辺 = 前面）
BW, BH = 170.0, 140.0     # 2026-10-29 逓倍の段間同調と PLL を足したので奥行きを 130 → 140mm に
GAP = 1.0          # 部品どうしのすき間
# ブロックの区画 (x0, y0, x1, y1)。送信は中段を左から右へ（変調 → 逓倍 → PLL）、上段の送信 RF は右へ、受信は右列を上から下へ流れる
# （2026-10-29 逓倍に段間同調、PLL を足したので区画を割り直した）
REGIONS = {
    '電源':           (0, 0, 40, 40),
    '送信RF':         (40, 0, 170, 46),
    'セラゾイド変調': (0, 40, 30, 100),
    '逓倍':           (30, 46, 72, 100),
    'PLL':            (72, 46, 122, 100),
    '受信':           (122, 46, 170, 140),
    '制御':           (0, 100, 70, 140),
    '送信音声':       (70, 100, 122, 140),
}
# 基板上で別の区画に置く部品（値 → 区画）。Si5351 は CLK0（変調）と CLK1（受信）の間に置く
BLOCK_OVERRIDE = {}
# 配線長の重み: RF の線と、変調のタイミングに関わる線を優先して短くする
TIMING = {'TK1', 'TK2', 'TK3', 'SQ1', 'SQ2', 'SQ3', 'SQO1', 'SQO2', 'SQO3', 'X2S', 'X4S', 'X8S',
          'PFD_UP', 'PFD_DN', 'PFD_RST', 'VCO_CK', 'TXOSC', 'TXDRV', 'VCO_IN', 'VCO_OA', 'VCO_O', 'VCO_L', 'VAR_K',
          'RAMP', 'RAMP_E', 'RAMP_B', 'RC1', 'RC2', 'RC3', 'RC4', 'LPF2', 'LPF3', 'RFA_D', 'RFA_S', 'THRESH', 'PM_OUT', 'COMP_OUT', 'RST_P', 'RST_G', 'CLK0', 'CLK0_IN', 'CLK1', 'LO_IN', 'LO_DIV',
          'X2', 'X4', 'X8', 'X16', 'DLY1', 'DLY2', 'DLY3', 'DLY4', 'OS_C', 'OS_RC', 'MIX_IN', 'MIX_OUT', 'IF1', 'MIX3', 'LIM_IN',
          'MIX_BYP', 'LO_IN', 'LO_DIV'}
# NJM2594 の出力 → 10.7MHz 増幅 → 水晶フィルタ は 1 か所にまとめる（増幅の部品は一覧の最後で、ほかより後に置かれるため重みを大きく）
MIXER = {'MIX_EF', 'IFA_B', 'IFA_C', 'IFA_E', 'IFA_E2', 'MIX_OUT'}
# VCO の LC と段間同調の共振回路も 1 か所にまとめる（線が長いと容量・飛び込みが増える）
MIXER |= {'VCO_IN', 'VCO_OA', 'VCO_O', 'VCO_L', 'VAR_K', 'TK1', 'TK2', 'TK3', 'SQ1', 'SQ2', 'SQ3'}
# 位置を決めて置く部品: 部品番号 → (x, y, 角度)
def fixed_positions(byref):
    """位置を決めて置く部品（コネクタ・リレー・ファイナル）。ほかは place.py が配線長の短い位置を探す
    （送信の主要部品も固定する案は、全体の配線長が伸び未接続が残ったので採用しない）"""
    by_value = {'DC 13.8V': (12, 4, 0), 'ANT': (153, 4, 0), 'G5V-2 DC12': (152, 16, 0), 'RD16HHF1': (120, 4.5, 0)}
    return {p['ref']: by_value[p['value']] for p in parts if p['value'] in by_value}

KCLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
def sch_nets():
    """回路図から書き出したネットリストの {(部品番号, ピン): ネット名}"""
    out = os.path.join(tempfile.mkdtemp(), 'n.net')
    subprocess.run([KCLI, 'sch', 'export', 'netlist', '-o', out, os.path.join(ROOT, 'kicad', PROJ + '.kicad_sch')],
                   check=True, capture_output=True)
    s = open(out).read(); r = {}
    for m in re.finditer(r'\(net\s+\(code "\d+"\)\s+\(name "((?:[^"\\]|\\.)*)"\)(.*?)(?=\(net\s+\(code|\Z)', s, re.S):
        for ref, pin in re.findall(r'\(ref "([^"]*)"\)\s*\(pin "([^"]*)"\)', m.group(2)): r[(ref, pin)] = m.group(1).replace('\\"', '"')
    return r

def fp_load(fpid):
    lib, name = fpid.split(':')
    path = LOCALFP if lib == PROJ else os.path.join(SYSFP, lib + '.pretty')
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None: raise SystemExit('フットプリントが見つからない: ' + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

def box(fp):
    """部品の占有範囲（コートヤード、なければ外形）を位置からの相対で"""
    for L in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        c = fp.GetCourtyard(L)
        if c.OutlineCount():
            bb = c.BBox(); break
    else:
        bb = fp.GetBoundingBox(False)
    p = fp.GetPosition()
    return (mm(bb.GetX() - p.x), mm(bb.GetY() - p.y), mm(bb.GetRight() - p.x), mm(bb.GetBottom() - p.y))

def overlap(a, b):
    return not (a[2] + GAP <= b[0] or b[2] + GAP <= a[0] or a[3] + GAP <= b[1] or b[3] + GAP <= a[1])

def main(report_only=False):
    b = pcbnew.NewBoard(os.path.join(ROOT, 'kicad', PROJ + '.kicad_pcb'))
    b.SetCopperLayerCount(4)
    b.SetLayerName(pcbnew.In1_Cu, 'GND1')
    b.SetLayerName(pcbnew.In2_Cu, 'GND2')
    ds = b.GetDesignSettings()
    ds.SetBoardThickness(M(1.6))
    nets = {}
    SN = sch_nets()
    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
        return nets[n]
    fps = {}
    for p in parts:
        if p['ref'].startswith('#') or not p['fp']: continue
        fp = fp_load(p['fp'])
        fp.SetReference(p['ref']); fp.SetValue(p['value'])
        fp.SetPath(pcbnew.KIID_PATH('/' + str(uuid.uuid5(NS, '%s:1' % p['ref']))))
        fp.SetSheetfile(PROJ + '.kicad_sch'); fp.SetSheetname('')
        b.Add(fp)
        fp.SetExcludedFromBOM(False)
        for pad in fp.Pads():
            n = SN.get((p['ref'], pad.GetNumber()))
            if n: pad.SetNet(net(n))
            elif pad.GetNumber():
                print('警告: %s のパッド %s は回路図にない' % (p['ref'], pad.GetNumber()))
            # 接続が circuit.py と同じことは verify_sch.py で確認済み
        fps[p['ref']] = (fp, p)
    # 面積の見積もり
    area = {}
    for fp, p in fps.values():
        x0, y0, x1, y1 = box(fp); area[p['block']] = area.get(p['block'], 0) + (x1 - x0 + GAP) * (y1 - y0 + GAP)
    for k, (x0, y0, x1, y1) in REGIONS.items():
        print('%-10s 部品 %6.0f mm2 / 区画 %6.0f mm2 (%3.0f%%)' % (k, area.get(k, 0), (x1 - x0) * (y1 - y0), 100 * area.get(k, 0) / ((x1 - x0) * (y1 - y0))))
    if report_only: return
    # 配置
    placed = []      # 絶対座標の占有範囲
    fixed = fixed_positions(fps)
    for r, (x, y, a) in fixed.items():
        fp, p = fps[r]; fp.SetOrientationDegrees(a); fp.SetPosition(V(x, y))
        bx = box(fp); placed.append((x + bx[0], y + bx[1], x + bx[2], y + bx[3]))
    # RD06HHF1 の放熱器（PSN_TRX と同じ相対位置）。配置では RD06HHF1 と一体の大きさとして扱う
    q5ref = [r for r, (fp, p) in fps.items() if p['value'] == 'RD06HHF1'][0]
    if q5ref in fixed:
        q5 = fps[q5ref][0]; q5.SetOrientationDegrees(0); q5.SetPosition(V(*fixed[q5ref][:2]))
    q5 = fps[q5ref][0]
    hs = fp_load(PROJ + ':Heatsink_20PB020'); hs.SetReference('HS1'); hs.SetValue('20PB020')
    hs.SetOrientationDegrees(180); hs.SetBoardOnly(True); b.Add(hs)
    HS_OFF = (2.54, -13.15)
    # 取付穴
    for i, (x, y) in enumerate([(4, 4), (BW - 4, 4), (4, BH - 4), (BW - 4, BH - 4)]):
        h = fp_load('MountingHole:MountingHole_3.2mm_M3_Pad'); h.SetReference('H%d' % (i + 1)); h.SetValue('M3')
        h.SetPosition(V(x, y)); h.SetBoardOnly(True); b.Add(h)
        for pad in h.Pads(): pad.SetNet(net('GND'))
        placed.append((x - 4, y - 4, x + 4, y + 4))
    # 機能ブロックの区画の中で、配線長が短くなるように置く（tools/place.py）
    from place import Placer
    from netclass import HEAVY, RF
    pl = Placer(BW, BH, REGIONS)
    for r in placed: pl.add_obstacle(r)
    # ケースの放熱器（RD16HHF1 のタブを当てる、幅 50mm）のベースが基板の上辺に 1.1mm かかる（enclosure/serrasoid_trx_case.scad）。
    # RD16HHF1 の左右のその範囲（上辺から 1.6mm）には部品を置かない
    pl.add_obstacle((122.54 - 25.5, 0, 122.54 + 25.5, 1.6))
    # 後面の DC ジャック（ケース X 27 = 基板 u 12、本体 φ12・奥行き 15mm）の下には背の高い部品（レギュレータなど）を置けないので、
    # その範囲（基板の左奥）を部品禁止にする（2026-10-29、L7808 が当たったため。enclosure/serrasoid_trx_case.scad の assert）
    pl.add_obstacle((5, 0, 19, 13))
    order = [p['ref'] for p in parts if p['ref'] in fps]
    for ref in order:
        fp, p = fps[ref]
        rots = {}
        for rot in ((0,) if (ref in fixed or ref == q5ref) else (0, 90, 180, 270)):
            a0 = fixed[ref][2] if ref in fixed else rot
            fp.SetOrientationDegrees(a0); fp.SetPosition(V(0, 0))
            pads = {pd.GetNumber(): (mm(pd.GetPosition().x), mm(pd.GetPosition().y)) for pd in fp.Pads()}
            bx = box(fp)
            if ref == q5ref:
                hs.SetPosition(V(*HS_OFF)); hb = box(hs)
                hb = (hb[0] + HS_OFF[0], hb[1] + HS_OFF[1], hb[2] + HS_OFF[0], hb[3] + HS_OFF[1])
                bx = (min(bx[0], hb[0]), min(bx[1], hb[1]), max(bx[2], hb[2]), max(bx[3], hb[3]))
            rots[a0] = (bx, pads)
        pl.add_part(ref, BLOCK_OVERRIDE.get(p['value'], p['block']), rots, fixed.get(ref))
    GLOBALS = {'+13V8', '+8V', '+5V', '+5VT', '+5VA', '+3V3S', '+3V3X', 'TX8V', 'RX8V'}
    pins = {}
    for ref in order:
        for pd in fps[ref][0].Pads():
            n = pd.GetNetname()
            if n: pins.setdefault(n, []).append((ref, pd.GetNumber()))
    for n, lst in pins.items():
        if n == 'GND' or n.startswith('unconnected'): continue
        r0, n0 = lst[0]; k = fps[r0][1]['pins'].get(n0) or n      # circuit.py でのネット名
        w = 0.3 if (n in GLOBALS or len(lst) > 12) else 20.0 if k in MIXER else 8.0 if (k in HEAVY or k in RF) else 6.0 if k in TIMING else 1.0
        pl.add_net(n, w, lst)
    # 電源と GND だけにつながる部品（パスコンなど）は、回路一覧で直前にある同じ電源の部品のそばへ
    def power_only(ref):
        return all((pd.GetNetname() in GLOBALS or pd.GetNetname() == 'GND' or not pd.GetNetname()) for pd in fps[ref][0].Pads())
    for i, ref in enumerate(order):
        if not power_only(ref) or ref in fixed: continue
        for pd in fps[ref][0].Pads():
            n = pd.GetNetname()
            if n not in GLOBALS: continue
            for ref2 in reversed(order[:i]):
                if power_only(ref2): continue
                hit = [q.GetNumber() for q in fps[ref2][0].Pads() if q.GetNetname() == n]
                if hit:
                    pl.add_net('dec:%s:%s' % (ref, n), 1.5, [(ref, pd.GetNumber()), (ref2, hit[0])]); break
    res = pl.run()
    for ref, (pos, rot) in res.items():
        fp = fps[ref][0]; fp.SetOrientationDegrees(rot); fp.SetPosition(V(pos[0], pos[1]))
    hs.SetPosition(q5.GetPosition() + V(*HS_OFF))
    out = [ref for ref, (pos, rot) in res.items() if not ref in fixed and not all(
        REGIONS[fps[ref][1]['block']][k] - 0.01 <= v if k < 2 else v <= REGIONS[fps[ref][1]['block']][k] + 0.01
        for k, v in enumerate(pl.rect(ref)))]
    if out: print('区画からはみ出した部品:', out)
    # リード部品だけにする方針。例外は NJM2594V（SA612 が製造中止のため。2026-10-16 にユーザーが表面実装を了承）
    SMD_OK = {'NJM2594V'}
    smd = ['%s.%s' % (ref, pd.GetNumber()) for ref, (fp, p) in fps.items() for pd in fp.Pads()
           if pd.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p['value'] not in SMD_OK]
    if smd: raise SystemExit('表面実装のパッドがある（リード部品だけにする方針）: %s' % smd)
    # 外形
    for (x0, y0, x1, y1) in [(0, 0, BW, 0), (BW, 0, BW, BH), (BW, BH, 0, BH), (0, BH, 0, 0)]:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(M(0.1)); b.Add(s)
    # GND 内層 2 枚
    for L in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(L); z.SetNet(net('GND'))
        o = z.Outline(); o.NewOutline()
        for (x, y) in [(0.3, 0.3), (BW - 0.3, 0.3), (BW - 0.3, BH - 0.3), (0.3, BH - 0.3)]: o.Append(M(x), M(y))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetLocalClearance(M(0.3)); z.SetMinThickness(M(0.25))
        b.Add(z)
    # 表面実装 IC の GND パッドを内層の GND へ（ビア）。配線の前に入れて、Freerouting にはよけてもらう
    from pcb_smd_gnd import add_gnd_vias
    print('表面実装の GND ビア', add_gnd_vias(b))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(os.path.join(ROOT, 'kicad', PROJ + '.kicad_pcb'))
    print('saved', len(fps), 'footprints', len(nets), 'nets')

if __name__ == '__main__':
    main('--area' in sys.argv)
