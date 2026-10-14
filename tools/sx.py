import re, math
class Sym(str): pass
def parse(s):
    toks=re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+',s)
    stack=[[]]
    for t in toks:
        if t=='(': stack.append([])
        elif t==')': x=stack.pop(); stack[-1].append(x)
        elif t[0]=='"': stack[-1].append(t)
        else: stack[-1].append(Sym(t))
    return stack[0][0]
def dump(x):
    if isinstance(x,list): return '('+' '.join(dump(i) for i in x)+')'
    return x
def unq(t): return t[1:-1].replace('\\"','"') if isinstance(t,str) and t.startswith('"') else t
def q(t): return '"'+t.replace('"','\\"')+'"'
def find(x,tag): return [c for c in x if isinstance(c,list) and c and c[0]==tag]
def find1(x,tag):
    r=find(x,tag); return r[0] if r else None
def prop(sym,name):
    for p in find(sym,'property'):
        if unq(p[1])==name: return unq(p[2])
def libpins(libsym):
    out={}
    def walk(n,unit):
        for c in n:
            if isinstance(c,list) and c and c[0]=='symbol':
                m=re.search(r'_(\d+)_(\d+)$',unq(c[1])); walk(c, int(m.group(1)) if m else unit)
            elif isinstance(c,list) and c and c[0]=='pin':
                at=find1(c,'at'); num=unq(find1(c,'number')[1])
                out.setdefault(num,[]).append((float(at[1]),float(at[2]),unit))
    walk(libsym,0); return out
def pinpos(inst,lx,ly):
    at=find1(inst,'at'); x,y,r=float(at[1]),float(at[2]),float(at[3]) if len(at)>3 else 0
    mir=find1(inst,'mirror')
    ly=-ly  # lib y up -> sch y down
    if mir and mir[1]=='x': ly=-ly
    if mir and mir[1]=='y': lx=-lx
    a=math.radians(r)
    # rotation in schematic is counter-clockwise on screen (y down)
    rx=lx*math.cos(a)+ly*math.sin(a); ry=-lx*math.sin(a)+ly*math.cos(a)
    return round(x+rx,4),round(y+ry,4)
