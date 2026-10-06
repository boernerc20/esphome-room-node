# Rev A schematic — draw from this

One section per KiCad sheet in `kicad/room-node/`. Each section lists the parts and
every connection. Use the net names as global labels. Pin map: [`pinout.md`](pinout.md).
Part numbers and LCSC: [`../../reports/bom/rev-a-bom-lcsc.csv`](../../reports/bom/rev-a-bom-lcsc.csv).

**Status (2026-10-01, SQU-27):** all 6 sheets are drawn from this doc and included in
the root sheet `room-node.kicad_sch`. Project ERC: 0 errors, 1 explained warning
([`reports/schematic/`](../../reports/schematic/)). The netlist matches `pinout.md`
(`python3 tools/check_pinout.py`). The earlier MCU sheet (2xx refs, wiring errors) was
redrawn from scratch. Chris reviews and tidies.

**2026-10-02 (SQU-29):** status LED D1 + R12 on GPIO2 added to the MCU sheet.

**2026-10-05 (SQU-17):** voice button SW3 + R5 removed (wake word only). U1 pin 31
(GPIO38) is now not connected.

**Refs:** the schematic uses the refs in this doc (R1, C1, U1 …). Net names are the
ones in this doc (`+3V3`, `EN`).

**Rules for all sheets**
- Passives are 0603 minimum (hand assembly). No 0402.
- Every IC gets 0.1 µF at its supply pin.
- Board: 4 layers, solid ground plane. Assembly and layout rules: [`layout.md`](layout.md).

## Block diagram

```
USB-C 5V ──┬── ESD (D+/D−) ─────────────── U1 USB (GPIO19/20)
           ├── CC1/CC2 → 2×100k → CC_SENSE → GPIO1
           │
           +5V ──┬── LDO U2 → +3V3 ──┬── U1 ESP32-S3 module
                 │                   ├── MK1 mic (I2S in)
                 │                   ├── U6 AHT20 (I2C)
                 │                   └── J3 e-paper (SPI)
                 ├── U3 MAX98357A (I2S out) → J2 speaker
                 └── J4 LED strip (DIN ← GPIO21 via 470 Ω)

U1 GPIO2 → R12 1 kΩ → D1 status LED (green) → GND
```

---

## Sheet 1 — MCU + power + USB (`mcu.kicad_sch`)

| Ref | Value | Symbol | Footprint |
|---|---|---|---|
| U1 | ESP32-S3-WROOM-1-N16R8 | `RF_Module:ESP32-S3-WROOM-1` (set Value to N16R8) | `RF_Module:ESP32-S3-WROOM-1` |
| U2 | AP7361C-33ER-13 | `Regulator_Linear:AP1117-33` (same pinout) | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` |
| U5 | USBLC6-2SC6 | `Power_Protection:USBLC6-2SC6` | `Package_TO_SOT_SMD:SOT-23-6` |
| J1 | USB4085-GF-A | `Connector:USB_C_Receptacle_USB2.0_16P` | `Connector_USB:USB_C_Receptacle_GCT_USB4085` |
| R1, R2 | 5.1 kΩ 1% | `Device:R` | 0603 |
| R3, R4 | 10 kΩ | `Device:R` | 0603 |
| R6, R7 | 100 kΩ 1% | `Device:R` | 0603 |
| C1 | 10 µF 16 V | `Device:C` | 0805 |
| C2, C5, C7, C9 | 0.1 µF | `Device:C` | 0603 |
| C3, C8 | 1 µF | `Device:C` | 0603 |
| C4, C6 | 22 µF 10 V | `Device:C` | 0805 |
| SW1, SW2 | TL3342 (RESET, BOOT) | `Switch:SW_Push` | `Button_Switch_SMD:SW_SPST_TL3342` |
| TP1–TP8 | test pad | `Connector:TestPoint` | `TestPoint:TestPoint_Pad_D1.5mm` |
| R12 | 1 kΩ | `Device:R` | 0603 |
| D1 | KT-0805G green LED | `Device:LED` | `LED_SMD:LED_0805_2012Metric` |

**USB-C (J1)**
- VBUS A4, B4, A9, B9 → `+5V`. C1 10 µF + C2 0.1 µF to GND at J1.
- GND A1, B1, A12, B12 and shield → `GND`.
- CC1 A5 → R1 5.1 kΩ → GND, and → R6 100 kΩ → `CC_SENSE`.
- CC2 B5 → R2 5.1 kΩ → GND, and → R7 100 kΩ → `CC_SENSE`.
- D+ A6 + B6 → `USB_D+_CONN`. D− A7 + B7 → `USB_D-_CONN`.
- SBU1 A8, SBU2 B8 → no connect.

**ESD (U5, USBLC6-2SC6)** — pinout checked against ST datasheet. Place at J1.

| U5 pin | Net |
|---|---|
| 1 | `USB_D-_CONN` |
| 2 | `GND` |
| 3 | `USB_D+_CONN` |
| 4 | `USB_D+` → U1 pin 14 |
| 5 | `+5V` |
| 6 | `USB_D-` → U1 pin 13 |

**CC sense** — `CC_SENSE` → U1 pin 39 (GPIO1). C9 0.1 µF to GND at U1. TP8 on the net.
R6/R7 near J1. Firmware reads the USB source current from it (about 0.2 V = 500 mA
port, 0.46 V = 1.5 A, 0.84 V = 3 A) and limits LED brightness.

**LDO (U2)** — pin 3 VIN ← `+5V`, C3 1 µF. Pin 1 → GND. Pin 2 + tab → `+3V3`,
C4 22 µF + C5 0.1 µF. Buy the **-33ER** suffix only (other suffixes have a different
pinout). Give the tab a copper pour (heat).

**Module (U1)** — pin 2 ← `+3V3`, C6 22 µF + C7 0.1 µF at the pin. Pins 1, 40, 41 → GND.
Other pins: see [`pinout.md`](pinout.md).

**Reset and boot buttons**
```
 +3V3        +3V3
  R3 10k      R4 10k
  ├─ EN       ├─ IO0
  C8 1µF      SW2 BOOT
  SW1 RESET   │
  GND         GND
```
EN = pin 3, IO0 = pin 27. SW1 and C8 both go from EN to GND. No voice button: wake
word only. Pin 31 (GPIO38) has a no-connect flag.

**Status LED (D1)** — U1 pin 38 (GPIO2) → `STATUS_LED` → R12 1 kΩ → D1 anode (pin 2);
D1 cathode (pin 1) → GND. HIGH = on.
- GPIO2 is not a strapping pin on the S3 (straps: GPIO0, 3, 45, 46). It is an input
  with no pull at reset, so D1 is off until firmware drives it.
- Current: (3.3 V − Vf) / 1 kΩ. Vf is about 2.4 V at 1 mA (typical curve) and up to
  about 2.8 V for the highest Vf bin, so **0.5–0.9 mA**. The ESP32-S3 GPIO is good for
  tens of mA, so this is no load. At 1 mA the LED gives roughly a tenth of its 20 mA
  brightness, which is plenty for an indicator in a bedroom. Firmware can dim it further with PWM (LEDC).
- **Why 0805, not 0603:** JLC has no green or blue 0603 LED in its Basic library
  (checked 2026-10-02: only red C2286 and white C2290 at 0603). KT-0805G (C2297) is the
  green Basic part. 0805 is easier to hand-solder. If you want 0603, use KT-0603G
  (C12624, Extended) and change the footprint to `LED_SMD:LED_0603_1608Metric`.
- **Polarity:** the KENTO datasheet numbers the anode pad ① ("+"); KiCad numbers the
  cathode pad 1. Do not go by pad numbers. The green corner mark on the LED is the
  cathode: place it on the cathode (pad 1) side of the footprint.
- Put D1 where it can be seen through the case (a light pipe or a thin wall).
  It is not near the antenna and not near U6.

**Test points:** TP1 EN, TP2 IO0, TP3 TXD0 (pin 37), TP4 RXD0 (pin 36), TP5 +3V3,
TP6 +5V, TP7 GND, TP8 CC_SENSE.

---

## Sheet 2 — Audio out (`audio_out.kicad_sch`)

| Ref | Value | Symbol | Footprint |
|---|---|---|---|
| U3 | MAX98357AETE+ | `Audio:MAX98357A` | `Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm` |
| C20 | 470–1000 µF 16 V radial | `Device:C_Polarized` | radial THT (see BOM) |
| C21 | 0.1 µF | `Device:C` | 0603 |
| C22 | 10 µF 16 V | `Device:C` | 0805 |
| R20 | 100 kΩ | `Device:R` | 0603 |
| J2 | JST-PH 2-pin | `Connector_Generic:Conn_01x02` | `Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical` |

| U3 pin | Name | Net |
|---|---|---|
| 1 | DIN | `I2S_SPK_DIN` (GPIO18) |
| 2 | GAIN_SLOT | `+5V` → **6 dB gain** (tested on the breadboard; 9 dB clips) |
| 4 | SD_MODE | `AMP_SD` (GPIO7). R20 100 kΩ to GND keeps the amp off during boot (the chip also has an internal 100 kΩ pull-down). GPIO HIGH = left channel |
| 7, 8 | VDD | `+5V`. C20, C21, C22 to GND, **at the chip** |
| 9 | OUTP | J2 pin 1 |
| 10 | OUTN | J2 pin 2 |
| 14 | LRCLK | `I2S_SPK_LRCLK` (GPIO16) |
| 16 | BCLK | `I2S_SPK_BCLK` (GPIO17) |
| 3, 11, 15, 17 (EP) | GND | `GND`. EP is pin 17 (`PAD`) on the stock symbol; it is not connected inside the chip, so wire it. Vias in the pad |
| 5, 6, 12, 13 | NC | no connect |

Speaker: Dayton CE32A-8 (8 Ω) on J2. Do not connect either speaker wire to GND.
C20 + C21 + the star ground removed the breadboard crackle. Keep all three.

---

## Sheet 3 — Microphone (`microphone.kicad_sch`)

Use the **stock** symbol `Sensor_Audio:SPH0645LM4H` and footprint
`Sensor_Audio:Knowles_SPH0645LM4H-6_3.5x2.65mm`. The SPH0645 that was in the project
library (wrong pin numbers, no sound hole) was removed in SQU-27.

| Ref | Value | Footprint |
|---|---|---|
| MK1 | SPH0645LM4H-B | stock (above) |
| R8 | 100 kΩ | 0603 |
| R9, R10, R11 | 33 Ω | 0603 |
| C10 | 0.1 µF | 0603 |
| C11 | 100 pF C0G, **DNP** (do not fit) | 0603 |

| MK1 pin | Name | Connection |
|---|---|---|
| 1 | WS | → R10 33 Ω → `I2S_MIC_WS` (GPIO5). R10 at U1 |
| 2 | SELECT | GND (left channel) |
| 3 | GND | GND (ring around the sound hole) |
| 4 | BCLK | → R9 33 Ω → `I2S_MIC_BCLK` (GPIO4). R9 at U1 |
| 5 | VDD | `+3V3`. C10 0.1 µF + C11 100 pF to GND, at the pin |
| 6 | DATA | → R11 33 Ω → `I2S_MIC_DATA` (GPIO6). R11 at MK1. R8 100 kΩ from `I2S_MIC_DATA` to GND |

The 33 Ω parts are optional damping. If you remove them, use 0 Ω or a wire.
Mic mute is software only. There is no mute switch.

---

## Sheet 4 — LED ring (`led_ring.kicad_sch`)

| Ref | Value | Footprint |
|---|---|---|
| R30 | 470 Ω | 0603 |
| C30 | 1000 µF 16 V radial | radial THT (see BOM) |
| J4 | 3-pin connector to the strip | `Connector_JST:JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal`: JST S3B-XH-A(LF)(SN), side entry, LCSC C157928 (3 A; full white is ~1.6 A). Side entry since SQU-42: the cable leaves flat out of the bottom edge |

- `LED_DIN` (GPIO21) → R30 470 Ω → J4 pin 2 (DIN). R30 near U1.
- J4 pin 1 → `+5V`. J4 pin 3 → `GND`. C30 across pins 1 and 3, at J4.
- No level shifter (works on the breadboard). If the strip flickers on rev A, rev B adds a 74AHCT125.
- Strip: 27 × WS2812B, off-board.

---

## Sheet 5 — Sensor (`sensors.kicad_sch`)

| Ref | Value | Footprint |
|---|---|---|
| U6 | AHT20 | `room-node:AHT20`, 3 × 3 mm DFN-6, 1.0 mm pitch (LCSC C2757850) |
| R40, R41 | 4.7 kΩ | 0603 |
| C40 | 0.1 µF | 0603 |

The project-library AHT20 was wrong (4 pins, 4 invented pads). It is now replaced
(SQU-27) with a 6-pin symbol and a 6-pad footprint made from the LCSC C2757850 import,
pin 1 top-left as in the Aosong datasheet v1.1 §3. Pins 1 and 6 are no-connect pins.

| U6 pin | Name | Net |
|---|---|---|
| 1 | NC | no connect |
| 2 | VDD | `+3V3`, C40 0.1 µF to GND at the pin |
| 3 | SCL | `I2C_SCL` (GPIO9), R41 4.7 kΩ to `+3V3` |
| 4 | SDA | `I2C_SDA` (GPIO8), R40 4.7 kΩ to `+3V3` |
| 5 | GND | `GND` |
| 6 | NC | no connect |

- I2C address 0x38.
- Source: Aosong AHT20 datasheet v1.1, §3 pin diagram (top view).
- Place U6 on a board edge, far from U1, U2, U3 and J4, with slots on three sides
  (heat from the board reads as room temperature).

---

## Sheet 6 — Display (`display.kicad_sch`)

Rev A plugs in the same Waveshare 2.9" e-paper module as the breadboard, with its
own driver board, through its cable. (A bare panel on an FPC needs an extra boost
circuit; not for rev A.)

| Ref | Value | Footprint |
|---|---|---|
| J3 | 8-pin JST-PH **side entry** (Waveshare cable) | `Connector_JST:JST_PH_S8B-PH-SM4-TB_1x08-1MP_P2.00mm_Horizontal` |
| C50 | 0.1 µF | 0603 |

| J3 pin | Waveshare name | Net |
|---|---|---|
| 1 | VCC | `+3V3` (C50 to GND at J3) |
| 2 | GND | `GND` |
| 3 | DIN | `EPD_MOSI` (GPIO11) |
| 4 | CLK | `EPD_CLK` (GPIO12) |
| 5 | CS | `EPD_CS` (GPIO10) |
| 6 | DC | `EPD_DC` (GPIO13) |
| 7 | RST | `EPD_RST` (GPIO14) |
| 8 | BUSY | `EPD_BUSY` (GPIO15) |

**Side entry (Chris, 2026-10-05, SQU-32).** J3 is the horizontal **S8B-PH-SM4-TB**, not the
top-entry B8B. The board sits on ~10 mm M2 standoffs behind the display, parts side facing
away from it, so the cable has to leave the board edge towards the display. Pinout and pin
numbering are unchanged: pin 1 is still pin 1.

**Edge (Chris, 2026-10-05, SQU-35).** The connector mouth faces out over the **right**
board edge (looking at the parts side with USB-C on the left), not the bottom edge. Pin 1
is the **lower** of the eight pads and is marked with a filled triangle on the silkscreen.
The LED connector J4 moved to the left edge just below USB-C at the same time; see
`docs/pcb/layout.md`.

⚠ Check the pin order and pin count on your cable. Newer Waveshare modules have a
9th pin (PWR); if yours has it, use a 9-pin connector and tie PWR to `+3V3`.

⚠ **Cable.** The breadboard cable has a PH plug only at the module end; the other end
is loose jumper wires. For J3 as drawn you need a PH-to-PH 8-pin cable that maps
pin 1 to pin 1 (some ready-made cables reverse it: beep it out before power-on).
The other option is a 1×8 2.54 mm pin header (`Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical`)
that takes the existing jumper ends. Same pin order either way.

---

## Global labels (checklist)

- [ ] `+5V`, `+3V3`, `GND`
- [ ] `USB_D+`, `USB_D-`, `USB_D+_CONN`, `USB_D-_CONN`, `CC1`, `CC2`, `CC_SENSE`
- [ ] `EN`, `IO0`, `TXD0`, `RXD0`, `STATUS_LED`
- [ ] `I2S_MIC_BCLK`, `I2S_MIC_WS`, `I2S_MIC_DATA`
- [ ] `I2S_SPK_BCLK`, `I2S_SPK_LRCLK`, `I2S_SPK_DIN`, `AMP_SD`
- [ ] `I2C_SDA`, `I2C_SCL`
- [ ] `EPD_CLK`, `EPD_MOSI`, `EPD_CS`, `EPD_DC`, `EPD_RST`, `EPD_BUSY`
- [ ] `LED_DIN`

## Datasheets

ESP32-S3-WROOM-1 and ESP32-S3 Hardware Design Guidelines (Espressif), AP7361C (Diodes),
USBLC6-2 (ST), MAX98357A (Analog Devices), SPH0645LM4H-B (Knowles, DigiKey mirror),
AHT20 (Aosong), KT-0805G LED (Hubei KENTO, rev A.0, 2018-12-06), USB Type-C spec R2.0 §4.11.3 (CC voltages).
