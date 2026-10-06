#!/usr/bin/env kicadpython
"""SQU-35 / SQU-39 measurements: connector positions, +5V widths and path, clearances,
distances.

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

def d(a, b_):
    return math.dist(a, b_)


print('\n== J1 / J4 / C30 placement (SQU-39) ==')
j1c = cy('J1')
pins = [p[1] for k_, p in pads('J1').items() if k_[0] in 'AB']
print('J1 courtyard centre y %.3f (board centre %.3f); A/B pin field y %.3f-%.3f, centre %.3f'
      % ((j1c[1] + j1c[3]) / 2, (Y0 + Y1) / 2, min(pins), max(pins), (min(pins) + max(pins)) / 2))


def gap(a, b_):
    ca, cb = cy(a), cy(b_)
    dx = max(cb[0] - ca[2], ca[0] - cb[2], 0)
    dy = max(cb[1] - ca[3], ca[1] - cb[3], 0)
    return math.hypot(dx, dy)


def ctr(ref):
    q = FPS[ref].GetPosition()
    return (T(q.x), T(q.y))


u6 = ctr('U6')
print('J4 courtyard -> U6 courtyard   %6.2f mm' % gap('J4', 'U6'))
print('J4 courtyard -> island left slot (x = 147.60)  %6.2f mm' % (147.6 - cy('J4')[2]))
print('J4 pin 1 (+5V) -> U6 centre    %6.2f mm' % math.dist(pads('J4')['1'], u6))
print('J4 nearest pad -> U6 centre    %6.2f mm' % min(math.dist(p, u6) for p in pads('J4').values()))
print('C30 courtyard -> J4 courtyard  %6.2f mm;  C30 + pad -> J4 pin 1 %.2f mm'
      % (gap('C30', 'J4'), math.dist(pads('C30')['1'], pads('J4')['1'])))
k = copper_extent('J4')
print('J4 copper to bottom edge %.3f mm; courtyard to bottom edge %.3f mm'
      % (Y1 - k[3], Y1 - cy('J4')[3]))

print('\n== +5V J1 -> J4 copper path (SQU-39) ==')
# Walk the +5V tracks from J1's VBUS pads to J4 pin 1 (shortest path over the track
# graph), and report each width's share plus the IPC-2221 rise at the LED current.
seg5 = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() == '+5V']
vias5 = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == '+5V']
key = lambda q: (round(T(q.x), 3), round(T(q.y), 3))
adj = {}
for t in seg5:
    a_, b2 = key(t.GetStart()), key(t.GetEnd())
    for u, v in ((a_, b2), (b2, a_)):
        adj.setdefault(u, []).append((v, T(t.GetLength()), round(T(t.GetWidth()), 2),
                                      b.GetLayerName(t.GetLayer())))
for v in vias5:   # layer change: zero length
    pv = key(v.GetPosition())
    for u in list(adj):
        if math.dist(u, pv) < 1e-3 and u != pv:
            adj.setdefault(u, []).append((pv, 0.0, 0, 'via'))
            adj.setdefault(pv, []).append((u, 0.0, 0, 'via'))
import heapq
src = [n for n in adj if any(math.dist(n, pads('J1')[p]) < 0.4 for p in ('A4', 'A9', 'B4', 'B9'))]
dst = [n for n in adj if math.dist(n, pads('J4')['1']) < 0.4]
dist, prev = {}, {}
h = [(0.0, n) for n in src]
for _, n in h:
    dist[n] = 0.0
while h:
    d0, u = heapq.heappop(h)
    if d0 > dist.get(u, 1e9):
        continue
    for v, L, w, lay in adj.get(u, []):
        if d0 + L < dist.get(v, 1e9):
            dist[v] = d0 + L
            prev[v] = (u, L, w, lay)
            heapq.heappush(h, (d0 + L, v))
end = min(dst, key=lambda n: dist.get(n, 1e9))
legs, n_ = [], end
while n_ in prev:
    u, L, w, lay = prev[n_]
    legs.append((w, lay, L))
    n_ = u
byw2 = {}
for w, lay, L in legs:
    if L:
        byw2[(w, lay)] = byw2.get((w, lay), 0.0) + L
total = sum(L for _, _, L in legs)
print('J1 VBUS pad -> J4 pin 1: %.2f mm of copper' % total)
for (w, lay), L in sorted(byw2.items(), reverse=True):
    print('    %.2f mm wide on %-5s %6.2f mm' % (w, lay, L))


def ipc_rise(i, w_mm, oz=1.0):
    area = (w_mm / 0.0254) * (1.378 * oz)          # mil^2
    return (i / (0.048 * area ** 0.725)) ** (1 / 0.44)


def mohm(L, w_mm, oz=1.0):
    return 0.5 * oz ** -1 * L / w_mm                   # 1 oz Cu ~0.5 mOhm/square at 25 C


for i in (1.6, 2.0, 3.4):
    print('  IPC-2221 rise at %.1f A: 1.50 mm %4.1f C, 0.60 mm neck (half each) %4.1f C'
          % (i, ipc_rise(i, 1.5), ipc_rise(i / 2, 0.6)))
r = sum(mohm(L, w) for (w, lay), L in byw2.items() if w >= 1.0)
print('  DC resistance of the >= 1.0 mm part %.1f mOhm -> %.0f mV drop at 1.6 A'
      % (r, 1.6 * r))
far = 1e9
for t in seg5:
    if T(t.GetWidth()) < 1.0:
        continue
    sh = t.GetEffectiveShape(t.GetLayer())
    isl = pcbnew.SHAPE_RECT(pcbnew.VECTOR2I(pcbnew.FromMM(147.6), pcbnew.FromMM(130.6)),
                            pcbnew.FromMM(156.4 - 147.6), pcbnew.FromMM(Y1 - 130.6))
    far = min(far, T(sh.GetClearance(isl)) if hasattr(sh, 'GetClearance') else far)
print('  nearest wide (>= 1.0 mm) +5V copper to the AHT20 island box: %s'
      % ('%.2f mm' % far if far < 1e8 else 'n/a'))
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
      % (hx, hy, cy('J4')[0] - hx))
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
