#!/usr/bin/env kicadpython
"""SQU-32 item 11: move reference designators off pads, off other silkscreen and
off the board edge.

With a DRC report as the argument only the references named in it are moved, so the
rest of the silkscreen stays where the placement put it.

Only the reference *fields* are moved. Footprint silkscreen graphics are left alone:
editing them would trade a silk warning for a `lib_footprint_mismatch` warning.

    kicad-cli pcb drc ... -o drc.rpt && kicadpython tools/pcb_silk.py drc.rpt
"""
import os, re, sys
import pcbnew
from pcbnew import FromMM as mm, ToMM as T, VECTOR2I

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'kicad/room-node/room-node.kicad_pcb')
CLR = 0.17                  # silk clearance 0.15 mm + a little margin
EDGE = 0.32                 # silk to board edge 0.15 mm, kept generous

board = pcbnew.LoadBoard(PCB)
fps = list(board.GetFootprints())


def box(item, grow=0.0):
    b = item.GetBoundingBox()
    return [T(b.GetLeft()) - grow, T(b.GetTop()) - grow,
            T(b.GetRight()) + grow, T(b.GetBottom()) + grow]


def hit(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


# fixed obstacles: every pad, every footprint silkscreen graphic, every board edge
fixed = []
for fp in fps:
    for p in fp.Pads():
        fixed.append(box(p, CLR))
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_SilkS:
            fixed.append(box(g, CLR))
edges = [box(d, EDGE) for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
# the board rectangle; silkscreen that lands outside it is simply not printed
BX0, BY0, BX1, BY1 = 100.0 + EDGE, 100.0 + EDGE, 189.5 - EDGE, 138.0 - EDGE

want = None
if len(sys.argv) > 1:
    want = set(re.findall(r'Reference field of (\S+)', open(sys.argv[1]).read()))
    print('from %s: %d references to move: %s'
          % (sys.argv[1], len(want), ' '.join(sorted(want))))
refs = []
for fp in fps:
    r = fp.Reference()
    if r.IsVisible() and r.GetLayer() == pcbnew.F_SilkS and (want is None
                                                            or fp.GetReference() in want):
        refs.append((fp, r))
# start from the current layout, then replace each entry as it is placed
placed = {id(fp): box(r, CLR) for fp, r in refs}

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0), (-0.75, -0.75), (0.75, -0.75),
        (-0.75, 0.75), (0.75, 0.75)]
moved, stuck = {}, []

# Two passes: in the first, parts later in the list are still obstacles at their
# original spots, so a few tight clusters cannot resolve until everyone has moved.
for fp, r in [x for x in refs] * 2:
    ref = fp.GetReference()
    b = box(r)
    w, h = b[2] - b[0], b[3] - b[1]
    cx, cy = (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0
    pos = r.GetPosition()
    px, py = T(pos.x), T(pos.y)
    try:
        cb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        half = (min(max(T(cb.GetRight()) - T(cb.GetLeft()), 0.2) / 2.0, 4.0),
                min(max(T(cb.GetBottom()) - T(cb.GetTop()), 0.2) / 2.0, 4.0))
    except Exception:
        half = (1.0, 1.0)
    fx, fy = T(fp.GetPosition().x), T(fp.GetPosition().y)

    def free(ax, ay):
        """ax/ay = wanted centre of the text box."""
        cand = [ax - w / 2 - CLR, ay - h / 2 - CLR, ax + w / 2 + CLR, ay + h / 2 + CLR]
        if cand[0] < BX0 or cand[1] < BY0 or cand[2] > BX1 or cand[3] > BY1:
            return None
        for o in fixed:
            if hit(cand, o):
                return None
        for k, o in placed.items():
            if k != id(fp) and hit(cand, o):
                return None
        for o in edges:
            if hit(cand, o):
                return None
        return cand

    best = free(cx, cy)
    if best is not None:
        placed[id(fp)] = best
        continue
    found = None
    for extra in [0.0, 0.3, 0.6, 1.0, 1.4, 1.9, 2.5, 3.2]:
        for dx, dy in DIRS:
            ax = fx + dx * (half[0] + w / 2 + 0.25 + extra)
            ay = fy + dy * (half[1] + h / 2 + 0.25 + extra)
            cand = free(ax, ay)
            if cand is not None:
                found = (ax, ay, cand)
                break
        if found:
            break
    if found:
        ax, ay, cand = found
        r.SetPosition(VECTOR2I(mm(ax - (cx - px)), mm(ay - (cy - py))))
        placed[id(fp)] = cand
        moved[ref] = ((ax - cx) ** 2 + (ay - cy) ** 2) ** 0.5 + moved.get(ref, 0.0)
    else:
        stuck.append(ref)

pcbnew.SaveBoard(PCB, board)
stuck = [r for r in dict.fromkeys(stuck) if stuck.count(r) > 1]
print('moved %d reference fields; largest move %.1f mm (%s)'
      % (len(moved), max(moved.values()), max(moved, key=moved.get)))
print('%s' % ', '.join('%s %.1f' % kv for kv in sorted(moved.items())))
print('no free spot for %d: %s' % (len(stuck), ', '.join(stuck) or 'none'))
