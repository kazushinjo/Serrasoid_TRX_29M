# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 真城和一 (JA6FUF/JH1XHX)
"""
Nextion NX4832T035（3.5 インチ 480x320）用の背景画像（アナログ S メーターの目盛り入り）を作る。PSN_TRX の nextion/make_background.py が元。
  python3 make_background.py  → background.png（Nextion Editor でピクチャ 0 として取り込み、page0 の背景 sta=image, pic=0 にする）
                                 preview_rx.png・preview_tx.png（表示の見本。画面データには使わない）
目盛りの位置はスケッチ（Serrasoid_TRX.ino）の METER_* と同じ値にすること。
メーターは 2 段: 外側 = 受信の S メーター（S0〜S9 黒、+10〜+60dB 赤。PSN_TRX と同じ目盛り）、
              内側（青）= 送信出力 0〜15W（出力検出の電圧に比例して針が振れるので、目盛りは √W の位置）
必要: Pillow
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

W, H = 480, 320
PANEL = (28, 30, 36)          # 画面の地の色（テキスト部品の bco = RGB565 で 6372）
FACE = (240, 232, 208)        # メーター面
INK = (20, 20, 20)
RED = (200, 30, 30)
BLUE = (30, 80, 170)

# メーター（スケッチの METER_* と同じ）
FACE_BOX = (16, 112, 320, 292)   # メーター面 x0, y0, x1, y1
PIV = (168, 318)                 # 針の支点（メーター面の下に隠れる）
R_ARC = 165                      # S の目盛りの半径
R_PWR = 128                      # 出力の目盛りの半径
ANG_L, ANG_R = 135.0, 45.0       # 左端・右端の角度（右向き 0°、反時計回り）
S9_POS = 0.6                     # S9 の位置（左端 0〜右端 1）
PWR_FULL = 15.0                  # 右端の出力 [W]


def pos_of_db(db):               # S9 = 0dB、S0 = -54dB、右端 = +60dB
    if db <= 0:
        return max(0.0, (db + 54) / 54 * S9_POS)
    return min(1.0, S9_POS + db / 60 * (1 - S9_POS))


def pt(p, r):
    a = math.radians(ANG_L + p * (ANG_R - ANG_L))
    return PIV[0] + r * math.cos(a), PIV[1] - r * math.sin(a)


def font(sz, bold=True):
    for path in ("/System/Library/Fonts/Helvetica.ttc", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(path, sz, index=1 if (bold and path.endswith('.ttc')) else 0)
        except OSError:
            pass
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), PANEL)
d = ImageDraw.Draw(img)
d.rounded_rectangle(FACE_BOX, radius=10, fill=FACE, outline=(90, 90, 90), width=2)


def arc(p0, p1, r, color, width):
    n = 80
    d.line([pt(p0 + (p1 - p0) * i / n, r) for i in range(n + 1)], fill=color, width=width, joint="curve")


# 外側: S メーター（S0〜S9 は黒、S9 から上は赤）
arc(0, S9_POS, R_ARC, INK, 3)
arc(S9_POS, 1, R_ARC, RED, 5)
for s in range(0, 10):
    p = pos_of_db((s - 9) * 6)
    major = s % 2 == 1
    d.line([pt(p, R_ARC), pt(p, R_ARC + (12 if major else 7))], fill=INK, width=3 if major else 2)
    if major:
        x, y = pt(p, R_ARC + 24)
        d.text((x, y), str(s), font=font(18), fill=INK, anchor="mm")
for db in range(10, 61, 10):
    p = pos_of_db(db)
    major = db % 20 == 0
    d.line([pt(p, R_ARC), pt(p, R_ARC + (12 if major else 7))], fill=RED, width=3 if major else 2)
    if major:
        x, y = pt(p, R_ARC + 26)
        d.text((x, y), f"+{db}", font=font(16), fill=RED, anchor="mm")

# 内側: 送信出力 W（内向きの目盛り、数字は内）。針は電圧（√W）に比例
arc(0, 1, R_PWR, BLUE, 3)
for w in (0, 0.5, 1, 2, 3, 5, 7, 10, 15):
    p = math.sqrt(w / PWR_FULL)
    major = w in (0, 1, 2, 5, 10, 15)
    d.line([pt(p, R_PWR), pt(p, R_PWR - (11 if major else 6))], fill=BLUE, width=3 if major else 2)
    if major:
        x, y = pt(p, R_PWR - 22)
        d.text((x, y), ("%g" % w), font=font(15), fill=BLUE, anchor="mm")

d.text((FACE_BOX[0] + 14, FACE_BOX[3] - 14), "S", font=font(22), fill=INK, anchor="lm")
d.text((FACE_BOX[2] - 14, FACE_BOX[3] - 14), "W", font=font(18), fill=BLUE, anchor="rm")
# 支点カバー
d.rounded_rectangle((PIV[0] - 22, FACE_BOX[3] - 18, PIV[0] + 22, FACE_BOX[3] - 2), radius=4, fill=(60, 60, 64))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "background.png")
img.save(out)
print(out, W, H)


# ---- 表示の見本（preview_rx.png・preview_tx.png。画面データには使わない）----
def needle(im, pos):
    dd = ImageDraw.Draw(im)
    a = math.radians(ANG_L + pos * (ANG_R - ANG_L))
    p0 = (PIV[0] + 50 * math.cos(a), PIV[1] - 50 * math.sin(a))
    p1 = (PIV[0] + 160 * math.cos(a), PIV[1] - 160 * math.sin(a))
    dd.line([p0, p1], fill=(0, 0, 0), width=2)


def sample(name, texts, pos):
    im = img.copy()
    needle(im, pos)
    dd = ImageDraw.Draw(im)
    for (x, y, w, h, sz, s, color) in texts:
        dd.text((x, y + h / 2), s, font=font(sz), fill=color, anchor="lm")
    im.save(os.path.join(os.path.dirname(out), name))


WHITE, RED16, GREEN, YELLOW = (255, 255, 255), (255, 0, 0), (0, 252, 0), (255, 252, 0)
fixed = (344, 68, 120, 32, 22, "SERRASOID", WHITE)
sample("preview_rx.png", [(16, 16, 448, 40, 32, "29.300 MHz", WHITE), fixed, (16, 68, 320, 32, 22, "STEP: 10kHz", WHITE),
                          (344, 116, 120, 32, 22, "S5", WHITE), (344, 160, 120, 32, 22, "RX", WHITE),
                          (344, 204, 120, 32, 22, "SQL 3", WHITE), (344, 248, 120, 32, 22, "BUSY", GREEN)], pos_of_db(-24))
sample("preview_tx.png", [(16, 16, 448, 40, 32, "29.300 MHz", WHITE), fixed, (16, 68, 320, 32, 22, "STEP: 10kHz", WHITE),
                          (344, 116, 120, 32, 22, "9.8W", WHITE), (344, 160, 120, 32, 22, "TX", RED16),
                          (344, 204, 120, 32, 22, "SQL 3", WHITE)], math.sqrt(9.8 / PWR_FULL))
sample("preview_scan.png", [(16, 16, 448, 40, 32, "29.120 MHz", WHITE), fixed, (16, 68, 320, 32, 22, "SCAN >>  PUSH=STOP", YELLOW),
                            (344, 116, 120, 32, 22, "S0", WHITE), (344, 160, 120, 32, 22, "SCAN", YELLOW),
                            (344, 204, 120, 32, 22, "SQL 3", WHITE)], 0.0)
print("preview_rx.png preview_tx.png preview_scan.png")
