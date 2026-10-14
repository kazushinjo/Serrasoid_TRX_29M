#!/bin/sh
# 回路図を生成して ERC を実行し、違反を種類ごとに数える
set -e
cd "$(dirname "$0")/.."
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
OUT=${TMPDIR:-/tmp}/serrasoid_erc.json
python3 tools/gen_sch.py
$K sch erc --format json --severity-all -o "$OUT" kicad/Serrasoid_TRX.kicad_sch >/dev/null 2>&1 || true
python3 - "$OUT" <<'PY'
import json,collections,sys
d=json.load(open(sys.argv[1]))
v=[x for s in d['sheets'] for x in s['violations']]
print('ERC', dict(collections.Counter((x['severity'],x['type']) for x in v)))
for x in v: print(' ',x['severity'],x['type'],x['description'][:70],[i['description'][:50] for i in x['items']][:3])
PY
