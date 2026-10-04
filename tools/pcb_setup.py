#!/usr/bin/env kicadpython
"""One-time rev A board setup: stack-up, outline, holes, parts, nets, planes, rough placement.

Usage (from the repo root):
    kicadpython tools/pcb_setup.py            # refuses if the board already has parts
    kicadpython tools/pcb_setup.py --force    # overwrite (loses all layout work!)

Writes kicad/room-node/room-node.kicad_pcb. Footprints are linked to their schematic
symbols (same as Tools -> Update PCB from Schematic), so F8 later updates them in place.
Zones are saved unfilled: press B in the PCB editor to fill.

Placement is rough, by function. Final placement and all routing are done by hand.
"""
import os, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
import pcbnew
from pcbnew import FromMM as mm, VECTOR2I

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRJ = os.path.join(ROOT, 'kicad/room-node')
SCH = os.path.join(PRJ, 'room-node.kicad_sch')
PCB = os.path.join(PRJ, 'room-node.kicad_pcb')
LIBS = {'room-node': os.path.join(PRJ, 'lib/footprints/room-node.pretty')}
STOCK = os.environ.get('KICAD_FOOTPRINTS', '/usr/share/kicad/footprints')

# Board outline (mm). Placeholder size: change it when the case is known.
X0, Y0, W, H = 100.0, 100.0, 90.0, 50.0
X1, Y1 = X0 + W, Y0 + H
CORNER_R = 2.0
HOLE_INSET = 3.5

# Rough placement: ref -> (x, y, rotation deg). Grouped by function.
# U1 antenna overhangs the top edge (board edge at the antenna / pad boundary).
PLACE = {
    # MCU
    'U1': (130.0, Y0 + 6.75, 0),
    'C5': (118.5, 102.5, 0), 'C7': (115.5, 102.5, 0),          # 3V3 pin 2
    'C8': (118.5, 104.5, 0), 'R3': (118.5, 106.5, 0),          # EN pin 3
    'C9': (142.0, 103.0, 0), 'TP8': (146.0, 103.0, 0),         # CC_SENSE, pin 39
    'R30': (143.0, 113.0, 90),                                  # LED data, near U1
    # USB-C and protection (left edge)
    'J1': None,                                                 # placed at the edge below
    'U5': (114.0, 114.0, 0),
    'R1': (111.0, 110.0, 90), 'R2': (113.0, 110.0, 90),
    'R6': (115.0, 110.0, 90), 'R7': (117.0, 110.0, 90),
    # LDO
    'U2': (109.0, 131.0, 0),
    'C1': (104.0, 124.0, 90), 'C2': (107.0, 124.0, 90), 'C3': (109.5, 124.0, 90),
    'C4': (112.5, 124.0, 90), 'C6': (115.5, 124.0, 90),
    # Test points, buttons, pull-ups, status LED
    'TP1': (123.0, 123.0, 0), 'TP2': (126.0, 123.0, 0), 'TP3': (129.0, 123.0, 0),
    'TP4': (132.0, 123.0, 0), 'TP5': (135.0, 123.0, 0), 'TP6': (138.0, 123.0, 0),
    'TP7': (141.0, 123.0, 0),
    'SW1': (126.0, 129.0, 0), 'SW2': (136.0, 129.0, 0), 'SW3': (146.0, 129.0, 0),
    'R4': (132.0, 136.0, 90), 'R5': (134.0, 136.0, 90),
    'R12': (138.0, 136.0, 90), 'D1': (141.0, 136.0, 90),
    # Microphone (bottom-left, far from speaker, LEDs and antenna)
    'MK1': (112.0, 145.0, 0),
    'C10': (105.0, 139.5, 90), 'C11': (107.0, 139.5, 90), 'R8': (109.0, 139.5, 90),
    'R9': (111.0, 139.5, 90), 'R10': (113.0, 139.5, 90), 'R11': (115.0, 139.5, 90),
    # Sensor (bottom edge)
    'U6': (125.0, 146.0, 0),
    'C40': (122.0, 141.0, 90), 'R40': (124.0, 141.0, 90), 'R41': (126.0, 141.0, 90),
    # Display connector (bottom edge)
    'J3': (148.0, 145.0, 0), 'C50': (134.0, 145.0, 90),
    # Amplifier + speaker (bottom-right)
    'U3': (172.0, 138.0, 0),
    'C21': (168.5, 134.5, 0), 'C22': (174.5, 134.5, 0), 'R20': (172.0, 142.5, 0),
    'C20': (164.0, 144.0, 0),
    'J2': (182.0, 136.0, 0),
    # LED ring connector (top-right)
    'J4': (180.0, 112.0, 0), 'C30': (168.0, 112.0, 0),
}

# +5V area on In2.Cu (the rest of In2.Cu is +3V3): USB/LDO strip, a band, amp/LED side.
P5V = [(X0, Y0), (120, Y0), (120, 124), (155, 124), (155, Y0), (X1, Y0), (X1, Y1),
       (155, Y1), (155, 128), (120, 128), (120, 137), (X0, 137)]

STITCH_PITCH = 5.0     # GND vias along the edge
STITCH_INSET = 1.2


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


def zone(board, net, layer, pts, priority, name):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetZoneName(name)
    z.SetAssignedPriority(priority)
    z.SetMinThickness(mm(0.2))
    z.SetLocalClearance(mm(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(mm(x), mm(y))
    board.Add(z)


def main():
    if os.path.exists(PCB) and not '--force' in sys.argv:
        old = pcbnew.LoadBoard(PCB)
        if len(old.GetFootprints()):
            sys.exit('board already has parts; use --force to overwrite (loses layout work)')

    root = netlist()
    board = pcbnew.NewBoard(PCB)

    # Stack-up: JLC04161H-7628, 1.6 mm. L2 GND plane, L3 power.
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_MIXED)
    board.SetLayerName(pcbnew.In1_Cu, 'In1.Cu')
    board.SetLayerName(pcbnew.In2_Cu, 'In2.Cu')

    outline(board)

    # Nets
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

    # Footprints, linked to their schematic symbols
    for c in root.find('components'):
        ref = c.get('ref')
        fp = load_fp(c.findtext('footprint'))
        fp.SetReference(ref)
        fp.SetValue(c.findtext('value'))
        sp = c.find('sheetpath')
        fp.SetPath(pcbnew.KIID_PATH(sp.get('tstamps') + c.findtext('tstamps')))
        fp.SetSheetname(sp.get('names'))
        fp.SetSheetfile(c.find('property[@name="Sheetfile"]').get('value')
                        if c.find('property[@name="Sheetfile"]') is not None else '')
        for fl in c.find('fields'):
            if fl.get('name') != 'Footprint':
                fp.SetField(fl.get('name'), fl.text or '')
                fp.GetField(fl.get('name')).SetVisible(False)
        fp.SetDNP(c.find('property[@name="dnp"]') is not None)
        fp.SetExcludedFromBOM(False)   # match the schematic (test pads stay in the BOM)
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

    # USB-C: opening faces left, front of the courtyard flush with the left edge.
    j1 = board.FindFootprintByReference('J1')
    j1.SetOrientationDegrees(270)
    j1.SetPosition(VECTOR2I(0, 0))
    bb = courtyard_box(j1)
    j1.SetPosition(VECTOR2I(mm(X0) - bb.GetLeft(), mm(114.0) - bb.GetCenter().y))

    # Mounting holes, M3, board-only (not in the schematic)
    for i, (x, y) in enumerate([(X0 + HOLE_INSET, Y0 + HOLE_INSET), (X1 - HOLE_INSET, Y0 + HOLE_INSET),
                                (X0 + HOLE_INSET, Y1 - HOLE_INSET), (X1 - HOLE_INSET, Y1 - HOLE_INSET)], 1):
        h = load_fp('MountingHole:MountingHole_3.2mm_M3')
        h.SetReference('H%d' % i)
        h.SetValue('M3')
        h.SetBoardOnly(True)
        h.SetPosition(VECTOR2I(mm(x), mm(y)))
        board.Add(h)

    # Planes. Outline slightly inside the board; the edge clearance rule trims the rest.
    full = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    gnd, p5, p33 = nets['GND'], nets['+5V'], nets['+3V3']
    zone(board, gnd, pcbnew.In1_Cu, full, 0, 'GND plane L2')
    zone(board, p33, pcbnew.In2_Cu, full, 0, '+3V3 L3')
    zone(board, p5, pcbnew.In2_Cu, P5V, 1, '+5V L3')
    zone(board, gnd, pcbnew.F_Cu, full, 0, 'GND fill L1')
    zone(board, gnd, pcbnew.B_Cu, full, 0, 'GND fill L4')

    # GND stitching vias along the edge, away from parts and holes
    boxes = []
    for fp in board.GetFootprints():
        b = courtyard_box(fp)
        b.Inflate(mm(0.6))
        boxes.append(b)
    pts = []
    t = X0 + 6.0
    while t <= X1 - 6.0:
        pts += [(t, Y0 + STITCH_INSET), (t, Y1 - STITCH_INSET)]
        t += STITCH_PITCH
    t = Y0 + 6.0
    while t <= Y1 - 6.0:
        pts += [(X0 + STITCH_INSET, t), (X1 - STITCH_INSET, t)]
        t += STITCH_PITCH
    nvia = 0
    for x, y in pts:
        p = VECTOR2I(mm(x), mm(y))
        if any(b.Contains(p) for b in boxes):
            continue
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(p)
        v.SetWidth(mm(0.6))
        v.SetDrill(mm(0.3))
        v.SetNet(gnd)
        board.Add(v)
        nvia += 1

    board.BuildConnectivity()
    pcbnew.SaveBoard(PCB, board, True)
    print('saved %s: %d footprints, %d nets, %d stitching vias'
          % (os.path.relpath(PCB, ROOT), len(board.GetFootprints()), len(nets), nvia))


if __name__ == '__main__':
    main()
