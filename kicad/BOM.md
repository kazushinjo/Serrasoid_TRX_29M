# Serrasoid TRX 29M 部品表（BOM）

回路一覧 `tools/circuit.py` から `tools/gen_bom.py` で生成。回路図 `Serrasoid_TRX.kicad_sch` と同じ内容。

- 表面実装部品は使わない（すべてリード部品）
- IC はすべて丸ピン IC ソケットを使う前提のフットプリント
- 基板専用部品（回路図にない）: RD06HHF1 の放熱器（秋月 20PB020）、取付穴

## 抵抗 R

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| R1, R2, R15, R51, R58 | 4.7k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 5 | R1, R2: I2C プルアップ<br>R51: Q 調整 |
| R3-R6, R9, R13, R22, R23, R26, R29, R34, R48, R50, R57, R59, R60, R62-R64, R67 | 10k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 20 | R6: PTT プルアップ<br>R22: VREF = 2.5V<br>R57: ディエンファシス 470µs |
| R7, R8, R42, R47, R53 | 1k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 5 | R7: PTT 保護抵抗<br>R8: リレー駆動のベース電流 約 2.6mA（コイル約 42mA を確実に飽和させる）<br>R42, R47: ゲートバイアス<br>R53: 負荷（利得を約 8dB に抑える） |
| R10, R12 | 1.5k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 2 | R10: TX ランプ電流<br>R12: 定電流源エミッタ抵抗 |
| R11, R14, R21, R55 | 100 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 4 | R11: Si5351 CLK0 の直列抵抗<br>R21: BPF への直列抵抗 |
| R16 | 3.9k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | ×2 段 1 の遅延 273ns（915.6kHz の 1/4 周期） |
| R17 | 1.8k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | ×2 段 2 の遅延 137ns（1.83MHz の 1/4 周期） |
| R18 | 910 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | ×2 段 3 の遅延 68ns（3.66MHz の 1/4 周期） |
| R19 | 510 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | ×2 段 4 の遅延 34ns（7.33MHz の 1/4 周期） |
| R20, R52 | 330 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 2 | R20: ×2 段 5 の遅延 17ns（14.65MHz の 1/4 周期） |
| R24 | 470 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | マイク電源デカップリング |
| R25, R30 | 2.2k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 2 | R25: エレクトレットのバイアス<br>R30: IDC（クリップ） |
| R27 | 220k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | マイクアンプ利得 22 |
| R28, R33, R66 | 100k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 3 | R28: 利得 11 |
| R31, R32 | 15k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 2 | R31: 3kHz LPF（サレンキー） |
| R35 | 560 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | ベースバイアス（分圧電流 約 12mA、hFE が低くても約 40mA を保つ） |
| R36 | 120 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 |  |
| R37 | 4.7 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 帰還（バイパスしない） |
| R38, R39, R43, R61 | 10 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 4 | R39, R43: ゲートストッパー |
| R40 | 47 | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 入力スワンプ |
| R41, R46 | 3.3k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 2 |  |
| R44, R45 | 100 | R Axial DIN0414 L11.9mm D4.5mm P5.08mm Vertical | 2 | 入力スワンプ（2 本並列で 50Ω） |
| R49 | 47k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 |  |
| R54 | 1.2k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | 局発を約 0.25Vp-p に減衰（SA612 の範囲 200〜300mVp-p の中央） |
| R56 | 20k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | ダンピング（データシートは 20k）。音が歪むときは 6.8k〜47k で調整 |
| R65 | 470k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | ノイズアンプ利得 47 |
| R68 | 22k | R Axial DIN0207 L6.3mm D2.5mm P2.54mm Vertical | 1 | ADC 入力を 3.1V 以下に |

**抵抗 R 合計: 68**

## 半固定抵抗 VR

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| VR1 | 1k | Potentiometer TOCOS GF063P Vertical | 1 | のこぎり波の傾き調整（約 260〜430µA） |
| VR2-VR5 | 10k | Potentiometer TOCOS GF063P Vertical | 4 | VR2: パルス幅（デューティ 50%）調整<br>VR3: マイク利得<br>VR4: 周波数偏移（±5kHz に調整）<br>VR5: しきい値の中心（エッジがのこぎり波の中央に来るように） |
| VR6, VR7 | 5k | Potentiometer TOCOS GF063P Vertical | 2 | VR6: RD06HHF1 アイドル電流（約 100mA）<br>VR7: RD16HHF1 アイドル電流（約 300mA） |

**半固定抵抗 VR 合計: 7**

## コンデンサ C

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| C1 | 470u | CP Radial D8.0mm P3.50mm | 1 | 25V 以上 |
| C2, C5, C8, C9, C11, C13, C17, C18, C20, C22, C28-C30, C41, C51, C55, C58, C66, C74, C78-C80, C84, C88, C92, C93 | 0.1u | C Disc D5.0mm W2.5mm P2.50mm | 26 | C58: 約 1.6Arms 流れるので、円板ではなく積層セラミック（X7R、100V）を使う<br>C78, C79: データシートどおり VCC へ |
| C3, C4, C7, C10, C12, C32, C40, C83, C89, C90 | 10u | CP Radial D5.0mm P2.00mm | 10 | C3: 25V 以上 |
| C6 | 0.33u | C Disc D5.0mm W2.5mm P2.50mm | 1 |  |
| C14, C31, C45-C50, C52-C54, C56, C65, C70-C73, C75 | 0.01u | C Disc D5.0mm W2.5mm P2.50mm | 18 |  |
| C15, C16, C33 | 47u | CP Radial D5.0mm P2.00mm | 3 |  |
| C19, C21, C23-C25, C64 | 100p | C Disc D3.0mm W1.6mm P2.50mm | 6 | C19: C0G（NP0）必須。のこぎり波の直線性に直結<br>C21: ワンショット時定数<br>C23-C25: NP0 |
| C26 | 82p | C Disc D3.0mm W1.6mm P2.50mm | 1 | NP0 |
| C27 | 47p | C Disc D3.0mm W1.6mm P2.50mm | 1 | NP0 |
| C34, C36, C39, C82 | 1u | C Disc D5.0mm W2.5mm P2.50mm | 4 |  |
| C35, C77 | 220p | C Disc D3.0mm W1.6mm P2.50mm | 2 | C35: 高域カット<br>C77: NP0（データシートどおり VCC へ） |
| C37 | 4.7n | C Disc D5.0mm W2.5mm P2.50mm | 1 |  |
| C38, C91 | 2.2n | C Disc D5.0mm W2.5mm P2.50mm | 2 | C91: ノイズ HPF（約 7kHz 以上） |
| C42, C44, C67, C69 | 22p | C Disc D3.0mm W1.6mm P2.50mm | 4 | NP0 |
| C43, C68 | 2p | C Disc D3.0mm W1.6mm P2.50mm | 2 | NP0、段間結合 |
| C57 | 220u | CP Radial D8.0mm P3.50mm | 1 | 25V 以上 |
| C59, C62 | 120p | C Disc D5.0mm W2.5mm P5.00mm | 2 | NP0 500V |
| C60, C61 | 220p | C Disc D5.0mm W2.5mm P5.00mm | 2 | NP0 500V |
| C63 | 4.7p | C Disc D3.0mm W1.6mm P2.50mm | 1 | NP0 500V。容量分割 |
| C76 | 68p | C Disc D3.0mm W1.6mm P2.50mm | 1 | NP0 |
| C81, C86 | 0.047u | C Disc D5.0mm W2.5mm P2.50mm | 2 |  |
| C85 | 100u | CP Radial D6.3mm P2.50mm | 1 |  |
| C87 | 220u | CP Radial D6.3mm P2.50mm | 1 | 16V 以上 |
| C94 | 0.47u | C Disc D5.0mm W2.5mm P2.50mm | 1 |  |

**コンデンサ C 合計: 94**

## トリマコンデンサ TC

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| TC1-TC4 | 30p | C Trimmer TMCV01 | 4 | 29.3MHz に同調 |

**トリマコンデンサ TC 合計: 4**

## コイル L

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| L1, L4, L12 | 10uH | L Axial L9.5mm D4.0mm P2.54mm Vertical Fastron SMCC | 3 | L1: DC-DC 入力フィルタ<br>L4: コレクタチョーク<br>L12: ドレインチョーク（2N3819 の Idss のばらつきでドレイン電圧が下がらないように） |
| L2, L3, L10, L11 | T30-6 17T/2T | L T30 3pin Vertical | 4 | L2: 送信 BPF 1 段目。T-30-6 に 0.4mm 線 17 回、コールド側から 2 回目でタップ<br>L3: 送信 BPF 2 段目<br>L10: 受信 BPF 1 段目<br>L11: 受信 BPF 2 段目（タップは使わない） |
| L5 | FT37-43 10T | L T50 2pin Vertical | 1 | ドレインチョーク（約 35µH） |
| L6 | FT50-43 8T | L T50 2pin Vertical | 1 | ドレインチョーク（0.8mm 線、3A） |
| L7, L9 | T50-6 9T | L T50 2pin Vertical | 2 | 約 0.35µH |
| L8 | T50-6 10T | L T50 2pin Vertical | 1 | 約 0.39µH |

**コイル L 合計: 12**

## トランス T

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| T1 | BN43-202 2T:5T | Transformer BN43-202 | 1 | 出力整合 1:6.25（8Ω → 50Ω）。一次 2 回・二次 5 回。13.8V で 10W 出すにはドレイン負荷 約 8Ω が必要 |

**トランス T 合計: 1**

## ダイオード D

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| D1 | 1N5408 | D DO-201AD P5.08mm Vertical AnodeUp | 1 | 逆接続保護（逆接続でヒューズを切る） |
| D2 | 1N5819 | D DO-41 SOD81 P5.08mm Vertical AnodeUp | 1 | USB 接続時の逆流防止 |
| D3 | 1N4001 | D DO-41 SOD81 P5.08mm Vertical AnodeUp | 1 | リレーコイルの逆起電力吸収 |
| D4-D7, D9, D10 | 1N4148 | D DO-35 SOD27 P2.54mm Vertical AnodeUp | 6 | D4: 基準電圧（ダイオード 2 本）<br>D6: クリップ ±0.6V<br>D9, D10: 入力保護 |
| D8, D11, D12 | 1N60 | D DO-35 SOD27 P2.54mm Vertical AnodeUp | 3 | D8: 出力検波（ゲルマニウム）<br>D11: 倍電圧検波 |

**ダイオード D 合計: 12**

## トランジスタ・FET Q

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| Q1, Q8 | 2SC1815 | TO-92 Inline | 2 | Q1: リレー駆動<br>Q8: スケルチのミュート（MUTE = High で消音） |
| Q2 | 2SA1015 | TO-92 Inline | 1 | 定電流源 |
| Q3 | 2N7000 | TO-92 Inline | 1 | 放電スイッチ |
| Q4 | 2N3866 | TO-39-3 | 1 | バッファ（TO-39、放熱クリップを付ける） |
| Q5 | RD06HHF1 | TO-220-3 Vertical | 1 | ドライバ（約 1W）。放熱器 HS1 に固定 |
| Q6 | RD16HHF1 | TO-220-3 Vertical | 1 | ファイナル（10W）。基板端に置き、シャーシの放熱器にねじ止め（絶縁不要: タブ = ソース = GND） |
| Q7 | 2N3819 | TO-92 Inline | 1 | RF アンプ（ソース接地） |

**トランジスタ・FET Q 合計: 8**

## IC・モジュール U

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| U1 | R-78E5.0-1.0 | Converter DCDC RECOM R-78E-0.5 THT | 1 | デジタル系 5V（XIAO・表示） |
| U2 | L7808 | TO-220-3 Vertical | 1 | 受信・送信バイアス・アナログ系。小型放熱器を付ける |
| U3 | L7805 | TO-220-3 Vertical | 1 | 変調部専用 5V（リニア。DC-DC のリプルを変調に入れないため） |
| U4 | LP2950-3.3 | TO-92 Inline | 1 | Si5351 モジュール用 3.3V |
| U5 | XIAO ESP32C3 | Seeeduino XIAO Socket | 1 | ソケット実装。起動設定ピン D0（GPIO2）・D9（GPIO9）は起動時に High が必要なので、ふだん開放の PTT とエンコーダ SW をつなぐ（PTT・つまみを押したまま電源を入れない）。D8（GPIO8）はフラッシュ起動に関係しないのでエンコーダ B 相 |
| U6 | AE-Si5351A | DIP-8 W7.62mm | 1 | 秋月 AE-Si5351A。CLK0 = 変調基準 9.15625MHz（送信時のみ）、CLK1 = 受信局発 18.6MHz（受信時のみ） |
| U7 | 74HCT4017 | DIP-16 W7.62mm Socket | 1 | ÷10。Q0 が 1.09µs ごとに約 110ns 幅のリセットパルス。HCT 品（3.3V 入力を受けるため） |
| U8 | MAX913CPA | DIP-8 W7.62mm Socket | 1 | 高速コンパレータ（10ns、DIP-8）。単電源 5V（V- = GND）で入力範囲は -0.2〜+3.5V、出力は TTL（High 2.4〜3.4V）。LE は Low でラッチしない（データシート: High または開放でラッチ）ので GND に固定。LT1016 は単電源では入力範囲が足りないので使わない |
| U9 | 74HCT123 | DIP-16 W7.62mm Socket | 1 | コンパレータの立ち上がりで約 545ns（デューティ 50%）のパルス。MAX913 の TTL 出力を受けるため HCT 品。2 回路目は未使用 |
| U10 | 74AC14 | DIP-14 W7.62mm Socket | 1 | RC 遅延の後の波形整形（シュミット）。74AC86 に遅い波形を入れないため。必ず AC 品 |
| U11, U12 | 74AC86 | DIP-14 W7.62mm Socket | 2 | U11: ×2 段 1〜4（1.83 → 3.66 → 7.33 → 14.65MHz）。必ず AC 品<br>U12: ×2 段 5（29.3MHz）と出力バッファ。必ず AC 品 |
| U13 | MCP6004 | DIP-14 W7.62mm Socket | 1 | A: マイクアンプ、B: 利得段、C: 3kHz LPF、D: しきい値バッファ |
| U14 | SA612AN | DIP-8 W7.62mm Socket | 1 | 第 1 混合 |
| U15 | MC3361 | DIP-16 W7.62mm Socket | 1 | 第 2 混合（455kHz）・リミッタ・検波。スケルチは XIAO 側で行うので 10〜14 番は未使用 |
| U16 | LM386N-1 | DIP-8 W7.62mm Socket | 1 | 低周波増幅（利得 20） |
| U17 | 78L05 | TO-92 Inline | 1 | 受信用 5V（SA612・MC3361・スケルチ） |
| U18 | MCP6002 | DIP-8 W7.62mm Socket | 1 | A: スケルチ用ノイズアンプ、B: 未使用（ボルテージフォロワで固定） |

**IC・モジュール U 合計: 18**

## 水晶・ディスクリミネータ X

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| X1 | 10.245MHz | Crystal HC49-U Vertical | 1 | 第 2 局発。データシートの試験回路どおり 1 番と VCC の間 |
| X2 | CDBM455C24 | C Disc D5.0mm W2.5mm P5.00mm | 1 | 455kHz セラミックディスクリミネータ（2 端子、5mm ピッチ） |

**水晶・ディスクリミネータ X 合計: 2**

## フィルタ FL

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| FL1 | 10M15A | Crystal HC49-U-3Pin Vertical | 1 | 10.7MHz 水晶フィルタ（帯域 ±7.5kHz）。ピン配置は実物で確認 |
| FL2 | CFWLA455KFFA | Filter Ceramic 3pin P2.54mm | 1 | 455kHz セラミックフィルタ（±7.5kHz 程度）。ピン配置は実物で確認 |

**フィルタ FL 合計: 2**

## リレー K

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| K1 | G5V-2 DC12 | Relay DPDT Omron G5V-2 | 1 | 送受切替。1 極目: アンテナ（NC=受信、NO=送信）、2 極目: 8V を RX8V / TX8V へ |

**リレー K 合計: 1**

## コネクタ J

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| J1 | DC 13.8V | SolderWire-1sqmm 1x02 P5.4mm D1.4mm OD2.7mm | 1 | 後面の DC ジャックから（ヒューズ 5A は後面パネル側） |
| J2 | I2C | PinHeader 1x04 P2.54mm Vertical | 1 | OLED 表示を使う場合の予備 |
| J3 | TJC | PinHeader 1x04 P2.54mm Vertical | 1 | TJC 表示器（XIAO の TX → 表示器の RX。表示器からの受信は使わない） |
| J4 | ENC | PinHeader 1x05 P2.54mm Vertical | 1 | ロータリーエンコーダ（上面 TUNE） |
| J5 | ANT | SolderWire-1sqmm 1x02 P5.4mm D1.4mm OD2.7mm | 1 | 後面 BNC へ（RG-174 で配線） |
| J6 | TX LED | PinHeader 1x02 P2.54mm Vertical | 1 | 上面の TX ランプ |
| J7 | MIC | PinHeader 1x03 P2.54mm Vertical | 1 | エレクトレットマイク・PTT（上面 MIC） |
| J8 | VOL | PinHeader 1x03 P2.54mm Vertical | 1 | 上面 VOL（10kΩ A カーブ） |
| J9 | SP | PinHeader 1x02 P2.54mm Vertical | 1 | スピーカー 8Ω |

**コネクタ J 合計: 9**

## テストポイント TP

| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |
|---|---|---|---|---|
| TP1 | RAMP | TestPoint THTPad D1.5mm Drill0.7mm | 1 | のこぎり波の観測点 |
| TP2 | THRESH | TestPoint THTPad D1.5mm Drill0.7mm | 1 | しきい値（1.5V ± 音声）の観測点 |
| TP3 | PM | TestPoint THTPad D1.5mm Drill0.7mm | 1 | 位相変調された 915.625kHz の観測点（立ち上がりが音声で揺れる） |
| TP4 | X32 | TestPoint THTPad D1.5mm Drill0.7mm | 1 | 29.3MHz の観測点 |

**テストポイント TP 合計: 4**

---

**部品総数: 242**
