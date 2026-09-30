# Block 1 — MCU + Power + USB

The foundation sheet: USB-C 5 V in → 3V3 rail → ESP32-S3 module, plus native USB
and reset/boot. Draw this KiCad sheet only after cross-checking against the
datasheets listed at the bottom.

**Module: ESP32-S3-WROOM-1-N16R8** (16 MB flash / 8 MB octal PSRAM) — matches the
validated breadboard part, not the N8R8 earlier drafts named.

> **KiCad symbol note:** there is no per-variant symbol. `RF_Module:ESP32-S3-WROOM-1`
> covers every flash/PSRAM variant because the pinout is identical — set the **Value**
> field to `ESP32-S3-WROOM-1-N16R8` and let the symbol be generic.

---

## Parts (KiCad symbol / footprint / MPN)

| Ref | Symbol | Footprint | MPN / value | Notes |
|---|---|---|---|---|
| U1 | `RF_Module:ESP32-S3-WROOM-1` | `RF_Module:ESP32-S3-WROOM-1` | ESP32-S3-WROOM-1-N16R8 | set Value to the N16R8 string |
| U2 | `Regulator_Linear:AP1117-33` | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` | AP7361C-33ER-13 | pin-compatible with AP1117; see LDO section |
| U5 | `Power_Protection:USBLC6-2SC6` | `Package_TO_SOT_SMD:SOT-23-6` | USBLC6-2SC6 | USB ESD array |
| J1 | `Connector:USB_C_Receptacle_USB2.0_16P` | `Connector_USB:USB_C_Receptacle_GCT_USB4085` | USB4085-GF-A | JLCPCB alt: HRO TYPE-C-31-M-12 |
| R1, R2 | `Device:R` | 0603 | 5.1 kΩ 1% | CC1/CC2 pull-downs |
| R3, R4, R5 | `Device:R` | 0603 | 10 kΩ | EN / IO0 / VA_BTN pull-ups |
| C1 | `Device:C` | 0805 | 10 µF 16 V X5R | VBUS bulk |
| C2 | `Device:C` | 0603 | 0.1 µF 50 V X7R | VBUS |
| C3 | `Device:C` | 0603 | 1 µF 16 V X7R | LDO input |
| C4 | `Device:C` | 0805 | 22 µF 10 V X5R | LDO output bulk |
| C5, C7 | `Device:C` | 0603 | 0.1 µF 50 V X7R | LDO out / module pin 2 |
| C6 | `Device:C` | 0805 | 22 µF 10 V X5R | module 3V3 bulk |
| C8 | `Device:C` | 0603 | 1 µF 16 V X7R | EN RC |
| SW1–SW3 | `Switch:SW_Push` | `Button_Switch_SMD:SW_SPST_TL3342` | TL3342F160QG | RESET / BOOT / VA button |
| TP1–TP7 | `Connector:TestPoint` | `TestPoint:TestPoint_Pad_D1.5mm` | — | EN, IO0, TXD0, RXD0, +3V3, +5V, GND |
| R6, R7 | `Device:R` | 0603 | 100 kΩ 1% | CC1/CC2 → `CC_SENSE` sum (added 2026-09-28) |
| C9 | `Device:C` | 0603 | 0.1 µF 50 V X7R | `CC_SENSE` filter at GPIO1 (added 2026-09-28) |
| TP8 | `Connector:TestPoint` | `TestPoint:TestPoint_Pad_D1.5mm` | — | `CC_SENSE` (added 2026-09-28) |

*Doc refs vs drawn refs:* the drawn `mcu.kicad_sch` annotates with a 2xx prefix
(R1 → R201, C1 → C201, TP1 → TP201, …). The 2026-09-28 additions become R206, R207,
C209, TP208 there.

*Class-correct choices, not stock-checked — verify LCSC/JLCPCB availability and
basic-vs-extended part status before finalizing the BOM.*

---

## U1 — ESP32-S3-WROOM-1-N16R8 (Block 1 nets)

Pin numbers verified against the KiCad symbol.

| Pin | Name | Net |
|---|---|---|
| 1, 40, 41 (pad) | GND | `GND` |
| 2 | 3V3 | `+3V3` |
| 3 | EN | `EN` |
| 13 | USB_D− / GPIO19 | `USB_D-` |
| 14 | USB_D+ / GPIO20 | `USB_D+` |
| 27 | IO0 | `IO0` |
| 39 | IO1 (ADC1_CH0) | `CC_SENSE` — USB-C CC voltage (added 2026-09-28) |
| 31 | IO38 | `VA_BTN` |
| 36 | RXD0 (IO44) | `RXD0` → test point |
| 37 | TXD0 (IO43) | `TXD0` → test point |

All other GPIO go to their peripheral sheets — see the master pin map in
[`rev-a-architecture.md`](rev-a-architecture.md).

> Confirm whether the symbol stacks GND pins 40/41 onto pin 1 or exposes them
> separately. Wire all of them regardless, plus a via array under the thermal pad.

**Unusable pins on N16R8:** 26–32 not broken out (flash); **35/36/37 consumed by
octal PSRAM** (the symbol labels them `PSRAM`). Strapping: 0, 3, 45, 46.
IO1 = `CC_SENSE` (this sheet). Free after all assignments: IO2 (pin 38, ADC1_CH1),
IO39–42 (JTAG), IO47, IO48 — only IO2 is ADC-capable.

## J1 — USB-C receptacle

| Pin(s) | Net |
|---|---|
| A4, B4, A9, B9 (VBUS) | `+5V` |
| A1, B1, A12, B12 (GND) | `GND` |
| A5 (CC1) | `CC1` → R1 5.1 kΩ → `GND`; → R6 100 kΩ → `CC_SENSE` |
| B5 (CC2) | `CC2` → R2 5.1 kΩ → `GND`; → R7 100 kΩ → `CC_SENSE` |
| A6, B6 (D+) | `USB_D+_CONN` |
| A7, B7 (D−) | `USB_D-_CONN` |
| SBU1, SBU2 | no connect |
| Shield | `GND` (optionally via 1 MΩ ∥ 4.7 nF) |

Dumb 5 V source — the 5.1 kΩ CC pull-downs are the whole sink advertisement, no PD.
Both D+ pins tie together, both D− pins tie together.

**CC sensing (added 2026-09-28):** R6/R7 sum CC1 and CC2 onto `CC_SENSE` → IO1 with
C9 0.1 µF to GND at the module and TP8. The node reads ≈ 0.51 × the active CC voltage
in either plug orientation. Firmware uses it to pick the LED brightness cap. Full
derivation, thresholds and ADC settings:
[`rev-a-architecture.md` → USB-C CC sensing](rev-a-architecture.md#usb-c-cc-sensing-block-1-addition).
Place R6/R7 near J1, C9/TP8 near U1 pin 39.

## U5 — USBLC6-2SC6

✅ **Verified against ST datasheet (DocID 11265 Rev 5, Figure 1) — pins 1&6 are
I/O1 (one line), pins 3&4 are I/O2 (the other), pin 2 = GND, pin 5 = VBUS.**

| Pin | ST name | Net |
|---|---|---|
| 1 | I/O1 | `USB_D-_CONN` |
| 2 | GND | `GND` |
| 3 | I/O2 | `USB_D+_CONN` |
| 4 | I/O2 | `USB_D+` |
| 5 | VBUS | `+5V` |
| 6 | I/O1 | `USB_D-` |

Place U5 physically at J1, ahead of any other trace on D+/D−.

## U2 — 3V3 LDO

AP7361C-33ER-13 in **SOT-223** is a 3-pin part — no EN, always on:

| Pin | Name | Net |
|---|---|---|
| 1 | GND | `GND` |
| 2 (+ tab) | VOUT | `+3V3` — C4 22 µF + C5 0.1 µF |
| 3 | VIN | `+5V` — C3 1 µF |

If you switch to a DFN variant that has an EN pin, tie **EN → VIN**.

### Why linear, and why the package matters

Average 3V3 load is ~100–150 mA (module average + mic + sensor + intermittent
e-ink); WiFi-TX pulls ~0.5 A but only in millisecond bursts. So average dissipation
is **~0.2 W**, not the ~0.85 W a peak-current calculation suggests.

At 0.2 W the package is the whole story: SOT-23-5 (θJA ≈ 250 °C/W) gives a ~50 °C
rise — unacceptable. **SOT-223 or DFN with a copper pour** (θJA ≈ 60 °C/W) gives
~12 °C — fine. Do not put this regulator in a tiny package.

**Buck rejected for rev A.** A buck saves ~0.17 W out of ~1.5 W total board
dissipation — the S3 module (0.3–0.5 W streaming audio over WiFi) and the WS2812B
strip (0.75 W at the measured 0.31 A idle state) both out-dissipate the regulator.
So a buck does *not* solve the temperature-sensor problem, and it injects switching
noise beside a MEMS mic and a Class-D amp in a design where Phase 0 was spent
eliminating exactly that. A buck is a tractable rev-B swap if bring-up shows thermal
trouble; a noisy audio path is not.

**The temp-sensor fix is mechanical, not electrical:** put the AHT20 on a thermal
island — board edge, opposite corner from module/LDO/amp/LED connector, slot-routed
on three sides so only a narrow copper neck connects it, enclosure vent above it.
Measure the residual offset against a reference and trim it in an ESPHome filter.

*Revisit if the LED duty cycle grows in v2 or a second display lands — the 5 V budget
tightens and a buck starts earning its place.*

## Reset (EN), Boot (IO0), and the VA button

```
  +3V3            +3V3              +3V3
   │               │                 │
  R3 10k          R4 10k            R5 10k
   │               │                 │
   ├── EN (pin 3)  ├── IO0 (pin 27)  ├── VA_BTN (IO38, pin 31)
   │               │                 │
  C8 1µF          SW2                SW3
   │               │                 │
  GND             GND               GND
   │
  SW1 ── GND
```

- **EN:** 10 kΩ pull-up + 1 µF to GND (power-on reset delay) + SW1 to GND.
- **IO0/BOOT:** idles HIGH; held LOW at reset = download mode. SW1+SW2 together is
  the manual flash sequence. The module has an internal pull-up; R4 is margin.
- **VA button on IO38 — not IO0.** GPIO0 was the breadboard's user button; on a
  shipped board that means a user holding the voice button through a power cycle
  lands in download mode and the node looks bricked, with no display feedback to
  explain it. Unfixable in firmware after fab. IO38 has no strapping, JTAG, or PSRAM
  conflict.
- Bring **EN, IO0, TXD0, RXD0, +3V3, +5V, GND** to test points for recovery, plus
  **CC_SENSE** (TP8) to check the CC reading against a DMM at bring-up.

> **Firmware follow-up:** `room-node.yaml` still binds the VA button to GPIO0 (correct
> for the breadboard). Move it to a substitution so the PCB build can select IO38
> without forking the config.

## Antenna keep-out

The WROOM-1 PCB antenna must overhang the board edge with a copper keep-out under and
around it, per Espressif's ESP32-S3 Hardware Design Guidelines. No traces, pour, or
parts in the antenna zone — the KiCad footprint carries the keep-out courtyard, so
respect it rather than overriding DRC.

## Cross-check before drawing

- **ESP32-S3-WROOM-1 datasheet** — pin numbers above (already validated against the
  KiCad symbol). [Espressif PDF](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)
- **ESP32-S3-DevKitC-1 schematic (PDF)** — [dl.espressif.com](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf).
  Confirms EN RC (10 kΩ + 1 µF, matches R3/C8 here) and module pin numbers
  (GND1=1, 3V3=2, EN=3, IO19=13, IO20=14, IO0=27, GND2/EPAD=40/41).
  **Not a valid reference for the USB-C front end** — the DevKitC-1 uses Micro-USB
  (no CC1/CC2 pins) and a 4-channel steering-diode ESD array (`LESD5D5.0CT1G`), not
  USBLC6-2 or a real USB-C connector. It also adds a CP2102N UART bridge with two
  auto-program transistors (DTR/RTS → EN/IO0) that this design does not need — Block 1
  has no UART bridge (native USB only), so the plain button+RC EN/IO0 circuit here
  is the correct simplification, not a missing feature.
- **ESP32-S3 Hardware Design Guidelines** — antenna keep-out, power decoupling.
- **USBLC6-2SC6 datasheet** — [ST DocID 11265](https://www.st.com/resource/en/datasheet/usblc6-2.pdf).
  Pinout verified above (pins 1&6 = I/O1, 3&4 = I/O2, 2 = GND, 5 = VBUS).
- **AP7361C datasheet** — exact in/out cap requirements and thermal derating.
