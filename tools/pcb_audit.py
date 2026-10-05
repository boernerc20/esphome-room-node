#!/usr/bin/env kicadpython
"""SQU-35 measurements: connector positions, +5V widths, clearances, distances.

    kicadpython tools/pcb_audit.py
"""
import math, os, sys
import pcbnew
from pcbnew import ToMM as T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(ROOT, 'kicad/room-node/room-node.kicad_pcb'))
X0, Y0, X1, Y1 = 100.0, 100.0, 189.5, 138.0
FPS = {f.GetReference(): f for f in b.GetFootprints()}


def pads(ref):
    return {p.GetNumber(): (T(p.GetPosition().x), T(p.GetPosition().y))
            for p in FPS[ref].Pads() if p.GetNumber()}


def cy(ref):
    s = FPS[ref].GetCourtyard(pcbnew.F_CrtYd)
    bb = s.BBox() if s.OutlineCount() else FPS[ref].GetBoundingBox(False)
    return (T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom()))


def copper_extent(ref):
    xs, ys = [], []
    for p in FPS[ref].Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            continue
        bb = p.GetBoundingBox()
        xs += [T(bb.GetLeft()), T(bb.GetRight())]
        ys += [T(bb.GetTop()), T(bb.GetBottom())]
    return min(xs), min(ys), max(xs), max(ys)


print('== connectors ==')
for ref in ('J1', 'J2', 'J3', 'J4'):
    f = FPS[ref]
    p = f.GetPosition()
    c, k = cy(ref), copper_extent(ref)
    print('%-3s %-46s at (%7.3f, %7.3f) rot %4.0f' %
          (ref, f.GetFPIDAsString().split(':')[1], T(p.x), T(p.y), f.GetOrientationDegrees()))
    print('     courtyard x[%.3f, %.3f] y[%.3f, %.3f]   copper x[%.3f, %.3f] y[%.3f, %.3f]'
          % (c[0], c[2], c[1], c[3], k[0], k[2], k[1], k[3]))
    print('     copper to nearest board edge: left %.3f right %.3f top %.3f bottom %.3f'
          % (k[0] - X0, X1 - k[2], k[1] - Y0, Y1 - k[3]))
print('J3 pin 1 pad at (%.3f, %.3f), pin 8 at (%.3f, %.3f)'
      % (pads('J3')['1'] + pads('J3')['8']))
print('J4 pin 1 (+5V) at (%.3f, %.3f), pin 2 (data) (%.3f, %.3f), pin 3 (GND) (%.3f, %.3f)'
      % (pads('J4')['1'] + pads('J4')['2'] + pads('J4')['3']))

print('\n== +5V path lengths (pad centre to pad centre) ==')
P = {r: pads(r) for r in ('J1', 'J4', 'C30', 'C20', 'U3', 'U2', 'C1', 'C2')}
def d(a, b_):
    return math.dist(a, b_)
print('J1 VBUS (B4)  -> J4 pin 1      %6.2f mm' % d(P['J1']['B4'], P['J4']['1']))
print('J1 VBUS (B4)  -> C30 pad 1     %6.2f mm' % d(P['J1']['B4'], P['C30']['1']))
print('J4 pin 1      -> C30 pad 1     %6.2f mm' % d(P['J4']['1'], P['C30']['1']))
print('C30 courtyard to J4 courtyard gap  %.3f mm'
      % (cy('C30')[0] - cy('J4')[2]))

print('\n== +5V track widths ==')
seg = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == '+5V']
byw = {}
for t in seg:
    w = round(T(t.GetWidth()), 3)
    byw.setdefault(w, [0, 0.0])
    byw[w][0] += 1
    byw[w][1] += T(t.GetLength())
for w in sorted(byw, reverse=True):
    print('  %.2f mm : %2d segments, %6.2f mm total' % (w, byw[w][0], byw[w][1]))
print('  thin (< 0.60 mm) segments:')
for t in seg:
    if T(t.GetWidth()) < 0.6 - 1e-6:
        s, e = t.GetStart(), t.GetEnd()
        print('    %.2f mm  %-5s (%7.3f,%7.3f)-(%7.3f,%7.3f)  len %.2f'
              % (T(t.GetWidth()), b.GetLayerName(t.GetLayer()), T(s.x), T(s.y),
                 T(e.x), T(e.y), T(t.GetLength())))

print('\n== heat / sensor isolation ==')
tab = [p for p in FPS['U2'].Pads() if p.GetNumber() == '2' and p.GetSize().y > pcbnew.FromMM(2)][0]
tabp = (T(tab.GetPosition().x), T(tab.GetPosition().y))
print('U2 tab centre (%.3f, %.3f); U6 +3V3 pad (%.3f, %.3f) -> %.2f mm'
      % (tabp + pads('U6')['2'] + (d(tabp, pads('U6')['2']),)))
print('U3 centre -> U6 centre %.2f mm'
      % d((T(FPS['U3'].GetPosition().x), T(FPS['U3'].GetPosition().y)),
          (T(FPS['U6'].GetPosition().x), T(FPS['U6'].GetPosition().y))))
hole = [p for p in FPS['MK1'].Pads() if not p.GetNumber()][0].GetPosition()
hx, hy = T(hole.x), T(hole.y)
print('mic sound hole at (%.3f, %.3f); J4 courtyard %.2f mm away (nearest edge)'
      % (hx, hy, hy - cy('J4')[3]))
bad = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        q = t.GetPosition()
        r = math.dist((T(q.x), T(q.y)), (hx, hy))
        if r < 2.0:
            bad.append((round(r, 2), round(T(q.x), 2), round(T(q.y), 2)))
print('vias within 2.00 mm of the sound hole: %s' % (bad or 'none'))

print('\n== antenna end: lowest-y copper under the module ==')
worst = None
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() in ('GND', '+3V3'):
        continue
    for p in (t.GetStart(), t.GetEnd()):
        x, y = T(p.x), T(p.y)
        if 118.25 <= x <= 137.75 and (worst is None or y < worst[0]):
            worst = (y, t.GetNetname(), x)
print('closest signal track to the antenna line (y = 100) under the module: '
      'y = %.2f (%s at x = %.2f)' % worst)

print('\n== speaker pair ==')
for net in ('Net-(J2-Pin_1)', 'Net-(J2-Pin_2)'):
    L = sum(T(t.GetLength()) for t in b.GetTracks()
            if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == net)
    nv = len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net])
    w = sorted({round(T(t.GetWidth()), 2) for t in b.GetTracks()
                if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == net})
    print('  %-16s %5.2f mm, %d vias, widths %s' % (net, L, nv, w))

print('\n== EPD nets (U1 -> J3) ==')
for net in ('EPD_MOSI', 'EPD_CLK', 'EPD_CS', 'EPD_DC', 'EPD_RST', 'EPD_BUSY'):
    L = sum(T(t.GetLength()) for t in b.GetTracks()
            if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == net)
    nv = len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net])
    print('  %-9s %6.2f mm, %d vias' % (net, L, nv))

print('\n== LED data (U1 -> R30 -> J4) ==')
for net in ('LED_DIN', 'Net-(J4-Pin_2)'):
    L = sum(T(t.GetLength()) for t in b.GetTracks()
            if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == net)
    print('  %-16s %6.2f mm' % (net, L))

print('\n== L2 (In1.Cu) GND integrity ==')
for lay, name in ((pcbnew.In1_Cu, 'In1.Cu (L2 GND)'), (pcbnew.In2_Cu, 'In2.Cu (L3 +3V3)')):
    n = len([t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == lay])
    print('  %s: %d tracks' % (name, n))

print('\n== mounting holes vs courtyards ==')
for h in ('H1', 'H2', 'H3', 'H4'):
    q = FPS[h].GetPosition()
    hx, hy = T(q.x), T(q.y)
    near = []
    for ref, f in FPS.items():
        if ref.startswith('H'):
            continue
        c = cy(ref)
        dx = max(c[0] - hx, 0, hx - c[2])
        dy = max(c[1] - hy, 0, hy - c[3])
        near.append((math.hypot(dx, dy), ref))
    near.sort()
    print('  %s (%.1f, %.1f): nearest courtyards %s'
          % (h, hx, hy, ', '.join('%s %.2f' % (r, d_) for d_, r in near[:3])))
