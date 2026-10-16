#!/bin/sh
# 基板を Freerouting で自動配線し、外層に GND ベタを入れて DRC する
#   tools/route.sh [作業フォルダ]
set -e
cd "$(dirname "$0")/.."
P=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
FR=${FREEROUTING:-$HOME/tools/freerouting-1.9.jar}   # 1.9.0（Java 17 で動く。2.x は時間がかかり未配線が残った）
W=${1:-${TMPDIR:-/tmp}/serrasoid_route}
mkdir -p "$W"
PCB=kicad/Serrasoid_TRX.kicad_pcb
$P - "$PCB" "$W/in.dsn" <<'PY' 2>&1 | grep -v 'swig\|assert\|^$' || true
import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); print('dsn', pcbnew.ExportSpecctraDSN(b, sys.argv[2]))
PY
python3 tools/mkdsn.py "$W/in.dsn" "$W/route.dsn"
rm -f "$W/route.ses"
java -jar "$FR" -de "$W/route.dsn" -do "$W/route.ses" -mp ${PASSES:-100} -mt 1 -da > "$W/fr.log" 2>&1 || true
grep -E 'Auto-routing was|optimization was|unrouted|incomplete' "$W/fr.log" | tail -5 || true
$P - "$PCB" "$W/route.ses" <<'PY' 2>&1 | grep -v 'swig\|assert\|^$' || true
import pcbnew,sys
sys.path.insert(0,'tools')
import pcb_post
b=pcbnew.LoadBoard(sys.argv[1]); print('ses', pcbnew.ImportSpecctraSES(b, sys.argv[2]))
pcb_post.finish(b)
b.Save(sys.argv[1])
PY
# Freerouting で残った未接続を、表・裏の格子で探して引く
$P tools/fix_route.py "$PCB" 2>&1 | grep -E "引いた|引けない" || true
$K pcb drc --schematic-parity --format json -o "$W/drc.json" "$PCB" >/dev/null 2>&1 || true
python3 - "$W/drc.json" <<'PY'
import json,collections,sys
d=json.load(open(sys.argv[1]))
print('DRC', dict(collections.Counter((x['severity'],x['type']) for x in d['violations'])), 'unconnected', len(d['unconnected_items']), 'parity', len(d.get('schematic_parity',[])))
for x in d['violations'][:15]: print(' ',x['severity'],x['type'],[i['description'][:60] for i in x['items']])
for x in d['unconnected_items'][:15]: print('  unconn',[i['description'][:60] for i in x['items']])
for x in d.get('schematic_parity',[])[:10]: print('  parity',x['description'][:80],[i['description'][:50] for i in x['items']])
PY
