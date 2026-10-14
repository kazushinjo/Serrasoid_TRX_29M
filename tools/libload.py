"""KiCad 記号ライブラリから記号を読み出す（extends を展開）"""
import os, re, copy
from sx import parse, find, find1, unq, q, Sym
SYMDIR = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols'
_cache = {}
def lib(name, path=None):
    if name not in _cache:
        p = path or os.path.join(SYMDIR, name + '.kicad_sym')
        root = parse(open(p).read())
        _cache[name] = {unq(s[1]): s for s in find(root, 'symbol')}
    return _cache[name]
def get(lib_id, path=None):
    """lib_id 'Lib:Name' の記号を、extends を解決した完全な定義で返す"""
    ln, sn = lib_id.split(':')
    L = lib(ln, path)
    s = copy.deepcopy(L[sn] if sn in L else L[lib_id])
    ext = find1(s, 'extends')
    if ext:
        base = get(ln + ':' + unq(ext[1]), path)
        bname = unq(base[1]).split(':')[-1]
        s.remove(ext)
        # 派生側のプロパティを優先し、図形・ピンは親から
        props = {unq(p[1]): p for p in find(s, 'property')}
        out = [Sym('symbol'), q(sn)]
        for c in base[2:]:
            if isinstance(c, list) and c and c[0] == 'property':
                n = unq(c[1]); out.append(props.pop(n, c))
            elif isinstance(c, list) and c and c[0] == 'symbol':
                c = copy.deepcopy(c); c[1] = q(unq(c[1]).replace(bname, sn, 1)); out.append(c)
            else:
                out.append(c)
        for p in props.values(): out.append(p)
        s = out
    return s
def pins(sym):
    """{番号: (x, y, 向き, 長さ, 名前, 種類, unit)}"""
    out = {}
    for c in find(sym, 'symbol'):
        m = re.search(r'_(\d+)_(\d+)$', unq(c[1])); unit = int(m.group(1))
        for p in find(c, 'pin'):
            at = find1(p, 'at'); num = unq(find1(p, 'number')[1]); nm = unq(find1(p, 'name')[1])
            ln = float(find1(p, 'length')[1])
            out.setdefault(num, (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0, ln, nm, str(p[1]), unit))
    return out
