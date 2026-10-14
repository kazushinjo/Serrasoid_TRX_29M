#!/bin/sh
# 基板の上面（部品外形・番号・外形線）を PNG に書き出す: tools/render.sh 出力.png [層]
cd "$(dirname "$0")/.."
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
OUT=$1; LAYERS=${2:-F.Fab,F.SilkS,Edge.Cuts,F.Cu}
SVG=${OUT%.png}.svg
$K pcb export svg -l "$LAYERS" --mode-single --exclude-drawing-sheet --fit-page-to-board -o "$SVG" kicad/Serrasoid_TRX.kicad_pcb >/dev/null 2>&1
${PYVENV:-python3} -W ignore -c "
import pymupdf,sys
d=pymupdf.open(sys.argv[1]); d2=pymupdf.open('pdf',d.convert_to_pdf()); d2[0].get_pixmap(dpi=int(sys.argv[3])).save(sys.argv[2])" "$SVG" "$OUT" ${DPI:-110}
