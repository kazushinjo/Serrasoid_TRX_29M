#!/bin/sh
# 回路図を生成し、ERC と回路一覧（circuit.py）との接続照合を行う
set -e
cd "$(dirname "$0")/.."
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
OUT=${TMPDIR:-/tmp}/serrasoid_erc.json
python3 tools/gen_sch.py
$K sch erc --format json -o "$OUT" kicad/Serrasoid_TRX.kicad_sch >/dev/null 2>&1 || true
python3 - "$OUT" <<'PY'
import json,collections,sys
d=json.load(open(sys.argv[1]))
v=[(s['path'],x) for s in d['sheets'] for x in s['violations']]
print('ERC', dict(collections.Counter((x['severity'],x['type']) for _,x in v)) or '違反なし')
for p,x in v[:30]: print(' ',p,x['severity'],x['type'],[i['description'][:50] for i in x['items']][:3])
PY
python3 tools/verify_sch.py
