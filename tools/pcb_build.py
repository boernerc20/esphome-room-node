#!/usr/bin/env kicadpython
"""Rev A board build: outline, holes, parts, nets, planes, placement, routing import.

The board mounts behind the Waveshare 2.9" e-paper module (89.5 x 38 mm, 4 x M2 holes
2.5 mm in from each corner). Same outline and hole pattern, M2 standoffs between them.

Usage (from the repo root):
    kicadpython tools/pcb_build.py place  out.dsn   # new board + placement + planes, export DSN
    (route out.dsn with Freerouting -> out.ses)
    kicadpython tools/pcb_build.py route  out.ses   # import routes, GND fills, stitching, fill

`place` overwrites kicad/room-node/room-node.kicad_pcb (all layout work is lost).
Footprints are linked to their schematic symbols, so F8 later updates them in place.
"""
import math, os, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
import pcbnew
from pcbnew import FromMM as mm, VECTOR2I

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRJ = os.path.join(ROOT, 'kicad/room-node')
SCH = os.path.join(PRJ, 'room-node.kicad_sch')
PCB = os.path.join(PRJ, 'room-node.kicad_pcb')
LIBS = {'room-node': os.path.join(PRJ, 'lib/footprints/room-node.pretty')}
STOCK = os.environ.get('KICAD_FOOTPRINTS', '/usr/share/kicad/footprints')

# Board = Waveshare 2.9" e-paper module outline (Waveshare drawing, 89.50 x 38.00 mm).
X0, Y0, W, H = 100.0, 100.0, 89.5, 38.0
X1, Y1 = X0 + W, Y0 + H
CORNER_R = 1.0
HOLE_INSET = 2.5          # hole centres 2.5 mm from each edge -> 84.5 x 33.0 mm pattern

# U1 antenna overhangs the top edge (board edge at the antenna / pad boundary).
# ref -> (x, y, rotation deg)
PLACE = {
    # MCU (centre-left, antenna over the top edge)
    'U1': (128.0, Y0 + 6.75, 0),
    'C6': (116.3, 103.0, 0), 'C7': (116.3, 105.2, 0),          # +3V3 pin 2
    'R3': (116.3, 107.4, 0), 'C8': (116.3, 109.6, 0),          # EN pin 3
    'R9': (113.8, 103.4, 90), 'R10': (112.1, 103.4, 90),      # mic BCLK / WS, at U1
    # USB-C, ESD, CC (left edge)
    'J1': None,
    'U5': (114.5, 113.5, 90),
    'R1': (110.6, 105.0, 90), 'R2': (108.8, 105.0, 90),
    'R6': (112.2, 108.0, 90), 'R7': (114.0, 108.0, 90),
    'C1': (104.0, 121.2, 0), 'C2': (104.0, 123.4, 0),
    # LDO (left, below USB)
    'U2': (111.5, 124.5, 0),
    'C3': (105.2, 126.5, 90), 'C4': (117.0, 122.8, 90), 'C5': (118.9, 123.0, 90),
    # Microphone (bottom-left corner, sound hole through the board)
    'MK1': (108.5, 134.8, 0),
    'C10': (111.0, 132.2, 90), 'C11': (112.8, 132.2, 90),
    'R11': (111.8, 136.0, 0), 'R8': (115.0, 136.0, 0),
    # Display connector under U1, bottom edge
    'J3': (127.0, 133.4, 0), 'C50': (115.0, 131.5, 90),
    # Test pads between U1 and J3
    'TP1': (121.5, 124.5, 0), 'TP2': (124.3, 124.5, 0), 'TP3': (127.1, 124.5, 0),
    'TP4': (129.9, 124.5, 0), 'TP5': (132.7, 124.5, 0), 'TP6': (135.5, 124.5, 0),
    'TP7': (138.3, 124.5, 0),
    'R30': (135.0, 121.6, 0),                                  # LED data, near U1 pin 23
    # Right of U1: CC sense, BOOT/RESET buttons, pull-ups, status LED
    'C9': (141.2, 102.6, 0), 'TP8': (144.6, 102.6, 0),
    'SW2': (151.0, 106.0, 0), 'SW1': (151.0, 113.4, 0),
    'R4': (142.0, 107.0, 90),
    'R12': (142.0, 111.6, 90), 'D1': (143.0, 128.6, 0),
    # Sensor island (bottom edge, slots on three sides)
    'U6': (152.6, 135.0, 0), 'C40': (149.7, 135.0, 270), 'R40': (157.6, 132.0, 90), 'R41': (159.4, 132.0, 90),
    # LED ring connector + bulk cap (top-right)
    'J4': (172.0, 104.0, 0), 'C30': (178.0, 113.5, 0),
    # Amplifier + speaker (bottom-right)
    'U3': (169.5, 121.0, 0),
    'C21': (165.2, 119.6, 90), 'C22': (165.2, 123.4, 0), 'R20': (166.0, 125.6, 0),
    'C20': (166.4, 132.6, 0),
    'J2': (179.2, 133.0, 0),
}

# AHT20 island: slots (Edge.Cuts) left and right, open at the top for the 4 tracks.
# No copper pour inside, so board heat does not reach the sensor.
ISLAND = (148.6, 130.6, 155.4, Y1)      # x0, y0, x1, y1
SLOT_W = 1.0
SLOTS = [(ISLAND[0] - SLOT_W, ISLAND[1] + 2.0, ISLAND[0], ISLAND[3] - 1.2),   # left
         (ISLAND[2], ISLAND[1] + 2.0, ISLAND[2] + SLOT_W, ISLAND[3] - 1.2)]   # right

# In1.Cu (L2) solid GND, In2.Cu (L3) solid +3V3. +5V is a wide track (0.8 mm) from J1
# to the LDO, the amp and the LED connector.

STITCH_PITCH = 5.0
STITCH_INSET = 1.0


def netlist():
    out = os.path.join(tempfile.mkdtemp(), 'room-node.xml')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml',
                    '-o', out, SCH], check=True, capture_output=True)
    return ET.parse(out).getroot()


def load_fp(fpid):
    lib, name = fpid.split(':', 1)
    path = LIBS.get(lib, os.path.join(STOCK, lib + '.pretty'))
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        sys.exit('footprint not found: ' + fpid)
    fp.SetFPIDAsString(fpid)
    return fp


def courtyard_box(fp):
    sh = fp.GetCourtyard(pcbnew.F_CrtYd)
    return sh.BBox() if sh.OutlineCount() else fp.GetBoundingBox(False)


def line(board, a, b, layer=pcbnew.Edge_Cuts, width=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(VECTOR2I(mm(a[0]), mm(a[1])))
    s.SetEnd(VECTOR2I(mm(b[0]), mm(b[1])))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)


def arc(board, center, start, angle_deg):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(VECTOR2I(mm(center[0]), mm(center[1])))
    s.SetStart(VECTOR2I(mm(start[0]), mm(start[1])))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle_deg, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts)
    s.SetWidth(mm(0.1))
    board.Add(s)


def outline(board):
    r = CORNER_R
    line(board, (X0 + r, Y0), (X1 - r, Y0))
    line(board, (X1, Y0 + r), (X1, Y1 - r))
    line(board, (X1 - r, Y1), (X0 + r, Y1))
    line(board, (X0, Y1 - r), (X0, Y0 + r))
    arc(board, (X1 - r, Y0 + r), (X1 - r, Y0), 90)
    arc(board, (X1 - r, Y1 - r), (X1, Y1 - r), 90)
    arc(board, (X0 + r, Y1 - r), (X0 + r, Y1), 90)
    arc(board, (X0 + r, Y0 + r), (X0, Y0 + r), 90)


def slot(board, xa, ya, xb, yb):
    """Closed rectangular cut-out on Edge.Cuts (routed slot)."""
    pts = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
    for i in range(4):
        line(board, pts[i], pts[(i + 1) % 4])


def zone(board, net, layer, pts, priority, name):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetZoneName(name)
    z.SetAssignedPriority(priority)
    z.SetMinThickness(mm(0.2))
    z.SetLocalClearance(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(mm(x), mm(y))
    board.Add(z)
    return z


def keepout(board, pts, name, tracks=False, vias=True):
    """Rule area on all copper layers: no pours; optionally no tracks / vias."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(not tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(mm(x), mm(y))
    board.Add(z)


def place(dsn):
    root = netlist()
    board = pcbnew.NewBoard(PCB)

    # Stack-up: JLC04161H-7628, 1.6 mm. L2 GND plane, L3 power.
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)   # planes only, no signal tracks

    outline(board)
    ix0, iy0, ix1, iy1 = ISLAND
    s = SLOT_W
    for sl in SLOTS:
        slot(board, *sl)

    nets = {}
    for n in root.find('nets'):
        name = n.get('name')
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni
    pin_net = {}
    for n in root.find('nets'):
        for nd in n.findall('node'):
            pin_net[(nd.get('ref'), nd.get('pin'))] = nets.get(n.get('name'))

    for c in root.find('components'):
        ref = c.get('ref')
        fp = load_fp(c.findtext('footprint'))
        fp.SetReference(ref)
        fp.SetValue(c.findtext('value'))
        sp = c.find('sheetpath')
        fp.SetPath(pcbnew.KIID_PATH(sp.get('tstamps') + c.findtext('tstamps')))
        fp.SetSheetname(sp.get('names'))
        sf = c.find('property[@name="Sheetfile"]')
        fp.SetSheetfile(sf.get('value') if sf is not None else '')
        for fl in c.find('fields'):
            if fl.get('name') != 'Footprint':
                fp.SetField(fl.get('name'), fl.text or '')
                fp.GetField(fl.get('name')).SetVisible(False)
        fp.SetDNP(c.find('property[@name="dnp"]') is not None)
        fp.SetExcludedFromBOM(False)
        board.Add(fp)
        for pad in fp.Pads():
            ni = pin_net.get((ref, pad.GetNumber()))
            if ni is not None:
                pad.SetNet(ni)
        if ref not in PLACE:
            sys.exit('no placement for ' + ref)
        if PLACE[ref]:
            x, y, rot = PLACE[ref]
            fp.SetOrientationDegrees(rot)
            fp.SetPosition(VECTOR2I(mm(x), mm(y)))
        # Small, readable reference text
        rf = fp.Reference()
        rf.SetTextSize(VECTOR2I(mm(0.8), mm(0.8)))
        rf.SetTextThickness(mm(0.15))

    # J1 GND pins: solid to the pours (thermal spokes are blocked by the VBUS loop)
    for p in board.FindFootprintByReference('J1').Pads():
        if p.GetNetname() == 'GND':
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # USB-C: opening faces left, front of the courtyard flush with the left edge.
    j1 = board.FindFootprintByReference('J1')
    j1.SetOrientationDegrees(270)
    j1.SetPosition(VECTOR2I(0, 0))
    bb = courtyard_box(j1)
    j1.SetPosition(VECTOR2I(mm(X0) - bb.GetLeft(), mm(113.5) - bb.GetCenter().y))

    # Mounting holes: M2, on the e-paper module's hole pattern. Board-only.
    for i, (x, y) in enumerate([(X0 + HOLE_INSET, Y0 + HOLE_INSET), (X1 - HOLE_INSET, Y0 + HOLE_INSET),
                                (X0 + HOLE_INSET, Y1 - HOLE_INSET), (X1 - HOLE_INSET, Y1 - HOLE_INSET)], 1):
        h = load_fp('MountingHole:MountingHole_2.2mm_M2')
        h.SetReference('H%d' % i)
        h.SetValue('M2')
        h.SetBoardOnly(True)
        h.SetPosition(VECTOR2I(mm(x), mm(y)))
        board.Add(h)

    # Planes on the inner layers (used by the router as plane nets)
    full = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    zone(board, nets['GND'], pcbnew.In1_Cu, full, 0, 'GND plane L2')
    zone(board, nets['+3V3'], pcbnew.In2_Cu, full, 0, '+3V3 plane L3')

    # Slots: no copper within 0.35 mm (edge clearance 0.3 mm)
    m = 0.35
    for xa, ya, xb, yb in SLOTS:
        keepout(board, [(xa - m, ya - m), (xb + m, ya - m), (xb + m, yb + m), (xa - m, yb + m)], 'slot')
    # Sensor island: no pours, no vias (tracks allowed)
    keepout(board, [(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)], 'AHT20 island', tracks=True)
    # Mic sound hole: nothing on any layer inside the GND ring except the mic pads
    mk = board.FindFootprintByReference('MK1')
    hole = [p for p in mk.Pads() if p.GetNumber() == ''][0].GetPosition()
    r = 0.4
    keepout(board, [(hole.x / 1e6 + r * math.cos(a * math.pi / 8), hole.y / 1e6 + r * math.sin(a * math.pi / 8))
                    for a in range(16)], 'MK1 sound hole', tracks=False)

    prerouted = preroute(board, nets)
    nfan, missed = fanout(board, nets)
    print('pre-routed %d tracks; fan-out vias: %d; pads without via: %s'
          % (prerouted, nfan, ', '.join(missed) or 'none'))

    board.BuildConnectivity()
    pcbnew.SaveBoard(PCB, board, True)
    board = pcbnew.LoadBoard(PCB)
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        sys.exit('DSN export failed')
    router_rules(dsn)
    print('saved %s: %d footprints, %d nets; DSN -> %s'
          % (os.path.relpath(PCB, ROOT), len(board.GetFootprints()), len(nets), dsn))


def track(board, net, layer, pts, width):
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(VECTOR2I(mm(a[0]), mm(a[1])) if isinstance(a[0], float) else a)
        t.SetEnd(VECTOR2I(mm(b[0]), mm(b[1])) if isinstance(b[0], float) else b)
        t.SetLayer(layer)
        t.SetWidth(mm(width))
        t.SetNet(net)
        board.Add(t)
    return len(pts) - 1


def via(board, net, pos, w=0.6, d=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pos)
    v.SetWidth(mm(w))
    v.SetDrill(mm(d))
    v.SetNet(net)
    board.Add(v)
    return v


def preroute(board, nets):
    """Hand routes the router cannot do."""
    def pads(ref):
        return {p.GetNumber(): p.GetPosition() for p in board.FindFootprintByReference(ref).Pads()}

    def at(pt, dx=0.0, dy=0.0):
        return VECTOR2I(pt.x + mm(dx), pt.y + mm(dy))

    def xy(x, y):
        return VECTOR2I(mm(x), mm(y))

    F = pcbnew.F_Cu
    # J1: VBUS pins tied together around the A row (B.Cu)
    pad = pads('J1')
    p5 = nets['+5V']
    xo = pad['A4'].x + mm(1.05)
    n = track(board, p5, pcbnew.B_Cu, [pad['B9'], pad['A4'], VECTOR2I(xo, pad['A4'].y),
                                       VECTOR2I(xo, pad['A9'].y), pad['A9'], pad['B4']], 0.5)
    # U3 (0.5 mm pitch): VDD pins 7+8 joined, short stubs out of the pin rows
    u = pads('U3')
    mid = VECTOR2I((u['7'].x + u['8'].x) // 2, u['7'].y)
    n += track(board, p5, F, [u['7'], u['8']], 0.25)
    n += track(board, p5, F, [mid, at(mid, dy=1.0)], 0.4)
    n += track(board, p5, F, [u['2'], at(u['2'], dx=-0.9)], 0.25)
    # Speaker pair U3 -> J2, side by side (0.25 mm out of the pins, then 0.4 mm)
    j = pads('J2')
    a, b = u['9'], at(u['9'], dx=1.0)
    c1 = at(b, 0.7, 0.7)
    c2 = VECTOR2I(j['1'].x, c1.y + (j['1'].x - c1.x))
    net = nets['Net-(J2-Pin_1)']
    n += track(board, net, F, [a, b, c1], 0.25)
    n += track(board, net, F, [c1, c2, j['1']], 0.4)
    a, b = u['10'], at(u['10'], dx=2.1)
    c2 = VECTOR2I(j['2'].x, b.y + (j['2'].x - b.x))
    net = nets['Net-(J2-Pin_2)']
    n += track(board, net, F, [a, b], 0.25)
    n += track(board, net, F, [b, c2, j['2']], 0.4)
    # AHT20 island: 4 tracks out through the open top, plane vias just outside
    s6, c = pads('U6'), pads('C40')
    top = ISLAND[1] - 1.0
    vdd, gnd = nets['+3V3'], nets['GND']
    x_v = s6['2'].x - mm(0.9)
    n += track(board, vdd, F, [s6['2'], VECTOR2I(x_v, s6['2'].y), VECTOR2I(x_v, c['1'].y), c['1']], 0.25)
    n += track(board, vdd, F, [c['1'], VECTOR2I(c['1'].x, mm(top))], 0.3)
    via(board, vdd, VECTOR2I(c['1'].x, mm(top)))
    yb = c['2'].y + mm(1.1)
    x_g = s6['5'].x + mm(0.9)
    n += track(board, gnd, F, [c['2'], VECTOR2I(c['2'].x, yb), VECTOR2I(x_g, yb), VECTOR2I(x_g, s6['5'].y), s6['5']], 0.25)
    n += track(board, gnd, F, [VECTOR2I(x_g, s6['5'].y), VECTOR2I(x_g, mm(top))], 0.3)
    via(board, gnd, VECTOR2I(x_g, mm(top)))
    xm = (s6['3'].x + s6['4'].x) // 2
    for net, pin, dx in (('I2C_SCL', '3', -0.25), ('I2C_SDA', '4', 0.25)):
        x = xm + mm(dx)
        end = VECTOR2I(x + mm(3 * dx), mm(top))
        n += track(board, nets[net], F, [s6[pin], VECTOR2I(x, s6[pin].y),
                                         VECTOR2I(x, mm(top + 0.75)), end], 0.2)
        via(board, nets[net], end)
    return n


def fanout(board, nets):
    """One via per SMD GND / +3V3 pad, on a short stub, so every pad reaches its plane
    (L2 GND, L3 +3V3). The router then only routes signals and +5V."""
    plane = {'GND', '+3V3'}
    vr = mm(0.3)
    clr = mm(0.2)
    u1 = board.FindFootprintByReference('U1').GetCourtyard(pcbnew.F_CrtYd)
    edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    rules = [z for z in board.Zones() if z.GetIsRuleArea()]
    count, missed = 0, []

    def other_pads(net):
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() != net or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    yield p

    allpads = [p for fp in board.GetFootprints() for p in fp.Pads()]

    def ok(netname, own, a, b):
        circ = pcbnew.SHAPE_CIRCLE(b, vr)
        seg = pcbnew.SHAPE_SEGMENT(a, b, mm(0.3))
        if u1.Contains(b) and own.GetParentFootprint().GetReference() != 'U1':
            return False
        for p in allpads:
            if p.GetNetname() == netname and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                continue
            for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                if not p.IsOnLayer(lay) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    continue
                sh = p.GetEffectiveShape(lay)
                if sh.Collide(circ, clr) or (lay == pcbnew.F_Cu and sh.Collide(seg, clr)):
                    return False
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and \
               p.GetEffectiveShape(pcbnew.F_Cu).Collide(circ, mm(0.4)):
                return False
        for t in board.GetTracks():
            if t.GetNetname() == netname and t.Type() != pcbnew.PCB_VIA_T:
                continue
            gap = mm(0.25) if t.GetNetname() == netname else clr
            lay = t.GetLayer() if t.Type() != pcbnew.PCB_VIA_T else pcbnew.F_Cu
            if t.GetEffectiveShape(lay).Collide(circ, gap):
                return False
            if t.GetNetname() != netname and t.Type() != pcbnew.PCB_VIA_T and lay == pcbnew.F_Cu \
               and t.GetEffectiveShape(lay).Collide(seg, clr):
                return False
        for e in edges:
            if e.GetEffectiveShape().Collide(circ, mm(0.35)):
                return False
        for z in rules:
            if z.GetDoNotAllowVias() and z.Outline().Collide(b, vr):
                return False
        return True

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        c = fp.GetPosition()
        for p in fp.Pads():
            name = p.GetNetname()
            if name not in plane or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not p.GetNumber():
                continue
            if ref == 'U6':
                continue                       # sensor island: no vias
            q = p.GetPosition()
            net = nets[name]
            # Thermal pads: U1's footprint has its own vias; U3 gets one in the pad (tented)
            if ref == 'U1' and p.GetNumber() == '41':
                continue
            # LDO tab: 3 extra vias in the pad carry heat into the L3 +3V3 plane
            if ref == 'U2' and p.GetNumber() == '2' and p.GetSize().y > mm(2):     # the 2.0 x 3.8 mm tab
                for dy in (-1.0, 0.0, 1.0):
                    via(board, net, VECTOR2I(q.x, q.y + mm(dy)))
                    count += 1
            if ref == 'U3' and p.GetNumber() == '17':
                via(board, net, fp.GetPosition())
                count += 1
                continue
            bb = p.GetBoundingBox()
            out = (q.x - c.x, q.y - c.y)
            dirs = []
            for k in range(16):
                ang = k * math.pi / 8
                d = (math.cos(ang), math.sin(ang))
                dirs.append((-(d[0] * out[0] + d[1] * out[1]), k, d))
            dirs.sort()
            placed = False
            for extra in (0.05, 0.3, 0.6, 1.0, 1.5):
                for _, _, d in dirs:
                    half = abs(d[0]) * bb.GetWidth() / 2 + abs(d[1]) * bb.GetHeight() / 2
                    r = half + vr + mm(extra)
                    b = VECTOR2I(int(q.x + d[0] * r), int(q.y + d[1] * r))
                    if ok(name, p, q, b):
                        track(board, net, pcbnew.F_Cu, [q, b], 0.3)
                        via(board, net, b)
                        count += 1
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                missed.append('%s.%s' % (ref, p.GetNumber()))
    return count, missed


def router_rules(dsn):
    """Router-only track widths. Power nets reach the L2/L3 planes through short stubs
    and vias, so 0.3 mm is enough there; 0.6 mm does not fit the 0.5 mm-pitch amp pins.
    The speaker pair also leaves U3 at 0.3 mm."""
    import re
    t = open(dsn).read()

    def sub(cls, width, clr, via):
        nonlocal t
        pat = r'(\(class %s,Default .*?\(use_via ")[^"]+("\)[\s)]*\(rule\s*\(width )\d+(\)\s*\(clearance )\d+' % cls
        t, n = re.subn(pat, r'\g<1>%s\g<2>%d\g<3>%d' % (via, width, clr), t, flags=re.S)
        if n != 1:
            sys.exit('router rule not found for class ' + cls)

    sub('Power', 300, 150, 'Via[0-3]_600:300_um')
    sub('Audio', 300, 200, 'Via[0-3]_800:400_um')
    # +5V gets its own class: routed at 0.6 mm (the amp pins have hand-made stubs), 0.8/0.4 vias.
    # route() then widens every +5V segment that has room (up to 1.0 mm).
    t, n = re.subn(r'(\(class Power,Default [^\n(]*?) \+5V', r'\1', t)
    if n != 1:
        sys.exit('+5V not in Power class')
    t = t.replace('    (class Power,Default',
                  '    (class P5V +5V\n      (circuit\n        (use_via "Via[0-3]_800:400_um")\n      )\n'
                  '      (rule\n        (width 600)\n        (clearance 150)\n      )\n    )\n    (class Power,Default', 1)
    open(dsn, 'w').write(t)


def route(ses):
    board = pcbnew.LoadBoard(PCB)
    if not pcbnew.ImportSpecctraSES(board, ses):
        sys.exit('SES import failed')
    nets = board.GetNetInfo().NetsByName()
    gnd = nets['GND']

    widened = widen(board, {'+5V': (1.0, 0.8, 0.6, 0.5),
                            'Net-(J2-Pin_1)': (0.5, 0.4), 'Net-(J2-Pin_2)': (0.5, 0.4)})
    print('widened %d segments' % widened)

    full = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    zone(board, gnd, pcbnew.F_Cu, full, 0, 'GND fill L1')
    zone(board, gnd, pcbnew.B_Cu, full, 0, 'GND fill L4')

    # GND stitching: edge ring plus a 5 mm grid, wherever a via fits.
    board.BuildConnectivity()
    ds = board.GetDesignSettings()
    vw, vd = mm(0.6), mm(0.3)
    pts = []
    t = X0 + 4.0
    while t <= X1 - 4.0:
        pts += [(t, Y0 + STITCH_INSET), (t, Y1 - STITCH_INSET)]
        t += STITCH_PITCH
    t = Y0 + 4.0
    while t <= Y1 - 4.0:
        pts += [(X0 + STITCH_INSET, t), (X1 - STITCH_INSET, t)]
        t += STITCH_PITCH
    gx = X0 + 4.0
    while gx < X1 - 3:
        gy = Y0 + 4.0
        while gy < Y1 - 3:
            pts.append((gx, gy))
            gy += STITCH_PITCH
        gx += STITCH_PITCH
    nvia = 0
    for x, y in pts:
        if fits(board, x, y, vw):
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(VECTOR2I(mm(x), mm(y)))
            v.SetWidth(vw)
            v.SetDrill(vd)
            v.SetNet(gnd)
            board.Add(v)
            nvia += 1

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(PCB, board, True)
    print('routed board saved, %d stitching vias' % nvia)


def widen(board, plan):
    """Make each segment of the given nets as wide as its surroundings allow."""
    clr = mm(0.2)
    edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    rules = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]
    pads = [p for fp in board.GetFootprints() for p in fp.Pads()]
    n = 0
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() not in plan:
            continue
        name, lay = t.GetNetname(), t.GetLayer()
        for w in plan[name]:
            if mm(w) <= t.GetWidth():
                break
            seg = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), mm(w))
            bad = False
            for p in pads:
                if p.GetNetname() == name and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                    continue
                if (p.IsOnLayer(lay) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH) and \
                   p.GetEffectiveShape(lay).Collide(seg, clr):
                    bad = True
                    break
            if not bad:
                for o in board.GetTracks():
                    if o.GetNetname() == name:
                        continue
                    if o.Type() == pcbnew.PCB_VIA_T or o.GetLayer() == lay:
                        if o.GetEffectiveShape(lay).Collide(seg, clr):
                            bad = True
                            break
            if not bad:
                bad = any(e.GetEffectiveShape().Collide(seg, mm(0.3)) for e in edges) or \
                      any(z.GetLayerSet().Contains(lay) and z.Outline().Collide(seg) for z in rules)
            if not bad:
                t.SetWidth(mm(w))
                n += 1
                break
    return n


def fits(board, x, y, vw):
    """True if a GND via at (x, y) clears every pad, track, via, hole, slot and keep-out."""
    p = VECTOR2I(mm(x), mm(y))
    need = vw // 2 + mm(0.25)
    for fp in board.GetFootprints():
        b = courtyard_box(fp)
        if fp.GetReference().startswith('H'):
            b.Inflate(mm(0.4))
        if b.Contains(p):
            return False
        for pad in fp.Pads():
            if pad.GetEffectiveShape(pcbnew.F_Cu).Collide(p, need) or \
               pad.GetEffectiveShape(pcbnew.B_Cu).Collide(p, need):
                return False
    for t in board.GetTracks():
        if t.GetEffectiveShape(t.GetLayer() if t.Type() != pcbnew.PCB_VIA_T else pcbnew.F_Cu).Collide(p, need):
            return False
    for z in board.Zones():
        if z.GetIsRuleArea() and z.Outline().Collide(p, need):
            return False
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetEffectiveShape().Collide(p, vw // 2 + mm(0.4)):
            return False
    ix0, iy0, ix1, iy1 = ISLAND
    if ix0 - 1.5 <= x <= ix1 + 1.5 and y >= iy0 - 1.5:
        return False
    return True


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('place', 'route'):
        sys.exit(__doc__)
    {'place': place, 'route': route}[sys.argv[1]](sys.argv[2])
