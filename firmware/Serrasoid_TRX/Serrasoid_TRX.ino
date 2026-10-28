// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 真城和一 (JA6FUF/JH1XHX)
/*
 * Serrasoid TRX 29M 制御 - Seeed Studio XIAO ESP32C3 + Si5351（秋月 AE-Si5351A）
 * 29.000 ~ 29.700 MHz FM（呼出 29.300MHz）。PSN_TRX のスケッチが元。
 *
 * ---- Si5351 ----
 *   CLK0 = 変調基準 = 送信周波数 × 10 ÷ 16（29.300MHz で 18.3125MHz）。送信中だけ出す
 *          （74HCT4017 で ÷10 → セラゾイド変調 1.83125MHz → ×16 → PLL の VCO が追従）
 *   CLK1 = 受信局発 = 受信周波数 − 10.7MHz（29.300MHz で 18.600MHz）。受信中だけ出す
 *
 * ---- 送受切替（D10 TX_EN → Q → リレー K1。2 極目で 8V を TX8V / RX8V に切り替える）----
 *   PTT を押す : CLK1 を止める → TX_EN = High（リレー） → RELAY_MS 待つ → CLK0 を出す（VCO が PLL に引き込まれる）
 *   PTT を離す : CLK0 を止める → RELAY_MS 待つ → TX_EN = Low → CLK1 を出す
 *   送信は 29.000〜29.700MHz の中だけ（範囲外では PTT を受け付けない）
 *
 * ---- 表示器 Nextion NX4832T035（3.5 インチ 480x320、PSN_TRX と同じ品）または TJC4832T135 ----
 *   どちらも送る命令（t0.txt= / picq / line / baud= / pco=）は同じなので、スケッチはそのまま使える。
 *   画面データだけ、Nextion は Nextion Editor、TJC は USART HMI で作る（互換性がない。nextion/画面データ作成手順.md）
 *   XIAO の D6（TX）→ 表示器の RX の一方向（表示器からの返信は受けない）
 *   t0 : 周波数（"29.300 MHz"、font1）
 *   t1 : ステップ（設定モード中はメニュー・設定値、スキャン中は "SCAN >>"）
 *   t2 : 固定表示（FIXED_TEXT）
 *   S メーター : アナログメーター。背景（ピクチャ 0、nextion/background.png）の目盛りの上に、
 *                picq（メーター面の描き直し）と line（針）で針を描く
 *                受信中 = 外側の S 目盛り、送信中 = 内側の出力 W 目盛り
 *                S は 10.7MHz 水晶フィルタの後ろの強さを AD8307（対数増幅、25mV/dB）で測り、ADS1115（I2C の ADC、
 *                アドレス 0x48、A0）で読む。ADS1115 が見つからないときは、スケルチ用ノイズの減り方（FM のクワイティング）
 *                から計算した目安に切り替わる（こちらは S5 前後より上は振れない）
 *   t3 : メーターの値（"S5" / "9.8W"）
 *   t4 : "RX" / 送信中は赤い "TX" / スキャン中は黄色の "SCAN"（文字色 pco はスケッチが変える）
 *   t5 : スケルチの深さ（"SQL 3" / "SQL OFF"）
 *   t6 : スケルチが開いているとき緑の "BUSY"
 *   配置（480x320）: font0 = 24 ドット、font1 = 32 ドット（半角英数）、page0 の背景 = ピクチャ 0（sta=image）
 *     t0 (16,16)  448x40 font1 maxl16 | t1 (16,68)  320x32 font0 maxl32 | t2 (344,68)  120x32 font0 maxl12
 *     メーター面 (16,112) 305x181（背景画像、部品は置かない）
 *     t3 (344,116) 120x32 font0 maxl10 | t4 (344,160) 120x32 font0 maxl6 | t5 (344,204) 120x32 font0 maxl8
 *     t6 (344,248) 120x32 font0 maxl6
 *     テキスト部品はすべて sta=crop image（ピクチャ 0）または bco=6372（背景と同じ色）
 *   詳しくは nextion/画面データ作成手順.md
 *
 * ---- 操作（上面 TUNE のエンコーダ）----
 *   通常       : ダイヤル = 周波数、押す = 設定モードへ、長押し = 呼出周波数 29.300MHz へ
 *   設定モード : ダイヤル = 機能を選ぶ（STEP / SQL / SCAN / EXIT）、押す = その機能へ
 *   値の変更   : ダイヤル = 値を変える、押す = 確定して通常に戻る
 *   設定モード・値の変更中に長押し、または 15 秒操作なし = 取り消して通常に戻る
 *   スキャン   : メニューの SCAN を押すと、今の周波数から 10kHz ずつ上へ 29.000〜29.700MHz をくり返し探す。
 *                1 チャンネル SCAN_DWELL_MS ずつ聞き、スケルチが開いたら止まる（BUSY）。信号が消えて
 *                SCAN_RESUME_MS たつと再開する。ダイヤル = 向きを変える、押す・長押し・PTT = スキャンをやめる
 *                （SQL OFF のときは SQL SCAN_SQL_DEFAULT で探す）
 *   周波数・ステップ・スケルチは NVS に保存（電源を切っても残る。スキャン中は止めたときに保存）
 *
 * ---- 調整（実機で合わせる。シリアルモニタ 115200bps に生の値が出る）----
 *   NOISE_NOSIG_MV / NOISE_FULL_MV : スケルチ用ノイズ（D2）の電圧。無信号のときと、十分強い信号のとき
 *   RSSI_MV_S9 / RSSI_MV_PER_DB    : S9（−73dBm）を入れたときの AD8307 の出力 [mV] と、1dB あたりの変化（データシート 25mV）
 *   QUIET_RANGE_DB                 : ノイズが無信号から消えきるまでの信号の強さの幅 [dB]（ADS1115 がないときの S の換算）
 *   FWD_MV_10W                     : 出力検出（D1）の電圧。ダミーロードに 10W 出したとき
 *
 * Libraries:
 *   - Etherkit Si5351
 *   - Preferences（ESP32 標準内蔵・NVS フラッシュ保存）
 *
 * Wiring (XIAO ESP32C3、回路図の制御ブロック):
 *   D0  (GPIO2)  PTT_IN    PTT（押すと LOW、10k プルアップ）※ 起動設定ピン: PTT を押したまま電源を入れない
 *   D1  (GPIO3)  FWD_ADC   出力検出（容量分割 ＋ 1N60）
 *   D2  (GPIO4)  NOISE_ADC スケルチ用ノイズ（MCP6002 で増幅・倍電圧検波。無信号で高く、信号で下がる）
 *   D3  (GPIO5)  ENC_A     エンコーダ A
 *   D4  (GPIO6)  SDA       Si5351・ADS1115（S メーターの ADC モジュール）
 *   D5  (GPIO7)  SCL       Si5351・ADS1115
 *   D6  (GPIO21) UART_TX   表示器（Nextion）の RX へ
 *   D7  (GPIO20) MUTE      High = 受信音を消す（スケルチ）
 *   D8  (GPIO8)  ENC_B     エンコーダ B
 *   D9  (GPIO9)  ENC_SW    エンコーダの押しボタン ※ 起動設定ピン: 押したまま電源を入れない
 *   D10 (GPIO10) TX_EN     High = 送信（リレー）
 */

#include <Wire.h>
#include <si5351.h>
#include <Preferences.h>

// ============================================================
// ★ 調整値（実機で合わせる）
// ============================================================
#define FIXED_TEXT       "SERRASOID"
#define NOISE_NOSIG_MV   2000   // 無信号（スケルチ用ノイズ最大）のときの D2 の電圧 [mV]
#define NOISE_FULL_MV    150    // 十分強い信号（ノイズがほぼ消えた）のときの D2 の電圧 [mV]
#define FWD_MV_10W       1100   // 10W 出力のときの D1 の電圧 [mV]（計算値の目安）
#define RSSI_MV_S9       1275   // S9（−73dBm）で AD8307 の出力 [mV]（計算値の目安: 入力 約 −33dBm）
#define RSSI_MV_PER_DB   25.0f  // AD8307 の傾き [mV/dB]
#define ADS1115_ADDR     0x48   // ADDR = GND
#define QUIET_RANGE_DB   30     // 無信号（S0）からノイズが消えきるまでの幅 [dB]（ADS1115 がないときの換算）
#define SCAN_STEP        10000  // スキャンの刻み [Hz]
#define SCAN_DWELL_MS    200    // 1 チャンネルを聞く時間（スケルチ用ノイズの検波 0.47µF × 100k が落ち着くまで）
#define SCAN_RESUME_MS   3000   // 信号が消えてから再開するまで
#define SCAN_SQL_DEFAULT 3      // SQL OFF のときにスキャンで使うスケルチ
#define SI5351_XTAL      25000000UL
#define SI5351_CORR      0      // Si5351 の周波数補正（etherkit の set_correction、単位 ppb）
// ============================================================

// ---- ピン ----
#define PTT_IN   D0
#define FWD_ADC  D1
#define NOISE_ADC D2
#define ENC_A    D3
#define LCD_TX   D6
#define MUTE_OUT D7
#define ENC_B    D8
#define ENC_SW   D9
#define TX_EN    D10

// ---- 周波数 ----
#define FREQ_MIN     29000000L
#define FREQ_MAX     29700000L
#define FREQ_CALL    29300000L
#define IF_FREQ      10700000L
#define MULT_NUM     10         // CLK0 = 送信周波数 × 10 / 16
#define MULT_DEN     16

#define RELAY_MS       15       // リレー（G5V-2）が切り替わるのを待つ時間
#define LONG_PRESS_MS  800
#define UI_TIMEOUT_MS  15000
#define SQL_MAX        9

long currentFreq = FREQ_CALL;

// ---- ステップ ----
const long  stepValues[] = {1000, 5000, 10000, 100000};
const char* stepLabels[] = {"1kHz", "5kHz", "10kHz", "100kHz"};
const int   stepCount    = 4;
int stepIndex = 2;

// ---- スケルチ（0 = OFF、1〜9 = 深くなるほど強い信号でないと開かない）----
int sqlLevel = 3;

// ---- 設定モード ----
enum UiMode { UI_NORMAL, UI_MENU, UI_EDIT };
enum MenuId { MENU_STEP, MENU_SQL, MENU_SCAN, MENU_EXIT, MENU_COUNT };
const char* menuItems[MENU_COUNT] = {"STEP", "SQL", "SCAN", "EXIT"};
UiMode        uiMode    = UI_NORMAL;
int           menuIndex = MENU_STEP;
long          editValue = 0;
unsigned long lastUiMs  = 0;

Si5351      si5351;
Preferences prefs;

// ---- エンコーダ ----
volatile int encCount  = 0;
int          lastCount = 0;

// ---- ボタン ----
bool          lastBtnState = HIGH;
unsigned long lastBtnTime  = 0;
unsigned long btnDownTime  = 0;
bool          longHandled  = false;

// ---- 送受信 ----
bool txNow = false;

// ---- スキャン ----
bool          scanOn     = false;
int           scanDir    = 1;      // +1 = 上へ、-1 = 下へ
bool          scanHold   = false;  // 信号で止まっている
unsigned long scanHopMs  = 0;      // 今のチャンネルに来た時刻
unsigned long scanQuietMs = 0;     // 止まっている信号が消えた時刻（0 = まだ信号がある）

// ---- メーター・スケルチ ----
float noiseMv = NOISE_NOSIG_MV;   // ならした値
float fwdMv   = 0;
float sigLevel = 0;               // ノイズの減り方 0〜10（10 = 消えきった）
bool  adsOk    = false;           // ADS1115（S メーター）がある
float rssiMv   = 0;               // AD8307 の出力 [mV]（ならした値）
bool  sqlOpen  = false;
unsigned long lastMeterMs = 0;

// ---- アナログ S メーター（nextion/make_background.py の値と同じにする）----
#define METER_X0     16      // メーター面（picq で描き直す範囲）
#define METER_Y0     112
#define METER_W      305
#define METER_H      181
#define METER_PIV_X  168     // 針の支点（メーター面の下に隠れる）
#define METER_PIV_Y  318
#define METER_R0     50      // 針の根元（支点からの距離）
#define METER_R1     160     // 針の先
#define METER_ANG_L  135.0f  // 左端の角度（右向き 0°、反時計回り）
#define METER_ANG_R  45.0f   // 右端の角度
#define PWR_FULL     15.0f   // 右端の出力 [W]
#define METER_S9_POS 0.6f    // S9 の位置（左端 0〜右端 1）

// S メーター [dB、S9 = 0] → 針の位置 0〜1000（PSN_TRX と同じ目盛り）
int meterPos(float db) {
  float p;
  if (db <= 0) p = (db + 54.0f) / 54.0f * METER_S9_POS;
  else         p = METER_S9_POS + db / 60.0f * (1.0f - METER_S9_POS);
  if (p < 0) p = 0;
  if (p > 1) p = 1;
  return (int)(p * 1000.0f + 0.5f);
}

void updateDisplay();
void saveSettings();

// ---- ISR ----
void IRAM_ATTR encoderISR() {
  static int lastA = HIGH;
  int a = digitalRead(ENC_A);
  int b = digitalRead(ENC_B);
  if (a != lastA) {
    encCount += (b != a) ? 1 : -1;
    lastA = a;
  }
}

// ============================================================
// Si5351
// ============================================================
void setRxClock() {
  si5351.set_freq((uint64_t)(currentFreq - IF_FREQ) * 100ULL, SI5351_CLK1);
}

void setTxClock() {
  // 送信周波数は 1kHz 単位なので、× 10 / 16 は 0.625Hz 単位 → 0.01Hz 単位でちょうど割り切れる
  uint64_t f = (uint64_t)currentFreq * 100ULL * MULT_NUM / MULT_DEN;
  si5351.set_freq(f, SI5351_CLK0);
}

void startRx() {
  si5351.output_enable(SI5351_CLK0, 0);
  setRxClock();
  si5351.output_enable(SI5351_CLK1, 1);
}

void startTx() {
  si5351.output_enable(SI5351_CLK1, 0);
  setTxClock();
  si5351.output_enable(SI5351_CLK0, 1);
}

// ============================================================
// 送受切替
// ============================================================
void stopScan();

void setTx(bool on) {
  if (on == txNow) return;
  if (on) {
    if (scanOn) stopScan();
    if (currentFreq < FREQ_MIN || currentFreq > FREQ_MAX) return;
    digitalWrite(MUTE_OUT, HIGH);          // 切り替えの雑音を出さない
    si5351.output_enable(SI5351_CLK1, 0);
    digitalWrite(TX_EN, HIGH);
    delay(RELAY_MS);
    startTx();
  } else {
    si5351.output_enable(SI5351_CLK0, 0);
    delay(RELAY_MS);
    digitalWrite(TX_EN, LOW);
    delay(RELAY_MS);
    startRx();
  }
  txNow = on;
}

// ============================================================
// 設定モード
// ============================================================
void menuEnter(int id) {
  switch (id) {
    case MENU_STEP: editValue = stepIndex; break;
    case MENU_SQL:  editValue = sqlLevel;  break;
  }
}

void menuTurn(int id, int diff) {
  switch (id) {
    case MENU_STEP:
      editValue = ((editValue + diff) % stepCount + stepCount) % stepCount;
      break;
    case MENU_SQL:
      editValue += diff;
      if (editValue < 0) editValue = 0;
      if (editValue > SQL_MAX) editValue = SQL_MAX;
      break;
  }
}

void sqlText(long v, char* buf, size_t len) {
  if (v == 0) snprintf(buf, len, "SQL OFF");
  else        snprintf(buf, len, "SQL %ld", v);
}

void menuText(int id, long v, char* buf, size_t len) {
  switch (id) {
    case MENU_STEP: snprintf(buf, len, "STEP: %s", stepLabels[v]); break;
    case MENU_SQL:  sqlText(v, buf, len);                          break;
    default:        snprintf(buf, len, "EXIT");                     break;
  }
}

void menuCommit(int id) {
  switch (id) {
    case MENU_STEP: stepIndex = (int)editValue; break;
    case MENU_SQL:  sqlLevel  = (int)editValue; break;
  }
}

// スケルチの深さ（変更中は仮の値で効かせて、聞きながら合わせる）
int activeSql() {
  int sql = (uiMode == UI_EDIT && menuIndex == MENU_SQL) ? (int)editValue : sqlLevel;
  if (scanOn && sql == 0) sql = SCAN_SQL_DEFAULT;
  return sql;
}

// t1 の内容（通常はステップ、設定モード中はメニュー）
void uiLine(char* buf, size_t len) {
  if (uiMode == UI_MENU) {
    snprintf(buf, len, "MENU > %s", menuItems[menuIndex]);
  } else if (uiMode == UI_EDIT) {
    char v[24];
    menuText(menuIndex, editValue, v, sizeof(v));
    snprintf(buf, len, "> %s  [PUSH=OK]", v);
  } else if (scanOn) {
    if (scanHold) snprintf(buf, len, "SCAN: BUSY  PUSH=STOP");
    else          snprintf(buf, len, "SCAN %s  PUSH=STOP", scanDir > 0 ? ">>" : "<<");
  } else {
    snprintf(buf, len, "STEP: %s", stepLabels[stepIndex]);
  }
}

void leaveUi(bool commit) {
  if (commit && uiMode == UI_EDIT) {
    menuCommit(menuIndex);
    saveSettings();
  }
  uiMode = UI_NORMAL;
  updateDisplay();
}

// ============================================================
// 表示器 Nextion NX4832T035（一方向。命令の終わりに 0xFF を 3 つ）
// ============================================================
void nxSend(const char* cmd) {
  Serial1.print(cmd);
  Serial1.write(0xFF);
  Serial1.write(0xFF);
  Serial1.write(0xFF);
}

void nxSetText(const char* component, const char* value) {
  char buf[80];
  snprintf(buf, sizeof(buf), "%s.txt=\"%s\"", component, value);
  nxSend(buf);
}

void nxInit() {
  // 針の描画で送る量が増えるので 115200bps に上げる（表示器が既に 115200bps でも通るよう両方で送る）
  Serial1.begin(9600, SERIAL_8N1, -1, LCD_TX);
  delay(500);
  nxSend("baud=115200");
  Serial1.flush();
  delay(100);
  Serial1.updateBaudRate(115200);
  nxSend("baud=115200");
  delay(50);
  nxSend("page 0");
  nxSetText("t2", FIXED_TEXT);
}

void updateDisplay() {
  char buf[40];
  snprintf(buf, sizeof(buf), "%ld.%03ld MHz", currentFreq / 1000000, (currentFreq % 1000000) / 1000);
  nxSetText("t0", buf);
  uiLine(buf, sizeof(buf));
  nxSetText("t1", buf);
  sqlText(activeSql(), buf, sizeof(buf));
  nxSetText("t5", buf);
}

// 針を描く: メーター面を背景画像で描き直してから、黒い線 2 本（2 ドット幅）。pos = 0〜1000
void drawNeedle(int pos) {
  char buf[48];
  snprintf(buf, sizeof(buf), "picq %d,%d,%d,%d,0", METER_X0, METER_Y0, METER_W, METER_H);
  nxSend(buf);
  float a  = (METER_ANG_L + pos / 1000.0f * (METER_ANG_R - METER_ANG_L)) * PI / 180.0f;
  int   x0 = METER_PIV_X + (int)(METER_R0 * cosf(a));
  int   y0 = METER_PIV_Y - (int)(METER_R0 * sinf(a));
  int   x1 = METER_PIV_X + (int)(METER_R1 * cosf(a));
  int   y1 = METER_PIV_Y - (int)(METER_R1 * sinf(a));
  for (int dx = 0; dx <= 1; dx++) {
    snprintf(buf, sizeof(buf), "line %d,%d,%d,%d,0", x0 + dx, y0, x1 + dx, y1);
    nxSend(buf);
  }
}

// 変わった項目だけ送る
void updateMeter(int pos, const char* text, int mode, bool busy) {   // mode 0 = RX、1 = TX、2 = SCAN
  static int  shownPos = -1;
  static char shownText[12] = "?";
  static int  shownMode = -1, shownBusy = -1;
  if (pos / 4 != shownPos / 4 || shownPos < 0) {   // 0.4% 未満の変化では描き直さない
    drawNeedle(pos);
    shownPos = pos;
  }
  if (strcmp(text, shownText) != 0) {
    nxSetText("t3", text);
    strncpy(shownText, text, sizeof(shownText) - 1);
  }
  if (mode != shownMode) {
    // 送信中は赤（0xF800）、スキャン中は黄（0xFFE0）、受信中は白
    nxSend(mode == 1 ? "t4.pco=63488" : mode == 2 ? "t4.pco=65504" : "t4.pco=65535");
    nxSetText("t4", mode == 1 ? "TX" : mode == 2 ? "SCAN" : "RX");
    shownMode = mode;
  }
  if ((int)busy != shownBusy) {
    nxSend("t6.pco=2016");                          // 緑（0x07E0）
    nxSetText("t6", busy ? "BUSY" : "");
    shownBusy = busy;
  }
}

// ============================================================
// ADS1115（I2C 16 ビット ADC）: A0 を連続変換（±4.096V、128 回/秒）
// ============================================================
bool adsBegin() {
  // 設定レジスタ: MUX = AIN0−GND、PGA = ±4.096V、連続変換、128SPS、コンパレータ不使用
  Wire.beginTransmission(ADS1115_ADDR);
  Wire.write(0x01);
  Wire.write(0x42);
  Wire.write(0x83);
  if (Wire.endTransmission() != 0) return false;
  Wire.beginTransmission(ADS1115_ADDR);
  Wire.write(0x00);                                  // 以後は変換結果レジスタを読む
  return Wire.endTransmission() == 0;
}

// A0 の電圧 [mV]（1LSB = 0.125mV）。読めなければ負の値
float adsReadMv() {
  if (Wire.requestFrom(ADS1115_ADDR, 2) != 2) return -1;
  uint8_t hi = Wire.read();                          // 上位バイトが先（読む順を決めておく）
  uint8_t lo = Wire.read();
  int16_t v = (int16_t)((hi << 8) | lo);
  return v * 0.125f;
}

// ============================================================
// 測定（ADC は analogReadMilliVolts で補正済みの mV）
// ============================================================
// スケルチ用ノイズ → 信号の強さ 0〜10（FM はノイズが減るほど信号が強い）
float sigFromNoise(float mv) {
  float s = (NOISE_NOSIG_MV - mv) / (float)(NOISE_NOSIG_MV - NOISE_FULL_MV) * 10.0f;
  if (s < 0) s = 0;
  if (s > 10) s = 10;
  return s;
}

// スケルチ: SQL n で、SIG が n 以上になったら開く（閉じるのは 0.5 下がったとき）
void updateSquelch() {
  int sql = activeSql();
  if (txNow) { sqlOpen = false; return; }
  if (scanOn && !scanHold) {                         // 探している間は音を出さない
    sqlOpen = false;
    digitalWrite(MUTE_OUT, HIGH);
    return;
  }
  if (sql == 0)                    sqlOpen = true;
  else if (!sqlOpen && sigLevel >= sql)       sqlOpen = true;
  else if (sqlOpen && sigLevel < sql - 0.5f)  sqlOpen = false;
  digitalWrite(MUTE_OUT, sqlOpen ? LOW : HIGH);
}

// S メーター [dB、S9 = 0]。ADS1115 があれば AD8307 の出力から、なければノイズの減り方 0〜10 から
float smeterDb(float sig) {
  if (adsOk) return (rssiMv - RSSI_MV_S9) / RSSI_MV_PER_DB;
  return -54.0f + sig / 10.0f * QUIET_RANGE_DB;
}

void smeterText(float db, char* buf, size_t len) {
  if (db > 5.0f) {
    snprintf(buf, len, "S9+%d", ((int)(db + 5) / 10) * 10);
    return;
  }
  int s = 9 + (int)floorf(db / 6.0f + 0.5f);
  if (s < 0) s = 0;
  if (s > 9) s = 9;
  snprintf(buf, len, "S%d", s);
}

float watts(float mv) {
  float r = mv / FWD_MV_10W;
  return 10.0f * r * r;              // 検波電圧は振幅に比例 → 電力は 2 乗
}

// ============================================================
// スキャン
// ============================================================
void hopTo(long f) {
  if (f > FREQ_MAX) f = FREQ_MIN;
  if (f < FREQ_MIN) f = FREQ_MAX;
  currentFreq = f;
  setRxClock();
  scanHopMs = millis();
}

void startScan() {
  scanOn = true;
  scanDir = 1;
  scanHold = false;
  scanQuietMs = 0;
  currentFreq -= currentFreq % SCAN_STEP;
  hopTo(currentFreq);
  updateDisplay();
}

void stopScan() {
  scanOn = false;
  scanHold = false;
  saveSettings();
  updateDisplay();
}

// 20ms ごとに呼ぶ（スケルチの判定のあと）
void scanTick(unsigned long now) {
  if (!scanOn) return;
  int sql = activeSql();
  if (scanHold) {
    if (sigLevel >= sql - 0.5f) {
      scanQuietMs = 0;                               // まだ信号がある
    } else if (scanQuietMs == 0) {
      scanQuietMs = now;
    } else if (now - scanQuietMs >= SCAN_RESUME_MS) {
      scanHold = false;
      hopTo(currentFreq + scanDir * SCAN_STEP);
      updateDisplay();
    }
    return;
  }
  if (now - scanHopMs < SCAN_DWELL_MS) return;
  if (sigLevel >= sql) {                             // 信号があったので止まる
    scanHold = true;
    scanQuietMs = 0;
    updateDisplay();
  } else {
    hopTo(currentFreq + scanDir * SCAN_STEP);
    updateDisplay();
  }
}

// ============================================================
// NVS
// ============================================================
void saveSettings() {
  prefs.begin("serrasoid", false);
  prefs.putLong("freq", currentFreq);
  prefs.putInt("step", stepIndex);
  prefs.putInt("sql", sqlLevel);
  prefs.end();
}

void loadSettings() {
  prefs.begin("serrasoid", true);
  currentFreq = prefs.getLong("freq", FREQ_CALL);
  stepIndex   = prefs.getInt("step", 2);
  sqlLevel    = prefs.getInt("sql", 3);
  prefs.end();
  if (currentFreq < FREQ_MIN || currentFreq > FREQ_MAX || currentFreq % 1000) currentFreq = FREQ_CALL;
  if (stepIndex < 0 || stepIndex >= stepCount) stepIndex = 2;
  if (sqlLevel < 0 || sqlLevel > SQL_MAX) sqlLevel = 3;
}

// ============================================================
void setup() {
  // 送信を確実に止めてから始める
  pinMode(TX_EN, OUTPUT);
  digitalWrite(TX_EN, LOW);
  pinMode(MUTE_OUT, OUTPUT);
  digitalWrite(MUTE_OUT, HIGH);

  Serial.begin(115200);
  pinMode(PTT_IN, INPUT_PULLUP);
  pinMode(ENC_A,  INPUT_PULLUP);
  pinMode(ENC_B,  INPUT_PULLUP);
  pinMode(ENC_SW, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), encoderISR, CHANGE);
  analogReadResolution(12);
  analogSetPinAttenuation(FWD_ADC, ADC_11db);
  analogSetPinAttenuation(NOISE_ADC, ADC_11db);

  Wire.begin();
  nxInit();

  adsOk = adsBegin();
  if (!adsOk) Serial.println("ADS1115 not found: S meter uses noise quieting");

  if (!si5351.init(SI5351_CRYSTAL_LOAD_8PF, SI5351_XTAL, SI5351_CORR))
    Serial.println("Si5351 not found");
  si5351.drive_strength(SI5351_CLK0, SI5351_DRIVE_8MA);
  si5351.drive_strength(SI5351_CLK1, SI5351_DRIVE_8MA);
  si5351.output_enable(SI5351_CLK2, 0);

  loadSettings();
  startRx();
  updateDisplay();
}

// ============================================================
void loop() {
  unsigned long now = millis();

  // PTT（押すと LOW）。20ms のチャタリング除け
  static bool          pttState = false;
  static unsigned long pttChange = 0;
  bool ptt = (digitalRead(PTT_IN) == LOW);
  if (ptt != pttState) {
    if (now - pttChange >= 20) {
      pttState = ptt;
      setTx(ptt);
    }
  } else {
    pttChange = now;
  }

  // エンコーダ（送信中は周波数を変えない）
  int cnt = encCount;
  if (cnt != lastCount) {
    int diff = cnt - lastCount;
    lastCount = cnt;
    if (uiMode == UI_NORMAL && scanOn) {
      scanDir = diff > 0 ? 1 : -1;
      if (scanHold) {                                // 止まっていたら、すぐ次へ
        scanHold = false;
        hopTo(currentFreq + scanDir * SCAN_STEP);
      }
    } else if (uiMode == UI_NORMAL) {
      if (!txNow) {
        long f = currentFreq + (long)diff * stepValues[stepIndex];
        f -= f % stepValues[stepIndex];            // ステップの刻みにそろえる
        if (f < FREQ_MIN) f = FREQ_MIN;
        if (f > FREQ_MAX) f = FREQ_MAX;
        currentFreq = f;
        setRxClock();
        saveSettings();
      }
    } else if (uiMode == UI_MENU) {
      menuIndex = ((menuIndex + diff) % MENU_COUNT + MENU_COUNT) % MENU_COUNT;
    } else {
      menuTurn(menuIndex, diff);
    }
    lastUiMs = now;
    updateDisplay();
  }

  // ボタン: 押す = 設定モードへ／機能を選ぶ／確定、長押し = 取り消し（通常時は呼出周波数へ）
  bool btn = digitalRead(ENC_SW);
  if (btn == LOW && lastBtnState == HIGH && now - lastBtnTime > 50) {
    btnDownTime = now;
    longHandled = false;
  }
  if (btn == LOW && !longHandled && now - btnDownTime >= LONG_PRESS_MS) {
    longHandled = true;
    if (scanOn) {
      stopScan();
    } else if (uiMode == UI_NORMAL && !txNow) {
      currentFreq = FREQ_CALL;
      setRxClock();
      saveSettings();
    }
    leaveUi(false);
  }
  if (btn == HIGH && lastBtnState == LOW) {
    if (!longHandled && now - btnDownTime > 50) {
      if (scanOn) {
        stopScan();
      } else if (uiMode == UI_NORMAL) {
        uiMode = UI_MENU;
        menuIndex = MENU_STEP;
        updateDisplay();
      } else if (uiMode == UI_MENU) {
        if (menuIndex == MENU_EXIT) {
          leaveUi(false);
        } else if (menuIndex == MENU_SCAN) {
          uiMode = UI_NORMAL;
          startScan();
        } else {
          menuEnter(menuIndex);
          uiMode = UI_EDIT;
          updateDisplay();
        }
      } else {
        leaveUi(true);
      }
      lastUiMs = now;
    }
    lastBtnTime = now;
  }
  lastBtnState = btn;

  if (uiMode != UI_NORMAL && now - lastUiMs >= UI_TIMEOUT_MS) leaveUi(false);

  // 測定・スケルチ（20ms ごと）、表示（100ms ごと）
  static unsigned long lastAdcMs = 0;
  if (now - lastAdcMs >= 20) {
    lastAdcMs = now;
    if (txNow) {
      float v = analogReadMilliVolts(FWD_ADC);
      fwdMv += (v - fwdMv) * (v > fwdMv ? 0.6f : 0.15f);   // すぐ上がり、ゆっくり下がる
    } else {
      float v = analogReadMilliVolts(NOISE_ADC);
      noiseMv += (v - noiseMv) * 0.3f;
      sigLevel = sigFromNoise(noiseMv);
      if (adsOk) {
        float r = adsReadMv();
        if (r >= 0) rssiMv += (r - rssiMv) * (r > rssiMv ? 0.7f : 0.2f);   // すぐ上がり、ゆっくり下がる
      }
      fwdMv = 0;
    }
    updateSquelch();
    scanTick(now);
  }

  if (now - lastMeterMs >= 100) {
    lastMeterMs = now;
    char text[12];
    int  pos;
    if (txNow) {
      float w = watts(fwdMv);
      snprintf(text, sizeof(text), "%.1fW", w);
      float p = sqrtf(w / PWR_FULL);               // 内側の目盛りは √W の位置
      pos = (int)((p > 1 ? 1 : p) * 1000.0f + 0.5f);
    } else {
      float db = smeterDb(sigLevel);
      smeterText(db, text, sizeof(text));
      pos = meterPos(db);
    }
    updateMeter(pos, text, txNow ? 1 : scanOn ? 2 : 0, sqlOpen);
    Serial.printf("%s rssi %.0f mV  noise %.0f mV  sig %.1f  fwd %.0f mV  sql %d %s\n", txNow ? "TX" : scanOn ? "SCAN" : "RX",
                  rssiMv, noiseMv, sigLevel, fwdMv, activeSql(), sqlOpen ? "open" : "closed");
  }
}
