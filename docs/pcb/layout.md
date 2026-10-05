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

## Rev A board (placed and routed, 2026-10-04)

`tools/pcb_build.py` builds the whole board: outline, holes, parts, planes, placement,
hand-made routes (J1 VBUS, amp pins, sensor island), plane fan-out vias. The rest is
routed by Freerouting 2.4.1 (Java 25, not in the container by default). The router is not
deterministic: a rebuild gives different tracks. **From here on, edit the board by hand
in KiCad**; do not re-run the script over hand work.

```
kicadpython tools/pcb_build.py place out.dsn     # overwrites room-node.kicad_pcb
java -jar freerouting-2.4.1.jar -de out.dsn -do out.ses -mp 150 --gui.enabled=false
kicadpython tools/pcb_build.py route out.ses     # import, widen +5V, GND fills, stitching
```

**Mounting.** Same outline and holes as the Waveshare 2.9" e-paper module
(Waveshare drawing: 89.5 × 38.0 mm, holes 2.5 mm from each edge, 84.5 × 33.0 mm pattern).
4 × M2 holes (2.2 mm, H1–H4). The board sits behind the display on M2 standoffs.
The bottom side (no parts) faces the display. All parts face the back of the case.

- **Standoffs:** the display's driver board has parts and its 8-pin connector on its back.
  Use standoffs tall enough to clear the plug: about 10 mm.
- **Cable:** J3 is a **side-entry** JST-PH 8-pin (S8B-PH-SM4-TB) on the bottom edge,
  under U1, with its mouth facing out over that edge so the cable runs straight to the
  display behind the board. The housing front face is 0.52 mm inside the board edge
  (y = 137.48 against an edge at y = 138.00); it cannot sit flush because the two
  mounting-tab pads reach y = 137.68 and need the 0.3 mm copper-to-edge clearance.
  Use a short PH-to-PH 8-pin cable, pin 1 to pin 1 (see the display sheet notes in
  `schematic.md`). Pin 1 is at x = 121.0, the pad row at y = 130.23; each pin has a
  via at y = 133.90 behind the pad row, under the housing, with a 2.4 mm F.Cu stub
  forward into the pad.
- **U1 antenna** overhangs the top edge, so it sticks out past the display outline by
  about 6 mm. The case must leave room for it. No metal in front of it.

**Placement** (looking at the parts side, USB-C on the left):

| Area | Parts |
|---|---|
| Left edge | J1 USB-C, U5 ESD, R1/R2/R6/R7 (CC), C1/C2 |
| Left, lower | U2 LDO (tab on a F.Cu +3V3 copper area with 5 vias to L3), C3/C4/C5 |
| Bottom-left corner | MK1 mic + R8/R11/C10/C11. Sound hole through the board |
| Centre-left, top edge | U1 module; C6/C7/R3/C8 and R9/R10 at its left pins |
| Under U1 | TP1–TP7 row, R30, J3 display connector on the bottom edge |
| Right of U1 | C9/TP8 (CC sense), SW2 BOOT / SW1 RESET, R4/R12, D1 |
| Bottom centre | U6 AHT20 + C40 on an island: slots left and right, no copper pour |
| Right, top | J4 LED connector, C30 1000 µF |
| Right, bottom | U3 amp + C21/C22 at VDD pins 7/8, R20, C20 470 µF, J2 speaker |

**Layers**

| Layer | Use |
|---|---|
| F.Cu (L1) | Parts, most signals, GND fill |
| In1.Cu (L2) | GND plane, solid |
| In2.Cu (L3) | +3V3 plane, solid. No tracks |
| B.Cu (L4) | Signals, +5V trunk to C30/J4/C20, GND fill |

- **+5V** is a track, not a plane. LED / amp path: J1 → C1 on F.Cu and B.Cu in parallel
  (0.7–0.9 mm each through the USB-C pin row and shell pads, then 1.2 mm), 1.0–1.2 mm to
  C3 and along the bottom row, **1.5 mm** from TP6 to C20, 1.0 mm B.Cu to C30/J4, 1.0 mm
  up to the amp. 1.5 mm carries about 3.2 A at a 10 °C rise (IPC-2221, 1 oz).
  Thin parts: 0.25–0.4 mm stubs at the amp pins (0.5 mm pitch), the J1 VBUS loop, and
  0.6 mm to amp pin 2 (GAIN_SLOT, no current) and to U5.
- **GND / +3V3:** every SMD pad has its own via to its plane (fan-out). GND stitching
  vias on a 5 mm grid and along the edge.
- **Speaker pair** U3 → J2: 0.4–0.5 mm, side by side, no vias.
- **USB D±:** about 18–19 mm per line from J1 to U1 (about 9 mm on the MCU side of U5),
  0.2 mm tracks, matched to about 1 mm. USB is Full Speed (12 Mbit/s), so length
  match and impedance are not critical.

- **LDO heat:** the U2 tab sits on a F.Cu +3V3 copper area (about 6 × 3.3 mm, 20.4 mm²,
  full connection) with vias to the L3 plane next to the tab, not in it (no solder
  wicking): **4 × 0.3 mm drill plus 1 × 0.4 mm drill beside the tab, 7 vias in total on
  the copper area** (the other two are C4's and C5's). C4/C5 +3V3 pads are on the same
  area. The 0.3 mm column sits at x = 116.3, 0.65 mm clear of the tab copper, so a weak
  via tent cannot pull solder off the tab.
- **Amp decoupling:** C21 (0.1 µF) 0.7 mm below VDD pins 7/8, C22 (10 µF) right below it,
  both on the +5V feed to the pins. Each GND pad has its own via to L2.

**Design review fixes (Iris, SQU-31, 2026-10-05):** M1 C21/C22 moved to U3 pins 7/8;
M2 0.6 mm +5V sections on the LED path widened or rerouted (see +5V above); M3 U2 tab
copper area + vias; M4 AMP_SD under U1 moved to y = 106.4 (0.76 mm from the module's
GND pad, was 0.15 mm).

**Review polish (SQU-32, 2026-10-05)**, on top of the J3 side-entry change:

| Item | Result |
|---|---|
| C6 rotated | C6's +3V3 pad now faces U1 pin 2, with a 2.01 mm × 0.3 mm F.Cu track straight to it (was plane-only, 4.5 mm apart). C7 is unchanged: the EN track crosses the corridor between C7 and C6 at y = 104.03, so C7 keeps its own +3V3 plane via. |
| CC_SENSE lower | The 14.3 mm run across the module at y = 102.76 (2.76 mm below the antenna line) became 12.05 mm at y = 105.90 (5.90 mm below). Only 2.25 mm is left at y = 102.76, at the module pad itself. |
| C40 GND | **Skipped**, no room — see SQU-32. |
| Mic hole | The GND via at (109.70, 136.81) moved to (110.45, 137.25), 2.61 mm from the sound hole (was 1.77 mm). Nothing is now within a 2.0 mm radius of the hole on B.Cu, so a gasket sits flat. |
| Island neck slot | 1.00 × 1.25 mm routed slot at x 150.20–151.20, y 131.35–132.60. The 6.80 mm top neck becomes 5.80 mm. 1.0 mm is the JLC routed-slot minimum and is all that fits between the +3V3 feed at x = 149.7 and the I2C_SCL B.Cu run that crosses the neck. |
| U3 pin 3/11 vias | Pin 11's via moved from (170.175, 120.75) to (171.90, 120.60): it overlapped the exposed pad by 0.24 mm, now 1.49 mm clear. **Pin 3's via could not move** — see SQU-32. |
| U2 via column | x 116.0 → 116.3 (see LDO heat above). |
| +5V widths | Bottom row at y = 127.275 is 1.50 mm, except the 26.19 mm length that passes the U2 tab, which is 1.40 mm (0.175 mm to the tab pad; 1.5 mm would leave 0.125 mm, under the 0.15 mm rule). C1 → C2 → C3 is now 1.20 mm. |
| U3 pins 7/8 | The 0.8 mm feed stops at y = 123.138, 0.30 mm clear of the pad row; the last 0.70 mm is 0.25 mm, equal to the pad width, so the fillets are even. |
| Silkscreen | 23 reference fields moved off pads, off other silk and off the board edge. 51 silk warnings → 5. |

`tools/pcb_squ32.py` and `tools/pcb_silk.py` are the one-shot patch scripts that produced
this state from `f8a871e`. They are coordinate-exact and are not meant to be re-run.

**DRC at hand-over:** 0 errors, 0 unconnected, 0 schematic-parity issues. 5 warnings,
all silkscreen: 2 are U1's module body outline where the antenna overhangs the top edge
(the module footprint would have to be edited, which trades them for a
`lib_footprint_mismatch` warning), and 3 are R9's reference in the R1/R2/R9/R10 cluster,
where the parts are 1.7 mm apart and there is no free spot for the text. Report:
`reports/pcb/room-node-drc.rpt`. Pictures: `reports/pcb/room-node-top.png`,
`room-node-copper-top.png`, `room-node-copper-bottom.png`.
Gerbers + drill (JLCPCB): `reports/fab/room-node-rev-a-gerbers.zip`.

**Open points for review**
1. Hole positions are from the Waveshare drawing. Check them on the real module.
2. Mic sound hole faces the display (bottom side). The case needs an air path from the
   room to the gap between the boards, near the bottom-left corner.
3. SW1/SW2 (RESET/BOOT, only for flashing) and D1 face the back of the case. The
   voice button was removed (2026-10-05, wake word only).
4. Some F.Cu tracks run under U1 (under the module's solder mask). Normal for this
   module, but Iris checks it.
5. Silkscreen: the C6/C7/R3/C8 references ended up at x ≈ 121.5, under the module body,
   where they cannot be read after U1 is fitted. Fine for assembly (the module goes on
   last), but worth a look at rev B.

## Placement

- **Antenna:** the module antenna hangs over the board edge. No copper, parts or traces
  under or near it. Respect the footprint keep-out.
- **Mic (MK1):** opposite end of the board from the speaker connector and the amp.
  Away from the LED connector and the antenna. Sound enters from the **bottom** through
  the hole in the footprint: no copper, vias or traces inside the GND ring, and keep the
  bottom side around the hole clear for a gasket.
- **AHT20 (U6):** board edge, far from module, LDO, amp and LED connector. Slots on two sides, open at the top for the tracks.
- **USB:** U5 at J1. R6/R7 near J1. C9/TP8 near U1 pin 39.
- **Amp:** C20/C21/C22 at U3. Short, wide +5V and GND.
- **LED:** C30 at J4. R30 near U1.
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
