# Serrasoid TRX 29M 部品表（BOM）

回路一覧 `tools/circuit.py` から `tools/gen_bom.py` で生成。回路図 `Serrasoid_TRX.kicad_sch` と同じ内容。

- 部品はリード部品。第 1 混合の NJM2594V（U13）だけ表面実装（SSOP8、0.65mm ピッチ。SA612 が製造中止のため）
- IC はすべて丸ピン IC ソケットを使う前提のフットプリント
- 基板専用部品（回路図にない）: RD06HHF1 の放熱器（秋月 20PB020）、取付穴

## 抵抗 R

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| R1-R4 | 5.6k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 4 | 秋月電子 | RD25S 5K6（125562） |  |
| R5, R16, R26, R28, R35 | 4.7k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 5 | 秋月電子 | CF25J4K7B（125472） | R5: Q 調整<br>R26, R28: I2C プルアップ |
| R6, R10, R17, R53, R63 | 1.5k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 5 | 秋月電子 | CF25J1K5B（125152） | R10: ダンピング（ζ 約 0.7）<br>R17: コレクタ負荷（水晶フィルタの入力側の終端。10M15A の規格に合わせて調整）<br>R53: TX ランプ電流<br>R63: 定電流源エミッタ抵抗 |
| R7, R37-R39, R88 | 330 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 5 | 秋月電子 | CF25J330RB（125331） | R37: 送信 BPF への直列抵抗。VCO の出力バッファ 3 回路を 330Ω ずつで合わせる（並列で約 110Ω）<br>R38: VCO の出力バッファ 2 個目の直列抵抗<br>R39: VCO の出力バッファ 3 個目の直列抵抗<br>R88: ×2 段 4 の遅延 17ns（14.65MHz の 1/4 周期） |
| R8 | 1.2k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J1K2B（125122） | 局発を約 106mVrms に減衰（NJM2594 のキャリア入力 1200Ω。データシートの規格 100mVrms・−7dBm、約 100mV 以上で出力一定） |
| R9, R12, R14, R21, R44, R76, R78, R82, R89 | 1k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 9 | 秋月電子 | CF25J1KB（125102） | R9: 負荷（NJM2594 の入力 600Ω と並列で約 375Ω、利得 約 4dB。感度が足りなければ外す）<br>R14: NJM2594 のエミッタフォロワの負荷（アイドル電流 約 3.3mA ＝（5V − 1.7V）÷ 1k）<br>R21: PTT 保護抵抗<br>R44: リレー駆動のベース電流 約 2.6mA（コイル約 42mA を確実に飽和させる）<br>R76, R82: ゲートバイアス<br>R78: 同調 1（3.66MHz）の駆動。Q 約 5 を決める<br>R89: 同調 2（7.33MHz）の駆動。Q 約 5 を決める |
| R11, R58, R62 | 100 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 3 | 秋月電子 | CF25J100RB（125101） | R58: Si5351 CLK0 の直列抵抗 |
| R13, R15, R48 | 22k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 3 | 秋月電子 | CF25J22KB（125223） | R15: 10.7MHz 増幅のベースバイアス（約 1.4V）<br>R48: ADC 入力を 3.1V 以下に |
| R18 | 82 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J82RB（114276） | エミッタ帰還（バイパスしない。利得 ≒ 1.5k ÷ 91Ω） |
| R19 | 180 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J180RB（125181） |  |
| R20, R22, R23, R27, R29, R31-R34, R36, R41, R42, R46, R47, R51, R52, R54, R56, R64, R66, R90, R93 | 10k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 22 | 秋月電子 | RD25S 10K（125103） | R29: PTT プルアップ<br>R31: ディエンファシス 470µs<br>R51: VREF = 2.5V |
| R24, R84, R85, R91 | 1M | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 4 | 秋月電子 | CF25J1MB（125105） | R24: 自己バイアス<br>R84, R85, R91: 自己バイアス（しきい値 = 入力の平均） |
| R25 | 20k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J20KB（103940） | ダンピング（データシートは 20k）。音が歪むときは 6.8k〜47k で調整 |
| R30 | 220 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J220RB（125221） | 出力の直列抵抗（発振振幅・高調波を抑える） |
| R40 | 470k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | RD25S 470K（125474） | ノイズアンプ利得 47 |
| R43, R73, R75, R83 | 10 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 4 | 秋月電子 | CF25J10RB（125100） | R75, R83: ゲートストッパー |
| R45, R57, R65 | 100k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 3 | 秋月電子 | CF25J100KB（125104） | R57: 利得 11 |
| R49, R79 | 470 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 2 | 秋月電子 | CF25J470RB（125471） | R49: マイク電源デカップリング<br>R79: 同調 3（14.65MHz）の駆動。Q 約 5 を決める |
| R50, R59, R67 | 2.2k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 3 | 秋月電子 | CF25J2K2B（125222） | R50: エレクトレットのバイアス<br>R59: IDC（クリップ） |
| R55 | 220k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J220KB（125224） | マイクアンプ利得 22 |
| R60, R61 | 15k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 2 | 秋月電子 | MFS25F15KB（108552） | R60: 3kHz LPF（サレンキー） |
| R68 | 120 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J120RB（125121） |  |
| R69 | 1.8k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | MFS25F1K8B（108538） | ×2 段 1 の遅延 137ns（1.83MHz の 1/4 周期） |
| R70 | 510 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J510RB（125511） | ×2 段 3 の遅延 34ns（7.33MHz の 1/4 周期） |
| R71 | 560 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J560RB（125561） | ベースバイアス（分圧電流 約 12mA、hFE が低くても約 40mA を保つ） |
| R72 | 4.7 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J4R7B（125047） | 帰還（バイパスしない） |
| R74 | 47 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J47RB（125470） | 入力スワンプ |
| R77, R86 | 3.3k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 2 | 秋月電子 | CF25J3K3B（125332） |  |
| R80, R81 | 100 | R Axial DIN0414 L11.9mm D4.5mm P5.08mm Vertical | 2 | 秋月電子 | CFS50J100RB（107803） | 入力スワンプ（2 本並列で 50Ω） |
| R87 | 910 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J910RB（114277） | ×2 段 2 の遅延 68ns（3.66MHz の 1/4 周期） |
| R92 | 47k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 秋月電子 | CF25J47KB（118208） |  |

**抵抗 R 合計: 93**

## 半固定抵抗 VR

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| VR1, VR3, VR4 | 10k | Potentiometer TOCOS GF063P Vertical | 3 | 秋月電子 | GF063P B103K（114905） | VR1: マイク利得<br>VR3: 周波数偏移（±5kHz に調整）<br>VR4: しきい値の中心（エッジがのこぎり波の中央に来るように） |
| VR2 | 1k | Potentiometer TOCOS GF063P Vertical | 1 | 秋月電子 | GF063P B102K（114901） | のこぎり波の傾き調整（約 260〜430µA） |
| VR5-VR7 | 5k | Potentiometer TOCOS GF063P Vertical | 3 | 秋月電子 | GF063P B502K（114904） | VR5: パルス幅（デューティ 50%）調整<br>VR6: RD06HHF1 アイドル電流（約 100mA）<br>VR7: RD16HHF1 アイドル電流（約 300mA） |

**半固定抵抗 VR 合計: 7**

## コンデンサ C

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| C1, C3, C6, C9, C15-C17, C20, C27, C30-C33, C36, C37, C40, C41, C47, C52, C54, C56, C68, C73, C75, C77, C78, C89, C91, C93, C99, C101, C102, C107, C117 | 0.1u | C Disc D5.0mm W2.5mm P2.50mm | 34 | 秋月電子 | C1, C3, C6, C9, C15-C17, C20, C27, C30-C33, C36, C37, C40, C41, C47, C52, C54, C56, C68, C73, C75, C77, C78, C89, C91, C93, C99, C101, C107, C117: RDER71H104K0P1H03B（113582）<br>C102: RDER72A104K1K1H03B（115927） | C33: 差動入力の中点（6 番）の AC 接地<br>C40, C41: データシートどおり VCC へ<br>C102: 約 1.6Arms 流れるので、円板ではなく積層セラミック（X7R、100V）を使う |
| C2 | 470u | CP Radial D8.0mm P3.50mm | 1 | 秋月電子 | 25PX470MEFC8X11.5（117883） | 25V 以上 |
| C4, C10, C79, C81 | 22p | C Disc D3.0mm W1.6mm P2.50mm | 4 | 秋月電子 | RD15N220J1HL2L（104060） | NP0 |
| C5 | 0.33u | C Disc D5.0mm W2.5mm P2.50mm | 1 | 秋月電子 | RD15W334K1HL2L-10（115937） |  |
| C7, C11, C14, C19, C22, C28, C49, C57, C65, C74 | 10u | CP Radial D5.0mm P2.00mm | 10 | 秋月電子 | 50PX10MEFC5X11（117897） | C11: 25V 以上 |
| C8 | 2p | C Disc D3.0mm W1.6mm P2.50mm | 1 | 秋月電子 | RDE5C1H2R0C0K1H03B（108044） | NP0、段間結合 |
| C12, C13, C43, C66 | 220p | C Disc D3.0mm W1.6mm P2.50mm | 4 | 秋月電子 | RDE5C1H221J0K1H03B（108106） | C12, C13: PFD のパルスをならす<br>C43: NP0（データシートどおり VCC へ）<br>C66: 高域カット |
| C18, C21, C23-C26, C34, C38, C44, C45, C53, C82, C85-C88, C90, C92, C96, C100, C103, C116 | 0.01u | C Disc D5.0mm W2.5mm P2.50mm | 22 | 秋月電子 | C18, C21: RDE5C1H103J1K1H03B（108043）<br>C23-C26, C34, C38, C44, C45, C53, C82, C85-C88, C90, C92, C96, C100, C103, C116: RD15W103K1HL2L-10（104063） | C18: フィルム（または C0G）<br>C21: フィルム（または C0G）。積分<br>C45: DC カット（受信中に入力を GND に落としても出力から電流が流れない） |
| C29 | 470p | C Disc D3.0mm W1.6mm P2.50mm | 1 | 秋月電子 | RDE5C1H471J0K1H03B（108110） | 339kHz の極（PFD の残りを落とす） |
| C35, C106 | 47p | C Disc D3.0mm W1.6mm P2.50mm | 2 | 秋月電子 | RDE5C1H470J0K1H03B（108045） | C35: NP0。可変容量の結合（範囲 約 0.8MHz）<br>C106: NP0 |
| C39 | 27p | C Disc D3.0mm W1.6mm P2.50mm | 1 | 秋月電子 | RDE5C1H270J0K1H03B（108095） | NP0 |
| C42, C71 | 68p | C Disc D3.0mm W1.6mm P2.50mm | 2 | 秋月電子 | RDE5C1H680J0P1H03B（114323） | C42: NP0<br>C71: C0G（NP0）必須。のこぎり波の直線性に直結。546ns で約 1.9〜3.1V |
| C46 | 56p | C Disc D3.0mm W1.6mm P2.50mm | 1 | 秋月電子 | RDE5C1H560J0K1H03B（108099） | NP0 |
| C48, C69 | 2.2n | C Disc D5.0mm W2.5mm P2.50mm | 2 | 秋月電子 | RDER71H222K0P1H03B（112060） | C48: ノイズ HPF（約 7kHz 以上） |
| C50, C58 | 0.047u | C Disc D5.0mm W2.5mm P2.50mm | 2 | 秋月電子 | RDER71H473K0P1H03B（112059） |  |
| C51, C62, C67, C72 | 1u | C Disc D5.0mm W2.5mm P2.50mm | 4 | 秋月電子 | RD15W105K1HL2L-503（115940） |  |
| C55 | 100u | CP Radial D6.3mm P2.50mm | 1 | 秋月電子 | 25PX100MEFC5X11（117877） |  |
| C59 | 0.47u | C Disc D5.0mm W2.5mm P2.50mm | 1 | 秋月電子 | RD15W474K1HL2L-10（115938） |  |
| C60 | 220u | CP Radial D6.3mm P2.50mm | 1 | 秋月電子 | 25PX220MEFC6.3X11（117879） | 16V 以上 |
| C61, C63, C64 | 47u | CP Radial D5.0mm P2.00mm | 3 | 秋月電子 | 35PX47MEFC5X11（117887） |  |
| C70 | 4.7n | C Disc D5.0mm W2.5mm P2.50mm | 1 | 秋月電子 | 50F2D472J（110336） |  |
| C76, C83, C105, C112, C114 | 100p | C Disc D3.0mm W1.6mm P2.50mm | 5 | 秋月電子 | C76, C114: RD15N101J1HL2L-10（104061）<br>C83, C105, C112: RDE5C1H101J0K1H03B（108063） | C76: ワンショット時定数<br>C83, C105: NP0<br>C112: NP0。同調 2（7.33MHz、配線と 74HCU04 の入力を含めて） |
| C80 | 1p | C Disc D3.0mm W1.6mm P2.50mm | 1 | 秋月電子 | RDE5C1H1R0C0K1H03B（108082） | NP0、段間結合（2p では過結合で ±1.8MHz が落ちない。1p で 29.0〜29.7MHz の偏差 0.6dB 以内） |
| C84 | 82p | C Disc D3.0mm W1.6mm P2.50mm | 1 | 秋月電子 | RDE5C1H820J0K1H03B（108101） | NP0 |
| C94 | 180p | C Disc D3.0mm W1.6mm P2.50mm | 1 | 秋月電子 | RDE5C1H181J0K1H03B（108105） | NP0。同調 1（3.66MHz、配線と 74HCU04 の入力を含めて） |
| C95 | 120p | C Disc D3.0mm W1.6mm P2.50mm | 1 | 秋月電子 | RDE5C1H121J0K1H03B（108103） | NP0。同調 3（14.65MHz、配線と 74HCU04 の入力を含めて） |
| C97, C98, C115 | 1000p | C Disc D3.0mm W1.6mm P2.50mm | 3 | 秋月電子 | RDE5C1H102J0K1H03B（108114） |  |
| C104 | 220u | CP Radial D8.0mm P3.50mm | 1 | 秋月電子 | 25PX220MEFC6.3X11（117879） | 25V 以上 |
| C108, C111 | 120p | C Disc D5.0mm W2.5mm P5.00mm | 2 | DigiKey／Mouser（要確認） | C0G 500V〜1kV ディスク 120pF | NP0 500V |
| C109, C110 | 220p | C Disc D5.0mm W2.5mm P5.00mm | 2 | DigiKey／Mouser（要確認） | C0G 500V〜1kV ディスク 220pF | NP0 500V |
| C113 | 4.7p | C Disc D3.0mm W1.6mm P2.50mm | 1 | DigiKey／Mouser（要確認） | C0G 500V〜1kV ディスク 4.7pF | NP0 500V。容量分割 |

**コンデンサ C 合計: 117**

## トリマコンデンサ TC

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| TC1-TC5 | 30p | C Trimmer TMCV01 | 5 | 秋月電子 | TMCV01-30P100VBG（115472） | TC1, TC2, TC4, TC5: 29.3MHz に同調<br>TC3: VCO の中心。VT が約 2.5V で 29.3MHz に |

**トリマコンデンサ TC 合計: 5**

## コイル L

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| L1, L3, L6, L7 | T30-6 17T/2T | L T30 3pin Vertical | 4 | 秋月電子 | T-30-6（116458） | L1: 受信 BPF 1 段目<br>L3: 受信 BPF 2 段目（タップは使わない）<br>L6: 送信 BPF 1 段目。T-30-6 に 0.4mm 線 17 回、コールド側から 2 回目でタップ<br>L7: 送信 BPF 2 段目 |
| L2, L4, L8, L10 | 10uH | L Axial L9.5mm D4.0mm P2.54mm Vertical Fastron SMCC | 4 | 秋月電子 | AL0510-100K（104922） | L2: DC-DC 入力フィルタ<br>L4: ドレインチョーク（2N3819 の Idss のばらつきでドレイン電圧が下がらないように）<br>L8: コレクタチョーク<br>L10: 同調 1（3.66MHz）。マイクロインダクタ（Q 40 程度）、±10% 品で可 |
| L5 | T50-6 15T | L T50 2pin Vertical | 1 | 秋月電子 | T-50-6（111947） | 約 0.9µH（0.5mm 線） |
| L9 | FT37-43 10T | L T50 2pin Vertical | 1 | 秋月電子 | FT-37-43（131660） | ドレインチョーク（約 35µH） |
| L11 | 1uH | L Axial L9.5mm D4.0mm P2.54mm Vertical Fastron SMCC | 1 | 秋月電子 | AL0410-1R0K（104930） | 同調 3（14.65MHz）。マイクロインダクタ（Q 40 程度）、±10% 品で可 |
| L12 | FT50-43 8T | L T50 2pin Vertical | 1 | 秋月電子 | FT-50-43（116918） | ドレインチョーク（0.8mm 線、3A） |
| L13, L15 | T50-6 9T | L T50 2pin Vertical | 2 | 秋月電子 | T-50-6（111947） | 約 0.35µH |
| L14 | T50-6 10T | L T50 2pin Vertical | 1 | 秋月電子 | T-50-6（111947） | 約 0.39µH |
| L16 | 4.7uH | L Axial L9.5mm D4.0mm P2.54mm Vertical Fastron SMCC | 1 | 秋月電子 | AL0410-4R7K（104931） | 同調 2（7.33MHz）。マイクロインダクタ（Q 40 程度）、±10% 品で可 |

**コイル L 合計: 16**

## トランス T

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| T1 | BN43-202 2T:5T | Transformer BN43-202 | 1 | DigiKey／Mouser（要確認） | Fair-Rite 2843002402（BN-43-202 相当） | 出力整合 1:6.25（8Ω → 50Ω）。一次 2 回・二次 5 回。13.8V で 10W 出すにはドレイン負荷 約 8Ω が必要 |

**トランス T 合計: 1**

## ダイオード D

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| D1 | 1N5408 | D DO-201AD P5.08mm Vertical AnodeUp | 1 | 秋月電子 | 1N5822（102229） | 逆接続保護（逆接続でヒューズを切る） |
| D2, D3, D9-D12 | 1N4148 | D DO-35 SOD27 P2.54mm Vertical AnodeUp | 6 | 秋月電子 | 1N4148（100941） | D2, D3: 入力保護<br>D9: クリップ ±0.6V<br>D11: 基準電圧（ダイオード 2 本） |
| D4 | 1N4007 | D DO-41 SOD81 P5.08mm Vertical AnodeUp | 1 | 秋月電子 | 1N4007-3485（100934） | 可変容量として使う（逆バイアス 0.5〜4.5V で約 20〜9pF）。可変容量ダイオード（1SV101 など）でも可 |
| D5 | 1N5819 | D DO-41 SOD81 P5.08mm Vertical AnodeUp | 1 | 秋月電子 | 1N5819（117244） | USB 接続時の逆流防止 |
| D6, D7, D13 | 1N60 | D DO-35 SOD27 P2.54mm Vertical AnodeUp | 3 | サトー電気 など（要確認） | 1N60 | D6: 倍電圧検波<br>D13: 出力検波（ゲルマニウム） |
| D8 | 1N4001 | D DO-41 SOD81 P5.08mm Vertical AnodeUp | 1 | 秋月電子 | 1N4007-3485（100934） | リレーコイルの逆起電力吸収 |

**ダイオード D 合計: 13**

## トランジスタ・FET Q

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| Q1 | 2N3819 | TO-92 Inline | 1 | DigiKey／サトー電気 など（要確認） | 2N3819 | RF アンプ（ソース接地） |
| Q2-Q5 | 2SC1815 | TO-92 Inline | 4 | 秋月電子 | 2SC1815L-GR-T92（106477） | Q2: 10.7MHz 増幅（エミッタ接地、約 18dB。Ic 約 2.9mA）<br>Q3: 受信中（RX8V）に VCO の入力を GND に落として発振を止める<br>Q4: スケルチのミュート（MUTE = High で消音）<br>Q5: リレー駆動 |
| Q6 | 2N7000 | TO-92 Inline | 1 | 秋月電子 | 2N7000（109723） | 放電スイッチ |
| Q7 | 2SA1015 | TO-92 Inline | 1 | 秋月電子 | 2SA1015L-GR-T92（106734） | 定電流源 |
| Q8 | 2N3866 | TO-39-3 | 1 | DigiKey／RF 部品店（要確認） | 2N3866 | バッファ（TO-39、放熱クリップを付ける） |
| Q9 | RD06HHF1 | TO-220-3 Vertical | 1 | RF 部品店／Mouser（要確認） | RD06HHF1 | ドライバ（約 1W）。放熱器 HS1 に固定 |
| Q10 | RD16HHF1 | TO-220-3 Vertical | 1 | RF 部品店／Mouser（要確認） | RD16HHF1 | ファイナル（10W）。基板端に置き、シャーシの放熱器にねじ止め（絶縁不要: タブ = ソース = GND） |

**トランジスタ・FET Q 合計: 10**

## IC・モジュール U

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| U1 | 74AC74 | DIP-14 W7.62mm Socket | 1 | DigiKey／Mouser（要確認） | SN74AC74N | 位相周波数比較。1 個目のクロック = ×16（基準）、2 個目 = VCO。必ず AC 品（29.3MHz） |
| U2 | 78L05 | TO-92 Inline | 1 | 秋月電子 | L78L05ACZ（101250） | 受信用 5V（NJM2594・MC3361・スケルチ） |
| U3 | 74AC00 | DIP-14 W7.62mm Socket | 1 | DigiKey／Mouser（要確認） | SN74AC00N | 位相比較のリセット（UP・DN が両方 High で両方の D-FF をクリア）。2〜4 回路目は未使用 |
| U4 | L7808 | TO-220-3 Vertical | 1 | DigiKey／Mouser（要確認） | L7808CV | 受信・送信バイアス・アナログ系。小型放熱器を付ける |
| U5 | R-78E5.0-1.0 | Converter DCDC RECOM R-78E-0.5 THT | 1 | DigiKey／Mouser | R-78E5.0-1.0 | デジタル系 5V（XIAO・表示） |
| U6 | L7805 | TO-220-3 Vertical | 1 | 秋月電子 | L7805CV-DG（107903） | 変調部専用 5V（リニア。DC-DC のリプルを変調に入れないため） |
| U7, U14 | MCP6002 | DIP-8 W7.62mm Socket | 2 | 秋月電子 | MCP6002-E/P（130011） | U7: A: ループフィルタ（レール・ツー・レール出力 0〜5V）、B: 未使用（ボルテージフォロワで固定）<br>U14: A: スケルチ用ノイズアンプ、B: 未使用（ボルテージフォロワで固定） |
| U8 | LP2950-3.3 | TO-92 Inline | 1 | 秋月電子 | LP2950L-33-T92（108749） | Si5351 モジュール用 3.3V |
| U9 | NJM2594V | TSSOP-8 4.4x3mm P0.65mm | 1 | 秋月電子 | NJM2594V（111195） | 第 1 混合（DBM、変換利得 0dB）。表面実装 SSOP8（0.65mm ピッチ）、部品面に手はんだ（この部品だけ表面実装）。3 番エミッタフォロワ出力、2 番は開放、8 番（内部で未接続）は開放（基板で両側を信号線に挟まれ GND に落とせないため） |
| U10 | AE-Si5351A | DIP-8 W7.62mm | 1 | 秋月電子 | AE-Si5351A-B（110679） | 秋月 AE-Si5351A。CLK0 = 変調基準 18.3125MHz（送信時のみ。29.3MHz ÷ 16 × 10）、CLK1 = 受信局発 18.6MHz（受信時のみ） |
| U11, U22 | 74HCU04 | DIP-14 W7.62mm Socket | 2 | DigiKey／Mouser（要確認） | SN74HCU04N | U11: VCO 専用（必ず U 付き）。1: 発振、2: 位相比較行きのバッファ、3〜5: 送信 RF 行きのバッファ（出力を 330Ω ずつで合わせ、駆動を強くする）、6: 未使用。受信中は 1 の入力が GND に落ち、バッファの出力は Low のまま止まる<br>U22: アンバッファ品（必ず U 付き）。1〜3: 同調 1〜3 の後の自己バイアス増幅。4〜6 回路目は未使用 |
| U12 | MC3361 | DIP-16 W7.62mm Socket | 1 | サトー電気／海外通販 など（要確認） | MC3361 | 第 2 混合（455kHz）・リミッタ・検波。スケルチは XIAO 側で行うので 10〜14 番は未使用 |
| U13 | XIAO ESP32C3 | Seeeduino XIAO Socket | 1 | 秋月電子 | 113991054（117454） | ソケット実装。起動設定ピン D0（GPIO2）・D9（GPIO9）は起動時に High が必要なので、ふだん開放の PTT とエンコーダ SW をつなぐ（PTT・つまみを押したまま電源を入れない）。D8（GPIO8）はフラッシュ起動に関係しないのでエンコーダ B 相 |
| U15 | LM386N-1 | DIP-8 W7.62mm Socket | 1 | 秋月電子 | LM386G-D08（114548） | 低周波増幅（利得 20） |
| U16 | MCP6004 | DIP-14 W7.62mm Socket | 1 | DigiKey／Mouser（要確認） | MCP6004-I/P | A: マイクアンプ、B: 利得段、C: 3kHz LPF、D: しきい値バッファ |
| U17 | 74HCT4017 | DIP-16 W7.62mm Socket | 1 | DigiKey／Mouser（要確認） | CD74HCT4017E | ÷10。Q0 が 546ns ごとに約 55ns 幅のリセットパルス。HCT 品（3.3V 入力を受けるため）。CLK0 18.3MHz は最高クロック（5V・最悪条件で約 20MHz）に近いので、代替品は 74HC4017（3.3V 入力でも動く品）を確かめてから |
| U18 | MAX913CPA | DIP-8 W7.62mm Socket | 1 | DigiKey／Mouser（要確認） | MAX913CPA+ | 高速コンパレータ（10ns、DIP-8）。単電源 5V（V- = GND）で入力範囲は -0.2〜+3.5V、出力は TTL（High 2.4〜3.4V）。LE は Low でラッチしない（データシート: High または開放でラッチ）ので GND に固定。LT1016 は単電源では入力範囲が足りないので使わない |
| U19 | 74HCT123 | DIP-16 W7.62mm Socket | 1 | DigiKey／Mouser（要確認） | CD74HCT123E | コンパレータの立ち上がりで約 273ns（デューティ 50%）のパルス。MAX913 の TTL 出力を受けるため HCT 品。2 回路目は未使用 |
| U20, U23 | 74AC14 | DIP-14 W7.62mm Socket | 2 | DigiKey／Mouser（要確認） | SN74AC14N | U20: RC 遅延の後の波形整形（シュミット）と、段 1・2 の同調の後の整形。74AC86 に遅い波形を入れないため。必ず AC 品<br>U23: 同調 3 の後の整形（シュミット）。2〜6 回路目は未使用。必ず AC 品 |
| U21 | 74AC86 | DIP-14 W7.62mm Socket | 1 | DigiKey／Mouser（要確認） | SN74AC86N | ×2 段 1〜4（1.83 → 3.66 → 7.33 → 14.65 → 29.3MHz）。必ず AC 品 |

**IC・モジュール U 合計: 23**

## 水晶・ディスクリミネータ X

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| X1 | 10.245MHz | Crystal HC49-U Vertical | 1 | 要確認 | 10.245MHz | 第 2 局発。データシートの試験回路どおり 1 番と VCC の間 |
| X2 | CDBM455C24 | C Disc D5.0mm W2.5mm P5.00mm | 1 | 要確認 | CDBM455C24（村田） | 455kHz セラミックディスクリミネータ（2 端子、5mm ピッチ） |

**水晶・ディスクリミネータ X 合計: 2**

## フィルタ FL

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| FL1 | 10M15A | Crystal HC49-U-3Pin Vertical | 1 | 要確認 | 10M15A | 10.7MHz 水晶フィルタ（帯域 ±7.5kHz）。ピン配置は実物で確認 |
| FL2 | CFWLA455KFFA | Filter Ceramic 3pin P2.54mm | 1 | 秋月電子 | LT455EU（116046） | 455kHz セラミックフィルタ（±7.5kHz 程度）。ピン配置は実物で確認 |

**フィルタ FL 合計: 2**

## リレー K

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| K1 | G5V-2 DC12 | Relay DPDT Omron G5V-2 | 1 | DigiKey／Mouser | G5V-2-DC12 | 送受切替。1 極目: アンテナ（NC=受信、NO=送信）、2 極目: 8V を RX8V / TX8V へ |

**リレー K 合計: 1**

## コネクタ J

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| J1 | DC 13.8V | SolderWire-1sqmm 1x02 P5.4mm D1.4mm OD2.7mm | 1 | 手持ち／ホームセンター |  | 後面の DC ジャックから（ヒューズ 5A は後面パネル側） |
| J2 | I2C | PinHeader 1x04 P2.54mm Vertical | 1 | 秋月電子 | PH-1x40SG（100167） | OLED 表示を使う場合の予備 |
| J3 | LCD | PinHeader 1x04 P2.54mm Vertical | 1 | 秋月電子 | PH-1x40SG（100167） | Nextion NX4832T035（または TJC4832T135）表示器。2 番（XIAO の TX）→ 表示器の RX（黄）。表示器の TX（青）はつながない（表示器からの受信は使わない） |
| J4 | VOL | PinHeader 1x03 P2.54mm Vertical | 1 | 秋月電子 | PH-1x40SG（100167） | 上面 VOL（10kΩ A カーブ） |
| J5 | ENC | PinHeader 1x05 P2.54mm Vertical | 1 | 秋月電子 | PH-1x40SG（100167） | ロータリーエンコーダ（上面 TUNE） |
| J6 | SP | PinHeader 1x02 P2.54mm Vertical | 1 | 秋月電子 | PH-1x40SG（100167） | スピーカー 8Ω |
| J7 | MIC | PinHeader 1x03 P2.54mm Vertical | 1 | 秋月電子 | PH-1x40SG（100167） | エレクトレットマイク・PTT（上面 MIC） |
| J8 | ANT | SolderWire-1sqmm 1x02 P5.4mm D1.4mm OD2.7mm | 1 | 手持ち／ホームセンター |  | 後面 BNC へ（RG-174 で配線） |
| J9 | TX LED | PinHeader 1x02 P2.54mm Vertical | 1 | 秋月電子 | PH-1x40SG（100167） | 上面の TX ランプ |

**コネクタ J 合計: 9**

## テストポイント TP

| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|---|---|
| TP1 | VT | TestPoint THTPad D1.5mm Drill0.7mm | 1 | 手持ち |  | VCO 制御電圧。29.3MHz 送信で約 2.5V になるよう TC（VCO）を調整 |
| TP2 | TXOSC | TestPoint THTPad D1.5mm Drill0.7mm | 1 | 手持ち |  | 29.3MHz（PLL の VCO）の観測点 |
| TP3 | RAMP | TestPoint THTPad D1.5mm Drill0.7mm | 1 | 手持ち |  | のこぎり波の観測点 |
| TP4 | THRESH | TestPoint THTPad D1.5mm Drill0.7mm | 1 | 手持ち |  | しきい値（約 0.85V ± 音声）の観測点 |
| TP5 | PM | TestPoint THTPad D1.5mm Drill0.7mm | 1 | 手持ち |  | 位相変調された 1.83125MHz の観測点（立ち上がりが音声で揺れる） |
| TP6 | X16 | TestPoint THTPad D1.5mm Drill0.7mm | 1 | 手持ち |  | ×16 の出力（29.3MHz、PLL の基準）の観測点 |

**テストポイント TP 合計: 6**

## 回路図に載っていない部品

| 品名 | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |
|---|---|---|---|---|
| IC ソケット 8P | 4 | 秋月電子 | 2227-08-03（100017） | U7・U14・U15・U18 |
| IC ソケット 14P | 8 | 秋月電子 | 2227-14-03（100006） | U1・U3・U11・U16・U20・U21・U22・U23 |
| IC ソケット 16P | 3 | 秋月電子 | 2227-16-03（100007） | U12・U17・U19 |
| ピンソケット 1×7（XIAO 用） | 2 | 秋月電子 | FH-1x7SG/RH（104285） | U13 |
| 放熱器 20PB020（RD06HHF1 用） | 1 | 秋月電子 | 20PB020-01025（105054） | HS1（基板に付ける） |
| 放熱器 16PB017（L7808 用） | 1 | 秋月電子 | 16PB017-01025（105053） | U4。取り付けられる向き・隙間を要確認 |
| 放熱器（RD16HHF1 用、ケース内に立てる） | 1 | 秋月／マルツ など（要確認） | 熱抵抗 5〜8℃/W、幅 50 × 高さ 30 mm 程度 | ケースの後面の窓からフィンを出す（enclosure/README.md） |
| ロータリーエンコーダ | 1 | 秋月電子 | EC12E2420801（106357） | TUNE（J5） |
| AF ボリューム 10kΩA | 1 | 秋月電子 | SH16K4A103L20KCCI（129553） | VOL（J4） |
| 電源スイッチ | 1 | 要確認 | φ13 穴に合う 2A 以上のもの | POWER |
| 電源 LED（3mm 緑） | 1 | 秋月電子 | OSG5TA3Z74A（111635） | ON |
| TX ランプ（3mm 赤） | 1 | 秋月電子 | OSR5JA3Z74A（111577） | TX（J9） |
| マイクコネクタ 4P 丸型（パネル取付 φ16） | 1 | 千石電商／マルツ など（要確認） | 4P 丸型マイクコネクタ（メス） | MIC（J7） |
| 外部スピーカージャック（スイッチ付き） | 1 | 秋月電子 | MJ-352W-C（117359） | EXT SP（J6） |
| スピーカー 5cm 8Ω 0.5W | 1 | 秋月電子 | DXYD50N-22Z-8A-F（116024） | ふた裏に M3 皿ねじ＋ナット 4 本 |
| LCD Nextion NX4832T035（3.5 インチ 480×320） | 1 | Nextion 公式ストア／Amazon など（要確認） | NX4832T035 | J3 |
| DC ジャック 2.1mm（パネル取付） | 1 | 秋月電子 | MJ-14（106342） | 後面 |
| ヒューズホルダ（パネル取付） | 1 | 秋月電子 | MF-524M（107079） | 後面 |
| ヒューズ 5A（5×20mm） | 1 | 秋月電子 | MF51NR 250V 5（107131） |  |
| BNC コネクタ（パネル取付） | 1 | 秋月電子 | B-014IF（100093） | 後面、J8 へ RG-174 |
| M3 インサートナット | 24 | Amazon／モノタロウ |  | ケース（enclosure/README.md） |
| M3 ねじ・皿ねじ・ナット | 1 | ホームセンター／モノタロウ |  | 本数は enclosure/README.md |

購入先・販売コード・価格は `kicad/bom_purchase.csv`（`tools/make_bom_purchase.py`、秋月電子の通販サイトで 2026-10-16 に確認）。「要確認」は秋月で扱いがなく、型番・在庫を確かめていない部品。

---

**部品総数: 305**
