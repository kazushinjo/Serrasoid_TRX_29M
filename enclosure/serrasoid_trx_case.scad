// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2026 真城和一 (JA6FUF/JH1XHX)
// ============================================================
// Serrasoid TRX 29M  ケース（筐体）  OpenSCAD パラメトリックモデル
//   PSN_TRX_XIAO_ESP32C3 のケース（enclosure/psn_trx_case.scad）を元にしている
//   基板: kicad/Serrasoid_TRX.kicad_pcb  170 x 150 mm, M3 取付穴 4 か所（角から 4 mm）
//   構成: ベース（底板＋左右側板）／ふた／前面パネル／後面パネル（溝に差し込み）／LCD ベゼル
//   操作部（LCD・TUNE・VOL・POWER・MIC・内蔵スピーカー・外部 SP ジャック）はふたの上面、前面は機種名、
//   後面は DC・ヒューズ・ANT と、終段 RD16HHF1 の放熱器（ケースの内側に置き、フィンを後面の窓から外へ出す）
//
//   表示・出力する部品は mode（数字）で選択（コマンドライン: -D mode=1 等）
//     0: 組立図（ふたを浮かせて表示）      ← 確認用
//     1: ベース（底板＋左右側板）          ← 3D 印刷用（そのままの向き）
//     2: ふた                            ← 3D 印刷用（外面を上）
//     3: 前面パネル（ボス一体）            ← 3D 印刷用（上端を下にして立てる）
//     4: 後面パネル（ボス一体）            ← 3D 印刷用（同上）
//     5: 組立図（ふたを閉じた状態）         ← 確認用
//     6: ふたなし内部                      ← 確認用
//     7: 前面パネル穴あけ図（2D、DXF/SVG 出力用）
//     8: 後面パネル穴あけ図（2D、DXF/SVG 出力用）
//     9: LCD ベゼル（ふた上面に取付）       ← 3D 印刷用（表を下、ボスが上）
//   3D 印刷用（1〜4, 9）は Z=0 のベッド面上、X/Y が正の範囲に置いてある。
//
//   座標: X = 左→右（前から見て）、Y = 前→後（前面 Y=0）、Z = 下→上
//   ねじ: 基板固定 M3x6（4 本）、ふた固定 M3x10（8 本。うち 4 本は前後パネル一体のボス）、
//         前後パネル→底板 M3x10 皿（4 本）、LCD→ベゼル M3x6（4 本）、ベゼル→ふた M3x8（4 本、ふた裏から）、
//         スピーカー→ふた M3x8 皿＋ナット（4 本、ふたの上から）、
//         RD16HHF1→放熱器 M3x8＋ナット（1 本、放熱器のベースに φ3.2 の穴）。ボス・スタンドオフには M3 インサートナット（下穴 φ5.0）。
//   ※ LCD・コネクタ類・放熱器の寸法は代表値。実物を実測して下の値を修正してから出力すること。
// ============================================================

mode = 0;   // ← ここを 0〜9 に変えて F5/F6（上の一覧参照）
$fn = 64;

// ---------------- 外形 ----------------
W  = 200;      // 幅（220mm 角ベッドで印刷可）
D  = 175;      // 奥行き
H  = 50;       // 高さ（ふた込み）。ふた裏の電源スイッチ（本体 20mm）が基板の部品（高さ 11mm）に当たらない高さ
wall   = 3.0;  // 側板厚
floor_t = 3.0; // 底板厚
lid_t  = 3.0;  // ふた厚
panel_t = 3.0; // 前後パネル厚
groove_d = 1.5;
groove_w = panel_t + 0.4;
overhang = 2.0;
fit = 0.4;
panel_inset = overhang - fit / 2;
lid_under = H - lid_t;                                  // ふた裏面の Z
y_front_in = panel_inset + fit / 2 + panel_t;           // 前面パネル内面の Y
y_rear_in  = D - panel_inset - fit / 2 - panel_t;       // 後面パネル内面の Y

// ---------------- 終段の放熱器（ケースの内側、フィンを後面の窓から外へ） ----------------
// 押し出しアルミ放熱器: ベース面に RD16HHF1 のタブを M3 で留める。熱抵抗 5〜8℃/W（10W 送信で約 8W の発熱）
hs_w    = 50;    // 幅（X）
hs_h    = 30;    // 高さ（Z）。ふた裏と基板の間に収まる値
hs_base = 4;     // ベース厚（ベース面 = 基板側）
hs_fin  = 18;    // ベースから先のフィンの長さ（後面パネル 3mm を通って外へ約 15mm 出る）
// ベースの後ろ面を後面パネルの内面に合わせ、フィンが窓を通る
hs_y0 = y_rear_in - hs_base;   // ベース面（RD16HHF1 のタブが当たる面）の Y

// ---------------- 基板 ----------------
pcb_u = 170.0;  // 基板 横（KiCad X）
pcb_v = 150.0;  // 基板 縦（KiCad Y）。2026-10-29 Ver 1.2 で 130 → 150（逓倍の段間同調・PLL・S メーターを足した）。KiCad の上辺（v=0: DC 入力・RD16HHF1・ANT）が後面を向く
pcb_t = 1.6;
standoff_h = 5;
standoff_od = 9;
standoff_hole = 5.0;
part_h = 11;                   // 基板上の一般の部品の高さ（縦置き抵抗・電解・IC ソケット）
q6_uv = [120, 4.5];            // RD16HHF1（Q13）のピン 1 の位置（基板座標）
q6_tab_inset = 1.1;            // 基板の上辺からタブの裏面までの距離（TO-220 縦置き、コートヤードより）
q6_hole_h = 16;                // 基板上面から RD16HHF1 の取付穴の中心まで ※要実測
bx = (W - pcb_u) / 2;                         // 基板の X 位置（左端）
by_rear = hs_y0 + q6_tab_inset;               // 基板の上辺（後ろの端）の Y。タブの裏面が放熱器のベース面に当たる
by = by_rear - pcb_v;                         // 基板の前端の Y
bz = floor_t + standoff_h;                    // 基板下面の Z
pcb_top = bz + pcb_t;
// 基板座標(u: KiCad X, v: KiCad Y、原点 = 基板左上) → ケース座標
function bp(u, v) = [bx + u, by_rear - v];
mount_uv = [[4, 4], [pcb_u - 4, 4], [4, pcb_v - 4], [pcb_u - 4, pcb_v - 4]];
hs_x = bp(q6_uv[0] + 2.54, 0)[0];             // 放熱器の中心 X（RD16HHF1 のタブの中心）
hs_z0 = pcb_top + 0.5;                        // 放熱器の下端（ベースが基板の端に 1.1mm かかるので基板より上に）
q6_hole_z = pcb_top + q6_hole_h;
assert(hs_z0 + hs_h + 1 <= lid_under, "放熱器がふたに当たる");
assert(q6_hole_z > hs_z0 + 4 && q6_hole_z < hs_z0 + hs_h - 4, "RD16HHF1 の取付穴が放熱器の範囲に入らない");
assert(by >= y_front_in + 5, "基板が前面パネルに近すぎる");

// ---------------- パネル ----------------
inner_w = W - 2 * wall;
panel_w = inner_w + 2 * groove_d - fit;
panel_z0 = floor_t - groove_d + fit / 2;
panel_h = H - lid_t - panel_z0 - fit / 2;
panel_x0 = wall - groove_d + fit / 2;
function pz(z) = panel_z0 + z;   // パネル座標 z → ケース Z
function zp(z) = z - panel_z0;   // ケース Z → パネル座標 z

// ---------------- 基板上の背の高い部品（基板座標 u, v = 中心、幅、奥行き、高さ。kicad/Serrasoid_TRX.kicad_pcb より） ----------------
tall = [
    [107.3, 17.7, 20.6, 20.1, 25,   "dimgray",   "HS1 放熱器（RD06HHF1）"],
    [122.5,  3.5, 10.6,  5.0, 20,   "black",     "Q13 RD16HHF1"],
    [107.3, 30.2, 10.6,  5.0, 20,   "black",     "Q12 RD06HHF1"],
    [ 26.4, 31.1,  5.0, 10.6, 20,   "black",     "U4 L7808"],
    [ 19.4, 34.3,  5.0, 10.6, 20,   "black",     "U6 L7805"],
    [ 35.3, 33.6,  9.1, 12.2, 10.5, "orange",    "U5 R-78E"],
    [155.8, 24.9, 10.7, 20.9, 10.5, "white",     "K1 リレー"],
    [125.1, 17.8, 12.2, 19.3, 10,   "tan",       "T1 トランス"],
    [ 35.6, 21.4,  8.6,  8.6, 13,   "steelblue", "C2 470µF"],
    [ 91.4,  7.1,  8.6,  8.6, 13,   "steelblue", "C112 220µF"],
    [ 57.1, 133.4, 21.6, 18.1, 15,  "royalblue", "U15 XIAO（ソケット込み）"],
    [ 55.2, 113.8, 29.2, 18.9, 13,  "purple",    "U13 ADS1115 モジュール（ソケット込み）"],
    [149.2, 95.2,  5.8, 12.0, 13.5, "silver",    "FL1 10M15A"],
    [140.4, 80.0, 12.0,  5.8, 13.5, "silver",    "X1 10.245MHz"],
    [ 87.0, 85.7, 14.1, 10.7, 14,   "gold",      "L6 VCO（T50-6 縦置き）"],
];
tall_max = max([for (t = tall) t[4]]);
// ある範囲（ケース X/Y の矩形）の下の部品の最も高い上端の Z
function parts_top(x0, x1, y0, y1) = max(concat([pcb_top + part_h],
    [for (t = tall) let(c = bp(t[0], t[1])) if (c[0] + t[2] / 2 > x0 && c[0] - t[2] / 2 < x1 && c[1] + t[3] / 2 > y0 && c[1] - t[3] / 2 < y1) pcb_top + t[4]]));
// 放熱器のベースが基板の端にかかる 1.1mm の範囲には、RD16HHF1 以外の部品がない
for (t = tall) if (t[6] != "Q13 RD16HHF1")
    assert(t[1] - t[3] / 2 > q6_tab_inset || abs(bp(t[0], 0)[0] - hs_x) > hs_w / 2 + t[2] / 2, str(t[6], " が放熱器にかかる"));

// ---------------- 上面部品（ふた上面、ケース X/Y 座標） ----------------
// LCD: Nextion NX4832T035（3.5インチ 480×320、PSN_TRX と同じ）。寸法は PSN_TRX のケースと同じ推定値 ※要実測
lcd_mod   = [100.5, 54.94];
lcd_win   = [74.5, 50.0];
lcd_win_off = [0, 0];
lcd_holes = [94.5, 48.94];
lcd_depth = 10;
bezel      = [125, 62];
bezel_t    = 6.0;
bezel_r    = 4;
lcd_cut    = lcd_mod + [2, 2.06];
lcd_boss_h  = 4.0;
lcd_boss_od = 6.5;
lcd_insert  = 5.0;
lcd_insert_depth = lcd_boss_h + bezel_t - 1.0;
bezel_screw = [bezel[0] / 2 - 6, 20];
bezel_insert_depth = bezel_t - 1.0;
bezel_hole = 3.4;
lcd_c = [8 + bezel[0] / 2, 40 + bezel[1] / 2];   // ベゼル左端 X=8、前端 Y=40（手前に MIC・EXT SP、奥に内蔵スピーカー）
// 右の列（X = 170）: 手前から TUNE・VOL・POWER
col_x = 170;
enc_c   = [col_x, 40];  enc_hole = 7.2;  enc_knob = 32;  enc_body = 14; enc_depth = 12;   // ロータリーエンコーダ（J5）
afv_c   = [col_x, 82];  afv_hole = 7.2;  afv_knob = 20;  afv_body = 17; afv_depth = 10;   // AF ボリューム（J4、10kΩ A）
psw_c   = [col_x, 115]; psw_hole = 13.0; psw_body = 16; psw_depth = 20;                    // 電源スイッチ
led_c   = [col_x + 18, psw_c[1]]; led_hole = 3.1;                                         // 電源 LED
// 手前（基板より前、ふた裏が空いている所）: MIC・SP
mic_c   = [50, 20];  mic_hole = 16.2; mic_flange = 20; mic_body = 20; mic_depth = 25;    // 4P 丸型マイクコネクタ（J7: MIC・PTT・GND）
sp_c    = [85, 20];  sp_hole = 6.2;   sp_plug = 8;     sp_body = 12;  sp_depth = 15;     // 3.5mm 外部スピーカージャック（秋月 117359 MJ-352W-C、M6 P0.5 ねじ長 3.5mm、スイッチ付き。J6 からブレーク接点経由で内蔵スピーカーへ: 挿すと内蔵が切れる）
tx_c    = [mic_c[0] - 30, mic_c[1]]; tx_hole = 3.0; tx_depth = 6;   // TX ランプ（J9）: PSN_TRX と同じく MIC の左 30mm、MIC の穴と同じ高さ
sp_thin = 15; sp_thin_t = 1.8;   // SP ジャック穴を中心に 15x15mm を板厚 1.8mm に（ふた裏から座ぐり。ジャックのねじ長さ対策、PSN_TRX と同じ）
// 内蔵スピーカー（秋月 116024 DXYD50N-22Z-8A-F、5cm 角 8Ω 0.5W。PSN_TRX と同じ）: ふた裏に密着させ、四隅の穴を M3 皿ねじ＋ナットで留める
spk_c = [80, 130];       // 中心。PSN_TRX と同じく LCD の奥、通風スロットの左。後ろは後面の BNC、下は送信 RF の入口（背の低い部品）
spk_size = 50;           // 外形 50 × 50
spk_pitch = 40;          // 取付穴 φ4 のピッチ
spk_depth = 17.5;        // 枠の前面からマグネット後端まで
spk_magnet = 22;         // マグネット直径
spk_grille = 35;         // 放音穴を並べる範囲の直径
spk_hole = 2.5; spk_hole_pitch = 4.5;   // 放音穴（六角配置）
module spk_screw_pos() { for (sx = [-1, 1], sy = [-1, 1]) translate([spk_c[0] + sx * spk_pitch / 2, spk_c[1] + sy * spk_pitch / 2]) children(); }

knob_gap = 5;
assert(norm(afv_c - enc_c) >= enc_knob / 2 + afv_knob / 2 + knob_gap, "VOL つまみと TUNE つまみの隙間が 5mm 未満");
assert(norm(psw_c - afv_c) >= afv_knob / 2 + psw_hole / 2 + knob_gap, "電源スイッチと VOL つまみの隙間が 5mm 未満");
assert(enc_c[1] + enc_knob / 2 + 4 + 2 <= afv_c[1] - afv_knob / 2 - 1, "TUNE の文字が VOL つまみにかかる");
assert(afv_c[1] + afv_knob / 2 + 4 + 2 <= psw_c[1] - psw_hole / 2 - 1, "VOL の文字が電源スイッチにかかる");
assert(lcd_c[0] + bezel[0] / 2 + knob_gap <= enc_c[0] - enc_knob / 2, "ベゼルと TUNE つまみの隙間が 5mm 未満");
assert(mic_c[1] + mic_flange / 2 + 4 + 2 <= lcd_c[1] - bezel[1] / 2, "MIC の文字がベゼルにかかる");
assert(sp_c[0] - sp_plug / 2 >= mic_c[0] + mic_flange / 2 + 10, "MIC と SP の隙間が 10mm 未満");
assert(dc_thin > dc_hole + 1 && dc_thin_t < panel_t, "DC ジャックの薄肉部の寸法が不正");
assert(sp_thin > sp_hole + 1 && sp_thin_t < lid_t, "SP の薄肉部の寸法が不正");
assert(sp_c[0] - sp_thin / 2 >= mic_c[0] + mic_hole / 2 + 2, "SP の薄肉部が MIC の穴に近すぎる");
assert(sp_c[1] - sp_thin / 2 >= y_front_in + 1, "SP の薄肉部が前面パネルの上端にかかる");
// 内蔵スピーカー
function sq_dist(c, p, half) = norm([max(abs(p[0] - c[0]) - half, 0), max(abs(p[1] - c[1]) - half, 0)]);   // 正方形と点の距離
assert(spk_c[1] - spk_size / 2 >= lcd_c[1] + lcd_cut[1] / 2 + 2, "スピーカーが LCD にかかる");
assert(spk_c[1] - spk_pitch / 2 - 6.6 / 2 >= lcd_c[1] + bezel[1] / 2 + 2, "スピーカー取付ねじの頭がベゼルに近すぎる");
assert(spk_c[1] + spk_size / 2 + 1 <= y_rear_in, "スピーカーが後面パネルにかかる");
assert(spk_c[0] - spk_size / 2 >= wall + 1, "スピーカーが左の側板にかかる");
assert(spk_c[0] + spk_size / 2 + 3 <= lid_vent_x[0], "スピーカーが通風スロットに近すぎる");
for (b = boss_pos) assert(sq_dist(spk_c, b, spk_size / 2) >= ear_d / 2 + 1, "スピーカーがふた固定ボスにかかる");
// 後面の部品の本体（後面パネル内面から奥へ）: 平面で 1mm 以上離すか、本体の上端がマグネットの下端より 1mm 以上下
for (c = [[dc_c, dc_body, dc_depth, "DC"], [fuse_c, fuse_body, fuse_depth, "FUSE"], [bnc_c, bnc_body, bnc_depth, "BNC"]])
    let(dx = max(abs(c[0][0] - spk_c[0]) - spk_size / 2 - c[1] / 2, 0), dy = max((y_rear_in - c[2]) - (spk_c[1] + spk_size / 2), 0))
    assert(norm([dx, dy]) >= 1 || c[0][1] + c[1] / 2 + 1 <= lid_under - spk_depth, str("スピーカーが後面の ", c[3], " の本体にかかる"));
assert(lid_under - spk_depth >= parts_top(spk_c[0] - spk_size / 2, spk_c[0] + spk_size / 2, spk_c[1] - spk_size / 2, spk_c[1] + spk_size / 2) + 1, "スピーカーが基板の部品に当たる");
assert(tx_c[0] - tx_hole / 2 - 3 >= wall && led_c[0] + led_hole / 2 + 3 <= W - 3, "LED がふたの縁に近すぎる");
assert(tx_c[0] + tx_hole / 2 + 3 <= mic_c[0] - mic_flange / 2, "TX LED の穴が MIC に近すぎる");
// ふた裏の本体が基板の部品に当たらない（基板の上にあるもの）
for (c = [[enc_c, enc_body, enc_depth, "TUNE"], [afv_c, afv_body, afv_depth, "VOL"], [psw_c, psw_body, psw_depth, "POWER"],
          [mic_c, mic_body, mic_depth, "MIC"], [sp_c, sp_body, sp_depth, "SP"], [tx_c, 4, tx_depth, "TX"], [led_c, 4, tx_depth, "ON"]])
    let(on_pcb = c[0][1] + c[1] / 2 > by && c[0][0] + c[1] / 2 > bx && c[0][0] - c[1] / 2 < bx + pcb_u)
    assert(!on_pcb || lid_under - c[2] >= parts_top(c[0][0] - c[1] / 2, c[0][0] + c[1] / 2, c[0][1] - c[1] / 2, c[0][1] + c[1] / 2) + 1,
           str(c[3], " のふた裏の本体が基板の部品に当たる"));
for (c = [[mic_c, mic_body], [sp_c, sp_body]])
    assert(c[0][1] - c[1] / 2 >= y_front_in + 1 && (c[0][1] + c[1] / 2 <= by || true), "MIC・SP の本体が前面パネルにかかる");
assert(lid_under - lcd_depth >= parts_top(lcd_c[0] - lcd_mod[0] / 2, lcd_c[0] + lcd_mod[0] / 2, lcd_c[1] - lcd_mod[1] / 2, lcd_c[1] + lcd_mod[1] / 2) + 1,
       "LCD 裏のコネクタが基板の部品に当たる");

// ---------------- 後面部品（ケース X、Z は絶対値） ----------------
rear_z = 30;   // DC・ヒューズ・BNC の中心の高さ（ヒューズの本体を電源ブロックの部品の上に通す）
dc_c   = [27, rear_z]; dc_hole = 8.0;  dc_flange = 14; dc_body = 12; dc_depth = 15;      // DC ジャック（2.1/2.5mm、センタープラス）
dc_thin = 15; dc_thin_t = 1.8;   // DC ジャック穴を中心に 15x15mm を板厚 1.8mm に（パネル内側から座ぐり。ジャックのねじ長さ対策）
fuse_c = [176, rear_z]; fuse_hole = 12.5; fuse_flange = 18; fuse_body = 16; fuse_depth = 35;   // 5x20 パネル取付ヒューズホルダ
bnc_c  = [92, rear_z]; bnc_hole = 9.6; bnc_flange = 14; bnc_body = 12; bnc_depth = 12;     // BNC（アンテナ、J8 へ同軸）
hs_win = [hs_x - hs_w / 2 - 0.5, hs_x + hs_w / 2 + 0.5, hs_z0 - 0.2, hs_z0 + hs_h + 0.5];   // 放熱器の窓 [X0, X1, Z0, Z1]（下辺で放熱器を受ける）
for (c = [[dc_c, dc_flange], [fuse_c, fuse_flange], [bnc_c, bnc_flange]]) {
    assert(c[0][1] - c[1] / 2 >= floor_t + 0.5, "後面部品のつばが底板にかかる");
    assert(c[0][1] + c[1] / 2 <= lid_under - 0.5, "後面部品のつばがふたにかかる");
    assert(c[0][0] + c[1] / 2 + 3 <= hs_win[0] || c[0][0] - c[1] / 2 - 3 >= hs_win[1], "後面部品が放熱器の窓に近すぎる");
}
assert(abs(dc_c[0] - fuse_c[0]) >= dc_flange / 2 + fuse_flange / 2 + 4 && abs(fuse_c[0] - bnc_c[0]) >= fuse_flange / 2 + bnc_flange / 2 + 4, "後面部品の間が狭い");
// 後面部品のパネル内側の本体が基板の部品に当たらない
for (c = [[dc_c, dc_body, dc_depth, "DC"], [fuse_c, fuse_body, fuse_depth, "FUSE"], [bnc_c, bnc_body, bnc_depth, "BNC"]])
    assert(c[0][1] - c[1] / 2 >= parts_top(c[0][0] - c[1] / 2, c[0][0] + c[1] / 2, y_rear_in - c[2], y_rear_in) + 1, str(c[3], " の本体が基板の部品に当たる"));

// ---------------- ふた固定・パネル固定 ----------------
ear_y = [32, D - 32];
ear_d = 10; ear_h = 10; ear_hole = 5.0;
ear_x = [wall + ear_d / 2 - 1, W - wall - ear_d / 2 + 1];
// 前後パネル一体ボス: 基板と放熱器をよけて、左右の側板の近く（X = 9 と W-9）に 2 本ずつ
panel_boss_x = [wall + ear_d / 2 + 1, W - wall - ear_d / 2 - 1];
panel_boss_y = [panel_inset + groove_w + ear_d / 2, D - panel_inset - groove_w - ear_d / 2];
ear_pos = [for (x = ear_x, y = ear_y) [x, y]];
panel_boss_pos = [for (x = panel_boss_x, y = panel_boss_y) [x, y]];
boss_pos = concat(ear_pos, panel_boss_pos);
panel_boss_z = [floor_t + fit / 2, H - lid_t - fit / 2];
panel_boss_bot_insert = 8;
lid_screw = 3.4;
for (b = boss_pos) {
    assert(b[0] + ear_d / 2 + 1 <= bx || b[0] - ear_d / 2 - 1 >= bx + pcb_u, "ボスが基板にかかる");
    for (c = [[enc_c, enc_body], [afv_c, afv_body], [psw_c, psw_body], [mic_c, mic_body], [sp_c, sp_body]])
        assert(norm(c[0] - b) >= c[1] / 2 + ear_d / 2 + 1, "上面部品のふた裏の本体がボスにかかる");
    for (p = [tx_c, led_c]) assert(norm(p - b) >= 3.3 + 5, "LED の穴がふた固定ねじ頭に近すぎる");
    assert(abs(b[0] - lcd_c[0]) >= bezel[0] / 2 + 3.3 + 2 || abs(b[1] - lcd_c[1]) >= bezel[1] / 2 + 3.3 + 2, "ベゼルがふた固定ねじ頭にかかる");
}
for (c = [[dc_c, dc_body], [fuse_c, fuse_body], [bnc_c, bnc_body]], x = panel_boss_x)
    assert(abs(c[0][0] - x) >= c[1] / 2 + ear_d / 2 + 1, "後面部品の本体が後面パネル固定ボスにかかる");
for (x = panel_boss_x) assert(abs(x - hs_x) >= hs_w / 2 + ear_d / 2 + 1, "放熱器が後面パネル固定ボスにかかる");

// ふたの通風スロット（放熱器・RD06HHF1・T1 の上、スピーカーの右）
lid_vent_x = [spk_c[0] + spk_size / 2 + 3, bp(150, 0)[0]];
lid_vent_y0 = psw_c[1] + psw_hole / 2 + 12; lid_vent_n = 6; lid_vent_pitch = 5;
assert(lid_vent_y0 + (lid_vent_n - 1) * lid_vent_pitch + 2.5 + 3 <= y_rear_in, "ふたの通風スロットが後面パネルにかかる");
assert(lid_vent_x[1] + 3 <= col_x - psw_body / 2 || lid_vent_y0 >= psw_c[1] + psw_hole / 2 + 8, "ふたの通風スロットが電源スイッチにかかる");

// ---------------- 文字 ----------------
font = "Liberation Sans:style=Bold";
emboss = 1.2;

// ============================================================
module rounded_box(size, r = 2) {
    hull() for (x = [r, size[0] - r], y = [r, size[1] - r])
        translate([x, y, 0]) cylinder(r = r, h = size[2]);
}
module groove_cut(y0) {
    translate([wall - groove_d, y0, floor_t - groove_d]) cube([inner_w + 2 * groove_d, groove_w, H]);
}

// ---------------- ベース ----------------
module base() {
    hb = H - lid_t;
    difference() {
        union() {
            rounded_box([W, D, floor_t], 3);
            for (x = [0, W - wall]) translate([x, 0, 0]) cube([wall, D, hb]);
            for (m = mount_uv) let(p = bp(m[0], m[1]))
                translate([p[0], p[1], 0]) cylinder(d = standoff_od, h = bz);
            for (b = ear_pos)
                translate([b[0], b[1], 0]) cylinder(d = ear_d, h = hb);
        }
        groove_cut(panel_inset);
        groove_cut(D - panel_inset - groove_w);
        for (m = mount_uv) let(p = bp(m[0], m[1]))
            translate([p[0], p[1], 1]) cylinder(d = standoff_hole, h = bz);
        for (b = ear_pos)
            translate([b[0], b[1], hb - ear_h - 1]) cylinder(d = ear_hole, h = ear_h + 2);
        for (b = panel_boss_pos) translate([b[0], b[1], -1]) {
            cylinder(d = lid_screw, h = floor_t + 2);
            translate([0, 0, 1 - 0.01]) cylinder(d1 = 6.6, d2 = lid_screw, h = 1.81);
        }
        // 底面通風スロット（RD06HHF1・HS1 とレギュレータの下）
        for (c = [[107.3, 22], [23, 33]]) for (i = [-2:2]) let(p = bp(c[0], c[1] + i * 4.5))
            translate([p[0] - 14, p[1] - 1, -1]) cube([28, 2.2, floor_t + 2]);
        for (x = [14, W - 14], y = [14, D - 14]) translate([x, y, -0.01]) cylinder(d = 12.5, h = 1);
    }
}

// ---------------- ふた ----------------
module lid() {
    translate([0, 0, H - 0.01]) linear_extrude(emboss + 0.01) top_labels_2d();
    difference() {
        translate([0, 0, H - lid_t]) rounded_box([W, D, lid_t], 3);
        translate([0, 0, H - lid_t - 1]) linear_extrude(lid_t + 2) top_holes_2d();
        for (b = boss_pos) translate([b[0], b[1], H - lid_t - 1]) {
            cylinder(d = lid_screw, h = lid_t + 2);
            translate([0, 0, lid_t + 1 - 1.8]) cylinder(d1 = lid_screw, d2 = 6.6, h = 1.81);
        }
        for (i = [0:lid_vent_n - 1])
            translate([lid_vent_x[0], lid_vent_y0 + i * lid_vent_pitch, H - lid_t - 1]) cube([lid_vent_x[1] - lid_vent_x[0], 2.5, lid_t + 2]);
        // SP ジャック周りの薄肉部（ふた裏から掘り、上面は平らのまま）
        translate([sp_c[0], sp_c[1], H - lid_t - 1]) linear_extrude(1 + lid_t - sp_thin_t) square(sp_thin, center = true);
        // スピーカーの放音穴と取付穴（M3 皿ねじ、ふた上面から皿もみ）
        translate([0, 0, H - lid_t - 1]) linear_extrude(lid_t + 2) spk_grille_2d();
        spk_screw_pos() translate([0, 0, H - lid_t - 1]) {
            cylinder(d = lid_screw, h = lid_t + 2);
            translate([0, 0, lid_t + 1 - 1.8]) cylinder(d1 = lid_screw, d2 = 6.6, h = 1.81);
        }
    }
}
module spk_grille_2d() {
    n = ceil(spk_grille / spk_hole_pitch);
    for (i = [-n:n], j = [-n:n]) let(p = [i * spk_hole_pitch + (j % 2) * spk_hole_pitch / 2, j * spk_hole_pitch * sqrt(3) / 2])
        if (norm(p) <= spk_grille / 2 - spk_hole / 2) translate(spk_c + p) circle(d = spk_hole, $fn = 16);
}
module top_holes_2d() {
    translate(lcd_c) square(lcd_cut, center = true);
    bezel_screw_pos() circle(d = bezel_hole);
    translate(enc_c) circle(d = enc_hole);
    translate(afv_c) circle(d = afv_hole);
    translate(psw_c) circle(d = psw_hole);
    translate(led_c) circle(d = led_hole);
    translate(tx_c) circle(d = tx_hole);
    translate(mic_c) circle(d = mic_hole);
    translate(sp_c) circle(d = sp_hole);
}
module top_labels_2d() {
    module t(s, p, sz) translate(p) text(s, size = sz, font = font, halign = "center", valign = "center");
    t("TUNE", [enc_c[0], enc_c[1] + enc_knob / 2 + 4], 3.2);
    t("VOL", [afv_c[0], afv_c[1] + afv_knob / 2 + 4], 3.2);
    t("POWER", [psw_c[0], psw_c[1] + psw_hole / 2 + 4.5], 3.2);
    t("ON", [led_c[0], psw_c[1] + psw_hole / 2 + 4.5], 2.6);
    t("TX", [tx_c[0], mic_c[1] + mic_flange / 2 + 4], 3.2);   // MIC・EXT SP と高さをそろえる
    t("MIC", [mic_c[0], mic_c[1] + mic_flange / 2 + 4], 3.2);
    t("EXT SP", [sp_c[0], mic_c[1] + mic_flange / 2 + 4], 3.2);
}

// ---------------- 前面パネル ----------------
module front_labels_2d() {
    translate([panel_w / 2, panel_h / 2 + 4]) text("SERRASOID TRX", size = 8, font = font, halign = "center", valign = "center");
    translate([panel_w / 2, panel_h / 2 - 8]) text("29MHz FM 10W", size = 4.5, font = font, halign = "center", valign = "center");
}
module front_2d() square([panel_w, panel_h]);
module lcd_boss_pos() { for (sx = [-1, 1], sz = [-1, 1]) translate(lcd_c + [sx * lcd_holes[0] / 2, sz * lcd_holes[1] / 2]) children(); }
module bezel_screw_pos() { for (sx = [-1, 1], sz = [-1, 1]) translate(lcd_c + [sx * bezel_screw[0], sz * bezel_screw[1]]) children(); }
module front_print() {
    linear_extrude(panel_t) front_2d();
    translate([0, 0, panel_t - 0.01]) linear_extrude(emboss + 0.01) front_labels_2d();
}
module bezel_body() {
    difference() {
        union() {
            translate(lcd_c - bezel / 2) linear_extrude(bezel_t) offset(r = bezel_r) offset(delta = -bezel_r) square(bezel);
            lcd_boss_pos() translate([0, 0, -lcd_boss_h]) cylinder(d = lcd_boss_od, h = lcd_boss_h + 0.01);
        }
        translate(concat(lcd_c + lcd_win_off, [-0.01])) {
            linear_extrude(bezel_t + 0.02) square(lcd_win, center = true);
            translate([0, 0, bezel_t - 1.5]) linear_extrude(1.52, scale = [(lcd_win[0] + 3) / lcd_win[0], (lcd_win[1] + 3) / lcd_win[1]]) square(lcd_win, center = true);
        }
        lcd_boss_pos() translate([0, 0, -lcd_boss_h - 0.01]) cylinder(d = lcd_insert, h = lcd_insert_depth + 0.01);
        bezel_screw_pos() translate([0, 0, -0.01]) cylinder(d = lcd_insert, h = bezel_insert_depth + 0.01);
    }
}
module bezel_print() translate([bezel[0] / 2 - lcd_c[0], bezel[1] / 2 - lcd_c[1], bezel_t]) mirror([0, 0, 1]) bezel_body();
module panel_bosses(side) {
    yi = side == 0 ? y_front_in : y_rear_in;
    for (x = panel_boss_x) difference() {
        hull() {
            translate([x, panel_boss_y[side], panel_boss_z[0]]) cylinder(d = ear_d, h = panel_boss_z[1] - panel_boss_z[0]);
            translate([x - ear_d / 2, yi - 0.01, panel_boss_z[0]]) cube([ear_d, 0.02, panel_boss_z[1] - panel_boss_z[0]]);
        }
        translate([x, panel_boss_y[side], panel_boss_z[1] - ear_h]) cylinder(d = ear_hole, h = ear_h + 1);
        translate([x, panel_boss_y[side], panel_boss_z[0] - 1]) cylinder(d = ear_hole, h = panel_boss_bot_insert + 1);
    }
}
module front_panel() {
    translate([panel_x0, y_front_in, panel_z0]) rotate([90, 0, 0]) front_print();
    panel_bosses(0);
}
module front_panel_print() translate([panel_x0 + panel_w, -(panel_inset + fit / 2 - emboss), panel_boss_z[1]]) rotate([0, 180, 0]) front_panel();
module bezel_part() translate([0, 0, H]) bezel_body();

// ---------------- 後面パネル ----------------
// 2D は「後ろから見た向き」（ケース X を左右反転）、縦はパネル座標
function rx(x) = panel_w - (x - panel_x0);
module rear_holes_2d() {
    translate([rx(dc_c[0]), zp(dc_c[1])]) circle(d = dc_hole);
    translate([rx(fuse_c[0]), zp(fuse_c[1])]) circle(d = fuse_hole);
    translate([rx(bnc_c[0]), zp(bnc_c[1])]) circle(d = bnc_hole);
    // 放熱器の窓（フィンが外へ出る。下辺で放熱器の重さを受ける）
    translate([rx(hs_win[1]), zp(hs_win[2])]) square([hs_win[1] - hs_win[0], hs_win[3] - hs_win[2]]);
}
module rear_labels_2d() {
    module t(s, p, sz = 3.2) translate(p) text(s, size = sz, font = font, halign = "center", valign = "center");
    t("DC 13.8V", [rx(dc_c[0]), zp(dc_c[1]) + dc_flange / 2 + 3]);
    t("+ CENTER", [rx(dc_c[0]), zp(dc_c[1]) - dc_flange / 2 - 3], 2.4);
    t("FUSE 5A", [rx(fuse_c[0]), zp(fuse_c[1]) + fuse_flange / 2 + 3]);
    t("ANT", [rx(bnc_c[0]), zp(bnc_c[1]) + bnc_flange / 2 + 3]);
}
module rear_2d() { difference() { square([panel_w, panel_h]); rear_holes_2d(); } }
module rear_print() {
    difference() {
        linear_extrude(panel_t) rear_2d();
        // DC ジャック周りの薄肉部（内面 z=0 側から掘り、外面は平らのまま。PSN_TRX と同じ）
        translate([rx(dc_c[0]), zp(dc_c[1]), -0.01]) linear_extrude(panel_t - dc_thin_t + 0.01) square(dc_thin, center = true);
    }
    translate([0, 0, panel_t - 0.01]) linear_extrude(emboss + 0.01) rear_labels_2d();
}
module rear_panel() {
    translate([panel_x0 + panel_w, y_rear_in, panel_z0]) rotate([90, 0, 180]) rear_print();
    panel_bosses(1);
}
module rear_panel_print() translate([panel_x0 + panel_w, -(panel_boss_y[1] - ear_d / 2), panel_boss_z[1]]) rotate([0, 180, 0]) rear_panel();
// 文字が穴・窓・ふた・底板にかからない
assert(zp(fuse_c[1]) + fuse_flange / 2 + 3 + 1.6 + 0.5 <= panel_h, "FUSE の文字がふたにかかる");
assert(zp(dc_c[1]) - dc_flange / 2 - 3 - 1.2 - 0.5 >= zp(floor_t), "+ CENTER の文字が底板にかかる");

// ---------------- 組立図用ダミー ----------------
module pcb_dummy() {
    color("darkgreen") translate([bx, by, bz]) cube([pcb_u, pcb_v, pcb_t]);
    for (t = tall) let(p = bp(t[0], t[1])) color(t[5]) translate([p[0] - t[2] / 2, p[1] - t[3] / 2, pcb_top]) cube([t[2], t[3], t[4]]);
}
module heatsink_dummy() {
    color([0.75, 0.75, 0.78]) translate([hs_x - hs_w / 2, hs_y0, hs_z0]) {
        cube([hs_w, hs_base, hs_h]);
        for (i = [0:7]) translate([1 + i * (hs_w - 3) / 7, hs_base - 0.01, 0]) cube([1.5, hs_fin + 0.01, hs_h]);
    }
    color("silver") translate([hs_x, hs_y0 - 3, q6_hole_z]) rotate([-90, 0, 0]) cylinder(d = 5.5, h = 3);   // RD16HHF1 の取付ねじ
}
module top_parts_dummy() {
    color([0.2, 0.3, 0.6]) translate([lcd_c[0] - 42.75, lcd_c[1] - lcd_mod[1] / 2, H - lcd_boss_h]) cube([85.5, lcd_mod[1], lcd_boss_h]);
    color("black") translate([lcd_c[0] - lcd_mod[0] / 2, lcd_c[1] - lcd_mod[1] / 2, H - lcd_boss_h - 1.6]) cube([lcd_mod[0], lcd_mod[1], 1.6]);
    color("dimgray") translate([lcd_c[0] - lcd_mod[0] / 2 + 5, lcd_c[1] - 10, H - lcd_depth]) cube([10, 20, lcd_depth - lcd_boss_h - 1.6]);
    color("silver") translate([enc_c[0], enc_c[1], H]) cylinder(d = 6, h = 15);
    color("silver") translate([afv_c[0], afv_c[1], H]) cylinder(d = 6, h = 12);
    color("gray") translate([enc_c[0] - enc_body / 2, enc_c[1] - enc_body / 2, lid_under - enc_depth]) cube([enc_body, enc_body, enc_depth]);
    color("gray") translate([afv_c[0], afv_c[1], lid_under - afv_depth]) cylinder(d = afv_body, h = afv_depth);
    color("lightgray") translate([psw_c[0], psw_c[1], H]) cylinder(d = 15, h = 4);
    color("gray") translate([psw_c[0], psw_c[1], lid_under - psw_depth]) cylinder(d = psw_body, h = psw_depth);
    color("lime") translate([led_c[0], led_c[1], H]) cylinder(d = 3, h = 2);
    color("red") translate([tx_c[0], tx_c[1], H]) cylinder(d = 3, h = 2);
    // 内蔵スピーカー: 枠（ふた裏に密着）・コーン部・マグネット（PSN_TRX と同じ表示）
    color("black") translate([spk_c[0] - spk_size / 2, spk_c[1] - spk_size / 2, lid_under - 1.5]) cube([spk_size, spk_size, 1.5]);
    color("dimgray") translate([spk_c[0], spk_c[1], lid_under - spk_depth + 6]) cylinder(d1 = spk_magnet + 2, d2 = spk_size - 4, h = spk_depth - 7.5);
    color("silver") translate([spk_c[0], spk_c[1], lid_under - spk_depth]) cylinder(d = spk_magnet, h = 6);
    for (c = [[mic_c, mic_flange, 6, mic_body, mic_depth], [sp_c, sp_plug, 3, sp_body, sp_depth]])
        color("gray") translate([c[0][0], c[0][1], 0]) {
            translate([0, 0, H]) cylinder(d = c[1], h = c[2]);
            translate([0, 0, lid_under - c[4]]) cylinder(d = c[3], h = c[4]);
        }
}
module rear_parts_dummy() {
    yo = D - panel_inset;
    for (c = [[dc_c, 12, 4, dc_body, dc_depth, "black"], [fuse_c, 15, 12, fuse_body, fuse_depth, "black"], [bnc_c, 10, 12, bnc_body, bnc_depth, "silver"]])
        color(c[5]) translate([c[0][0], 0, c[0][1]]) {
            translate([0, yo, 0]) rotate([-90, 0, 0]) cylinder(d = c[1], h = c[2]);
            translate([0, y_rear_in - c[4], 0]) rotate([-90, 0, 0]) cylinder(d = c[3], h = c[4]);
        }
}
module assembly(explode = 0) {
    color([0.85, 0.85, 0.88]) base();
    color([0.25, 0.25, 0.28]) { front_panel(); rear_panel(); }
    rear_parts_dummy();
    heatsink_dummy();
    translate([0, 0, explode]) {
        color([0.85, 0.85, 0.88, 0.35]) lid();
        color([0.15, 0.15, 0.17]) bezel_part();
        top_parts_dummy();
    }
    pcb_dummy();
}

// ---------------- 出力選択（mode） ----------------
module lid_print() translate([0, 0, -(H - lid_t)]) lid();

if      (mode == 0) assembly(40);
else if (mode == 1) base();
else if (mode == 2) lid_print();
else if (mode == 3) front_panel_print();
else if (mode == 4) rear_panel_print();
else if (mode == 5) assembly(0);
else if (mode == 6) { color([0.85, 0.85, 0.88]) base(); color([0.25, 0.25, 0.28]) { front_panel(); rear_panel(); } heatsink_dummy(); color([0.15, 0.15, 0.17]) bezel_part(); pcb_dummy(); top_parts_dummy(); rear_parts_dummy(); }
else if (mode == 7) front_2d();
else if (mode == 8) rear_2d();
else if (mode == 9) bezel_print();
else echo("mode は 0〜9 を指定してください");
