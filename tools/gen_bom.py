"""circuit.py から部品表 kicad/BOM.md と kicad/bom.csv を作る"""
import os, sys, csv, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from circuit import parts, prefix
from make_bom_purchase import buy_of, EXTRA, CHECKED

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

def cell(b):
    shop, model, code = b[:3]
    return ('%s（%s）' % (model, code) if code else model)

def fpname(fp):
    return fp.split(':')[-1].replace('_', ' ')

def main():
    real = [p for p in parts if not p['ref'].startswith('#')]
    with open(os.path.join(ROOT, 'kicad', 'bom.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Reference', 'Value', 'Footprint', 'Block', 'Note'])
        for p in sorted(real, key=lambda p: refkey(p['ref'])): w.writerow([p['ref'], p['value'], p['fp'], p['block'], p['note']])
    md = ['# Serrasoid TRX 29M 部品表（BOM）', '',
          '回路一覧 `tools/circuit.py` から `tools/gen_bom.py` で生成。回路図 `Serrasoid_TRX.kicad_sch` と同じ内容。', '',
          '- 部品はリード部品。第 1 混合の NJM2594V（U13）だけ表面実装（SSOP8、0.65mm ピッチ。SA612 が製造中止のため）',
          '- IC はすべて丸ピン IC ソケットを使う前提のフットプリント',
          '- 基板専用部品（回路図にない）: ドライバ IRF510 の放熱器（秋月 20PB020）、取付穴', '']
    total = 0
    for pf, title in GROUPS:
        ps = [p for p in real if prefix(p) == pf]
        if not ps: continue
        g = collections.OrderedDict()
        for p in sorted(ps, key=lambda p: refkey(p['ref'])):
            g.setdefault((p['value'], p['fp']), []).append(p)
        md += ['## ' + title, '', '| Reference | 値 / 型番 | フットプリント | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |', '|---|---|---|---|---|---|---|']
        for (v, fp), lst in g.items():
            byn = collections.OrderedDict()
            for p in lst:
                if p['note']: byn.setdefault(p['note'], []).append(p['ref'])
            notes = [n if len(r) == len(lst) else '%s: %s' % (refrange(r), n) for n, r in byn.items()]
            buys = collections.OrderedDict()
            for p in lst: buys.setdefault(buy_of(p)[1], []).append(p['ref'])
            shop = '<br>'.join(dict.fromkeys(b[0] for b in buys))
            model = '<br>'.join(('%s: ' % refrange(r) if len(buys) > 1 else '') + cell(b) for b, r in buys.items())
            md.append('| %s | %s | %s | %d | %s | %s | %s |' % (refrange([p['ref'] for p in lst]), v, fpname(fp), len(lst), shop, model, '<br>'.join(notes)))
        md += ['', '**%s 合計: %d**' % (title, len(ps)), '']
        total += len(ps)
    md += ['## 回路図に載っていない部品', '', '| 品名 | 数量 | 購入先 | 購入先の型番（販売コード） | 備考 |', '|---|---|---|---|---|']
    for name, qty, b, note in EXTRA: md.append('| %s | %d | %s | %s | %s |' % (name, qty, b[0], cell(b), note))
    md += ['', '購入先・販売コード・価格は `kicad/bom_purchase.csv`（`tools/make_bom_purchase.py`、秋月電子の通販サイトで %s に確認）。'
           '「要確認」は秋月で扱いがなく、型番・在庫を確かめていない部品。' % CHECKED, '']
    md += ['---', '', '**部品総数: %d**' % total, '']
    open(os.path.join(ROOT, 'kicad', 'BOM.md'), 'w').write('\n'.join(md))
    print('BOM', total)

if __name__ == '__main__':
    main()
