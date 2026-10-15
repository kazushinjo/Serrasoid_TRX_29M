#!/bin/sh
# 1 ブロックだけ回路図を作って PNG にする（確認用）: tools/preview.sh 制御 出力.png
cd "$(dirname "$0")/.."
T=${TMPDIR:-/tmp}/serrasoid_preview; mkdir -p "$T"
cp kicad/sym-lib-table kicad/fp-lib-table kicad/Serrasoid_TRX.kicad_sym "$T"/ 2>/dev/null
cp kicad/Serrasoid_TRX.kicad_pro "$T"/p.kicad_pro
python3 tools/gen_sch.py "$1" --preview="$T/p.kicad_sch" | tail -3
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export pdf -o "$T/p.pdf" "$T/p.kicad_sch" >/dev/null 2>&1
${PYVENV:-python3} -W ignore -c "
import pymupdf,sys
d=pymupdf.open(sys.argv[1]); p=d[0]
b=None
for x in p.get_drawings():
    r=x['rect']; b=r if b is None else b|r
p.get_pixmap(dpi=int(sys.argv[3]), clip=pymupdf.Rect(20,20,p.rect.width*0.75,p.rect.height*0.7)).save(sys.argv[2])" "$T/p.pdf" "$2" ${DPI:-60}
