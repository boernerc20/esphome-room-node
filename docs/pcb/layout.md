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
- **Cable:** J3 (JST-PH 8-pin) is on the bottom edge, under U1. Use a short PH-to-PH
  8-pin cable, pin 1 to pin 1 (see the display sheet notes in `schematic.md`).
- **U1 antenna** overhangs the top edge, so it sticks out past the display outline by
  about 6 mm. The case must leave room for it. No metal in front of it.

**Placement** (looking at the parts side, USB-C on the left):

| Area | Parts |
|---|---|
| Left edge | J1 USB-C, U5 ESD, R1/R2/R6/R7 (CC), C1/C2 |
| Left, lower | U2 LDO (3 vias in the tab), C3/C4/C5 |
| Bottom-left corner | MK1 mic + R8/R11/C10/C11. Sound hole through the board |
| Centre-left, top edge | U1 module; C6/C7/R3/C8 and R9/R10 at its left pins |
| Under U1 | TP1–TP7 row, R30, J3 display connector on the bottom edge |
| Right of U1 | C9/TP8 (CC sense), SW2 BOOT / SW1 RESET / SW3 VOICE, R4/R5/R12, D1 |
| Bottom centre | U6 AHT20 + C40 on an island: slots left and right, no copper pour |
| Right, top | J4 LED connector, C30 1000 µF |
| Right, bottom | U3 amp + C21/C22/R20, C20 470 µF, J2 speaker |

**Layers**

| Layer | Use |
|---|---|
| F.Cu (L1) | Parts, most signals, GND fill |
| In1.Cu (L2) | GND plane, solid |
| In2.Cu (L3) | +3V3 plane, solid. No tracks |
| B.Cu (L4) | Signals, +5V trunk to C30/J4/C20, GND fill |

- **+5V** is a track, not a plane: 0.6–1.0 mm from J1 to the LDO, the amp and J4.
  Short 0.25–0.4 mm stubs only at the amp pins (0.5 mm pitch) and the J1 VBUS loop.
- **GND / +3V3:** every SMD pad has its own via to its plane (fan-out). GND stitching
  vias on a 5 mm grid and along the edge.
- **Speaker pair** U3 → J2: 0.4–0.5 mm, side by side, no vias.
- **USB D±:** about 9 mm, 0.2 mm tracks. USB is Full Speed (12 Mbit/s), so length
  match and impedance are not critical.

**DRC at hand-over:** 0 errors, 0 unconnected, 0 schematic-parity issues. 53 warnings,
all silkscreen (reference text overlaps pads or other text). Report:
`reports/pcb/room-node-drc.rpt`. Pictures: `reports/pcb/room-node-top.png`,
`room-node-copper-top.png`, `room-node-copper-bottom.png`.
Gerbers + drill (JLCPCB): `reports/fab/room-node-rev-a-gerbers.zip`.

**Open points for review**
1. Hole positions are from the Waveshare drawing. Check them on the real module.
2. Mic sound hole faces the display (bottom side). The case needs an air path from the
   room to the gap between the boards, near the bottom-left corner.
3. SW1–SW3 and D1 face the back of the case. The VOICE button and the status LED are
   not reachable / visible from the front. Plan a case opening or a light pipe.
4. Some F.Cu tracks run under U1 (under the module's solder mask). Normal for this
   module, but Iris checks it.
5. Silkscreen is not tidied.

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
