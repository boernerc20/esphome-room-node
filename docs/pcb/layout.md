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

## Rev A board (placed and routed; connectors moved to the edges 2026-10-05, SQU-35)

`tools/pcb_build.py` builds the whole board: outline, holes, slots, parts, planes,
placement, rule areas, hand-made routes (J1 VBUS, the whole +5V net, amp pins, the
C6 → U1 pin 2 link, the LDO tab copper, the sensor island) and plane fan-out vias.
Only signals are left to Freerouting 2.4.1 (needs Java 25, not in the container by
default). The router is not deterministic: a rebuild gives different signal tracks,
so re-running the pipeline means re-running the checks and the reports with it.

```
kicadpython tools/pcb_build.py place out.dsn     # overwrites room-node.kicad_pcb
java -jar freerouting-2.4.1.jar -de out.dsn -do out.ses -mp 100 --gui.enabled=false
kicadpython tools/pcb_build.py route out.ses     # import, widen +5V, GND fills, stitching
kicad-cli pcb drc --severity-all --format report -o drc.rpt kicad/room-node/room-node.kicad_pcb
kicadpython tools/pcb_silk.py drc.rpt            # repeat drc + silk until the count settles
kicadpython tools/pcb_audit.py                   # the measurements quoted below
```

Everything the design reviews asked for is now in the generator, not in one-shot patch
scripts, so it cannot be lost in a rebuild: M1 (C21/C22 at U3 pins 7/8), M3 (LDO tab
copper area and its vias), M4 and the SQU-32 items (C6 rotated with a direct track to
U1 pin 2, CC_SENSE kept away from the antenna end, the mic-hole gasket seat, the island
neck slot, the necked +5V feed at U3 pins 7/8, the +5V widths).
`tools/pcb_squ32.py` is the superseded one-shot patch and is kept only as history.

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
| J1 USB-C | left | unchanged, (109.155, 110.525), front flush with x = 100.0 | out of the left edge |
| J4 LED strip (B3B-XH-A, vertical) | left, below J1 | (103.500, 122.300); pin 1 +5V at x = 103.5, pin 2 data 106.0, pin 3 GND 108.5 | up, off the left end |
| J3 display (S8B-PH-SM4-TB, side entry) | right | (184.600, 117.500) rot 90; pad row at x = 181.75, pin 1 (181.75, **124.50**) at the bottom, pin 8 at 110.50 | straight out of the right edge |
| J2 speaker (B2B-PH-SM4-TB) | bottom right | (176.300, 133.000), clear of J3 | up |

- **J3** faces out over the right edge. Its mounting-tab pads reach x = 189.20, exactly
  the 0.3 mm copper-to-board-edge limit against the edge at x = 189.50, so the housing
  cannot sit any further out. Its courtyard spans y 106.86–128.15, which keeps it
  4.36 mm clear of H2 and 7.35 mm clear of H4. Use a short PH-to-PH 8-pin cable, pin 1
  to pin 1 (see the display sheet notes in `schematic.md`).
- **J3 pin 1** is hidden under the side-entry housing, so it is marked with a filled
  silkscreen triangle on the board side of the pad row, tip at (179.70, 124.50),
  pointing at pin 1.
- **J4 + C30.** J1 VBUS (pad B4) → J4 pin 1 is 7.94 mm and → C30 pad 1 is 12.18 mm, pad
  centre to pad centre; they were **65.24 mm** and **70.23 mm**. C30 is the next
  part along the trunk, 0.21 mm from J4's courtyard and 11.54 mm pad to pad; the 1000 µF
  can is 10 mm across, and the bottom-left corner is taken by the mic and H3, so this is
  as close as it gets without moving the mic.
- **Mic sound hole** stays at (108.500, 135.510) in the bottom-left corner, as does its
  case opening. J4 did **not** have to move it: the nearest point of J4's courtyard is
  **9.26 mm** away. Nothing is within 2.00 mm of the hole on any layer (a new
  "MK1 gasket seat" via keep-out of 2.5 mm radius enforces it).

**Placement** (looking at the parts side, USB-C on the left):

| Area | Parts |
|---|---|
| Left edge, upper | J1 USB-C, U5 ESD, R1/R2/R6/R7 (CC) |
| Left edge, below J1 | **J4 LED connector**, then C30 1000 µF to its right; C1/C2 below |
| Bottom-left corner | MK1 mic + C10/C11/R8/R11. Sound hole through the board |
| Centre-left, top edge | U1 module; C6/C7/R3/C8 and R9/R10 at its left pins |
| Under U1 | TP1–TP7 row (x 124.3–141.1, y 124.5), R30 at U1 pin 23 |
| Right of U1 | C9/TP8 (CC sense), SW2 BOOT / SW1 RESET, R4/R12, D1 |
| Bottom centre | U6 AHT20 + C40 on an island: slots left, right and in the neck |
| Right, top | **U2 LDO** (tab on a F.Cu +3V3 copper area with 5 vias to L3), C3/C4/C5 |
| Right edge | **J3 display connector**, side entry; C50 at its +3V3 pin |
| Right, lower | U3 amp + C21/C22 at VDD pins 7/8, R20, C20 470 µF, J2 speaker |

**What moved and why** (every number measured by `tools/pcb_audit.py`):

| Part | From | To | Reason |
|---|---|---|---|
| J3 | (128.0, 133.08), bottom edge under U1 | (184.6, 117.5) rot 90, right edge | display cable out of the right edge |
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

**Sensor isolation.** Moving the LDO is the change to look at hardest. U2's tab is now
**37.26 mm** from U6's +3V3 pad against **38.41 mm** before — 1.15 mm closer, with the
island and its three slots unchanged. The bottom-left corner could not hold J4, C30 and
the LDO as well as the mic and H3, and of the two spots that were left (bottom centre,
or the top right that the LED connector vacated) the top right is the far one: putting
U2 in the bottom centre would have taken the gap down to about 25 mm. The amp U3 is
21.95 mm from U6, unchanged.

**What got longer.** The display connector is now at the opposite end of the board from
U1, so the six EPD signals grew from 17.5–33.6 mm to 58.8–71.7 mm (longest: EPD_CLK,
71.65 mm, 4 vias). The display SPI is a few MHz and the e-paper refresh is not timing
critical, so this is a length the design can carry; it is the direct cost of the short
cable. Going the other way, the LED data line J4 pin 2 dropped from 56.85 mm to
35.22 mm and the speaker pair is unchanged (14.14 / 16.12 mm, no vias).

**Layers**

| Layer | Use |
|---|---|
| F.Cu (L1) | Parts, most signals, GND fill |
| In1.Cu (L2) | GND plane, solid |
| In2.Cu (L3) | +3V3 plane, solid. No tracks |
| B.Cu (L4) | Signals, +5V trunk from J1 to J4/C30 and along the bottom, GND fill |

- **+5V** is a track, not a plane, and the whole net is hand routed (`preroute()` in
  `tools/pcb_build.py`), not left to the router. Topology:

  | Leg | Layer | Width | Length | Carries |
  |---|---|---|---|---|
  | J1 VBUS loop + exit past the USB-C pin row | B.Cu and F.Cu in parallel | 0.50–0.60 | 4.3 + 4.8 + 5.4 mm | everything |
  | exit riser → trunk at y = 124.6 → **J4 pin 1** and **C30 pad 1** | B.Cu | 1.00 then **1.50** | 4.5 + 21.3 mm | LED strip, ~2 A |
  | C30 → spine along the bottom at y = 128.0 → C20 pad 1 | B.Cu | **1.50** | 59.3 mm | amp + LDO |
  | TP6 straight down onto the spine | F.Cu | 1.00 | 3.5 mm | test point |
  | C20 → C22 → C21 → U3 pins 7/8 | F.Cu | 1.00 / 0.80 | 24.5 mm | amp, ~0.9 A peak |
  | spine → up past U3 → U2 pin 3 and C3 | B.Cu + F.Cu | 1.00, 0.60 for 9.4 mm beside U3 | 24.0 mm | LDO, ≤ 0.5 A |
  | trunk → C1 → C2 | B.Cu + F.Cu | 1.00 | 6.3 mm | USB input caps |

  1.50 mm carries about 3.2 A and 1.00 mm about 2.3 A at a 10 °C rise (IPC-2221, 1 oz
  external). Everything on the LED path is 1.50 mm; nothing below 1.0 mm is on it.
  The deliberately thin parts are 0.25 mm stubs at U3's 0.5 mm-pitch pins (including the
  0.25 mm neck into pins 7/8 and the GAIN_SLOT stub to pin 2, which carries no current),
  0.6 mm through the USB-C pin field where the 0.7 mm pads on a 1.35 mm pitch leave no
  more room (F.Cu and B.Cu run in parallel there), and 0.6 mm for 9.4 mm of the LDO
  branch where it squeezes past U3.
- **GND / +3V3:** every SMD pad has its own via to its plane (fan-out). GND stitching
  vias on a 5 mm grid and along the edge, 45 of them.
- **Speaker pair** U3 → J2: 0.4–0.5 mm, side by side, no vias.
- **USB D±:** about 18–19 mm per line from J1 to U1 (about 9 mm on the MCU side of U5),
  0.2 mm tracks, matched to about 1 mm. USB is Full Speed (12 Mbit/s), so length
  match and impedance are not critical.

- **LDO heat:** the U2 tab sits on a F.Cu +3V3 copper area (6.2 × 3.3 mm, 20.4 mm², full
  connection) with vias to the L3 plane next to the tab, not in it (no solder wicking):
  **4 × 0.3 mm drill plus 1 × 0.4 mm drill beside the tab, 7 vias in total on the copper
  area** (the other two are C4's and C5's). C4/C5 +3V3 pads are on the same area. The
  0.3 mm column sits 0.65 mm clear of the tab copper, so a weak via tent cannot pull
  solder off the tab. The whole cluster moved with U2 as a rigid block in SQU-35, so the
  geometry is the one Iris reviewed; it is now generated from the tab pad position
  (`TAB_AREA` / `TAB_VIAS` in `tools/pcb_build.py`) instead of fixed coordinates. The
  area is at x 171.90–178.10, y 103.00–106.30.
- **Amp decoupling:** C21 (0.1 µF) 0.7 mm below VDD pins 7/8, C22 (10 µF) right below it,
  both on the +5V feed to the pins. Each GND pad has its own via to L2.
- **Antenna end:** a rule area at x 120.50–135.50, y 100.00–104.60 (all four copper
  layers) takes signal tracks and vias out of the strip between the top board edge and
  U1's pin 3 / pin 38 row. Pads and the pours are still allowed, so L2 is not slotted.
  This is what SQU-32 had to do by hand for CC_SENSE; it is now a constraint the router
  cannot break. CC_SENSE's run across the module is 13.12 mm at y = 104.99, 4.99 mm
  below the top edge (it was 14.30 mm at 2.76 mm when Iris flagged it). The only copper
  left at y = 102.76 is U1 pin 39's own pad.

**Design review fixes (Iris, SQU-31, 2026-10-05):** M1 C21/C22 moved to U3 pins 7/8;
M2 0.6 mm +5V sections on the LED path widened or rerouted (see +5V above); M3 U2 tab
copper area + vias; M4 AMP_SD under U1 moved to y = 106.4 (0.76 mm from the module's
GND pad, was 0.15 mm).

**Review polish (SQU-32, 2026-10-05)**, on top of the J3 side-entry change:

| Item | Result |
|---|---|
| C6 rotated | C6's +3V3 pad now faces U1 pin 2, with a 2.01 mm × 0.3 mm F.Cu track straight to it (was plane-only, 4.5 mm apart). C7 is unchanged: the EN track crosses the corridor between C7 and C6 at y = 104.03, so C7 keeps its own +3V3 plane via. |
| CC_SENSE lower | Was 14.3 mm across the module at y = 102.76, 2.76 mm below the antenna line. Now 13.12 mm at y = 104.99, 4.99 mm below, held there by the antenna-end rule area rather than by hand. Only U1 pin 39's own pad is left at y = 102.76. |
| C40 GND | **Skipped**, no room — see SQU-32. |
| Mic hole | Nothing on any layer within 2.00 mm of the sound hole at (108.50, 135.51), so the case gasket sits flat. Enforced by the "MK1 gasket seat" rule area: a 2.5 mm radius ring that forbids vias but still allows tracks and the pours, so the planes stay solid round the mic. |
| Island neck slot | 1.00 × 1.25 mm routed slot at x 150.50–151.50, y 131.35–132.60. The 6.80 mm top neck becomes 5.80 mm. 1.0 mm is the JLC routed-slot minimum; it sits between the +3V3 feed at x = 149.7 and the I2C pair at x ≈ 152.4–152.9, with a 0.35 mm copper keep-out round it. |
| U3 pin 3/11 vias | Pin 11's via sits clear of the exposed pad. **Pin 3's via could not move** — see SQU-32. |
| U2 via column | 0.65 mm clear of the tab copper (see LDO heat above). |
| +5V widths | See the +5V table above. The LED path is 1.50 mm end to end. |
| U3 pins 7/8 | The wide feed stops 0.30 mm clear of the pad row; the last 0.70 mm is 0.25 mm, equal to the pad width, so the fillets are even. |
| Silkscreen | Reference fields moved off pads, off other silk and off the board edge. |

After SQU-35 all of these are rules inside `tools/pcb_build.py`, so a rebuild reproduces
them. `tools/pcb_squ32.py` was the one-shot, coordinate-exact patch that first applied
them to `f8a871e`; it is **superseded** and must not be re-run. `tools/pcb_silk.py` is
still the silkscreen pass and is re-runnable (it now also refuses to park a reference
nearer another part's centre than its own, so a label is never read as the neighbour's).
`tools/pcb_audit.py` prints the measurements quoted in this file.

**DRC at hand-over:** **0 errors, 0 unconnected, 0 schematic-parity issues**; ERC 0
errors (1 pre-existing warning: U3's PAD pin is Unspecified against a Power input).
`tools/check_pinout.py` PASS. 14 DRC warnings, all silkscreen:

- 2 are U1's module body outline where the antenna overhangs the top edge (the module
  footprint would have to be edited, which trades them for a `lib_footprint_mismatch`
  warning) — unchanged from before;
- 12 are reference designators in the two dense 0603 clusters (R1/R2, R6/R7, R9/R10 at
  1.7–1.8 mm pitch, and C1/C2/C10/C11), where the text is wider than the gap between
  parts. They were 3 before, because the old silk pass was allowed to park a reference
  on a neighbour; SQU-35 stopped that, so those labels now sit on their own part and
  overlap instead. Cosmetic either way, and the readable one is the safer trade.

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
6. **SQU-35, new:** the EPD signals are now 59–72 mm long because J3 sits at the far end
   from U1. Confirm that is acceptable for the Waveshare driver's SPI rate before the
   boards are ordered.
7. **SQU-35, new:** the LDO moved to the top-right corner, 37.3 mm from the AHT20
   (was 38.4 mm). Check the thermal reasoning in "Sensor isolation" above.
8. **SQU-35, new:** J3's mounting-tab copper is at exactly the 0.30 mm copper-to-edge
   limit on the right edge. Confirm JLCPCB will take it, or pull J3 in by 0.1 mm.
9. **SQU-35, new:** the case needs an opening or channel on the **right** side for the
   display cable, and the LED cable now leaves on the **left** next to USB-C. The
   enclosure notes in `docs/enclosure.md` predate this change.

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
- **LED:** J4 on the left edge under J1, C30 next to it on the +5V trunk. R30 stays at
  U1 pin 23, where a source series resistor belongs.
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
