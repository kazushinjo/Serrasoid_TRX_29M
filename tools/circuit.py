"""Serrasoid TRX 29M の回路（部品と接続）

各部品は (ブロック, 記号, 値, フットプリント, {ピン番号: ネット名}, 備考)。
ネット名 None は未接続（NC）。部品番号は種類ごとにこの並び順で自動で振る。
回路図（gen_sch.py）と基板（gen_pcb.py）はこの一覧から作る。
"""
L = 'Serrasoid_TRX:'
# ---- フットプリント
FP_R = 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical'
FP_R1W = 'Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P5.08mm_Vertical'
FP_C = 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm'
FP_CS = 'Capacitor_THT:C_Disc_D3.0mm_W1.6mm_P2.50mm'
FP_CHV = 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
FP_CP5 = 'Capacitor_THT:CP_Radial_D5.0mm_P2.00mm'
FP_CP6 = 'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm'
FP_CP8 = 'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm'
FP_TC = L + 'C_Trimmer_TMCV01'
FP_VR = L + 'Potentiometer_TOCOS_GF063P_Vertical'
FP_D35 = 'Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_AnodeUp'
FP_D41 = 'Diode_THT:D_DO-41_SOD81_P5.08mm_Vertical_AnodeUp'
FP_D201 = 'Diode_THT:D_DO-201AD_P5.08mm_Vertical_AnodeUp'
FP_TO92 = 'Package_TO_SOT_THT:TO-92_Inline'
FP_TO220 = 'Package_TO_SOT_THT:TO-220-3_Vertical'
FP_LAX = 'Inductor_THT:L_Axial_L9.5mm_D4.0mm_P2.54mm_Vertical_Fastron_SMCC'
FP_T50 = L + 'L_T50_2pin_Vertical'
FP_T30T = L + 'L_T30_3pin_Vertical'
FP_DIP8 = 'Package_DIP:DIP-8_W7.62mm_Socket'
FP_DIP14 = 'Package_DIP:DIP-14_W7.62mm_Socket'
FP_DIP16 = 'Package_DIP:DIP-16_W7.62mm_Socket'
FP_H = lambda n: 'Connector_PinHeader_2.54mm:PinHeader_1x%02d_P2.54mm_Vertical' % n
FP_WIRE = 'Connector_Wire:SolderWire-1sqmm_1x02_P5.4mm_D1.4mm_OD2.7mm'
FP_TP = 'TestPoint:TestPoint_THTPad_D1.5mm_Drill0.7mm'

parts = []
def add(blk, sym, val, fp, pins, note=''):
    parts.append(dict(block=blk, sym=sym, value=val, fp=fp, pins=pins, note=note))

def R(b, v, n1, n2, note='', fp=FP_R): add(b, 'Device:R', v, fp, {'1': n1, '2': n2}, note)
def C(b, v, n1, n2, note='', fp=FP_C): add(b, 'Device:C', v, fp, {'1': n1, '2': n2}, note)
def CP(b, v, plus, minus, note='', fp=FP_CP5): add(b, 'Device:C_Polarized', v, fp, {'1': plus, '2': minus}, note)
def TC(b, v, n1, n2, note=''): add(b, 'Device:C_Trim', v, FP_TC, {'1': n1, '2': n2}, note)
def Lx(b, v, n1, n2, note='', fp=FP_LAX): add(b, 'Device:L', v, fp, {'1': n1, '2': n2}, note)
def LT(b, v, hot, tap, cold, note=''): add(b, L + 'L_Tap', v, FP_T30T, {'1': hot, '2': tap, '3': cold}, note)
def VR(b, v, p1, w, p3, note=''): add(b, 'Device:R_Potentiometer_Trim', v, FP_VR, {'1': p1, '2': w, '3': p3}, note)
def D(b, v, k, a, note='', sym='Device:D', fp=FP_D35): add(b, sym, v, fp, {'1': k, '2': a}, note)
def NPN(b, v, e, c, bb, note=''): add(b, 'Transistor_BJT:Q_NPN_ECB', v, FP_TO92, {'1': e, '2': c, '3': bb}, note)
def PNP(b, v, e, c, bb, note=''): add(b, 'Transistor_BJT:Q_PNP_ECB', v, FP_TO92, {'1': e, '2': c, '3': bb}, note)
def HDR(b, v, nets, note='', fp=None):
    add(b, 'Connector_Generic:Conn_01x%02d' % len(nets), v, fp or FP_H(len(nets)),
        {str(i + 1): n for i, n in enumerate(nets)}, note)
def TP(b, v, net, note=''): add(b, 'Connector:TestPoint', v, FP_TP, {'1': net}, note)

G = 'GND'

# =====================================================================
# 電源
# =====================================================================
B = '電源'
HDR(B, 'DC 13.8V', ['+13V8', G], '後面の DC ジャックから（ヒューズ 5A は後面パネル側）', fp=FP_WIRE)
D(B, '1N5408', '+13V8', G, '逆接続保護（逆接続でヒューズを切る）', sym='Diode:1N5408', fp=FP_D201)
CP(B, '470u', '+13V8', G, '25V 以上', fp=FP_CP8)
C(B, '0.1u', '+13V8', G)
Lx(B, '10uH', '+13V8', 'DCDC_IN', 'DC-DC 入力フィルタ')
CP(B, '10u', 'DCDC_IN', G, '25V 以上')
add(B, 'Converter_DCDC:R-78E5.0-1.0', 'R-78E5.0-1.0', 'Converter_DCDC:Converter_DCDC_RECOM_R-78E-0.5_THT',
    {'1': 'DCDC_IN', '2': G, '3': '+5V'}, 'デジタル系 5V（XIAO・表示）')
CP(B, '10u', '+5V', G)
C(B, '0.1u', '+5V', G)
add(B, 'Regulator_Linear:L7808', 'L7808', FP_TO220, {'1': '+13V8', '2': G, '3': '+8V'}, '受信・送信バイアス・アナログ系。小型放熱器を付ける')
C(B, '0.33u', '+13V8', G)
CP(B, '10u', '+8V', G)
C(B, '0.1u', '+8V', G)
add(B, 'Regulator_Linear:L7805', 'L7805', FP_TO220, {'1': '+8V', '2': G, '3': '+5VT'}, '変調部専用 5V（リニア。DC-DC のリプルを変調に入れないため）')
C(B, '0.1u', '+8V', G)
CP(B, '10u', '+5VT', G)
C(B, '0.1u', '+5VT', G)
add(B, 'Regulator_Linear:LP2950-3.3_TO92', 'LP2950-3.3', FP_TO92, {'1': '+3V3S', '2': G, '3': '+5V'}, 'Si5351 モジュール用 3.3V')
CP(B, '10u', '+3V3S', G)
C(B, '0.1u', '+3V3S', G)
for n in ['+13V8', G, 'TX8V', 'RX8V', 'DCDC_IN']:
    add(B, 'power:PWR_FLAG', 'PWR_FLAG', '', {'1': n})

# =====================================================================
# 制御（XIAO ESP32C3・Si5351・送受切替）
# =====================================================================
B = '制御'
add(B, L + 'XIAO_ESP32C3', 'XIAO ESP32C3', L + 'Seeeduino_XIAO_Socket',
    {'1': 'ENC_B', '2': 'FWD_ADC', '3': 'NOISE_ADC', '4': 'ENC_A', '5': 'SDA', '6': 'SCL', '7': 'UART_TX',
     '8': 'XIAO_5V', '9': G, '10': '+3V3X', '11': 'TX_EN', '12': 'ENC_SW', '13': 'PTT_IN', '14': 'MUTE'},
    'ソケット実装。D8（PTT）・D9（エンコーダ SW）は起動設定ピンなので、PTT を押したまま電源を入れない')
D(B, '1N5819', 'XIAO_5V', '+5V', 'USB 接続時の逆流防止', sym='Diode:1N5819', fp=FP_D41)
add(B, 'power:PWR_FLAG', 'PWR_FLAG', '', {'1': 'XIAO_5V'})
R(B, '4.7k', '+3V3X', 'SDA', 'I2C プルアップ')
R(B, '4.7k', '+3V3X', 'SCL', 'I2C プルアップ')
add(B, L + 'Si5351_Module', 'AE-Si5351A', L + 'DIP-8_W7.62mm',
    {'1': '+3V3S', '2': 'SCL', '3': 'SDA', '4': G, '5': 'CLK0', '6': 'CLK1', '7': None, '8': '+3V3S'},
    '秋月 AE-Si5351A。CLK0 = 変調基準 9.15625MHz（送信時のみ）、CLK1 = 受信局発 18.6MHz（受信時のみ）')
HDR(B, 'I2C', ['+3V3X', 'SCL', 'SDA', G], 'OLED 表示を使う場合の予備')
HDR(B, 'TJC', ['+5V', 'UART_TX', None, G], 'TJC 表示器（XIAO の TX → 表示器の RX。表示器からの受信は使わない）')
HDR(B, 'ENC', ['ENC_A', 'ENC_B', 'ENC_SW', G, G], 'ロータリーエンコーダ（上面 TUNE）')
R(B, '10k', '+3V3X', 'ENC_A')
R(B, '10k', '+3V3X', 'ENC_B')
R(B, '10k', '+3V3X', 'ENC_SW')
R(B, '10k', '+3V3X', 'PTT_IN', 'PTT プルアップ')
R(B, '1k', 'MIC_PTT', 'PTT_IN', 'PTT 保護抵抗')
C(B, '0.01u', 'PTT_IN', G)
# 送受切替: TX_EN → Q → K1。K1 の 1 極目でアンテナ、2 極目で 8V を TX8V / RX8V に振り分ける
R(B, '4.7k', 'TX_EN', 'RLY_B')
R(B, '10k', 'RLY_B', G)
NPN(B, '2SC1815', G, 'RLY_C', 'RLY_B', 'リレー駆動')
D(B, '1N4001', '+13V8', 'RLY_C', 'リレーコイルの逆起電力吸収', sym='Diode:1N4001', fp=FP_D41)
add(B, 'Relay:G5V-2', 'G5V-2 DC12', 'Relay_THT:Relay_DPDT_Omron_G5V-2',
    {'1': '+13V8', '16': 'RLY_C', '4': 'ANT', '6': 'RX_ANT', '8': 'TX_OUT', '13': '+8V', '11': 'RX8V', '9': 'TX8V'},
    '送受切替。1 極目: アンテナ（NC=受信、NO=送信）、2 極目: 8V を RX8V / TX8V へ')
HDR(B, 'ANT', ['ANT', G], '後面 BNC へ（RG-174 で配線）', fp=FP_WIRE)
R(B, '1.5k', 'TX8V', 'TXLED', 'TX ランプ電流')
HDR(B, 'TX LED', ['TXLED', G], '上面の TX ランプ')
CP(B, '47u', 'TX8V', G)
CP(B, '47u', 'RX8V', G)

# =====================================================================
# セラゾイド変調（+5VT）
# =====================================================================
B = 'セラゾイド変調'
R(B, '100', 'CLK0', 'CLK0_IN', 'Si5351 CLK0 の直列抵抗')
add(B, '4xxx:4017', '74HCT4017', FP_DIP16,
    {'14': 'CLK0_IN', '13': G, '15': G, '3': 'RST_P', '8': G, '16': '+5VT',
     '2': None, '4': None, '7': None, '10': None, '1': None, '5': None, '6': None, '9': None, '11': None, '12': None},
    '÷10。Q0 が 1.09µs ごとに約 110ns 幅のリセットパルス。HCT 品（3.3V 入力を受けるため）')
C(B, '0.1u', '+5VT', G)
# のこぎり波: 2SA1015 定電流源で C を充電、2N7000 で放電
R(B, '1.5k', '+5VT', 'RE_N', '定電流源エミッタ抵抗')
VR(B, '1k', 'RE_N', 'RAMP_E', 'RAMP_E', 'のこぎり波の傾き調整（約 260〜430µA）')
D(B, '1N4148', 'VB1', '+5VT', '基準電圧（ダイオード 2 本）', sym='Diode:1N4148')
D(B, '1N4148', 'RAMP_B', 'VB1', '', sym='Diode:1N4148')
R(B, '10k', 'RAMP_B', G)
C(B, '0.1u', '+5VT', 'RAMP_B')
PNP(B, '2SA1015', 'RAMP_E', 'RAMP', 'RAMP_B', '定電流源')
C(B, '100p', 'RAMP', G, 'C0G（NP0）必須。のこぎり波の直線性に直結', fp=FP_CS)
R(B, '100', 'RST_P', 'RST_G')
add(B, 'Transistor_FET:2N7000', '2N7000', FP_TO92, {'1': G, '2': 'RST_G', '3': 'RAMP'}, '放電スイッチ')
TP(B, 'RAMP', 'RAMP', 'のこぎり波の観測点')
# コンパレータ
add(B, 'Comparator:TLV3501AID', 'TLV3501AID', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    {'3': 'RAMP', '2': 'THRESH', '6': 'COMP_OUT', '7': '+5VT', '4': G, '8': 'SHDN', '1': None, '5': None},
    '高速コンパレータ（唯一の表面実装部品、SOIC-8）')
add(B, 'Jumper:SolderJumper_3_Bridged12', 'SHDN', 'Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm',
    {'1': G, '2': 'SHDN', '3': '+5VT'}, 'TLV3501 の SHDN。初期は 1-2（GND）。データシートで論理を確認して必要なら 2-3 へ')
C(B, '0.1u', '+5VT', G)
TP(B, 'THRESH', 'THRESH', 'しきい値（1.5V ± 音声）の観測点')
# パルス整形（ワンショット）
add(B, '74xx:74HC123', '74HC123', FP_DIP16,
    {'1': G, '2': 'COMP_OUT', '3': '+5VT', '13': 'PM_OUT', '4': None, '14': 'OS_C', '15': 'OS_RC',
     '9': '+5VT', '10': G, '11': G, '5': None, '12': None, '6': None, '7': None, '8': G, '16': '+5VT'},
    'コンパレータの立ち上がりで約 545ns（デューティ 50%）のパルス。2 回路目は未使用')
C(B, '100p', 'OS_C', 'OS_RC', 'ワンショット時定数', fp=FP_CS)
R(B, '4.7k', '+5VT', 'OS_R')
VR(B, '10k', 'OS_R', 'OS_RC', 'OS_RC', 'パルス幅（デューティ 50%）調整')
C(B, '0.1u', '+5VT', G)
TP(B, 'PM', 'PM_OUT', '位相変調された 915.625kHz の観測点（立ち上がりが音声で揺れる）')

# =====================================================================
# 逓倍 ×32（+5VT）
# =====================================================================
B = '逓倍'
stages = [('PM_OUT', 'X2', '2k', '100p'), ('X2', 'X4', '1k', '100p'), ('X4', 'X8', '510', '100p'),
          ('X8', 'X16', '510', '47p'), ('X16', 'X32', '270', '47p')]
gate_pins = [('1', '2', '3'), ('4', '5', '6'), ('9', '10', '8'), ('12', '13', '11')]
dl = []
for i, (xi, xo, rv, cv) in enumerate(stages):
    dn = 'DLY%d' % (i + 1)
    R(B, rv, xi, dn, '×2 段 %d の遅延（出力周期の 1/4）' % (i + 1))
    C(B, cv, dn, G, '', fp=FP_CS)
    dl.append((xi, dn, xo))
u1 = {'7': G, '14': '+5VT'}
for (a, b2, y), (xi, dn, xo) in zip(gate_pins, dl[:4]):
    u1.update({a: xi, b2: dn, y: xo})
add(B, '74xx:74HC86', '74AC86', FP_DIP14, u1, '×2 段 1〜4（1.83 → 3.66 → 7.33 → 14.65MHz）。必ず AC 品')
u2 = {'7': G, '14': '+5VT', '1': 'X16', '2': 'DLY5', '3': 'X32', '4': 'X32', '5': G, '6': 'X32B', '9': G, '10': G, '8': None,
      '12': G, '13': G, '11': None}
add(B, '74xx:74HC86', '74AC86', FP_DIP14, u2, '×2 段 5（29.3MHz）と出力バッファ。必ず AC 品')
C(B, '0.1u', '+5VT', G)
C(B, '0.1u', '+5VT', G)
TP(B, 'X32', 'X32B', '29.3MHz の観測点')
R(B, '100', 'X32B', 'TXDRV', 'BPF への直列抵抗')
C(B, '0.01u', 'TXDRV', 'TXBPF_IN')

# =====================================================================
# 送信音声（MCP6004、+5VT）
# =====================================================================
B = '送信音声'
R(B, '10k', '+5VT', 'VREF', 'VREF = 2.5V')
R(B, '10k', 'VREF', G)
CP(B, '10u', 'VREF', G)
HDR(B, 'MIC', ['MIC', 'MIC_PTT', G], 'エレクトレットマイク・PTT（上面 MIC）')
R(B, '470', '+5VT', 'MICB', 'マイク電源デカップリング')
CP(B, '47u', 'MICB', G)
R(B, '2.2k', 'MICB', 'MIC', 'エレクトレットのバイアス')
C(B, '1u', 'MIC', 'MA_IN')
R(B, '10k', 'MA_IN', 'MA_N')
R(B, '220k', 'MA_N', 'MA_OUT', 'マイクアンプ利得 22')
C(B, '220p', 'MA_N', 'MA_OUT', '高域カット', fp=FP_CS)
C(B, '1u', 'MA_OUT', 'MG_IN')
VR(B, '10k', 'MG_IN', 'MG_W', 'VREF', 'マイク利得')
R(B, '100k', 'MB_N', 'MB_OUT', '利得 11')
R(B, '10k', 'MB_N', 'VREF')
R(B, '2.2k', 'MB_OUT', 'CLIP', 'IDC（クリップ）')
D(B, '1N4148', 'VREF', 'CLIP', 'クリップ ±0.6V', sym='Diode:1N4148')
D(B, '1N4148', 'CLIP', 'VREF', '', sym='Diode:1N4148')
R(B, '15k', 'CLIP', 'SK1', '3kHz LPF（サレンキー）')
R(B, '15k', 'SK1', 'SK2')
C(B, '4.7n', 'SK1', 'SK_OUT')
C(B, '2.2n', 'SK2', 'VREF')
C(B, '1u', 'SK_OUT', 'DEV_IN')
VR(B, '10k', 'DEV_IN', 'DEV_W', 'VREF', '周波数偏移（±5kHz に調整）')
R(B, '100k', 'DEV_W', 'TH_SUM')
VR(B, '10k', '+5VT', 'CEN_W', G, 'しきい値の中心（エッジがのこぎり波の中央に来るように）')
CP(B, '10u', 'CEN_W', G)
R(B, '10k', 'CEN_W', 'TH_SUM')
add(B, 'Amplifier_Operational:MCP6004', 'MCP6004', FP_DIP14,
    {'3': 'VREF', '2': 'MA_N', '1': 'MA_OUT',
     '5': 'MG_W', '6': 'MB_N', '7': 'MB_OUT',
     '10': 'SK2', '9': 'SK_OUT', '8': 'SK_OUT',
     '12': 'TH_SUM', '13': 'THRESH', '14': 'THRESH',
     '4': '+5VT', '11': G},
    'A: マイクアンプ、B: 利得段、C: 3kHz LPF、D: しきい値バッファ')
C(B, '0.1u', '+5VT', G)

# =====================================================================
# 送信 RF（BPF・2N3866・RD06HHF1・RD16HHF1・LPF）
# =====================================================================
B = '送信RF'
LT(B, 'T30-6 17T/2T', 'TB1', 'TXBPF_IN', G, '送信 BPF 1 段目。T-30-6 に 0.4mm 線 17 回、コールド側から 2 回目でタップ')
C(B, '22p', 'TB1', G, 'NP0', fp=FP_CS)
TC(B, '30p', 'TB1', G, '29.3MHz に同調')
C(B, '2p', 'TB1', 'TB2', 'NP0、段間結合', fp=FP_CS)
LT(B, 'T30-6 17T/2T', 'TB2', 'TXBPF_OUT', G, '送信 BPF 2 段目')
C(B, '22p', 'TB2', G, 'NP0', fp=FP_CS)
TC(B, '30p', 'TB2', G, '29.3MHz に同調')
# バッファ 2N3866（TX8V、約 50mA）
C(B, '0.01u', 'TXBPF_OUT', 'Q_BUF_B')
R(B, '4.7k', 'TX8V', 'Q_BUF_B')
R(B, '1k', 'Q_BUF_B', G)
add(B, 'Transistor_BJT:Q_NPN_EBC', '2N3866', 'Package_TO_SOT_THT:TO-39-3',
    {'1': 'Q_BUF_E', '2': 'Q_BUF_B', '3': 'Q_BUF_C'}, 'バッファ（TO-39、放熱クリップを付ける）')
R(B, '4.7', 'Q_BUF_E', 'Q_BUF_E2', '帰還（バイパスしない）')
R(B, '10', 'Q_BUF_E2', G)
C(B, '0.01u', 'Q_BUF_E2', G)
Lx(B, '10uH', 'TX8V', 'Q_BUF_C', 'コレクタチョーク')
C(B, '0.01u', 'TX8V', G)
C(B, '0.01u', 'Q_BUF_C', 'DRV_IN')
# ドライバ RD06HHF1（ドレイン 13.8V、ゲートバイアスは TX8V から）
R(B, '10', 'DRV_IN', 'DRV_G', 'ゲートストッパー')
R(B, '47', 'DRV_IN', 'DRV_SW', '入力スワンプ')
C(B, '0.01u', 'DRV_SW', G)
R(B, '3.3k', 'TX8V', 'DRV_BN')
VR(B, '5k', 'DRV_BN', 'DRV_BW', G, 'RD06HHF1 アイドル電流（約 100mA）')
C(B, '0.01u', 'DRV_BW', G)
R(B, '1k', 'DRV_BW', 'DRV_IN', 'ゲートバイアス')
add(B, L + 'RD_MOSFET_GSD', 'RD06HHF1', FP_TO220, {'1': 'DRV_G', '2': G, '3': 'DRV_D'},
    'ドライバ（約 1W）。放熱器 HS1 に固定')
Lx(B, 'FT37-43 10T', '+13V8', 'DRV_D', 'ドレインチョーク（約 25µH）', fp=FP_T50)
C(B, '0.1u', '+13V8', G)
C(B, '0.01u', 'DRV_D', 'PA_IN')
# ファイナル RD16HHF1
R(B, '10', 'PA_IN', 'PA_G', 'ゲートストッパー')
R(B, '100', 'PA_IN', 'PA_SW', '入力スワンプ（2 本並列で 50Ω）', fp=FP_R1W)
R(B, '100', 'PA_IN', 'PA_SW', '入力スワンプ（2 本並列で 50Ω）', fp=FP_R1W)
C(B, '0.01u', 'PA_SW', G)
R(B, '3.3k', 'TX8V', 'PA_BN')
VR(B, '5k', 'PA_BN', 'PA_BW', G, 'RD16HHF1 アイドル電流（約 300mA）')
C(B, '0.01u', 'PA_BW', G)
R(B, '1k', 'PA_BW', 'PA_IN', 'ゲートバイアス')
add(B, L + 'RD_MOSFET_GSD', 'RD16HHF1', FP_TO220, {'1': 'PA_G', '2': G, '3': 'PA_D'},
    'ファイナル（10W）。基板端に置き、シャーシの放熱器にねじ止め（絶縁不要: タブ = ソース = GND）')
Lx(B, 'FT50-43 8T', '+13V8', 'PA_D', 'ドレインチョーク（0.8mm 線、3A）', fp=FP_T50)
C(B, '0.1u', '+13V8', G)
C(B, '0.01u', '+13V8', G)
CP(B, '220u', '+13V8', G, '25V 以上', fp=FP_CP8)
C(B, '0.1u', 'PA_D', 'T1_P', '50V 以上')
add(B, 'Device:Transformer_1P_1S', 'BN43-202 2T:4T', L + 'Transformer_BN43-202',
    {'1': 'T1_P', '2': G, '3': 'LPF_IN', '4': G}, '出力整合 1:4（12.5Ω → 50Ω）。一次 2 回・二次 4 回')
# 7 次チェビシェフ LPF（fc 約 32MHz）
C(B, '120p', 'LPF_IN', G, 'NP0 500V', fp=FP_CHV)
Lx(B, 'T50-6 9T', 'LPF_IN', 'LPF2', '約 0.35µH', fp=FP_T50)
C(B, '220p', 'LPF2', G, 'NP0 500V', fp=FP_CHV)
Lx(B, 'T50-6 10T', 'LPF2', 'LPF3', '約 0.39µH', fp=FP_T50)
C(B, '220p', 'LPF3', G, 'NP0 500V', fp=FP_CHV)
Lx(B, 'T50-6 9T', 'LPF3', 'TX_OUT', '約 0.35µH', fp=FP_T50)
C(B, '120p', 'TX_OUT', G, 'NP0 500V', fp=FP_CHV)
# 出力検出（進行波の目安）
C(B, '4.7p', 'TX_OUT', 'FD1', 'NP0 500V。容量分割', fp=FP_CS)
C(B, '100p', 'FD1', G, '', fp=FP_CS)
R(B, '10k', 'FD1', G)
D(B, '1N60', 'FD2', 'FD1', '出力検波（ゲルマニウム）')
C(B, '0.01u', 'FD2', G)
R(B, '47k', 'FD2', G)
R(B, '10k', 'FD2', 'FWD_ADC')
C(B, '0.1u', 'FWD_ADC', G)

# =====================================================================
# 受信（BPF・2N3819・SA612・10.7MHz 水晶フィルタ・MC3361）
# =====================================================================
B = '受信'
D(B, '1N4148', G, 'RX_ANT', '入力保護', sym='Diode:1N4148')
D(B, '1N4148', 'RX_ANT', G, '入力保護', sym='Diode:1N4148')
LT(B, 'T30-6 17T/2T', 'RB1', 'RX_ANT', G, '受信 BPF 1 段目')
C(B, '22p', 'RB1', G, 'NP0', fp=FP_CS)
TC(B, '30p', 'RB1', G, '29.3MHz に同調')
C(B, '2p', 'RB1', 'RB2', 'NP0、段間結合', fp=FP_CS)
LT(B, 'T30-6 17T/2T', 'RB2', None, G, '受信 BPF 2 段目（タップは使わない）')
C(B, '22p', 'RB2', G, 'NP0', fp=FP_CS)
TC(B, '30p', 'RB2', G, '29.3MHz に同調')
R(B, '4.7k', 'RB2', G, 'Q 調整')
add(B, 'Transistor_FET:2N3819', '2N3819', 'Package_TO_SOT_THT:TO-92_Inline', {'1': 'RFA_D', '2': 'RB2', '3': 'RFA_S'},
    'RF アンプ（ソース接地）')
R(B, '330', 'RFA_S', G)
C(B, '0.01u', 'RFA_S', G)
R(B, '1k', 'RX8V', 'RFA_D')
C(B, '0.01u', 'RX8V', G)
C(B, '0.01u', 'RFA_D', 'MIX_IN')
# 第 1 混合 SA612
add(B, L + 'SA612', 'SA612AN', FP_DIP8,
    {'1': 'MIX_IN', '2': 'MIX_INB', '3': G, '4': 'MIX_OUT', '5': None, '6': 'LO_IN', '7': None, '8': '+5VA'}, '第 1 混合')
C(B, '0.01u', 'MIX_INB', G)
C(B, '0.1u', '+5VA', G)
R(B, '1k', 'CLK1', 'LO_DIV', '局発を約 0.3Vp-p に減衰')
R(B, '100', 'LO_DIV', G)
C(B, '0.01u', 'LO_DIV', 'LO_IN')
add(B, L + 'Filter_3pin', '10M15A', 'Crystal:Crystal_HC49-U-3Pin_Vertical', {'1': 'MIX_OUT', '2': G, '3': 'IF1'},
    '10.7MHz 水晶フィルタ（帯域 ±7.5kHz）。ピン配置は実物で確認')
# MC3361
add(B, L + 'MC3361', 'MC3361', FP_DIP16,
    {'16': 'IF1', '1': 'OSC_B', '2': 'OSC_E', '3': 'MIX3', '5': 'LIM_IN', '6': 'DEC1', '7': 'DEC2', '8': 'QUAD',
     '9': 'AF_DEM', '10': None, '11': None, '12': None, '13': None, '14': None, '4': '+5VA', '15': G},
    '第 2 混合（455kHz）・リミッタ・検波。スケルチは XIAO 側で行うので 10〜14 番は未使用')
add(B, 'Device:Crystal', '10.245MHz', 'Crystal:Crystal_HC49-U_Vertical', {'1': 'OSC_B', '2': G}, '第 2 局発（並列共振）')
C(B, '68p', 'OSC_B', 'OSC_E', 'NP0', fp=FP_CS)
C(B, '220p', 'OSC_E', G, 'NP0', fp=FP_CS)
add(B, L + 'Filter_3pin', 'CFWLA455KFFA', L + 'Filter_Ceramic_3pin_P2.54mm', {'1': 'MIX3', '2': G, '3': 'LIM_IN'},
    '455kHz セラミックフィルタ（±7.5kHz 程度）。ピン配置は実物で確認')
C(B, '0.1u', 'DEC1', G)
C(B, '0.1u', 'DEC2', G)
add(B, 'Device:Crystal', 'CDBM455C24', FP_CHV, {'1': 'QUAD', '2': '+5VA'}, '455kHz セラミックディスクリミネータ（2 端子、5mm ピッチ）')
R(B, '6.8k', 'QUAD', '+5VA', 'ディスクリミネータの Q 調整（音が歪むときは 3.9k〜10k で調整）')
C(B, '0.1u', '+5VA', G)
# ディエンファシス・音量・ミュート・LM386
R(B, '10k', 'AF_DEM', 'AF_DE', 'ディエンファシス 470µs')
C(B, '0.047u', 'AF_DE', G)
C(B, '1u', 'AF_DE', 'VOL_H')
HDR(B, 'VOL', ['VOL_H', 'VOL_W', G], '上面 VOL（10kΩ A カーブ）')
R(B, '4.7k', 'VOL_W', 'AF_IN')
NPN(B, '2SC1815', G, 'AF_IN', 'MUTE_B', 'スケルチのミュート（MUTE = High で消音）')
R(B, '10k', 'MUTE', 'MUTE_B')
R(B, '10k', 'MUTE_B', G)
add(B, 'Amplifier_Audio:LM386', 'LM386N-1', FP_DIP8,
    {'3': 'AF_IN', '2': G, '4': G, '6': 'RX8V', '7': 'AF_BYP', '5': 'AF_OUT', '1': None, '8': None}, '低周波増幅（利得 20）')
CP(B, '10u', 'AF_BYP', G)
C(B, '0.1u', 'RX8V', G)
CP(B, '100u', 'RX8V', G, '', fp=FP_CP6)
R(B, '10', 'AF_OUT', 'ZOBEL')
C(B, '0.047u', 'ZOBEL', G)
CP(B, '220u', 'AF_OUT', 'SPK', '16V 以上', fp=FP_CP6)
HDR(B, 'SP', ['SPK', G], 'スピーカー 8Ω')
add(B, 'Regulator_Linear:L78L05_TO92', '78L05', FP_TO92, {'1': '+5VA', '2': G, '3': 'RX8V'}, '受信用 5V（SA612・MC3361・スケルチ）')
C(B, '0.1u', 'RX8V', G)
CP(B, '10u', '+5VA', G)
# スケルチ用ノイズ検出（MCP6002、+5VA）
R(B, '10k', '+5VA', 'NREF')
R(B, '10k', 'NREF', G)
CP(B, '10u', 'NREF', G)
C(B, '2.2n', 'AF_DEM', 'NQ_IN', 'ノイズ HPF（約 7kHz 以上）')
R(B, '10k', 'NQ_IN', 'NQ_N')
R(B, '470k', 'NQ_N', 'NQ_OUT', 'ノイズアンプ利得 47')
add(B, 'Amplifier_Operational:MCP6002-xP', 'MCP6002', FP_DIP8,
    {'3': 'NREF', '2': 'NQ_N', '1': 'NQ_OUT', '5': 'NREF', '6': 'NQ_B', '7': 'NQ_B', '8': '+5VA', '4': G},
    'A: スケルチ用ノイズアンプ、B: 未使用（ボルテージフォロワで固定）')
C(B, '0.1u', '+5VA', G)
C(B, '0.1u', 'NQ_OUT', 'NR1')
D(B, '1N60', 'NR1', G, '倍電圧検波')
D(B, '1N60', 'NOISE_V', 'NR1')
C(B, '0.47u', 'NOISE_V', G)
R(B, '100k', 'NOISE_V', G)
R(B, '10k', 'NOISE_V', 'NOISE_ADC')
R(B, '22k', 'NOISE_ADC', G, 'ADC 入力を 3.1V 以下に')

PREFIX = {'Device:R': 'R', 'Device:C': 'C', 'Device:C_Polarized': 'C', 'Device:C_Trim': 'TC', 'Device:L': 'L',
          'Device:R_Potentiometer_Trim': 'VR', 'Device:Crystal': 'X', 'Device:Transformer_1P_1S': 'T',
          'Connector:TestPoint': 'TP', 'power:PWR_FLAG': '#FLG', 'Relay:G5V-2': 'K',
          'Jumper:SolderJumper_3_Bridged12': 'JP'}
def prefix(p):
    s = p['sym']
    if s in PREFIX: return PREFIX[s]
    if s.startswith('Connector_Generic'): return 'J'
    if s.startswith('Diode:') or s == 'Device:D': return 'D'
    if s.startswith('Transistor') or 'RD_MOSFET' in s: return 'Q'
    if s.endswith('L_Tap'): return 'L'
    if s.endswith('Filter_3pin'): return 'FL'
    return 'U'

def numbered():
    cnt = {}
    for p in parts:
        k = prefix(p); cnt[k] = cnt.get(k, 0) + 1
        p['ref'] = '%s%d' % (k, cnt[k]) if not k.startswith('#') else '%s0%d' % (k, cnt[k])
    return parts

numbered()

if __name__ == '__main__':
    import collections
    nets = collections.defaultdict(list)
    for p in parts:
        for k, n in p['pins'].items():
            if n: nets[n].append(p['ref'] + '.' + k)
    print(len(parts), 'parts', len(nets), 'nets')
    for n, v in sorted(nets.items()):
        if len(v) < 2: print('SINGLE', n, v)
