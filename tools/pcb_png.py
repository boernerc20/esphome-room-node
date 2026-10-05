#!/usr/bin/env kicadpython
"""Flat copper-layer pictures for reports/pcb (no SVG renderer in the container).

    kicadpython tools/pcb_png.py F.Cu reports/pcb/room-node-copper-top.png
    kicadpython tools/pcb_png.py B.Cu reports/pcb/room-node-copper-bottom.png
"""
import os, sys
import pcbnew
from pcbnew import ToMM as T
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'kicad/room-node/room-node.kicad_pcb')
LAYERS = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu,
          'In1.Cu': pcbnew.In1_Cu, 'In2.Cu': pcbnew.In2_Cu}
SCALE, PAD = 16, 20            # px per mm
COPPER, EDGE, VIA, BG = (200, 130, 40), (40, 200, 120), (235, 190, 90), (18, 20, 24)

layer = LAYERS[sys.argv[1]]
out = os.path.join(ROOT, sys.argv[2])
board = pcbnew.LoadBoard(PCB)
bb = board.GetBoardEdgesBoundingBox()
x0, y0 = T(bb.GetLeft()), T(bb.GetTop())
w = int((T(bb.GetRight()) - x0) * SCALE) + 2 * PAD
h = int((T(bb.GetBottom()) - y0) * SCALE) + 2 * PAD
img = Image.new('RGB', (w, h), BG)
d = ImageDraw.Draw(img)


def pt(v):
    return (PAD + (T(v.x) - x0) * SCALE, PAD + (T(v.y) - y0) * SCALE)


def poly(ps, fill):
    if len(ps) > 2:
        d.polygon(ps, fill=fill)


# filled zones on this layer
for z in board.Zones():
    if z.GetIsRuleArea() or not z.IsOnLayer(layer):
        continue
    sp = z.GetFilledPolysList(layer)
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i)
        poly([pt(o.CPoint(k)) for k in range(o.PointCount())], (90, 58, 18))
        for j in range(sp.HoleCount(i)):
            hh = sp.Hole(i, j)
            poly([pt(hh.CPoint(k)) for k in range(hh.PointCount())], BG)

for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    if t.GetLayer() != layer:
        continue
    d.line([pt(t.GetStart()), pt(t.GetEnd())], fill=COPPER,
           width=max(1, int(T(t.GetWidth()) * SCALE)), joint='curve')

for fp in board.GetFootprints():
    for p in fp.Pads():
        if not p.IsOnLayer(layer):
            continue
        sp = p.GetEffectivePolygon(layer)
        for i in range(sp.OutlineCount()):
            o = sp.Outline(i)
            poly([pt(o.CPoint(k)) for k in range(o.PointCount())], COPPER)

for t in board.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T:
        continue
    c, r = pt(t.GetPosition()), T(t.GetWidth(layer)) * SCALE / 2
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=VIA)
    r = T(t.GetDrill()) * SCALE / 2
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=BG)

for g in board.GetDrawings():
    if g.GetLayer() != pcbnew.Edge_Cuts:
        continue
    for a, b in zip(g.GetEffectiveShape().Outline(0).CPoints()
                    if False else [], []):
        pass
    if g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
        d.line([pt(g.GetStart()), pt(g.GetEnd())], fill=EDGE, width=2)
    else:
        sh = g.GetEffectiveShape()
        ps = [pt(p) for p in [g.GetStart(), g.GetArcMid(), g.GetEnd()]]
        d.line(ps, fill=EDGE, width=2)

img.save(out)
print('%s -> %s (%dx%d)' % (sys.argv[1], sys.argv[2], w, h))
