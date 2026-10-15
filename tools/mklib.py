"""プロジェクト用の記号ライブラリ kicad/Serrasoid_TRX.kicad_sym と独自フットプリントを作る"""
import os, copy
from sx import parse, dump, find, find1, unq, q, Sym
from libload import get, SYMDIR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBNAME = 'Serrasoid_TRX'
PSN = os.path.join(ROOT, '..', 'PSN_TRX_XIAO_ESP32C3', 'kicad', 'PSN_TRX.kicad_sym')
S = Sym

def F(v):
    return ('%.3f' % v).rstrip('0').rstrip('.')

def eff(hide=False):
    return '(effects (font (size 1.27 1.27))%s)' % (' (hide yes)' if hide else '')

def prop(name, val, x, y, hide=False):
    return '(property "%s" "%s" (at %s %s 0) %s)' % (name, val, F(x), F(y), eff(hide))

def pin(typ, x, y, ang, name, num, length=2.54):
    return '(pin %s line (at %s %s %d) (length %s) (name "%s" %s) (number "%s" %s))' % (
        typ, F(x), F(y), ang, F(length), name, eff(), num, eff())

def box_ic(name, ref, fp, desc, left, right, top=(), bottom=(), w=10.16):
    """左右（と上下）にピンを並べた箱形の記号。各リストは (番号, 名前, 種類)"""
    n = max(len(left), len(right))
    h = max(n * 2.54 + 2.54, 7.62)
    y0 = (n - 1) * 2.54 / 2
    hw = w / 2
    pins = []
    for i, (num, nm, t) in enumerate(left):
        pins.append(pin(t, -hw - 2.54, y0 - i * 2.54, 0, nm, num))
    for i, (num, nm, t) in enumerate(right):
        pins.append(pin(t, hw + 2.54, y0 - i * 2.54, 180, nm, num))
    for i, (num, nm, t) in enumerate(top):
        x = (i - (len(top) - 1) / 2) * 2.54
        pins.append(pin(t, x, h / 2 + 2.54, 270, nm, num))
    for i, (num, nm, t) in enumerate(bottom):
        x = (i - (len(bottom) - 1) / 2) * 2.54
        pins.append(pin(t, x, -h / 2 - 2.54, 90, nm, num))
    return ('(symbol "%s" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
            '%s %s %s %s %s '
            '(symbol "%s_0_1" (rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) (fill (type background)))) '
            '(symbol "%s_1_1" %s))') % (
        name, prop('Reference', ref, 0, h / 2 + 1.27 + (2.54 if top else 0)),
        prop('Value', name, 0, -h / 2 - 1.27 - (2.54 if bottom else 0)),
        prop('Footprint', fp, 0, 0, True), prop('Datasheet', '', 0, 0, True),
        prop('Description', desc, 0, 0, True),
        name, F(-hw), F(h / 2), F(hw), F(-h / 2), name, ' '.join(pins))

def two_terminal_filter(name, fp, desc):
    """入力・GND・出力の 3 端子フィルタ（水晶フィルタ・セラミックフィルタ）"""
    pins = [pin('passive', -7.62, 0, 0, 'IN', '1'), pin('passive', 0, -5.08, 90, 'GND', '2'),
            pin('passive', 7.62, 0, 180, 'OUT', '3')]
    g = ('(rectangle (start -5.08 2.54) (end 5.08 -2.54) (stroke (width 0.254) (type default)) (fill (type background))) '
         '(polyline (pts (xy -2.54 1.27) (xy -2.54 -1.27)) (stroke (width 0.254) (type default)) (fill (type none))) '
         '(polyline (pts (xy 2.54 1.27) (xy 2.54 -1.27)) (stroke (width 0.254) (type default)) (fill (type none))) '
         '(rectangle (start -1.524 1.778) (end 1.524 -1.778) (stroke (width 0.254) (type default)) (fill (type none)))')
    return ('(symbol "%s" (pin_names (offset 1.016) (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes) %s %s %s %s %s '
            '(symbol "%s_0_1" %s) (symbol "%s_1_1" %s))') % (
        name, prop('Reference', 'FL', 0, 3.81), prop('Value', name, 0, 5.588),
        prop('Footprint', fp, 0, 0, True), prop('Datasheet', '', 0, 0, True), prop('Description', desc, 0, 0, True),
        name, g, name, ' '.join(pins))

def l_tap(name, fp, desc):
    """タップ付きコイル（1=ホット 2=タップ 3=コールド）"""
    arcs = ' '.join('(arc (start 0 %s) (mid 1.016 %s) (end 0 %s) (stroke (width 0) (type default)) (fill (type none)))'
                    % (F(2.54 - i * 1.27), F(2.54 - i * 1.27 - 0.635), F(2.54 - (i + 1) * 1.27)) for i in range(4))
    pins = [pin('passive', 0, 5.08, 270, '1', '1'), pin('passive', 3.81, -1.27, 180, 'TAP', '2', 2.794),
            pin('passive', 0, -5.08, 90, '3', '3')]
    return ('(symbol "%s" (pin_numbers (hide yes)) (pin_names (offset 1.016) (hide yes)) (exclude_from_sim no) (in_bom yes) (on_board yes) %s %s %s %s %s '
            '(symbol "%s_0_1" %s (polyline (pts (xy 1.016 -1.27) (xy 0.762 -1.27)) (stroke (width 0) (type default)) (fill (type none)))) (symbol "%s_1_1" %s))') % (
        name, prop('Reference', 'L', -2.54, 0), prop('Value', name, 5.08, 2.54),
        prop('Footprint', fp, 0, 0, True), prop('Datasheet', '', 0, 0, True), prop('Description', desc, 0, 0, True),
        name, arcs, name, ' '.join(pins))

def power_sym(net):
    t = get('power:+5V')
    t[1] = q(net)
    for p in find(t, 'property'):
        if unq(p[1]) == 'Value': p[2] = q(net)
        if unq(p[1]) == 'Description': p[2] = q('Power symbol creates a global label with name "%s"' % net)
    for c in find(t, 'symbol'):
        c[1] = q(unq(c[1]).replace('+5V', net, 1))
    return dump(t)

def copy_psn(name, newname, fp=None, value=None, desc=None):
    s = get('PSN_TRX:' + name, PSN)
    s[1] = q(newname)
    for p in find(s, 'property'):
        n = unq(p[1])
        if n == 'Value': p[2] = q(value or newname)
        if n == 'Footprint' and fp: p[2] = q(fp)
        if n == 'Description' and desc: p[2] = q(desc)
    for c in find(s, 'symbol'):
        c[1] = q(unq(c[1]).replace('PSN_TRX:', '').replace(name, newname, 1))
    return dump(s)

def flip_y(text):
    """記号を上下反転する（ドレインを上・ソースを下の普通の向きに）"""
    t = parse(text)
    def walk(n, in_sub):
        for c in n:
            if not isinstance(c, list) or not c: continue
            if c[0] == 'symbol': walk(c, True); continue
            if c[0] == 'property': continue
            if in_sub and c[0] in ('xy', 'start', 'end', 'mid', 'center'):
                c[2] = S(F(-float(c[2])))
            elif in_sub and c[0] == 'at' and len(c) >= 3:
                c[2] = S(F(-float(c[2])))
                if len(c) > 3: c[3] = S(str({90: 270, 270: 90}.get(int(float(c[3])), int(float(c[3])))))
            walk(c, in_sub)
    walk(t, False)
    return dump(t)

POWER_NETS = ['+13V8', '+8V', '+5V', '+5VT', '+5VA', '+3V3S', '+3V3X', 'TX8V', 'RX8V']

def main():
    L = LIBNAME + ':'
    syms = [
        box_ic('SA612', 'U', 'Package_DIP:DIP-8_W7.62mm', 'Double-balanced mixer and oscillator (SA612A / NE612)',
               left=[('1', 'IN_A', 'input'), ('2', 'IN_B', 'input'), ('6', 'OSC_B', 'input'), ('7', 'OSC_E', 'passive')],
               right=[('4', 'OUT_A', 'output'), ('5', 'OUT_B', 'output')],
               top=[('8', 'VCC', 'power_in')], bottom=[('3', 'GND', 'power_in')]),
        box_ic('MC3361', 'U', 'Package_DIP:DIP-16_W7.62mm', 'Low power narrowband FM IF (MC3361 / MC3357 pinout)',
               left=[('16', 'MIX_IN', 'input'), ('1', 'OSC_B', 'passive'), ('2', 'OSC_E', 'passive'), ('5', 'LIM_IN', 'input'),
                     ('6', 'DEC1', 'passive'), ('7', 'DEC2', 'passive'), ('8', 'QUAD', 'passive'), ('10', 'FIL_IN', 'input')],
               right=[('3', 'MIX_OUT', 'output'), ('9', 'AUDIO', 'output'), ('11', 'FIL_OUT', 'output'), ('12', 'SQ_IN', 'input'),
                      ('13', 'SCAN', 'output'), ('14', 'MUTE', 'passive')],
               top=[('4', 'VCC', 'power_in')], bottom=[('15', 'GND', 'power_in')], w=15.24),
        two_terminal_filter('Filter_3pin', 'Crystal:Crystal_HC49-U-3Pin_Vertical', '3-terminal filter, 1=IN 2=GND 3=OUT'),
        l_tap('L_Tap', L + 'L_T30_3pin_Vertical', 'Tapped toroid coil, 1=hot 2=tap 3=cold'),
        flip_y(copy_psn('RD06HVF1', 'RD_MOSFET_GSD', value='RD16HHF1',
                 desc='Mitsubishi RF power MOSFET TO-220S (RD06HHF1 / RD16HHF1), 1=G 2=S 3=D')),
        copy_psn('Seeeduino_XIAO_Socket', 'XIAO_ESP32C3', fp=L + 'Seeeduino_XIAO_Socket', value='XIAO ESP32C3'),
        copy_psn('Si5351_DIP8', 'Si5351_Module', fp=L + 'DIP-8_W7.62mm', value='AE-Si5351A'),
    ] + [power_sym(n) for n in POWER_NETS]
    out = '(kicad_symbol_lib (version 20251024) (generator "serrasoid_mklib") (generator_version "10.0")\n' + '\n'.join(syms) + '\n)\n'
    # 書式確認を兼ねて一度パースする
    parse(out)
    open(os.path.join(ROOT, 'kicad', LIBNAME + '.kicad_sym'), 'w').write(out)
    mkfoot()

def mkfoot():
    d = os.path.join(ROOT, 'kicad', LIBNAME + '.pretty')
    def fpwrite(name, desc, pads, crt, silk):
        s = ['(footprint "%s" (version 20241209) (generator "serrasoid_mklib") (layer "F.Cu") (descr "%s") (attr through_hole)' % (name, desc),
             '(property "Reference" "REF**" (at %s %s 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))' % (F(crt[0]), F(crt[1] - 1.5)),
             '(property "Value" "%s" (at %s %s 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % (name, F(crt[0]), F(crt[3] + 1.5)),
             '(fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) (type default)) (fill no) (layer "F.CrtYd"))' % tuple(map(F, crt)),
             '(fp_rect (start %s %s) (end %s %s) (stroke (width 0.12) (type default)) (fill no) (layer "F.SilkS"))' % tuple(map(F, silk)),
             '(fp_rect (start %s %s) (end %s %s) (stroke (width 0.1) (type default)) (fill no) (layer "F.Fab"))' % tuple(map(F, silk))]
        for num, x, y, sz, dr in pads:
            s.append('(pad "%s" thru_hole %s (at %s %s) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask"))' % (
                num, 'rect' if num == '1' else 'circle', F(x), F(y), F(sz), F(sz), F(dr)))
        s.append(')')
        open(os.path.join(d, name + '.kicad_mod'), 'w').write('\n'.join(s) + '\n')
    # BN-43-202 双穴コア: 1-2 一次（ドレイン側）、3-4 二次（50Ω側）
    fpwrite('Transformer_BN43-202', 'Binocular core BN-43-202, 1-2 primary, 3-4 secondary, pad pitch 5.08mm, span 15.24mm',
            [('1', 0, 0, 2.4, 1.2), ('2', 0, 5.08, 2.4, 1.2), ('3', 15.24, 0, 2.4, 1.2), ('4', 15.24, 5.08, 2.4, 1.2)],
            (-2, -3.5, 17.24, 8.58), (1.6, -2.5, 13.64, 7.58))
    # 455kHz セラミックフィルタ（3 端子 2.54mm ピッチ一列、1=IN 2=GND 3=OUT）
    fpwrite('Filter_Ceramic_3pin_P2.54mm', 'Ceramic filter 455kHz, 3 pins inline P2.54mm (CFWLA455 / LTWC455 type), 1=IN 2=GND 3=OUT',
            [('1', 0, 0, 1.6, 0.8), ('2', 2.54, 0, 1.6, 0.8), ('3', 5.08, 0, 1.6, 0.8)],
            (-1.6, -2.6, 6.68, 2.6), (-1.3, -2.3, 6.38, 2.3))

if __name__ == '__main__':
    main()
