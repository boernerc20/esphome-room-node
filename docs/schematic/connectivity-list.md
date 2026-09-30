# Room Node — Master Connectivity List

The flat signal-list format used at companies with dedicated hardware teams: one row
per pin-to-net connection, so "is this pin used anywhere" or "what's on GPIO38" is a
table scan, not a hunt across six block docs. This is the **planning-time** record —
once a block is drawn in KiCad, the tool's own netlist (Tools → Generate Netlist,
or the PCB editor's ratsnest) becomes authoritative for that block; update this table
to match if they ever disagree, don't trust this over the drawn schematic.

Companion docs: [`rev-a-architecture.md`](rev-a-architecture.md) (block diagram, power
tree, rationale), `block-N-*.md` (per-block parts + wiring diagrams).

**Status:** Block 1 complete (drawn + reviewed); **CC sensing rows added 2026-09-28 —
not yet drawn** (R6, R7, C9, TP8). Block 3 (mic, SPH0645LM4H) rows added 2026-09-28 —
designed, not yet drawn. **Block 7 (mic-mute switch SW4) rows added 2026-09-30** — goes on
the Block 3 sheet, not yet drawn. Blocks 2, 4–6 not yet added — append as each is designed.

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
| `GND` | C9 | 2 | − | CC_SENSE filter return *(added 2026-09-28)* |
| `CC1` | J1 | A5 | CC1 | → R1 → GND |
| `CC1` | R1 | 1 | — | 5.1 kΩ |
| `CC1` | R6 | 1 | — | 100 kΩ to CC_SENSE *(added 2026-09-28)* |
| `CC2` | J1 | B5 | CC2 | → R2 → GND |
| `CC2` | R2 | 1 | — | 5.1 kΩ |
| `CC2` | R7 | 1 | — | 100 kΩ to CC_SENSE *(added 2026-09-28)* |
| `CC_SENSE` | R6 | 2 | — | *(added 2026-09-28)* |
| `CC_SENSE` | R7 | 2 | — | *(added 2026-09-28)* |
| `CC_SENSE` | C9 | 1 | + | 0.1 µF, at U1 |
| `CC_SENSE` | U1 | 39 | GPIO1 | ADC1_CH0 — USB-C current advertisement |
| `CC_SENSE` | TP8 | 1 | — | test point |
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

Drawn refs in `mcu.kicad_sch` carry a 2xx prefix (R1 → R201, …); the additions become
R206, R207, C209, TP208.

**Unused/reserved on U1 for this block:** GPIO26–32 (flash, not broken out),
GPIO35/36/37 (PSRAM — *GPIO* numbers, distinct from module *pin* 36/37 above, which
are UART0). **GPIO1 used** (`CC_SENSE`). **GPIO2 used** (`MIC_MUTE_N`, module pin 38 —
rows under Block 3 / Block 7). Free: GPIO39–42 (JTAG), 47, 48.

---

## Block 2 — Audio out (MAX98357A)

*Not yet drawn. Signals per master pin map: I2S LRCLK→GPIO16, BCLK→GPIO17,
DIN→GPIO18, SD(mute)→GPIO7. Append the flat rows here once wired.*

## Block 3 — Mic (SPH0645LM4H)

*Designed 2026-09-28, not yet drawn.* Sheet `microphone.kicad_sch`. Symbol
`Sensor_Audio:SPH0645LM4H`, footprint `Sensor_Audio:Knowles_SPH0645LM4H-6_3.5x2.65mm`
(includes the 0.5 mm acoustic NPTH; pad 3 is the GND seal ring). Rationale, placement
and acoustic-hole rules: [`rev-a-architecture.md` → Block 3](rev-a-architecture.md#block-3--mic-sph0645lm4h).
Refs are provisional — KiCad annotation on the sheet wins.

| Net | Ref | Pin | Pin name | Notes |
|---|---|---|---|---|
| `+3V3` | MK1 | 5 | VDD | always powered — the mute switch breaks DATA, not VDD (Block 7). The former `MIC_VDD` net is gone |
| `+3V3` | C10 | 1 | + | 0.1 µF X7R, at MK1 pin 5 |
| `+3V3` | C11 | 1 | + | 100 pF C0G, **DNP**, closest to MK1 pin 5 |
| `GND` | MK1 | 3 | GND | seal ring around the acoustic hole; vias beside the ring, not in it |
| `GND` | MK1 | 2 | SELECT | SEL → GND = **left channel** (matches `channel: left`) |
| `GND` | C10, C11 | 2 | − | via straight to the plane |
| `GND` | R8 | 2 | — | DATA pull-down return |
| `I2S_MIC_BCLK` | U1 | 4 | GPIO4 | |
| `I2S_MIC_BCLK` | R9 | 1 | — | 33 Ω, placed at U1 (driver end) |
| `I2S_MIC_BCLK_R` | R9 | 2 | — | |
| `I2S_MIC_BCLK_R` | MK1 | 4 | BCLK | |
| `I2S_MIC_WS` | U1 | 5 | GPIO5 | |
| `I2S_MIC_WS` | R10 | 1 | — | 33 Ω, placed at U1 (driver end) |
| `I2S_MIC_WS_R` | R10 | 2 | — | |
| `I2S_MIC_WS_R` | MK1 | 1 | WS | |
| `I2S_MIC_DATA_M` | MK1 | 6 | DATA | |
| `I2S_MIC_DATA_M` | R11 | 1 | — | 33 Ω, placed at MK1 (driver end) |
| `I2S_MIC_DATA_SW` | R11 | 2 | — | *(was `I2S_MIC_DATA` before Block 7)* |
| `I2S_MIC_DATA_SW` | SW4 | 3 | pole A, LIVE throw | |
| `I2S_MIC_DATA` | SW4 | 2 | pole A, common | |
| `I2S_MIC_DATA` | R8 | 1 | — | 100 kΩ pull-down (Knowles p.6, single mic on the bus), near U1 |
| `I2S_MIC_DATA` | U1 | 6 | GPIO6 | |

### Block 7 — Mic-mute switch (on the Block 3 sheet)

*Designed 2026-09-30 (SQU-10), not yet drawn.* SW4 symbol `Switch:SW_DPDT_x2` (unit A =
pins 1-2-3, unit B = pins 4-5-6), footprint
`Button_Switch_THT:SW_CK_JS202011AQN_DPDT_Angled`. MUTE position = pins 2↔1 and 5↔6.
Rationale: [`rev-a-architecture.md` → Block 7](rev-a-architecture.md#block-7--physical-mic-mute-switch-squ-10).

| Net | Ref | Pin | Pin name | Notes |
|---|---|---|---|---|
| `MIC_DATA_CLAMP` | SW4 | 1 | pole A, MUTE throw | |
| `MIC_DATA_CLAMP` | R12 | 1 | — | 1 kΩ, at SW4 |
| `GND` | R12 | 2 | — | holds GPIO6 low in MUTE |
| `MIC_MUTE_SW` | SW4 | 5 | pole B, common | |
| `MIC_MUTE_SW` | R13 | 2 | — | 10 kΩ pull-up, at SW4 |
| `+3V3` | R13 | 1 | — | |
| `MIC_MUTE_SW` | C12 | 1 | + | 100 nF, at SW4 — debounce (τ = 1 ms) + ESD sink |
| `GND` | C12 | 2 | − | |
| `MIC_MUTE_SW` | R14 | 1 | — | 1 kΩ series, at SW4 |
| `GND` | SW4 | 6 | pole B, MUTE throw | pulls `MIC_MUTE_SW` low in MUTE |
| — | SW4 | 4 | pole B, LIVE throw | no connect |
| `MIC_MUTE_N` | R14 | 2 | — | global label to the MCU sheet |
| `MIC_MUTE_N` | U1 | 38 | GPIO2 | LOW = muted, HIGH = live |

Net naming: `_R` = the mic side of a series resistor, `_M` = the mic side of the data
resistor, `_SW` = the switch side. If the 33 Ω parts are dropped, merge each `_R`/`_M`
pair into one net.

## Block 4 — LED ring (WS2812B)

*Not yet drawn. DIN→GPIO21 → 330–470 Ω series → strip. No level shifter (D4 2026-09-28); rev B adds the 74AHCT125 back if the strip flickers at bring-up.*

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
