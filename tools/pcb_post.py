"""配線後の仕上げ: 外層の GND ベタ、シルクの文字"""
import pcbnew
M = pcbnew.FromMM
def finish(b, title='Serrasoid TRX 29M', ver='Ver 1.2'):
    bb = b.GetBoardEdgesBoundingBox()
    gnd = b.FindNet('GND')
    have = {z.GetLayer() for z in b.Zones()}
    for L in (pcbnew.F_Cu, pcbnew.B_Cu):
        if L in have: continue      # 2 回目以降はベタを作り直さない（KiCad 10 は Remove 後に一覧が壊れるため）
        z = pcbnew.ZONE(b); z.SetLayer(L); z.SetNet(gnd)
        o = z.Outline(); o.NewOutline()
        for x, y in [(bb.GetX(), bb.GetY()), (bb.GetRight(), bb.GetY()), (bb.GetRight(), bb.GetBottom()), (bb.GetX(), bb.GetBottom())]:
            o.Append(x, y)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetLocalClearance(M(0.4)); z.SetMinThickness(M(0.3))
        z.SetAssignedPriority(0)
        b.Add(z)
    if any(isinstance(d, pcbnew.PCB_TEXT) and d.GetText().startswith(title) for d in b.GetDrawings()):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones()); return
    t = pcbnew.PCB_TEXT(b); t.SetText('%s  %s  Designed by JA6FUF/JH1XHX' % (title, ver)); t.SetLayer(pcbnew.B_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(M(1.5), M(1.5))); t.SetTextThickness(M(0.25)); t.SetMirrored(True)
    t.SetPosition(pcbnew.VECTOR2I(bb.GetX() + bb.GetWidth() // 2, bb.GetBottom() - M(2.5)))
    b.Add(t)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
