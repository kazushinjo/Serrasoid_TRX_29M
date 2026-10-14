"""circuit.py から部品表 kicad/BOM.md と kicad/bom.csv を作る"""
import os, sys, csv, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from circuit import parts, prefix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPS = [('R', '抵抗 R'), ('VR', '半固定抵抗 VR'), ('C', 'コンデンサ C'), ('TC', 'トリマコンデンサ TC'),
          ('L', 'コイル L'), ('T', 'トランス T'), ('D', 'ダイオード D'), ('Q', 'トランジスタ・FET Q'),
          ('U', 'IC・モジュール U'), ('X', '水晶・ディスクリミネータ X'), ('FL', 'フィルタ FL'), ('K', 'リレー K'),
          ('J', 'コネクタ J'), ('JP', 'はんだジャンパ JP'), ('TP', 'テストポイント TP')]

def refkey(r):
    m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))

def refrange(refs):
    refs = sorted(refs, key=refkey); out = []; i = 0
    while i < len(refs):
        j = i
        while j + 1 < len(refs) and refkey(refs[j + 1])[1] == refkey(refs[j])[1] + 1: j += 1
        out += refs[i:j + 1] if j - i < 2 else ['%s-%s' % (refs[i], refs[j])]; i = j + 1
    return ', '.join(out)

def fpname(fp):
    return fp.split(':')[-1].replace('_', ' ')

def main():
    real = [p for p in parts if not p['ref'].startswith('#')]
    with open(os.path.join(ROOT, 'kicad', 'bom.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Reference', 'Value', 'Footprint', 'Block', 'Note'])
        for p in sorted(real, key=lambda p: refkey(p['ref'])): w.writerow([p['ref'], p['value'], p['fp'], p['block'], p['note']])
    md = ['# Serrasoid TRX 29M 部品表（BOM）', '',
          '回路一覧 `tools/circuit.py` から `tools/gen_bom.py` で生成。回路図 `Serrasoid_TRX.kicad_sch` と同じ内容。', '',
          '- 表面実装は TLV3501（SOIC-8）と SHDN 選択用のはんだジャンパ JP1 だけ。ほかはすべてリード部品',
          '- IC はすべて丸ピン IC ソケットを使う前提のフットプリント',
          '- 基板専用部品（回路図にない）: RD06HHF1 の放熱器（秋月 20PB020）、取付穴', '']
    total = 0
    for pf, title in GROUPS:
        ps = [p for p in real if prefix(p) == pf]
        if not ps: continue
        g = collections.OrderedDict()
        for p in sorted(ps, key=lambda p: refkey(p['ref'])):
            g.setdefault((p['value'], p['fp']), []).append(p)
        md += ['## ' + title, '', '| Reference | 値 / 型番 | フットプリント | 数量 | 備考 |', '|---|---|---|---|---|']
        for (v, fp), lst in g.items():
            byn = collections.OrderedDict()
            for p in lst:
                if p['note']: byn.setdefault(p['note'], []).append(p['ref'])
            notes = [n if len(r) == len(lst) else '%s: %s' % (refrange(r), n) for n, r in byn.items()]
            md.append('| %s | %s | %s | %d | %s |' % (refrange([p['ref'] for p in lst]), v, fpname(fp), len(lst), '<br>'.join(notes)))
        md += ['', '**%s 合計: %d**' % (title, len(ps)), '']
        total += len(ps)
    md += ['---', '', '**部品総数: %d**' % total, '']
    open(os.path.join(ROOT, 'kicad', 'BOM.md'), 'w').write('\n'.join(md))
    print('BOM', total)

if __name__ == '__main__':
    main()
