# Rev A layout, assembly and bring-up

For later, when the schematic is done. Rev A is 5 boards, built by hand.

## Board

- 4 layers, solid ground plane. ENIG finish. Order a stencil with the boards.
- All parts on the top side. 0603 minimum. At least 0.5 mm between passives.
- Tent the vias under the module pad and the amp pad. Windowpane the stencil on those pads.
- Readable silkscreen: pin 1 marks, polarity marks, refs.

## Stack-up and design rules (JLCPCB 4-layer)

Stack-up: **JLC04161H-7628**, 1.6 mm, 1 oz outer / 0.5 oz inner.
L1 signals + parts, L2 GND plane, L3 +3V3 plane, L4 signals + +5V trunk.

The 4 copper layers are set in `room-node.kicad_pcb`. The DRC rules below are already in `room-node.kicad_pro` (Board Setup → Design Rules).

| Rule | Value |
|---|---|
| Min track / clearance | 0.1 / 0.1 mm |
| Min via | 0.45 mm pad / 0.2 mm drill (0.3 mm drill and up: no extra cost) |
| Min through-hole drill | 0.2 mm |
| Hole to hole / hole to copper | 0.25 / 0.2 mm |
| Copper to board edge | 0.3 mm |
| Silkscreen text | 0.8 mm high, 0.15 mm line |

| Net class | Nets | Track | Clearance | Via |
|---|---|---|---|---|
| Default | all others | 0.2 | 0.15 | 0.6 / 0.3 |
| Power | +5V, +3V3, GND | 0.6 | 0.15 (USB-C J1 pads are 0.15 apart) | 0.8 / 0.4 |
| Audio | speaker out (J2) | 0.4 | 0.2 | 0.8 / 0.4 |
| USB | USB_D± | 0.2, diff gap 0.15 (~90 Ω on L1 over L2) | 0.15 | 0.6 / 0.3 |
| LED | LED_DIN, J4 data | 0.2 | 0.15 | 0.6 / 0.3 |

The Audio and LED patterns use KiCad's auto net names (`Net-(J2-Pin_*)`, `Net-(J4-Pin_2)`).
If you rename those nets in the schematic, update the pattern in Board Setup → Net Classes.

## Rev A board (placed and routed; connectors moved to the edges 2026-10-05, SQU-35; re-review fixes 2026-10-06, SQU-38; J1 centred and J4 to the bottom edge 2026-10-06, SQU-39; J4 side entry 2026-10-06, SQU-42)

`tools/pcb_build.py` builds the whole board: outline, holes, slots, parts, planes,
placement, rule areas, hand-made routes (J1 VBUS, the whole +5V net, the J1 → U5 USB
pair, amp pins, the C6 → U1 pin 2 link, the LDO tab copper, the sensor island) and plane
fan-out vias. Only signals are left to Freerouting 2.4.1 (needs Java 25, not in the
container by default; SQU-39 used Eclipse Temurin 25 from adoptium.net in a scratch
directory). The router is not deterministic: a rebuild gives different signal tracks,
so re-running the pipeline means re-running the checks and the reports with it.

```
kicadpython tools/pcb_build.py place out.dsn     # overwrites room-node.kicad_pcb
java -jar freerouting-2.4.1.jar -de out.dsn -do out.ses -mp 100 --gui.enabled=false
kicadpython tools/pcb_build.py route out.ses     # import, widen +5V, GND fills, stitching
kicad-cli pcb drc --severity-all --format report -o drc.rpt kicad/room-node/room-node.kicad_pcb
kicadpython tools/pcb_silk.py drc.rpt            # repeat drc + silk until the count settles
kicadpython tools/pcb_audit.py                   # the measurements quoted below
```

Reports (`reports/`) are regenerated from the same board:

```
kicad-cli pcb drc --severity-all --format report -o reports/pcb/room-node-drc.rpt  <board>
kicad-cli sch erc --severity-all --format report -o reports/schematic/room-node-rev-a-erc.rpt <sch>
python3 tools/check_pinout.py > reports/schematic/pinout-netlist-check.md
kicadpython tools/pcb_png.py F.Cu reports/pcb/room-node-copper-top.png     # and B.Cu
kicad-cli pcb render --side top --width 4000 --height 1800 --background transparent \
    --quality high -o top.png <board>            # crop to the alpha bbox, scale to 1799 px
kicad-cli pcb export gerbers --output gerb/ \
    --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,Edge.Cuts" <board>
kicad-cli pcb export drill --output gerb/ --format excellon --excellon-separate-th \
    --excellon-units mm <board>                  # zip gerb/ -> reports/fab/...-gerbers.zip
```

The design-review fixes live in the generator, not in one-shot patch scripts, so a
rebuild cannot lose them: M1 (C21/C22 at U3 pins 7/8), M3 (LDO tab copper area, its vias
and their drills), M4, the SQU-32 items (C6 rotated with a direct track to U1 pin 2,
CC_SENSE kept away from the antenna end, the mic-hole gasket seat, the island neck slot,
the necked +5V feed at U3 pins 7/8, the +5V widths) and the SQU-38 items (J3 0.10 mm in,
the 1.50 mm +5V inlet, `fix_tab_vias()`).

Two one-shot patch scripts are kept as history and **must not be re-run**:
`tools/pcb_squ32.py` (superseded entirely by the generator) and `tools/pcb_squ38.py`.
The second exists because Freerouting needs Java 25, which is not in the container, so
the committed board could not be rebuilt end to end when the SQU-37 review came back;
its three coordinate-exact edits are the same geometry the generator now produces.

**SQU-39 rebuild.** The whole pipeline above was re-run end to end for SQU-39, so the
signal routes are a fresh Freerouting result: the EPD lengths below changed with it.
`tools/pcb_squ38.py` is now fully superseded as well.

**Mounting.** Same outline and holes as the Waveshare 2.9" e-paper module
(Waveshare drawing: 89.5 × 38.0 mm, holes 2.5 mm from each edge, 84.5 × 33.0 mm pattern).
4 × M2 holes (2.2 mm, H1–H4). The board sits behind the display on M2 standoffs.
The bottom side (no parts) faces the display. All parts face the back of the case.

- **Standoffs:** the display's driver board has parts and its 8-pin connector on its back.
  Use standoffs tall enough to clear the plug: about 10 mm.
- **U1 antenna** overhangs the top edge, so it sticks out past the display outline by
  about 6 mm. The case must leave room for it. No metal in front of it.

### Connectors at the edges (SQU-35)

Chris's rule: the cables have to be short when the board sits behind the display, so
each connector sits on the edge nearest what it plugs into. Frame of reference as
everywhere in this file: **looking at the parts side, USB-C on the left**.

| Connector | Edge | Position | Cable |
|---|---|---|---|
| J1 USB-C | left, **centred** (SQU-39) | (109.155, **116.025**) rot −90 (footprint origin = pin A1). Pin field A1–A12 y 116.025–121.975 and courtyard y 113.68–124.32 are both centred on **y = 119.000**, the board centre; it was 113.5 (origin 110.525) | out of the left edge |
| J4 LED strip (S3B-XH-A, **side entry**, SQU-42) | **bottom**, under U1, left of the AHT20 island (SQU-39) | (124.000, **128.450**) rot 0; pin 1 +5V at x = 124.0, pin 2 data 126.5, pin 3 GND 129.0; mouth facing the bottom edge | straight out of the bottom edge |
| J3 display (S8B-PH-SM4-TB, side entry) | right | (184.500, 117.500) rot 90; pad row at x = 181.65, pin 1 (181.65, **124.50**) at the bottom, pin 8 at 110.50 | straight out of the right edge |
| J2 speaker (B2B-PH-SM4-TB) | bottom right | (176.300, 133.000), clear of J3 | up |

- **J3** faces out over the right edge. Its mounting-tab pads reach x = 189.10 against
  the edge at x = 189.50: **0.40 mm** of copper-to-edge margin (SQU-38 item 1; it was
  189.20 / 0.30 mm, which is the DRC limit but not a safe milling margin — JLCPCB's
  routing tolerance is ±0.20 mm, so 0.30 mm nominal can finish at 0.10 mm). The housing
  front face sits at x = 188.95, 0.55 mm inside the edge, so the cable still leaves
  straight out over the right edge; only the overhanging courtyard got 0.10 mm shorter.
  The courtyard spans y 106.86–128.15, which keeps J3 4.36 mm clear of H2 and 7.35 mm
  clear of H4. Use a short PH-to-PH 8-pin cable, pin 1 to pin 1 (see the display sheet
  notes in `schematic.md`).
- **J3 pin 1** is hidden under the side-entry housing, so it is marked with a filled
  silkscreen triangle on the board side of the pad row, tip at (179.60, 124.50),
  0.30 mm from pin 1's pad edge and pointing at it.
- **J4 side entry (SQU-42, Chris).** J4 is now the right-angle THT XH header
  S3B-XH-A (`Connector_JST:JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal`, 3 A, LCSC C157928),
  mouth facing the bottom edge, so the plug goes in from the edge and the cable leaves
  flat, straight out of the bottom edge. The housing is 11.6 mm deep and its front face
  sits 9.25 mm in front of the pin row, so the pins are at y = 128.45: housing x
  121.50–131.50, y 126.10–**137.70**, i.e. the front face is **0.30 mm inside** the edge
  (y = 138.00); **no body overhang**. The footprint silk ends at y = 137.82, 0.18 mm off
  the edge (no new silk warning). Only the courtyard crosses the edge, by 0.15 mm
  (line centre; y 125.64–138.15, x 121.00–132.00; 0.175 mm with the line width, SQU-45). The plug itself sticks out past the edge, so the
  case needs a slot in the bottom wall about 10 mm wide centred on x = 126.5 (pin 2).
  Pad copper is **8.58 mm** from the edge (pad centre 9.55 mm; SQU-45 corrected the
  earlier "3.55 mm").
- **C30 at J4.** C30 (1000 µF) did not move: (118.0, 132.2) rot 180, + pad facing J4,
  courtyards **0.21 mm** apart. C30 + pad → J4 pin 1 is now **7.08 mm** (was 6.16 mm; J4's
  pins moved 5.15 mm towards U1). Measured on the board (SQU-45; the earlier "0.31 mm"
  was wrong): can outline (F.Fab, Ø 10.0 mm, centre (115.5, 132.2)) **0.80 mm** inside the
  bottom edge, courtyard (r 5.25) **0.55 mm**, pad copper **4.80 mm**. A real can up to
  Ø 10.5 mm still clears the edge by 0.55 mm. Chris confirmed the case clears it
  (SQU-17, 2026-10-06).
- **J4 to the AHT20 (SQU-39 constraint, ≥ ~15 mm), unchanged by SQU-42.** J4 courtyard →
  U6 courtyard **18.81 mm**; J4 courtyard → the island's left slot (x = 147.60)
  **15.60 mm**; nearest J4 pad → U6 centre 24.49 mm; J4 pin 1 (+5V) → U6 centre 29.34 mm.
- **Mic sound hole** stays at (108.500, 135.510) in the bottom-left corner, as does its
  case opening. Nothing had to move it: J4's courtyard is **12.50 mm** to the right of it
  (SQU-39), and the C30 can sits between the two. No **via** is within 2.00 mm of the hole on any layer, enforced by
  the "MK1 gasket seat" rule area (2.5 mm radius). It is a no-via rule, not a no-copper
  rule: tracks and the GND / +3V3 pours still run through it, which is what keeps the
  planes solid round the mic. The no-copper ring is the separate 0.4 mm
  "MK1 sound hole" keep-out inside the footprint's GND ring.

### Bottom edge: board separation and assembly (SQU-45)

Rev A is 5 boards built by hand (top of this file), so JLCPCB's assembly rule
("the body of the components and the edge of the board must be equal or greater than
2.5 mm", [assembly terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service))
does not apply to it. It would apply only if Rev A were ordered **with JLC assembly**.
How the boards are separated still matters, so the method is written down here.
**Chris decides the method (via Oscar); nothing has been ordered or uploaded.**

**Every edge has something on it**, not just the bottom one. Measured on the board
(edge at x 100.0 / 189.5, y 100.0 / 138.0; "body" = F.Fab outline):

| Edge | Part | Body to edge | Courtyard | Copper to edge |
|---|---|---|---|---|
| bottom | **J4** S3B-XH-A (THT) | **0.30** | −0.15 (crosses) | pads **8.58** |
| bottom | **C30** 1000 µF (THT) | **0.80** | 0.55 | pads **4.80** |
| bottom | C20 470 µF (THT) | 1.35 | 1.12 | pads 4.60 |
| bottom | U6 AHT20 | 1.45 | 1.22 | pads 1.75 |
| bottom | MK1 mic | 1.40 | 1.18 | pads 1.68 |
| bottom | J2 speaker (PH SMD) | 4.20 | 1.22 | tab pads 1.75 |
| bottom | C40 | 2.15 | 1.50 | pads 1.78 |
| bottom | H3 / H4 (M2, Waveshare pattern) | – | – | pad ring 1.40 |
| top | U1 antenna | **overhangs 6.05** | – | pads 1.04 |
| left | J1 USB-C | 0.50 | 0.02 | pads 3.94 |
| right | J3 display (side entry) | 0.55 | −0.12 (crosses) | tab pads 0.40 |
| all | GND / +3V3 pours, L1–L4 | – | – | **0.30** (the rule minimum); edge stitching vias 0.70 |

What follows from that:

- **No V-cut on any edge.** The pours are 0.30 mm from every edge, and JLC's V-cut guide
  wants at least 0.4 mm from the cut centre to copper. On top of that, U1's antenna hangs
  6 mm over the top edge, and J4's and J3's courtyards cross the bottom and right edges.
- **Moving J4 (and C30) 2.5 mm in would not make the board meet JLC's 2.5 mm rule.**
  C20, U6, MK1, J1, J3 and U1 fail it too, and the M2 holes are fixed by the display.
  A JLC-assembled board needs a rails/fixture plan for the whole board, not just J4.

**Options**

| | A. Single routed boards, hand assembly **(proposed)** | B. Routed + mouse-bite panel with rails (only for JLC assembly) | C. Placement revision: J4 and C30 2.5 mm in |
|---|---|---|---|
| What | 5 single PCBs, outline routed by the fab, no panel, no V-cut. Stencil as already planned. Paste + hot air for SMD, then J4, C30, C20 and J1 THT with an iron. Nothing to depanel. | KiKit-style panel: 2 mm milled gap, mouse-bite tabs only where no part is within 2.5 mm (e.g. bottom edge x 135–145, under the test pads), rails on the long sides; the top rail is kept clear of the antenna overhang (≥ 8 mm gap). J4/C30/C20 hand-soldered after depanelling. | J4 to y 126.25 (front 2.50 mm inside), C30 up 1.70 mm. Re-route the LED legs (Freerouting is not deterministic, so all signals re-route and need a full re-review). |
| J4 body / copper to the separation path | **0.30 / 8.58 mm** to the routed edge (fab outline tolerance is typically ±0.2 mm, so ≥ 0.10 mm worst case; the housing never overhangs) | 0.30 mm to the board edge, 2.3 mm to the panel frame (2 mm gap); no tab within 2.5 mm of J4 | 2.50 / 10.78 mm |
| C30 body / copper | **0.80 / 4.80 mm** | 0.80 mm to the edge, 2.8 mm to the frame | 2.50 / 6.50 mm |
| Edge copper | 0.30 mm, fine for a routed edge | 0.30 mm; mouse-bite tab spots need a local ≥ 0.5 mm copper keep-out (board edit) | unchanged |
| Cost | none extra | panel design + edge keep-outs at tabs + JLC rail/fixture charges; still breaks the 2.5 mm rule for 8 other parts | a re-route and re-review; the plug mouth sits 2.5 mm inside the board, so the case slot gets deeper and the cable bends over the PCB edge |
| Fixes | everything that matters for Rev A | lets JLC assemble the SMD parts | nothing on its own (other parts still fail the 2.5 mm rule) |

**Proposal: A for Rev A.** It matches the plan of record (5 boards, hand-built), needs no
board change, and the routed edge is the only separation path: J4's housing stays
0.30 mm inside it, its pads 8.58 mm. Order settings to state when Chris orders:
delivery format **single PCB** (no "panel by JLCPCB", no V-cut), **no PCBA**, stencil
yes. If a panel is ever forced, it must be **mouse bites, not V-cut**, with no tab on the
bottom edge between x 110 and 133 (C30 + J4), and J4 is soldered after depanelling.
B (or a bottom-edge redesign of the whole board) is a Rev B question, if Rev B goes to
JLC assembly.

**Production files checked (SQU-45):** `reports/fab/room-node-rev-a-gerbers.zip` has one
outline (`Edge_Cuts`, profile only: board, the island slots and the neck slot), no
V-score or panel layer, no CPL/position file and no panel. The BOM lists J4 / C30 / C20
with LCSC numbers for buying, not as JLC-assembly lines. Nothing in `reports/` implies
JLC assembly or a panel.

**Placement** (looking at the parts side, USB-C on the left):

| Area | Parts |
|---|---|
| Left edge, top | R1/R2/R6/R7 (CC), R9/R10 at U1; H1 |
| Left edge, centre | **J1 USB-C** (centred on y = 119.0), U5 ESD right of it |
| Left, under U5 | C1 (above) / C2 (below) on the +5V spine via |
| Bottom-left corner | H3, MK1 mic + C10/C11 at its +3V3 pin, R11/R8 left of them. Sound hole through the board |
| Centre-left, top edge | U1 module; C6/C7/R3/C8 at its left pins |
| Under U1 | R30 at U1 pin 23 |
| Right of J4 | **Test pads in a 2 × 4 block** (SQU-42), 2.8 mm pitch, x 134.0–142.4: top row y 127.5 TP4 RXD0, TP5 +3V3, TP6 +5V, TP7 GND; bottom row y 130.6 TP1 EN, TP2 IO0, TP3 TXD0 and D1 (142.9). Labels above the top row (y 125.85) and in one line under the bottom row (y 132.88; TP2's was 1.9 mm lower until SQU-45) |
| Bottom edge under U1 | **C30 1000 µF**, then **J4 LED connector** (side entry); 15.6 mm to the island, the test-pad block in between |
| Right of U1 | C9/TP8 (CC sense), SW2 BOOT / SW1 RESET, R4/R12 |
| Bottom centre | U6 AHT20 + C40 on an island: slots left, right and in the neck; R40/R41 |
| Right, top | **U2 LDO** (tab on a F.Cu +3V3 copper area with 5 vias to L3), C3/C4/C5 |
| Right edge | **J3 display connector**, side entry; C50 at its +3V3 pin |
| Right, lower | U3 amp + C21/C22 at VDD pins 7/8, R20, C20 470 µF, J2 speaker |

**What moved in SQU-42** (Chris: J4 side entry, cable flat out of the bottom edge;
numbers from `tools/pcb_audit.py` and the footprint geometry):

| Part | From (SQU-39) | To | Reason |
|---|---|---|---|
| J4 | B3B-XH-A vertical, (124.0, 133.6) | **S3B-XH-A side entry**, (124.0, 128.45) rot 0 | mouth on the bottom edge, housing front 0.30 mm inside it |
| TP1–TP3 | x 121.0–126.6, y 127.5 | x 134.0 / 136.8 / 139.6, y 130.6 | the 11.6 mm deep housing covers their old spots |
| TP4–TP7 | x 129.4–137.8, y 127.5 | x 134.0 / 136.8 / 139.6 / 142.4, y 127.5 | same; TP6 (+5V) stays in the top row and drops straight onto the spine |
| D1 | (141.6, 127.5) | (142.9, 130.6) | end of the bottom test-pad row; courtyard 2.98 mm from the island slot |

C30, U6 and the island, R30, the mic and every other part did not move. The board was
rebuilt end to end (`tools/pcb_build.py` place → Freerouting 2.4.1 on Temurin 25 →
route), so the signal tracks are a fresh router result again (see the EPD table).

**What moved in SQU-39** (Chris: J4 crowded the left edge right under J1, and the space
under U1 was empty; every number from `tools/pcb_audit.py`):

| Part | From (SQU-35/38) | To | Reason |
|---|---|---|---|
| J1 | origin (109.155, 110.525), body centre y 113.5 | (109.155, 116.025), body centre **y 119.0** | centred on the left edge |
| U5 | (114.5, 113.5) | (114.5, 119.0) | stays next to J1 (moved with it) |
| J4 | (103.5, 122.3), left edge | (124.0, 133.6), bottom edge | off the crowded left edge; cable out of the bottom edge, ≥ 15 mm from U6 |
| C30 | (114.5, 125.8) rot 0 | (118.0, 132.2) rot 180 | at J4, + pad facing J4 pin 1 |
| C1 / C2 | (103.6, 128.2 / 130.6) | (113.6, 122.4 / 125.6) | on the +5V spine via under U5 |
| C10 / C11 | (107.4 / 109.9, 130.0) rot 90 | (108.6, 131.4 / 128.6) rot 0 | C30 took their spot; still at MK1's +3V3 pin |
| R11 / R8 | (112.6, 133.2 / 135.6) | (104.0, 128.6 / 131.4) | same |
| TP1–TP7 | x 124.3–141.1, y 124.5 | x 121.0–137.8, y 127.5 (same 2.8 mm pitch) | clear of the +5V spine at y = 124.0; one row under U1 |
| D1 | (143.0, 128.6) | (141.6, 127.5) | in line with the test pads |

J3, J2, U2/C3/C4/C5, U3 and its caps, C20, U6 and the island, the mic sound hole and the
four M2 holes did not move.

**SQU-35 moves** (history, before the SQU-39 changes above):

**What moved and why** (every number measured by `tools/pcb_audit.py`):

| Part | From | To | Reason |
|---|---|---|---|
| J3 | (128.0, 133.08), bottom edge under U1 | (184.5, 117.5) rot 90, right edge | display cable out of the right edge (184.6 in the first SQU-35 cut, pulled 0.10 mm in for edge margin) |
| J4 | (172.0, 104.0), top right | (103.5, 122.3), left edge below J1 | LED cable out of the left edge, next to J1 |
| C30 | (178.0, 113.5) | (114.5, 125.8) | stays with J4 on the short +5V leg |
| C1 / C2 | (104.0, 121.2 / 123.4) | (103.6, 128.2 / 130.6) | J4 took their old spot |
| U2 + C3/C4/C5 | (111.5, 124.5) and around | (170.0, 104.6), same group translated by (+58.5, −19.9) | J4 and C30 took the lower left; the group moved as one rigid block so the reviewed M3 tab copper and its 5 vias are unchanged |
| C10/C11/R8/R11 | around the mic | (107.4/109.9, 130.0) and (112.6, 133.2/135.6) | C30 and the trunk took the old band |
| C50 | (115.0, 131.5) | (177.5, 121.0) | follows J3 to the right edge |
| TP1–TP7 | x 121.5–138.3 | x 124.3–141.1 (same 2.8 mm pitch, same y) | TP1 was inside C30's body circle |
| C20 | (166.4, 132.6) | (165.0, 132.6) | makes room for J2 under J3 |
| C22 | (171.0, 125.75) | (171.0, 126.0) | 0.20 mm courtyard gap to C21 |
| J2 | (179.2, 133.0) | (176.3, 133.0) | out from under J3's courtyard |

**Sensor isolation.** SQU-42 moves no heat source: J4 keeps its x span and C30 its
place, and the +5V copper is still 5.85 mm from the island box. SQU-39 moves no heat source nearer U6: J4 and its +5V leg are
15.60 mm (slot) / 18.81 mm (U6 courtyard) away, and the widest +5V copper (the 1.50 mm
spine) is now **5.85 mm** above the island box instead of 1.85 mm (spine at y = 128.0).
From SQU-35: moving the LDO is the change to look at hardest. U2's tab is now
**37.26 mm** from U6's +3V3 pad against **38.41 mm** before — 1.15 mm closer, with the
island and its three slots unchanged. The bottom-left corner could not hold J4, C30 and
the LDO as well as the mic and H3, and of the two spots that were left (bottom centre,
or the top right that the LED connector vacated) the top right is the far one: putting
U2 in the bottom centre would have taken the gap down to about 25 mm. The amp U3 is
21.95 mm from U6, unchanged.

**What got longer.** The display connector is now at the opposite end of the board from
U1, so the six EPD signals grew from 17.5–33.6 mm (before SQU-35) to **56.84–66.40 mm**,
measured on the SQU-42 board (`tools/pcb_audit.py`; SQU-39 was 56.84–66.40 mm, the
SQU-35/38 route 55.76–71.91 mm):

| Net | Length | Vias |
|---|---|---|
| EPD_BUSY | **65.46 mm** (longest) | 2 |
| EPD_MOSI | 61.20 mm | 2 |
| EPD_CS | 60.48 mm | 2 |
| EPD_CLK | 57.82 mm | 2 |
| EPD_RST | 57.06 mm | 4 |
| EPD_DC | 55.57 mm (shortest) | 2 |

EPD_RST came back from the router with 4 vias instead of 2 (two extra layer changes,
each over the solid L2 GND; at SQU-39 it was MOSI and CLK); harmless at 2 MHz and on a
static reset line, noted for Iris.

ESPHome 2026.9.0's Waveshare driver clocks the panel at 2 MHz (500 ns period) and the
firmware does not override it, so 72 mm of track with 2 vias over the solid L2 return is
not a timing problem; it is the direct cost of the short cable (Iris, SQU-37). Verify the
display at bring-up, with a short display cable. Going the other way, the LED data line
is now U1 → R30 7.18 mm and R30 → J4 pin 2 **12.53 mm** (SQU-42; 18.38 mm at SQU-39,
31.87 mm at SQU-35, 56.85 mm before); the speaker pair is unchanged (14.14 / 16.12 mm, no vias).

**Layers**

| Layer | Use |
|---|---|
| F.Cu (L1) | Parts, most signals, GND fill |
| In1.Cu (L2) | GND plane, solid |
| In2.Cu (L3) | +3V3 plane, solid. No tracks |
| B.Cu (L4) | Signals, +5V riser and spine (J1 → C30/J4 and → amp/LDO), GND fill |

- **+5V** is a track, not a plane, and the whole net is hand routed (`preroute()` in
  `tools/pcb_build.py`), not left to the router. Topology:

  | Leg | Layer | Width | Length | Carries |
  |---|---|---|---|---|
  | J1 VBUS pads B9→A4 and B4→A9, then out of the pin field to x = 110.60 | B.Cu | 0.60, **two in parallel** | 2 × (1.35 + 1.45) mm | everything, ~half each |
  | **riser** at x = 110.60, y 116.875 → spine at y = 124.0 | B.Cu | **1.50** | 7.13 mm | everything |
  | **spine** x 110.60 → 118.00 (the C30 + pad column) | B.Cu | **1.50** | 7.40 mm | everything |
  | LED leg: down x = 118.00 to **C30 +**, then to **J4 pin 1** | B.Cu | **1.50** | 8.20 + 7.08 mm | LED strip, up to ~1.6–2 A |
  | spine x 118.00 → 168.00 at y = 124.0, then down to C20 pad 1 | B.Cu | **1.50** | 50.00 + 9.84 mm | amp + LDO |
  | TP6 straight up onto the spine (TP6 at x = 139.6, SQU-42) | F.Cu | 1.00 | 3.5 mm | test point |
  | spine via → C1 (up) and C2 (down) | F.Cu | 1.00 | 1.60 + 1.60 mm | USB input caps |
  | U5 pin 5 (VBUS sense) up, via, to the riser top | F.Cu + B.Cu | 0.50 + 1.00 | 1.50 + 3.93 mm | ESD clamp, mA |
  | spine via → C22 → C21 → U3 pins 7/8 | F.Cu | 1.00 / 0.80 | — | amp, ~0.9 A peak |
  | spine → up past U3 → U2 pin 3 and C3 | B.Cu + F.Cu | 1.00, 0.60 beside U3 | — | LDO, ≤ 0.5 A |

  **J1 → J4 path (SQU-42), measured on the copper** (`tools/pcb_audit.py`, shortest
  track path from J1's VBUS pad A9 to J4 pin 1): **27.00 mm**, of which 25.55 mm is
  1.50 mm wide and 1.45 mm is one of the two parallel 0.60 mm necks (26.08 mm at SQU-39,
  ~22 mm at SQU-35 with J4 next to J1). DC resistance ~8.5 mΩ, **14 mV drop at 1.6 A**;
  IPC-2221 rise 2.1 °C at 1.6 A, 3.4 °C at 2.0 A on the 1.50 mm track.
  The leg never runs along the island: it leaves the spine 29.6 mm west of the island's
  left slot and drops to the bottom edge there.

  | Current | 1.50 mm rise | 0.60 mm neck (half the current each) |
  |---|---:|---:|
  | 1.6 A (LED, Chris's figure) | **2.1 °C** | 1.9 °C |
  | 2.0 A (LED full white) | 3.4 °C | 3.2 °C |
  | 3.4 A (LED + amp + LDO, riser and first 7.4 mm of spine only) | 11.4 °C | 10.7 °C |

  (IPC-2221, external layer, 1 oz, k = 0.048.) **The common inlet is 1.50 mm, not
  "1.50 mm end to end":** the only part of the path from J1 to the split that is narrower
  is the 2 × 1.45 mm of 0.60 mm neck through the USB-C pin field, where the 0.70 mm pads
  on a 0.85 mm pitch leave no more room (0.20 mm to the neighbouring pad either side).
  The two necks are in parallel and carry about half the current each. The riser clears
  J1's A-row pads by 0.345 mm.
  The other deliberately thin parts are 0.25 mm stubs at U3's 0.5 mm-pitch pins
  (including the 0.25 mm neck into pins 7/8 and the GAIN_SLOT stub to pin 2, which
  carries no current), 0.6 mm for the LDO branch where it squeezes past U3, and the
  0.50 mm U5 VBUS-sense stub (mA).
- **GND / +3V3:** every SMD pad has its own via to its plane (fan-out). GND stitching
  vias on a 5 mm grid and along the edge, 45 of them.
- **Speaker pair** U3 → J2: 0.4–0.5 mm, side by side, no vias.
- **USB D± (SQU-39):** 0.2 mm, **all on F.Cu over the L2 GND plane except the
  in-connector crossover, no vias.** USB-C puts D+ on A6/B6 and D− on A7/B7, and the two
  pairs cross inside the pin field, so one of them must join its two rows on the other
  layer: D+ joins B6–A6 on F.Cu, D− joins B7–A7 on B.Cu (1.60 mm, through J1's own
  pins). J1 → U5 is hand-routed in `preroute()`: D− straight into U5 pin 1, D+ between
  U5's two pad rows into pin 3. U5 → U1 is routed on F.Cu only (a `use_layer F.Cu` class
  in the DSN; at SQU-35/38 D+ had 2 vias and a B.Cu section here). Copper length J1 → U5
  → U1, pad to pad, excluding U5's internal path:

  | Plug orientation | D+ (J1→U5 + U5→U1) | D− (J1→U5 + U5→U1) | Difference |
  |---|---:|---:|---:|
  | A pads | 7.61 + 3.86 = **11.47 mm** | 4.68 + 7.73 = **12.41 mm** | 0.94 mm |
  | B pads | 9.20 + 3.86 = **13.06 mm** | 6.28 + 7.73 = **14.01 mm** | 0.95 mm |

  SQU-36 measured 28.20 / 12.70 mm (A) and 26.93 / 14.41 mm (B) on the SQU-35 board,
  15.5 mm apart; the D+ detour round the pin field is gone. Still Full Speed only
  (12 Mbit/s), so a 1 mm skew is irrelevant; USB enumeration stays a bring-up test (step 4).

- **LDO heat:** the U2 tab sits on a F.Cu +3V3 copper area (6.2 × 3.3 mm, 20.4 mm², full
  connection) with vias to the L3 plane next to the tab, not in it (no solder wicking):
  **4 × 0.3 mm drill plus 1 × 0.4 mm drill beside the tab, 7 vias in total on the copper
  area** (the other two are C4's and C5's). C4/C5 +3V3 pads are on the same area. The
  0.3 mm column sits 0.65 mm clear of the tab copper, so a weak via tent cannot pull
  solder off the tab. The whole cluster moved with U2 as a rigid block in SQU-35, so the
  geometry is the one Iris reviewed; it is now generated from the tab pad position
  (`TAB_AREA` / `TAB_VIAS` in `tools/pcb_build.py`) instead of fixed coordinates. The
  area is at x 171.90–178.10, y 103.00–106.30, the vias at (174.80, 103.40 / 104.60 /
  105.80), (175.70, 105.80) and (176.90, 105.80).
  The drills are re-asserted **after** the SES import (`fix_tab_vias()`): the DSN/SES
  round trip hands the pre-routed vias to Freerouting and they come back with the
  router's padstack for the net class, which is how the first SQU-35 board ended up with
  the 0.30 mm column at 0.40 mm (SQU-38 item 3).
- **Amp decoupling:** C21 (0.1 µF) 0.7 mm below VDD pins 7/8, C22 (10 µF) right below it,
  both on the +5V feed to the pins. Each GND pad has its own via to L2.
- **Antenna end:** a rule area at x 120.50–135.50, y 100.00–104.60 (all four copper
  layers) takes signal tracks and vias out of the strip between the top board edge and
  U1's pin 3 / pin 38 row. Pads and the pours are still allowed, so L2 is not slotted.
  This is what SQU-32 had to do by hand for CC_SENSE; it is now a constraint the router
  cannot break. CC_SENSE's run across the module is 13.12 mm at y = 104.99, 4.99 mm
  below the top edge (it was 14.30 mm at 2.76 mm when Iris flagged it). The only copper
  left at y = 102.76 is U1 pin 39's own pad and the 1.00 mm stub leaving it at
  x 136.75–137.75, both outside the rule area and east of the antenna.

**Design review fixes (Iris, SQU-31, 2026-10-05):** M1 C21/C22 moved to U3 pins 7/8;
M2 0.6 mm +5V sections on the LED path widened or rerouted (see +5V above); M3 U2 tab
copper area + vias; M4 AMP_SD under U1 moved to y = 106.4 (0.76 mm from the module's
GND pad, was 0.15 mm).

**Review polish (SQU-32, 2026-10-05)**, on top of the J3 side-entry change:

| Item | Result |
|---|---|
| C6 rotated | C6's +3V3 pad now faces U1 pin 2, with a 2.01 mm × 0.3 mm F.Cu track straight to it (was plane-only, 4.5 mm apart). C7 is unchanged: the EN track crosses the corridor between C7 and C6 at y = 104.03, so C7 keeps its own +3V3 plane via. |
| CC_SENSE lower | Was 14.3 mm across the module at y = 102.76, 2.76 mm below the antenna line. Now 13.12 mm at y = 104.99, 4.99 mm below, held there by the antenna-end rule area rather than by hand. What is left at y = 102.76 is U1 pin 39's own pad and the 1.00 mm stub leaving it, both east of the antenna and outside the rule area. |
| C40 GND | **Skipped**, no room — see SQU-32. |
| Mic hole | No via on any layer within 2.00 mm of the sound hole at (108.50, 135.51), so the case gasket sits flat. Enforced by the "MK1 gasket seat" rule area: a 2.5 mm radius ring that forbids **vias** but still allows tracks and the pours, so the planes stay solid round the mic. It is not a no-copper rule. |
| Island neck slot | 1.00 × 1.25 mm routed slot at x 150.50–151.50, y 131.35–132.60. The 6.80 mm top neck becomes 5.80 mm. 1.0 mm is the JLC routed-slot minimum; it sits between the +3V3 feed at x = 149.7 and the I2C pair at x ≈ 152.4–152.9, with a 0.35 mm copper keep-out round it. |
| U3 pin 3/11 vias | Pin 11's via sits clear of the exposed pad. **Pin 3's via could not move** — see SQU-32. |
| U2 via column | 0.65 mm clear of the tab copper (see LDO heat above). |
| +5V widths | See the +5V table above. The common inlet and the LED path are 1.50 mm; only the two parallel 0.60 mm necks through the USB-C pin field are narrower (SQU-38 item 2 corrected the earlier "1.50 mm end to end" claim). |
| U3 pins 7/8 | The wide feed stops 0.30 mm clear of the pad row; the last 0.70 mm is 0.25 mm, equal to the pad width, so the fillets are even. |
| Silkscreen | The silk pass moves reference fields away from pads, other silk and the board edge where it can. It cannot always: 7 references in the dense 0603 clusters still sit over a neighbour's pad — see the DRC warnings below. |

After SQU-35 all of these are rules inside `tools/pcb_build.py`, so a rebuild reproduces
them. `tools/pcb_squ32.py` was the one-shot, coordinate-exact patch that first applied
them to `f8a871e`; it is **superseded** and must not be re-run. `tools/pcb_silk.py` is
still the silkscreen pass and is re-runnable (it now also refuses to park a reference
nearer another part's centre than its own, so a label is never read as the neighbour's).
`tools/pcb_audit.py` prints the measurements quoted in this file.

**Re-review fixes (Iris, SQU-37 → SQU-38, 2026-10-06)**, on top of SQU-35:

| Item | Result |
|---|---|
| J3 edge margin | J3 (184.600 → **184.500**, 117.500) rot 90. Mounting-tab copper 189.200 → **189.100**, so the margin to the routed edge at 189.500 is **0.400 mm**, not 0.300 mm. The housing front stays 0.55 mm inside the edge and the cable still leaves straight out of the right edge; the pin-1 triangle moved with the footprint, tip now (179.60, 124.50). EPD track lengths are unchanged — the pads are 3.5 mm long, so the routes still land well inside them. |
| +5V inlet | The common section from J1's VBUS pads to the trunk split was 1.00 mm for 8.23 mm plus a 0.56 mm turn. It is now a single **1.50 mm** riser at x = 110.60, y 111.375 → 124.600 (13.23 mm), fed by two 0.60 mm × 1.45 mm necks out of the pin field. 0.345 mm to J1's A-row pads, 0.200 mm at the necks (unchanged). |
| M3 tab vias | The four 0.30 mm drills are back (0.60 mm pads), with the fifth at 0.40 mm: exactly the geometry Iris reviewed in SQU-31. `fix_tab_vias()` re-asserts them after the SES import so the router cannot change them again. |
| Records | EPD lengths, the +5V width table, the mic gasket-seat rule (no **vias**, not no copper) and the silkscreen warning breakdown are corrected above against the committed board. |

**DRC at hand-over (SQU-39):** **0 errors, 0 unconnected, 0 schematic-parity issues**;
ERC 0 errors (1 pre-existing warning: U3's PAD pin is Unspecified against a Power input).
`tools/check_pinout.py` PASS. 12 DRC warnings, all silkscreen (14 at SQU-38):

- **2 `silk_edge_clearance`:** U1's module body outline where the antenna overhangs the
  top edge (the module footprint would have to be edited, which trades them for a
  `lib_footprint_mismatch` warning) — unchanged from before;
- **3 `silk_overlap`:** reference designators touching other silk in the dense 0603
  clusters (R1/R2, R6/R7, R9/R10 at 1.7–1.8 mm pitch), where the text is wider than the
  gap between parts. Cosmetic. The C1/C2/C10/C11 overlaps are gone with SQU-39 (those
  parts now have room, and C30 / C10 / C11 / MK1 have fixed label spots, `REF_AT` in
  `tools/pcb_build.py`);
- **7 `silk_over_copper`:** four references (**R1, R7, R9, R10**, in the CC and mic 0603
  clusters) printed over a neighbouring part's pad. These are **not** harmless overlaps —
  the fab clips silkscreen off pads, so those four references may come out partly or
  completely missing on the real board. **Do not assume every reference prints legibly.**
  Accepted for five hand-assembled Rev A boards because assembly works from
  the KiCad board and the F.Fab layer, and the markings that matter without a screen —
  J3's pin-1 triangle, the electrolytic polarity marks and the connector outlines — are
  clear of pads. Worth a silkscreen pass at rev B (Iris, SQU-37).

The count was 5 before SQU-35, because the old silk pass was allowed to park a reference
on a neighbouring part; it is no longer, so labels sit on their own part and overlap
instead. The readable one is the safer trade.

**SQU-45 re-check** (TP2 reference moved up 1.90 mm into the TP1/TP3 label row; no other
board change): DRC 0 errors, 0 unconnected, 0 parity issues, the same 12 silkscreen
warnings (none on TP1–TP7); ERC unchanged; `tools/check_pinout.py` PASS. Only the
F.Silkscreen Gerber changed.

Report: `reports/pcb/room-node-drc.rpt`. Pictures: `reports/pcb/room-node-top.png`,
`room-node-bottom.png` (the side that faces the display), `room-node-copper-top.png`,
`room-node-copper-bottom.png`.
Gerbers + drill (JLCPCB): `reports/fab/room-node-rev-a-gerbers.zip`.

**Open points for review**
1. Hole positions are from the Waveshare drawing. Check them on the real module.
2. Mic sound hole faces the display (bottom side). The case needs an air path from the
   room to the gap between the boards, near the bottom-left corner.
3. SW1/SW2 (RESET/BOOT, only for flashing) and D1 face the back of the case. The
   voice button was removed (2026-10-05, wake word only).
4. Some F.Cu tracks run under U1 (under the module's solder mask). Normal for this
   module, but Iris checks it.
5. Silkscreen: the C6/C7/R3/C8 references end up at x ≈ 121.5, under the module body,
   where they cannot be read after U1 is fitted. Fine for assembly (the module goes on
   last), but worth a look at rev B.
6. **SQU-35:** the EPD signals are now 55.8–71.9 mm long because J3 sits at the far end
   from U1. Iris cleared this against the Waveshare driver's 2 MHz SPI (SQU-37); still
   verify the display at bring-up, with a short display cable.
7. **SQU-35, new:** the LDO moved to the top-right corner, 37.3 mm from the AHT20
   (was 38.4 mm). Check the thermal reasoning in "Sensor isolation" above.
8. **SQU-35, closed by SQU-38:** J3's mounting-tab copper was at exactly the 0.30 mm
   copper-to-edge limit; J3 moved 0.10 mm in and it is now 0.40 mm.
9. **SQU-35, updated by SQU-39:** the case needs an opening or channel on the **right**
   side for the display cable, and the LED cable now leaves at the **bottom edge**, under
   U1, about 24–30 mm from the left end (J4 courtyard x 121–132). USB-C stays on the
   left, now centred. The enclosure notes in `docs/enclosure.md` predate both changes.
10. **SQU-39, closed by SQU-42:** J4 is now the side-entry S3B-XH-A (Chris, SQU-17),
   cable straight out of the bottom edge. The housing front is 0.30 mm inside the edge;
   the plug sticks out past it, so the case needs a ~10 mm slot in the bottom wall
   centred on x = 126.5. `docs/enclosure.md` does not have this yet.
11. **SQU-39, closed:** C30 (10 mm can) sits on the bottom edge between the mic and J4;
   its courtyard is 0.31 mm inside the edge. Chris: OK, the case clears it (SQU-17).

## Placement

- **Antenna:** the module antenna hangs over the board edge. No copper, parts or traces
  under or near it. Respect the footprint keep-out.
- **Mic (MK1):** opposite end of the board from the speaker connector and the amp.
  Away from the LED connector and the antenna. Sound enters from the **bottom** through
  the hole in the footprint: no copper, vias or traces inside the GND ring, and keep the
  bottom side around the hole clear for a gasket.
- **AHT20 (U6):** board edge, far from module, LDO, amp and LED connector. Slots left,
  right and in the neck, open at the top for the tracks.
- **USB:** U5 at J1. R6/R7 near J1. C9/TP8 near U1 pin 39.
- **Amp:** C20/C21/C22 at U3. Short, wide +5V and GND.
- **LED:** J4 (side entry, mouth on the edge) on the bottom edge under U1, at least 15 mm from the AHT20 island, C30 at
  the connector. R30 stays at U1 pin 23, where a source series resistor belongs.
- **Display:** J3 on the right edge, side entry, pin 1 marked on the silk. C50 at its
  +3V3 pin.
- **Ground:** route amp and LED return currents so they do not pass under the mic or the sensor.

## Assembly

- Hand assembly: paste + stencil + hot air.
- The module pad and the amp pad cannot be inspected. If the board resets under Wi-Fi or
  the amp cuts out, suspect those joints first.
- After the mic is fitted: no board wash, no IPA, no ultrasonic. No hot air or air jet into the sound hole.

## Bring-up order

1. Check every rail to GND for shorts.
2. Bench supply, 5 V, current limit ~200 mA. Watch the current.
3. Check +5V, then +3V3.
4. USB: enumerate, flash, read logs.
5. Each part in turn: LEDs, display, sensor, mic, speaker.
6. **Hot-plug test:** plug into a laptop USB port 10+ times. If the port shuts off, rev B adds a soft-start switch.
7. **CC sense:** compare TP8 (multimeter) with the firmware value on a 3 A charger, a laptop port and a USB-A cable.
