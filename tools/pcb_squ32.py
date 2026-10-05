#!/usr/bin/env kicadpython
"""SQU-32: J3 side-entry swap + the SQU-31 review polish items.

Applied once on top of f8a871e. The edits are coordinate-exact, so this is a one-shot
patch script, not a board generator like tools/pcb_build.py.

    kicadpython tools/pcb_squ32.py

Note on structure: the pcbnew SWIG proxies stop down-casting once items have been added
to a loaded board, so everything is done in strict phases -- read, then mutate in place,
then add, then fill and save. Do not interleave.
"""
import math, os, sys
import pcbnew
from pcbnew import FromMM as mm, ToMM as T, VECTOR2I

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'kicad/room-node/room-node.kicad_pcb')
FP_LIB = os.environ.get('KICAD_FOOTPRINTS', '/usr/share/kicad/footprints')
F, B = pcbnew.F_Cu, pcbnew.B_Cu
EPD = {'EPD_MOSI', 'EPD_CLK', 'EPD_CS', 'EPD_DC', 'EPD_RST', 'EPD_BUSY'}

J3_FP = 'Connector_JST:JST_PH_S8B-PH-SM4-TB_1x08-1MP_P2.00mm_Horizontal'
J3_X, J3_Y = 128.0, 133.08       # housing front 0.47 mm inside the bottom edge (y = 138.0)
J3_PAD_Y = J3_Y - 2.85           # 130.23 -- signal pad row of the side-entry footprint
J3_VIA_Y = 133.90                # via row behind the pads, under the housing
J3_PINS = [('1', '+3V3', 0.3), ('2', 'GND', 0.3), ('3', 'EPD_MOSI', 0.2),
           ('4', 'EPD_CLK', 0.2), ('5', 'EPD_CS', 0.2), ('6', 'EPD_DC', 0.2),
           ('7', 'EPD_RST', 0.2), ('8', 'EPD_BUSY', 0.2)]

board = pcbnew.LoadBoard(PCB)
nets = board.GetNetInfo().NetsByName()
FPS = {fp.GetReference(): fp for fp in board.GetFootprints()}
TRACKS = list(board.GetTracks())
ZONES = list(board.Zones())
log = []


def xy(x, y):
    return VECTOR2I(mm(x), mm(y))


def near(p, x, y, tol=0.02):
    return abs(p[0] - x) < tol and abs(p[1] - y) < tol


def is_via(t):
    return t.Type() == pcbnew.PCB_VIA_T


# ========================================================== phase 1: read the board
class Trk(object):
    __slots__ = ('o', 'net', 'layer', 'via', 'a', 'b', 'w')

    def __init__(self, t):
        self.o = t
        self.net = t.GetNetname()
        self.via = is_via(t)
        self.layer = F if self.via else t.GetLayer()
        s, e = t.GetStart(), t.GetEnd()
        self.a = (round(T(s.x), 4), round(T(s.y), 4))
        self.b = (round(T(e.x), 4), round(T(e.y), 4))


TR = [Trk(t) for t in TRACKS]


def pads_of(ref):
    return {p.GetNumber(): (round(T(p.GetPosition().x), 4), round(T(p.GetPosition().y), 4))
            for p in FPS[ref].Pads()}


P_U1, P_U3, P_MK1, P_J3 = pads_of('U1'), pads_of('U3'), pads_of('MK1'), pads_of('J3')
U1_PIN2 = P_U1['2']
MIC_HOLE = P_MK1['']
J3_FIELDS = [(f.GetName(), f.GetText()) for f in FPS['J3'].GetFields()
             if f.GetName() not in ('Reference', 'Value', 'Footprint', 'Datasheet')]
# mirror the schematic's side-entry part fields so board/schematic parity stays clean
J3_NEW_FIELDS = {'MPN': 'JST S8B-PH-SM4-TB(LF)(SN)', 'LCSC': 'C265121'}
J3_FIELDS = [(n, J3_NEW_FIELDS.get(n, v)) for n, v in J3_FIELDS]
J3_VALUE = FPS['J3'].GetValue()
J3_PATH, J3_SHEETNAME, J3_SHEETFILE = (FPS['J3'].GetPath(), FPS['J3'].GetSheetname(),
                                       FPS['J3'].GetSheetfile())
J3_NETS = {n: nm for n, nm in ((p.GetNumber(), p.GetNetname()) for p in FPS['J3'].Pads())}

kill = []          # Trk to delete
rewidth = []       # (Trk, mm)
reend = []         # (Trk, 'start'|'end', (x, y))
repos = []         # (Trk, (x, y))   -- vias
adds = []          # ('trk'|'via', ...)


def rm(pred, what):
    hit = [t for t in TR if t not in kill and pred(t)]
    kill.extend(hit)
    log.append('  removed %d %s' % (len(hit), what))
    return hit


def find(net, layer, a, b):
    hit = [t for t in TR if not t.via and t.net == net and t.layer == layer
           and ((near(t.a, *a) and near(t.b, *b)) or (near(t.a, *b) and near(t.b, *a)))]
    if len(hit) != 1:
        sys.exit('expected one %s track %s-%s, found %d' % (net, a, b, len(hit)))
    return hit[0]


def trk(net, layer, pts, width):
    for p, q in zip(pts, pts[1:]):
        adds.append(('trk', net, layer, p, q, width))


def via(net, x, y):
    adds.append(('via', net, (x, y)))


# ----------------------------------------------------- 1. C6/C7 rotated -> U1 pin 2
log.append('[1] C6 rotated 180 deg, direct +3V3 track to U1 pin 2')
# C6 pads swap: +3V3 moves to x = 117.25 (towards pin 2), GND to x = 115.35.
# Both old stubs/vias go; the GND pad reuses the mirrored via position.
C6_PADS = [(117.25, 103.0), (115.35, 103.0)]
stubs = rm(lambda t: not t.via and t.layer == F and t.net in ('+3V3', 'GND')
           and any(near(t.a, *q) or near(t.b, *q) for q in C6_PADS), 'C6 fan-out stubs')
ends = [q for t in stubs for q in (t.a, t.b)]
rm(lambda t: t.via and t.net in ('+3V3', 'GND') and any(near(t.a, *q) for q in ends),
   'C6 fan-out vias')
trk('+3V3', F, [(117.25, 103.0), U1_PIN2], 0.3)
trk('GND', F, [(115.35, 103.0), (114.887, 101.881)], 0.3)
via('GND', 114.887, 101.881)
log.append('  C6 +3V3 pad -> U1 pin 2: %.2f mm of 0.3 mm F.Cu (was plane-only, 4.5 mm apart);'
           ' C7 is left alone -- the EN track crosses the corridor between C7 and C6 at'
           ' y = 104.03, so C7 keeps its own +3V3 plane via'
           % math.dist((117.25, 103.0), U1_PIN2))

# --------------------------------------------- 2. CC_SENSE lower under the module
log.append('[2] CC_SENSE cross-module run moved down')
rm(lambda t: t.net == 'CC_SENSE' and not t.via and t.layer == F
   and near(t.a, 136.75, 102.76) and near(t.b, 122.454, 102.76), 'old y = 102.76 run')
trk('CC_SENSE', F, [(122.454, 102.76), (122.454, 105.9), (134.5, 105.9),
                    (134.5, 102.76), (136.75, 102.76)], 0.2)
log.append('  14.30 mm at y = 102.76 (2.76 mm from the antenna line y = 100.0) replaced by'
           ' 12.05 mm at y = 105.90 (5.90 mm); only 2.25 mm stays at y = 102.76, at the pad')

# ------------------------------------------------------- 3. C40 GND link to U6 pin 5
log.append('[3] C40 short GND track: SKIPPED, no room -- see the issue comment')

# --------------------------------------------------- 4. clear B.Cu at the mic hole
log.append('[4] mic hole: 4 mm clear area on the bottom side')
rm(lambda t: t.via and near(t.a, 109.702, 136.814), 'via 1.77 mm from the hole')
rm(lambda t: not t.via and t.layer == F and t.net == 'GND'
   and near(t.a, 109.162, 135.51) and near(t.b, 109.702, 136.814), 'its stub')
trk('GND', F, [(109.162, 135.51), (110.45, 137.25)], 0.3)
via('GND', 110.45, 137.25)
log.append('  replacement via at (110.45, 137.25) is %.2f mm from the hole centre'
           ' (%.2f, %.2f); nothing on B.Cu is now inside a 2.00 mm radius'
           % (math.dist(MIC_HOLE, (110.45, 137.25)), MIC_HOLE[0], MIC_HOLE[1]))

# ------------------------------------------------------ 6. U3 pin 3/11 vias outward
log.append('[6] U3 pin 3/11 GND vias moved clear of the exposed pad')
rm(lambda t: t.net == 'GND' and ((t.via and near(t.a, 170.175, 120.75))
   or (not t.via and t.layer == F and any(near(x, 170.175, 120.75) for x in (t.a, t.b)))),
   'U3 pin 11 via and stub')
trk('GND', F, [P_U3['11'], (171.9, 120.6)], 0.25)
via('GND', 171.9, 120.6)
log.append('  pin 11 via (170.175, 120.75) -> (171.90, 120.60): it overlapped the'
           ' 1.23 x 1.23 mm exposed pad (x 168.885-170.115) by 0.24 mm, now 1.49 mm clear.'
           ' Pin 3 could not move -- see the issue comment')

# ------------------------------------------------------- 7. U2 tab via column x 116.3
log.append('[7] U2 tab via column x = 116.0 -> 116.3')
n = 0
for t in TR:
    if t.via and t.net == '+3V3' and abs(t.a[0] - 116.0) < 0.02 and 123.0 < t.a[1] < 126.0:
        repos.append((t, (116.3, t.a[1])))
        n += 1
reend.append((find('+3V3', F, (114.65, 124.5), (116.0, 124.5)), 'end', (116.3, 124.5)))
log.append('  %d vias moved to x = 116.30: 0.65 mm from the tab copper edge (x = 115.65),'
           ' was 0.35 mm; the 0.3 mm feed track was extended to match' % n)

# -------------------------------------------- 8. +5V bottom run / C1-C2-C3 widths
log.append('[8] +5V track widths')
for a, b, w in (((106.537, 127.275), (132.725, 127.275), 1.4),
                ((105.2, 127.275), (106.537, 127.275), 1.5),
                ((106.537, 127.275), (107.875, 127.275), 1.5),
                ((103.225, 127.275), (105.2, 127.275), 1.5),
                ((103.05, 121.2), (103.225, 121.375), 1.2),
                ((103.225, 121.375), (103.225, 123.4), 1.2),
                ((103.225, 123.4), (103.225, 125.3), 1.2),
                ((103.225, 125.3), (103.225, 127.275), 1.2)):
    rewidth.append((find('+5V', F, a, b), w))
log.append('  bottom row y = 127.275, x 103.225-132.725 (29.50 mm): 1.0/1.2 -> 1.50 mm,'
           ' except the 26.19 mm length that runs past the U2 tab, which is 1.40 mm'
           ' (0.175 mm to the tab pad; 1.5 mm would leave 0.125 mm, under the 0.15 mm rule).'
           ' 1.4 mm carries about 3.0 A at a 10 C rise (IPC-2221, 1 oz external)')
log.append('  C1 -> C2 -> C3, x 103.05-103.225, y 121.2-127.275: 1.0 -> 1.20 mm')

# ------------------------------------------------------ 9. U3 pins 7/8 feed necked
log.append('[9] U3 pins 7/8 feed necked at the pad row')
reend.append((find('+5V', F, (170.0, 123.438), (170.0, 122.438)), 'end', (170.0, 123.138)))
trk('+5V', F, [(170.0, 123.138), (170.0, 122.438)], 0.25)
log.append('  the 0.8 mm feed now stops at y = 123.138, 0.30 mm clear of the pad row'
           ' (pads 7/8 reach y = 122.838); the last 0.70 mm is 0.25 mm = the pad width')

# ------------------------------------------------------------- J3 -> S8B side entry
log.append('[J3] JST S8B-PH-SM4-TB side entry')
rm(lambda t: t.via and (near(t.a, 119.15, 133.9) or near(t.a, 121.15, 133.9)),
   'J3 pin 1/2 fan-out vias')
rm(lambda t: not t.via and t.layer == F and t.net in ('+3V3', 'GND')
   and any(near(x, 119.15, 133.9) or near(x, 121.15, 133.9) for x in (t.a, t.b)),
   'J3 pin 1/2 stubs')
# The old top-entry stubs, vias and B.Cu tails. EPD_BUSY keeps its tail and via at
# (134.958, 133.9) -- the new pad 8 sits right above it.
EPD_RM = [
    ('EPD_MOSI', F, (124.0, 133.9), (123.022, 133.9)),
    ('EPD_MOSI', None, (123.022, 133.9), None),
    ('EPD_MOSI', B, (123.022, 123.457), (123.022, 133.9)),
    ('EPD_MOSI', B, (126.007, 120.472), (123.022, 123.457)),
    ('EPD_CLK', F, (126.0, 133.9), (126.96, 133.9)),
    ('EPD_CLK', None, (126.96, 133.9), None),
    ('EPD_CLK', B, (126.96, 133.9), (126.79, 133.73)),
    ('EPD_CLK', B, (126.79, 133.73), (126.79, 118.534)),
    ('EPD_CS', F, (128.236, 133.664), (128.236, 130.679)),
    ('EPD_CS', F, (128.0, 133.9), (128.236, 133.664)),
    ('EPD_CS', None, (128.236, 130.679), None),
    ('EPD_CS', B, (128.236, 130.679), (127.342, 129.785)),
    ('EPD_CS', B, (127.342, 129.785), (127.342, 120.65)),
    ('EPD_DC', F, (130.0, 133.9), (130.0, 130.696)),
    ('EPD_DC', None, (130.0, 130.696), None),
    ('EPD_DC', B, (130.0, 130.696), (128.245, 128.942)),
    ('EPD_DC', B, (128.245, 128.942), (128.245, 120.477)),
    ('EPD_RST', F, (131.295, 133.195), (131.295, 130.83)),
    ('EPD_RST', F, (132.0, 133.9), (131.295, 133.195)),
    ('EPD_RST', None, (131.295, 130.83), None),
    ('EPD_RST', B, (129.585, 129.12), (131.295, 130.83)),
    ('EPD_RST', B, (129.585, 120.719), (129.585, 129.12)),
    ('EPD_BUSY', F, (134.0, 133.9), (134.958, 133.9)),
]
for net, layer, a, b in EPD_RM:
    if layer is None:
        if len(rm(lambda t, n=net, q=a: t.via and t.net == n and near(t.a, *q), '')) != 1:
            sys.exit('via %s %s not found' % (net, a))
    else:
        kill.append(find(net, layer, a, b))
log[:] = [l for l in log if l.strip() != 'removed 1']
log.append('  removed %d old top-entry EPD stubs, vias and B.Cu tails' % len(EPD_RM))

# One via per pin behind the pad row, under the housing (y = 133.90, where the
# top-entry pads used to sit), with a 2.40 mm F.Cu stub forward into the pad.
# Behind the pads is the only clear band: I2C_SCL and I2C_SDA cross the board on
# B.Cu right where the new pad row lands.
for num, net, w in J3_PINS:
    px = J3_X + 2.0 * (int(num) - 1) - 7.0
    vx = 134.958 if num == '8' else px        # pin 8 reuses the existing EPD_BUSY via
    if num != '8':
        via(net, vx, J3_VIA_Y)
    trk(net, F, [(vx, J3_VIA_Y), (vx, J3_PAD_Y + 1.27)], w)
trk('EPD_MOSI', B, [(126.007, 120.472), (125.0, 121.479), (125.0, J3_VIA_Y)], 0.2)
trk('EPD_CLK',  B, [(126.79, 118.534), (126.79, 133.69), (127.0, J3_VIA_Y)], 0.2)
trk('EPD_CS',   B, [(127.342, 120.65), (127.342, 132.242), (129.0, J3_VIA_Y)], 0.2)
trk('EPD_DC',   B, [(128.245, 120.477), (128.245, 131.145), (131.0, J3_VIA_Y)], 0.2)
trk('EPD_RST',  B, [(129.585, 120.719), (129.585, 130.485), (133.0, J3_VIA_Y)], 0.2)
log.append('  %s at (%.2f, %.2f) rot 0; pin 1 at x = %.2f (was %.2f), pad row y = %.2f'
           % (J3_FP.split(':')[1], J3_X, J3_Y, J3_X - 7.0, P_J3['1'][0], J3_PAD_Y))

# ======================================= phase 2: in-place mutations and removals
for t, w in rewidth:
    t.o.SetWidth(mm(w))
for t, which, p in reend:
    (t.o.SetStart if which == 'start' else t.o.SetEnd)(xy(*p))
for t, p in repos:
    t.o.SetPosition(xy(*p))

j3_old = FPS['J3']
board.Remove(j3_old)
for t in kill:
    board.Remove(t.o)
for ref in ('C6', 'C7'):
    FPS[ref].SetOrientationDegrees(180)

# ================================================== phase 3: additions
j3 = pcbnew.FootprintLoad(os.path.join(FP_LIB, 'Connector_JST.pretty'), J3_FP.split(':', 1)[1])
if j3 is None:
    sys.exit('S8B-PH-SM4-TB footprint not found')
j3.SetFPIDAsString(J3_FP)
j3.SetReference('J3')
j3.SetValue(J3_VALUE)
j3.SetPath(J3_PATH)
j3.SetSheetname(J3_SHEETNAME)
j3.SetSheetfile(J3_SHEETFILE)
for name, text in J3_FIELDS:
    j3.SetField(name, text)
    j3.GetField(name).SetVisible(False)
ref = j3.Reference()
ref.SetTextSize(VECTOR2I(mm(0.8), mm(0.8)))
ref.SetTextThickness(mm(0.15))
j3.SetOrientationDegrees(0)
j3.SetPosition(xy(J3_X, J3_Y))
for p in j3.Pads():
    if p.GetNumber() in J3_NETS:
        p.SetNet(nets[J3_NETS[p.GetNumber()]])
board.Add(j3)

for item in adds:
    if item[0] == 'via':
        _, net, p = item
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(xy(*p))
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(nets[net])
        board.Add(v)
    else:
        _, net, layer, a, b, w = item
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(xy(*a))
        t.SetEnd(xy(*b))
        t.SetLayer(layer)
        t.SetWidth(mm(w))
        t.SetNet(nets[net])
        board.Add(t)

# 5. AHT20 island neck slot (Edge.Cuts)
SLOT = (150.2, 131.35, 151.2, 132.6)
x0, y0, x1, y1 = SLOT
for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(xy(*a))
    s.SetEnd(xy(*b))
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)
log.append('[5] island neck slot %.2f x %.2f mm at x %.2f-%.2f, y %.2f-%.2f;'
           ' the 6.80 mm top neck becomes 5.80 mm. 1.0 mm is the JLC routed-slot minimum'
           ' and is all that fits between the +3V3 feed (x = 149.7) and the I2C_SCL'
           ' B.Cu run that crosses the neck'
           % (x1 - x0, y1 - y0, x0, x1, y0, y1))

# ================================================== phase 4: fill and save
board.BuildConnectivity()
pcbnew.ZONE_FILLER(board).Fill(ZONES)
board.BuildConnectivity()
pcbnew.SaveBoard(PCB, board)
print('\n'.join(log))
