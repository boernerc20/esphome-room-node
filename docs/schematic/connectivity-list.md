# Room Node — Master Connectivity List

The flat signal-list format used at companies with dedicated hardware teams: one row
per pin-to-net connection, so "is this pin used anywhere" or "what's on GPIO38" is a
table scan, not a hunt across six block docs. This is the **planning-time** record —
once a block is drawn in KiCad, the tool's own netlist (Tools → Generate Netlist,
or the PCB editor's ratsnest) becomes authoritative for that block; update this table
to match if they ever disagree, don't trust this over the drawn schematic.

Companion docs: [`rev-a-architecture.md`](rev-a-architecture.md) (block diagram, power
tree, rationale), `block-N-*.md` (per-block parts + wiring diagrams).

**Status:** Block 1 complete (drawn + reviewed). Blocks 2-6 not yet added — append as
each is designed.

---

## Block 1 — MCU + Power + USB

| Net | Ref | Pin | Pin name | Notes |
|---|---|---|---|---|
| `+5V` | J1 | A4,B4,A9,B9 | VBUS | USB-C input |
| `+5V` | U2 | 3 | VIN | LDO input |
| `+5V` | U5 | 5 | VBUS | ESD array supply |
| `+5V` | C1 | 1 | + | 10 µF bulk |
| `+5V` | C2 | 1 | + | 0.1 µF |
| `+5V` | TP6 | 1 | — | test point |
| `+3V3` | U1 | 2 | 3V3 | module supply |
| `+3V3` | U2 | 2 | VOUT/tab | LDO output |
| `+3V3` | R3,R4,R5 | 1 | — | EN/IO0/VA_BTN pull-ups |
| `+3V3` | C4,C5,C6,C7 | 1 | + | decoupling, see block-1 doc for values |
| `+3V3` | TP5 | 1 | — | test point |
| `GND` | J1 | A1,B1,A12,B12,SH | GND/Shield | |
| `GND` | U1 | 1,40,41 | GND + pad | thermal pad, via array under it |
| `GND` | U2 | 1 | GND | |
| `GND` | U5 | 2 | GND | |
| `GND` | R1,R2 | 2 | — | CC pull-downs |
| `GND` | C1–C8 | 2 | − | all decoupling returns |
| `GND` | SW1,SW2,SW3 | 2 | — | button returns |
| `GND` | TP7 | 1 | — | test point |
| `CC1` | J1 | A5 | CC1 | → R1 → GND |
| `CC1` | R1 | 1 | — | 5.1 kΩ |
| `CC2` | J1 | B5 | CC2 | → R2 → GND |
| `CC2` | R2 | 1 | — | 5.1 kΩ |
| `USB_D+_CONN` | J1 | A6,B6 | D+ | connector side |
| `USB_D+_CONN` | U5 | 3 | — | ESD array in |
| `USB_D-_CONN` | J1 | A7,B7 | D− | connector side |
| `USB_D-_CONN` | U5 | 1 | — | ESD array in |
| `USB_D+` | U5 | 4 | I/O2 | ESD array out, module side |
| `USB_D+` | U1 | 14 | GPIO20 | module pin 14, functional name USB_D+ |
| `USB_D-` | U5 | 6 | I/O1 | ESD array out, module side |
| `USB_D-` | U1 | 13 | GPIO19 | module pin 13, functional name USB_D− |
| `EN` | U1 | 3 | EN | |
| `EN` | R3 | 2 | — | 10 kΩ pull-up |
| `EN` | C8 | 1 | + | 1 µF RC |
| `EN` | SW1 | 1 | — | reset button |
| `EN` | TP1 | 1 | — | test point (tap) |
| `IO0` | U1 | 27 | GPIO0/BOOT | ⚠ strapping pin |
| `IO0` | R4 | 2 | — | 10 kΩ pull-up (module has internal too) |
| `IO0` | SW2 | 1 | — | boot button |
| `IO0` | TP2 | 1 | — | test point (tap) |
| `VA_BTN` | U1 | 31 | GPIO38 | not GPIO0 — see rev-a-architecture.md rationale |
| `VA_BTN` | R5 | 2 | — | 10 kΩ pull-up |
| `VA_BTN` | SW3 | 1 | — | VA button |
| `RXD0` | U1 | 36 | GPIO44 | UART0 RX → TP4 |
| `RXD0` | TP4 | 1 | — | test point |
| `TXD0` | U1 | 37 | GPIO43 | UART0 TX → TP3 |
| `TXD0` | TP3 | 1 | — | test point |
| — | J1 | A8,B8 | SBU1,SBU2 | no connect |

**Unused/reserved on U1 for this block:** GPIO26–32 (flash, not broken out),
GPIO35/36/37 (PSRAM — *GPIO* numbers, distinct from module *pin* 36/37 above, which
are UART0). GPIO1,2,39–42(JTAG),47,48 free.

---

## Block 2 — Audio out (MAX98357A)

*Not yet drawn. Signals per master pin map: I2S LRCLK→GPIO16, BCLK→GPIO17,
DIN→GPIO18, SD(mute)→GPIO7. Append the flat rows here once wired.*

## Block 3 — Mic (INMP441)

*Not yet drawn. BCLK→GPIO4, WS→GPIO5, DIN→GPIO6.*

## Block 4 — LED ring (WS2812B + 74AHCT125)

*Not yet drawn. DIN→GPIO21 → level shifter → strip.*

## Block 5 — Sensor (AHT20)

*Not yet drawn. SDA→GPIO8, SCL→GPIO9, both 4.7 kΩ pull-up to 3V3.*

## Block 6 — Display (2.9" e-paper)

*Not yet drawn. CLK→GPIO12, MOSI→GPIO11, CS→GPIO10, DC→GPIO13, RESET→GPIO14, BUSY→GPIO15.*

---

## How to keep this in sync

1. Draw/wire a block in KiCad per its `block-N-diagram.md`.
2. Add its rows here, same format: one row per pin, grouped by net.
3. If KiCad's ERC or generated netlist ever disagrees with this table, the drawn
   schematic wins — fix this table, not the schematic.
