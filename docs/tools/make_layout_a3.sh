#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 JA6FUF (kazushinjo)
# A3 の部品配置図（kicad/Serrasoid_TRX_部品配置図.pdf）を KiCad で出力する。
# 基板の原点が用紙の左上にあるので、作業用のコピーで基板を用紙の中央へ移し、用紙を A3 にしてタイトル欄を入れてから F.Fab を出す。
set -e
cd "$(dirname "$0")/../.."
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
T=$(mktemp -d)
"$KP" - "$T/Serrasoid_TRX.kicad_pcb" <<'PY' 2>&1 | grep -v wxApp || true
import pcbnew, re, sys
b = pcbnew.LoadBoard('kicad/Serrasoid_TRX.kicad_pcb')
off = pcbnew.VECTOR2I(pcbnew.FromMM(125), pcbnew.FromMM(70))
for it in list(b.GetDrawings()) + list(b.GetFootprints()) + list(b.GetTracks()) + list(b.Zones()): it.Move(off)
b.Save(sys.argv[1])
s = open(sys.argv[1]).read()
s = re.sub(r'\(title_block.*?\n\t\)\n', '', s, flags=re.S)
s = s.replace('(paper "A4")', '''(paper "A3")
	(title_block
		(title "Serrasoid TRX 29M 部品配置図（部品面）")
		(date "2026-10-16")
		(rev "1.0")
		(company "JA6FUF")
		(comment 1 "上辺 = 後面（DC・RD16HHF1・ANT）、下辺 = 前面。170 × 130 mm")
		(comment 2 "□パッド = 1 番ピン・電解の＋・ダイオードの K")
	)''', 1)
open(sys.argv[1], 'w').write(s)
PY
"$K" pcb export pdf --layers F.Fab,Edge.Cuts --mode-single --black-and-white --ibt --sp --ev --scale 1.4 \
    -o "kicad/Serrasoid_TRX_部品配置図.pdf" "$T/Serrasoid_TRX.kicad_pcb"
rm -rf "$T"
