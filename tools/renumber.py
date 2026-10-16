"""部品番号を回路図の位置順（X の小さい順、同じ X は Y の順。種類ごと）に振り直す（PSN_TRX 2026-10-15 と同じ方法）

  python3 tools/renumber.py          # 対応を計算して表示するだけ
  python3 tools/renumber.py --apply  # 回路図・基板・circuit.py・資料を書き換え、対応表 kicad/refdes_map_<日付>.csv を書く

多ユニットの部品は最も小さいユニットの位置で並べる。
回路図・基板では部品番号のほか、部品番号から作っている UUID（gen_sch.py / gen_pcb.py の uuid5）も新しい番号のものに替え、
作り直したときにも回路図と基板の対応が保たれるようにする。
circuit.py は部品を出現順に仮の番号で数えたあと、RENUMBER（旧 → 新）で最終の番号にする。
部品を足したら、回路図に置いてからもう一度これを実行する。
"""
import os, re, sys, uuid, csv, datetime, subprocess, ast
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sx import parse, find, find1, unq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = os.path.join(ROOT, 'kicad', 'Serrasoid_TRX.kicad_sch')
PCB = os.path.join(ROOT, 'kicad', 'Serrasoid_TRX.kicad_pcb')
KP = '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
KCLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
NS = uuid.UUID('6a1c3f3e-29a0-4c55-9d1e-5e7a50000000')
# 番号の後ろにユニット記号（U13A など）が付いたものも置き換える
TOK = re.compile(r'(?<![A-Za-z0-9_.\-/])(FL|TC|TP|VR|R|C|L|Q|U|D|J|K|T|X)(\d+)(?=[A-F](?![0-9A-Za-z_])|(?![0-9A-Za-z_]))')
RANGE = re.compile(r'(?<![A-Za-z0-9_.\-/])(FL|TC|TP|VR|R|C|L|Q|U|D|J|K|T|X)(\d+)〜(?:\1)?(\d+)(?![0-9A-Za-z_])')
# XIAO のピン名（D0〜D10）と同じ行には D の部品番号を置き換えない
XIAO_WORDS = ('GPIO', 'XIAO', '起動設定', 'VIN', '| D', 'D0', 'ピン割り当て')
# 資料のうち、当時の記録として旧番号のまま残し、冒頭に注記だけ入れるもの
RECORDS = ['docs/回路図論理チェック.md', 'docs/基板チェック.md']
TEXTS = ['README.md', 'tools/circuit.py', 'tools/gen_pcb.py', 'tools/pcb_report.py', 'tools/netclass.py',
         'docs/tools/make_parts_layout.py', 'docs/tools/make_serrasoid_doc.py', 'docs/tools/make_serrasoid_figs.py',
         'enclosure/serrasoid_trx_case.scad', 'enclosure/README.md', 'tools/make_bom_purchase.py']


def sch_positions():
    t = parse(open(SCH).read())
    pos, val = {}, {}
    for s in find(t, 'symbol'):
        ref = [unq(p[2]) for p in find(s, 'property') if unq(p[1]) == 'Reference'][0]
        if ref.startswith('#'): continue
        u = int(find1(s, 'unit')[1]); at = find1(s, 'at')
        val[ref] = [unq(p[2]) for p in find(s, 'property') if unq(p[1]) == 'Value'][0]
        if ref not in pos or u < pos[ref][0]: pos[ref] = (u, float(at[1]), float(at[2]))
    return pos, val


def mapping():
    pos, val = sch_positions()
    grp = {}
    for r, (u, x, y) in pos.items(): grp.setdefault(re.match(r'[A-Z]+', r).group(0), []).append((round(x, 2), round(y, 2), r))
    m = {}
    for k, v in grp.items():
        for i, (x, y, r) in enumerate(sorted(v)): m[r] = '%s%d' % (k, i + 1)
    return m, val


def fmt_set(pre, nums):
    nums = sorted(nums)
    if len(nums) > 2 and nums == list(range(nums[0], nums[-1] + 1)): return '%s%d〜%s%d' % (pre, nums[0], pre, nums[-1])
    return '・'.join('%s%d' % (pre, n) for n in nums)


def sub_text(s, m):
    out = []
    for line in s.split('\n'):
        if line.startswith('RENUMBER = '): out.append(line); continue   # 仮の番号の対応は apply で合成する
        def rng(mo):
            pre, a, b = mo.group(1), int(mo.group(2)), int(mo.group(3))
            olds = ['%s%d' % (pre, n) for n in range(a, b + 1)]
            if not all(o in m for o in olds): return mo.group(0)
            return '\0' + fmt_set(pre, [int(m[o][len(pre):]) for o in olds]).replace(pre, '\1' + pre) + '\0'
        line = RANGE.sub(rng, line)
        parts = line.split('\0')
        for i in range(0, len(parts), 2):   # 範囲を置き換えた所（奇数番目）は済み
            def tok(mo):
                r = mo.group(0)
                if r not in m: return r
                if mo.group(1) == 'D' and any(w in line for w in XIAO_WORDS): return r
                return m[r]
            parts[i] = TOK.sub(tok, parts[i])
        out.append(''.join(parts).replace('\1', ''))
    return '\n'.join(out)


def uid(ref, unit): return str(uuid.uuid5(NS, '%s:%d' % (ref, unit)))


def apply(m, val):
    # ---- 回路図・基板（同時に入れ替えるので、一度に置き換える）
    um = {uid(o, u): uid(n, u) for o, n in m.items() for u in range(1, 9)}
    for path, pat in ((SCH, r'\((property "Reference"|reference) "([^"]+)"'), (PCB, r'\((property "Reference") "([^"]+)"')):
        s = open(path).read()
        s = re.sub(pat, lambda mo: '(%s "%s"' % (mo.group(1), m.get(mo.group(2), mo.group(2))), s)
        s = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', lambda mo: um.get(mo.group(0), mo.group(0)), s)
        open(path, 'w').write(s)
    # ---- 文書・スクリプト
    for f in TEXTS:
        p = os.path.join(ROOT, f); s = open(p).read(); t = sub_text(s, m)
        if t != s: open(p, 'w').write(t)
    # ---- circuit.py の数え方（仮の番号 → 最終の番号）。前に振り直していれば、その対応と合成する
    p = os.path.join(ROOT, 'tools', 'circuit.py'); s = open(p).read()
    today = datetime.date.today().isoformat()
    def key(r): return (re.match(r'[A-Z]+', r).group(0), int(re.search(r'\d+', r).group(0)))
    mo = re.search(r'^RENUMBER = (\{.*\})$', s, re.M)
    prev = ast.literal_eval(mo.group(1)) if mo else {}
    inv = {v: k for k, v in prev.items()}
    comp = {inv.get(cur, cur): new for cur, new in m.items()}
    items = ', '.join("'%s': '%s'" % (o, n) for o, n in sorted(comp.items(), key=lambda x: key(x[0])) if o != n)
    if mo:
        s = s[:mo.start()] + 'RENUMBER = {' + items + '}' + s[mo.end():]
        s = re.sub(r'^# 部品番号の振り直し（[^）]*）', '# 部品番号の振り直し（%s、tools/renumber.py）' % today, s, count=1, flags=re.M)
    else:
        s = s.replace("        p['ref'] = '%s%d' % (k, cnt[k]) if not k.startswith('#') else '%s0%d' % (k, cnt[k])\n    return parts",
                      "        p['ref'] = '%s%d' % (k, cnt[k]) if not k.startswith('#') else '%s0%d' % (k, cnt[k])\n"
                      "        p['ref'] = RENUMBER.get(p['ref'], p['ref'])\n    return parts")
        s = s.replace('def numbered():', '# 部品番号の振り直し（%s、tools/renumber.py）: 出現順の仮の番号 → 回路図の位置順の番号\n' % today +
                      'RENUMBER = {' + items + '}\n\ndef numbered():', 1)
    open(p, 'w').write(s)
    # ---- 対応表（同じ日に 2 回目なら、その日の最初の振り直し前の番号との対応にする）、記録の資料に注記
    mp = 'refdes_map_%s.csv' % today
    mpath = os.path.join(ROOT, 'kicad', mp)
    orig = {}
    if os.path.exists(mpath):
        for r in list(csv.reader(open(mpath, encoding='utf-8-sig')))[1:]: orig[r[0]] = (r[1], r[2])
    with open(mpath, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['新しい番号', '旧番号（%s まで）' % today, '値/型番', '変更'])
        for cur, new in sorted(m.items(), key=lambda x: key(x[1])):
            o, ov = orig.get(cur, (cur, val[cur])) if (orig or True) else (cur, val[cur])
            if orig and cur not in orig: o, ov = '', ''
            note = '追加' if not o else ('変更' if o != new else '')
            if o and ov != val[cur]: note = (note + '・' if note else '') + '部品を変更（旧 %s）' % ov
            w.writerow([new, o, val[cur], note])
    for f in RECORDS:
        p = os.path.join(ROOT, f); s = open(p).read()
        if mp in s: continue
        s = s.split('\n', 1)
        note = ('\n> **注意（%s）**: この記録の部品番号は、%s に部品番号を回路図の位置順に振り直す前の旧番号です。'
                '現在の番号との対応は [`kicad/%s`](../kicad/%s) を見てください。\n' % (today, today, mp, mp))
        open(p, 'w').write(s[0] + '\n' + note + s[1])
    print('書き換え完了、対応表', mp)
    # 基板のネット名のうち部品番号から付いた名前（Net-(C23-Pad1) など）を、振り直した回路図の名前にそろえる（KiCad 付属の Python で）
    subprocess.run([KP, os.path.abspath(__file__), '--netnames'], check=True)


def netnames():
    """（KiCad 付属の Python で実行）回路図のネットリストの名前を、基板の各パッドのネットに付け直す"""
    import pcbnew, tempfile
    out = os.path.join(tempfile.mkdtemp(), 'n.net')
    subprocess.run([KCLI, 'sch', 'export', 'netlist', '-o', out, SCH], check=True, capture_output=True)
    t = open(out).read(); sn = {}
    for mo in re.finditer(r'\(net\s+\(code "\d+"\)\s+\(name "((?:[^"\\]|\\.)*)"\)(.*?)(?=\(net\s+\(code|\Z)', t, re.S):
        for ref, pin in re.findall(r'\(ref "([^"]*)"\)\s*\(pin "([^"]*)"\)', mo.group(2)): sn[(ref, pin)] = mo.group(1)
    b = pcbnew.LoadBoard(PCB); nm = {}
    for f in b.GetFootprints():
        for pad in f.Pads():
            o, n = pad.GetNetname(), sn.get((f.GetReference(), pad.GetNumber()))
            if o and n and o != n:
                if nm.get(o, n) != n: raise SystemExit('ネットの対応が一意でない: %s → %s / %s' % (o, nm[o], n))
                nm[o] = n
    s = open(PCB).read()
    s = re.sub(r'\(net "((?:[^"\\]|\\.)*)"\)', lambda mo: '(net "%s")' % nm.get(mo.group(1), mo.group(1)), s)
    open(PCB, 'w').write(s)
    print('基板のネット名を %d 個付け直した' % len(nm))


if __name__ == '__main__':
    if '--netnames' in sys.argv: netnames(); sys.exit()
    m, val = mapping()
    ch = sum(1 for o, n in m.items() if o != n)
    print('%d 点のうち %d 点の番号が変わる' % (len(m), ch))
    if '--apply' in sys.argv: apply(m, val)
