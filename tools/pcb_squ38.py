#!/usr/bin/env kicadpython
"""SQU-38: the three geometry fixes Iris asked for in the PR #23 re-review (SQU-37).

Applied once on top of 1fd49cd. Freerouting needs Java 25, which is not in the
container, so the board cannot be rebuilt from `tools/pcb_build.py place/route` here;
these edits are coordinate-exact patches on the committed board instead. The same three
changes are also in the generator (`PLACE['J3']`, `preroute()`, `fix_tab_vias()` in
tools/pcb_build.py), so the next full rebuild reproduces them.

    kicadpython tools/pcb_squ38.py

1. J3 0.10 mm inward: mounting-tab copper 0.40 mm from the right edge (was 0.30 mm,
   inside JLCPCB's ±0.20 mm routing tolerance). The pin-1 silk triangle moves with it.
2. The +5V inlet from J1's VBUS pads to the LED trunk becomes 1.50 mm for its whole
   length (was 1.00 mm for 8.23 mm + a 0.56 mm turn). Only the two necks through the
   USB-C pin field stay at 0.60 mm, and they are in parallel.
3. The four M3 LDO tab vias go back to the reviewed 0.30 mm drill (0.60 mm pad); the
   router had re-emitted them at 0.40 mm on the DSN/SES round trip.

Structure note, as in tools/pcb_squ32.py: the pcbnew SWIG proxies stop down-casting once
items have been added to a loaded board, so work in strict phases -- read, mutate in
place, add, then fill and save. Do not interleave.
"""
import math, os, sys
import pcbnew
from pcbnew import FromMM as mm, ToMM as T, VECTOR2I

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'kicad/room-node/room-node.kicad_pcb')
F, B = pcbnew.F_Cu, pcbnew.B_Cu

J3_DX = -0.10                    # inward, away from the right board edge
RISER_X = 110.60                 # new +5V inlet: in line with the trunk corner
TRUNK_Y = 124.60
# The old inlet: 1.00 mm at x = 110.205, its 0.56 mm turn, the two 0.60 mm pad necks
# that fed it, and the 1.50 mm piece of riser it handed over to. All replaced below.
OLD_INLET = [((110.205, 111.375), (110.205, 115.625)),
             ((110.205, 115.625), (110.205, 119.600)),
             ((110.205, 119.600), (110.600, 120.000)),
             ((109.155, 111.375), (110.205, 111.375)),
             ((110.205, 115.625), (109.155, 115.625)),
             ((110.600, 120.000), (110.600, 124.600))]
# M3 tab vias: offsets from the SOT-223 tab pad centre -> reviewed drill.
TAB_VIA_DRILL = {(1.65, -1.2): 0.3, (1.65, 0.0): 0.4, (1.65, 1.2): 0.3,
                 (2.55, 1.2): 0.3, (3.75, 1.2): 0.3}

board = pcbnew.LoadBoard(PCB)
nets = board.GetNetInfo().NetsByName()
FPS = {fp.GetReference(): fp for fp in board.GetFootprints()}
TRACKS = list(board.GetTracks())
log = []


def near(a, b, tol=0.02):
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def ends(t):
    s, e = t.GetStart(), t.GetEnd()
    return (T(s.x), T(s.y)), (T(e.x), T(e.y))


# ========================================================== phase 1: read the board
j3 = FPS['J3']
j3_pos = (T(j3.GetPosition().x), T(j3.GetPosition().y))
tab = [p for p in FPS['U2'].Pads()
       if p.GetNumber() == '2' and p.GetSize().y > mm(2)][0].GetPosition()
tab_mm = (T(tab.x), T(tab.y))

doomed = []
for t in TRACKS:
    if t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() != '+5V' or t.GetLayer() != B:
        continue
    a, b = ends(t)
    for p, q in OLD_INLET:
        if (near(a, p) and near(b, q)) or (near(a, q) and near(b, p)):
            doomed.append(t)
            break
if len(doomed) != len(OLD_INLET):
    sys.exit('expected %d old inlet segments, found %d' % (len(OLD_INLET), len(doomed)))

tab_vias = {}
for t in TRACKS:
    if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != '+3V3':
        continue
    p = t.GetPosition()
    off = (round(T(p.x) - tab_mm[0], 3), round(T(p.y) - tab_mm[1], 3))
    for key, drill in TAB_VIA_DRILL.items():
        if near(off, key):
            tab_vias[key] = (t, drill)
if len(tab_vias) != len(TAB_VIA_DRILL):
    sys.exit('expected %d tab vias, found %d' % (len(TAB_VIA_DRILL), len(tab_vias)))

# The pin-1 triangle is the only filled F.SilkS polygon on the board (pin1_mark()).
tri = [d for d in board.GetDrawings()
       if d.GetLayer() == pcbnew.F_SilkS and d.GetShape() == pcbnew.SHAPE_T_POLY]
if len(tri) != 1:
    sys.exit('expected 1 filled silk polygon (J3 pin 1), found %d' % len(tri))

# ========================================================== phase 2: mutate in place
# item 1 -- J3 inward
j3.Move(VECTOR2I(mm(J3_DX), 0))
tri[0].Move(VECTOR2I(mm(J3_DX), 0))
log.append('J3 %.3f -> %.3f mm in x (pin-1 triangle moved with it)'
           % (j3_pos[0], j3_pos[0] + J3_DX))

# item 3 -- M3 tab via drills back to the reviewed geometry
for key in sorted(TAB_VIA_DRILL):
    t, drill = tab_vias[key]
    before = T(t.GetDrill())
    t.SetDrill(mm(drill))
    t.SetWidth(mm(0.6))
    log.append('tab via at offset (%+.2f, %+.2f): drill %.2f -> %.2f mm, pad 0.60 mm'
               % (key[0], key[1], before, drill))

# item 2 -- drop the 1.00 mm inlet
for t in doomed:
    a, b = ends(t)
    log.append('removed %.2f mm B.Cu +5V (%.3f, %.3f)-(%.3f, %.3f)'
               % (T(t.GetWidth()), a[0], a[1], b[0], b[1]))
    board.Remove(t)

# ========================================================== phase 3: add the new inlet
p5 = nets['+5V']
pads = {p.GetNumber(): p.GetPosition() for p in FPS['J1'].Pads() if p.GetNumber()}


def track(net, layer, pts, width):
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(a if isinstance(a, VECTOR2I) else VECTOR2I(mm(a[0]), mm(a[1])))
        t.SetEnd(b if isinstance(b, VECTOR2I) else VECTOR2I(mm(b[0]), mm(b[1])))
        t.SetLayer(layer)
        t.SetWidth(mm(width))
        t.SetNet(net)
        board.Add(t)


# Two 0.60 mm necks out of the pin field (all the 0.70 mm pads on a 0.85 mm pitch
# leave), then one 1.50 mm riser straight down to the trunk.
for ref in ('A4', 'A9'):
    track(p5, B, [pads[ref], VECTOR2I(mm(RISER_X), pads[ref].y)], 0.6)
    log.append('neck J1.%s -> (%.3f, %.3f) at 0.60 mm, %.3f mm long'
               % (ref, RISER_X, T(pads[ref].y), RISER_X - T(pads[ref].x)))
# Split at the lower neck so both necks meet the riser end to end, not mid-segment.
y_top, y_bot = T(pads['A4'].y), T(pads['A9'].y)
track(p5, B, [(RISER_X, y_top), (RISER_X, y_bot), (RISER_X, TRUNK_Y)], 1.5)
log.append('riser x = %.3f, y %.3f-%.3f at 1.50 mm (%.2f mm), necks join at y = %.3f/%.3f'
           % (RISER_X, y_top, TRUNK_Y, TRUNK_Y - y_top, y_top, y_bot))

# ========================================================== phase 4: fill and save
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.BuildConnectivity()
pcbnew.SaveBoard(PCB, board, True)

print('SQU-38 patch applied to %s' % os.path.relpath(PCB, ROOT))
for s in log:
    print('  ' + s)
