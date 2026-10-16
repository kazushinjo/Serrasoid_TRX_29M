"""表面実装 IC（NJM2594V）の GND パッドから外側へ短い線を出し、ビアで内層の GND につなぐ
（0.65mm ピッチのパッドの間には外層の GND ベタが入らないため）。配置の直後（gen_pcb.py）と、手直しのときに使う"""
import pcbnew
M = pcbnew.FromMM

def add_gnd_vias(b, values=('NJM2594V',), dist=1.8):
    gnd = b.FindNet('GND'); n = 0
    for f in b.GetFootprints():
        if f.GetValue() not in values: continue
        c = f.GetPosition()
        for p in f.Pads():
            if p.GetNetname() != 'GND' or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            P = p.GetPosition(); d = P - c
            # パッドの列の外側（足の向き）へ出す
            if abs(d.x) >= abs(d.y): step = pcbnew.VECTOR2I(M(dist) * (1 if d.x > 0 else -1), 0)
            else: step = pcbnew.VECTOR2I(0, M(dist) * (1 if d.y > 0 else -1))
            vp = P + step
            if any(isinstance(t, pcbnew.PCB_VIA) and (t.GetPosition() - vp).EuclideanNorm() < M(0.05) for t in b.GetTracks()): continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(P); t.SetEnd(vp); t.SetWidth(M(0.3)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); b.Add(t)
            v = pcbnew.PCB_VIA(b); v.SetPosition(vp); v.SetWidth(M(0.8)); v.SetDrill(M(0.4)); v.SetNet(gnd); b.Add(v)
            n += 1
    return n
