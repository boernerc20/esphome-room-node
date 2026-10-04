# Rev A layout, assembly and bring-up

For later, when the schematic is done. Rev A is 5 boards, built by hand.

## Board

- 4 layers, solid ground plane. ENIG finish. Order a stencil with the boards.
- All parts on the top side. 0603 minimum. At least 0.5 mm between passives.
- Tent the vias under the module pad and the amp pad. Windowpane the stencil on those pads.
- Readable silkscreen: pin 1 marks, polarity marks, refs.

## Stack-up and design rules (JLCPCB 4-layer)

Stack-up: **JLC04161H-7628**, 1.6 mm, 1 oz outer / 0.5 oz inner.
L1 signals + parts, L2 GND plane, L3 power (+5V / +3V3 pours) + slow signals, L4 signals.

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

## Board setup (done)

`tools/pcb_setup.py` made the starting board. It runs once; it refuses to overwrite a board
that has parts. From here on, the board is edited by hand in KiCad.

- **Outline:** 90 × 50 mm, 2 mm corner radius. **Placeholder** — change it to fit the case.
- **Holes:** 4 × M3 (H1–H4), 3.5 mm from each corner. Board-only footprints.
- **Parts:** all 55 schematic parts, linked to their symbols. **F8** (Update PCB from
  Schematic) updates them in place; it does not add copies.
- **U1 antenna:** overhangs the top edge. The board edge is at the line between the antenna
  and the pads, so the footprint keep-out is fully off the board. Do not move the edge up.
- **Planes** (saved unfilled; press **B** to fill):

| Layer | Zone | Priority |
|---|---|---|
| F.Cu (L1) | GND fill | 0 |
| In1.Cu (L2) | GND plane, whole board | 0 |
| In2.Cu (L3) | +5V: USB/LDO strip (left), band at y 124–128, amp/LED side (right) | 1 |
| In2.Cu (L3) | +3V3: rest of the board | 0 |
| B.Cu (L4) | GND fill | 0 |

- **Stitching:** GND vias every 5 mm along the edge, 1.2 mm in, not under parts.
  Add more GND vias in the board area after routing.
- **Rough placement** by function: USB-C + ESD + CC resistors at the left edge, LDO below
  them, mic bottom-left, sensor and display connector on the bottom edge, buttons and test
  pads under U1, amp + speaker connector bottom-right, LED connector top-right.
  Silkscreen is not tidied.
- **DRC at hand-over:** 0 errors except unrouted nets (90). 0 schematic-parity issues.
  Warnings: silkscreen only, plus 4 small +3V3 islands on L3 (removed on fill).

## Placement

- **Antenna:** the module antenna hangs over the board edge. No copper, parts or traces
  under or near it. Respect the footprint keep-out.
- **Mic (MK1):** opposite end of the board from the speaker connector and the amp.
  Away from the LED connector and the antenna. Sound enters from the **bottom** through
  the hole in the footprint: no copper, vias or traces inside the GND ring, and keep the
  bottom side around the hole clear for a gasket.
- **AHT20 (U6):** board edge, far from module, LDO, amp and LED connector. Slots on three sides.
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
