# Room Node — Rev A Schematic Architecture

**Status:** in progress (Phase 2). This is the netlist-level design to draw in KiCad
(Eeschema) on the workstation. Opus authors/reviews here; CAD happens on the workstation.
Source-of-truth for connections = this doc + [`../../room-node.yaml`](../../room-node.yaml)
(as-built pin map) + [`../../HARDWARE.md`](../../HARDWARE.md).

**How to use:** each block below lists every net and pin. Draw one hierarchical sheet
per block in KiCad, wire per the tables, assign the footprints in the BOM section.
Review each block before layout — a wrong decision here costs a board spin.

**Design targets:** ESP32-S3-WROOM-1-N8R8 module, USB-C 5 V input (native USB for
flash/logs), 2-layer if routable (4-layer if audio noise demands a ground plane).
Everything the breadboard taught us in Phase 0 is designed in from day one.

---

## System block diagram

```
                 USB-C (5V, D+/D-)
                      │
              [USBLC6-2 ESD] ── D+/D- ─────────────┐
                      │ VBUS 5V                     │
        ┌─────────────┴───────────────┐            │
        │            5V RAIL          │            │
        │   (amp, LEDs, 3V3 LDO in)   │            │
        └──┬──────────┬───────────┬───┘            │
           │          │           │                │
     [3V3 LDO]   [MAX98357A]  [74AHCT125]          │
     low-noise    +decoupl.   level shift          │
           │          │           │                │
        3V3 RAIL   speaker     WS2812B (27px)       │
     ┌──┬──┬──┐    JST-PH       ring, DIN           │
     │  │  │  │                                     │
  ESP32 INMP AHT  e-paper ◄── SPI ──┐               │
  -S3   441  20   2.9"              │               │
   │     │    │    │                │               │
   └─────┴────┴────┴── I2S / I2C / SPI / GPIO ──────┘
                   ESP32-S3-WROOM-1-N8R8
```

Signal buses off the S3: **I2S-mic**, **I2S-speaker**, **I2C** (AHT20), **SPI** (e-paper),
**1-wire** (WS2812B via level shifter), **native USB** (D+/D-), plus GPIO straps.

---

## Power tree

Measured on the Phase 0 breadboard (bench supply, whole node):
**~0.31 A** blue-breathing state, **~1.0 A** solid-white 100%. USB-C 5 V covers this
with headroom — no dedicated LED supply.

```
USB-C VBUS 5V ──┬── bulk 10µF + 0.1µF (input)
                │
                ├── 5V RAIL ──┬── MAX98357A Vin  (+470–1000µF electrolytic + 0.1µF at chip)
                │             ├── WS2812B 5V      (+1000µF bulk at strip connector)
                │             ├── 74AHCT125 Vcc   (+0.1µF)
                │             └── 3V3 LDO Vin      (+ input cap per datasheet)
                │
                └── 3V3 LDO OUT ──┬── ESP32-S3 3V3 (+ bulk 22–47µF + per-pin 0.1µF)
                                  ├── INMP441 VDD  (+0.1µF)
                                  ├── AHT20 VDD    (+0.1µF)
                                  └── e-paper VCC  (+0.1µF)
```

**Rails & parts**
- **USB-C input:** 5.1 kΩ CC1/CC2 pull-downs to GND (sink advertisement). ESD:
  **USBLC6-2SC6** on D+/D-. Input bulk 10 µF + 0.1 µF on VBUS. Shield → GND (optionally
  via 1 MΩ ∥ small cap).
- **3V3 LDO — spec carefully (NOT AMS1117):** the S3 draws WiFi-TX bursts up to
  **~0.5 A** off 3V3, on top of mic + sensor + e-ink. Pick a **low-noise LDO rated ≥1 A**
  (e.g. AP7361-33, TLV75901, RT9080-33) with **22–47 µF bulk** on the output to ride out
  TX bursts. Low-noise matters — the amp and mic reference this rail's cleanliness.
- **Audio decoupling (Phase 0 lesson):** 470–1000 µF electrolytic + 0.1 µF ceramic
  across MAX98357A Vin↔GND, **at the chip**.
- **LED:** 1000 µF bulk at the strip connector; 330–470 Ω series on DIN (source-side,
  after the level shifter).
- **Grounding:** single ground pour, but route the amp and LED return currents so they
  do **not** share a path with the mic/sensor analog ground (Phase 0 star-ground lesson).
  On a 2-layer board this means deliberate return-path planning; if it fights you, go
  4-layer with a solid ground plane.
- **Firmware LED cap:** keep a max-brightness clamp so a legacy 500 mA USB-A source can't
  be over-drawn by a full-white command.

---

## Master pin map (as-built, strapping-checked)

From `room-node.yaml`. **Strapping pins on ESP32-S3: GPIO0, 3, 45, 46.**

| Function | Signal | GPIO | Note |
|---|---|---|---|
| I2S mic (INMP441) | BCLK | GPIO4 | |
| | WS/LRCLK | GPIO5 | |
| | DIN/SD (data in) | GPIO6 | |
| I2S speaker (MAX98357A) | LRCLK | GPIO16 | |
| | BCLK | GPIO17 | |
| | DIN (data to amp) | GPIO18 | |
| Amp shutdown/mute | SD | GPIO7 | HIGH=on (Left mode @3V3), LOW=mute |
| I2C (AHT20) | SDA | GPIO8 | 4.7 kΩ pull-up → 3V3 |
| | SCL | GPIO9 | 4.7 kΩ pull-up → 3V3 |
| SPI (e-paper) | CLK | GPIO12 | |
| | MOSI | GPIO11 | |
| e-paper | CS | GPIO10 | |
| | DC | GPIO13 | |
| | RESET | GPIO14 | |
| | BUSY | GPIO15 | input |
| WS2812B ring | DIN (→ level shifter) | GPIO21 | 3V3 → 74AHCT125 → 5V → 330–470 Ω → strip |
| VA button | INPUT_PULLUP | **GPIO0** | ⚠ strapping (BOOT). Dual-use as boot+user button is standard; must be HIGH at reset. |
| Native USB | D- / D+ | GPIO19 / GPIO20 | USB-CDC logging + flashing — reserve |

**Strapping check:** only **GPIO0** is a strapping pin in use — it's the BOOT button,
the conventional dual-use, safe as long as it idles HIGH (pull-up present). GPIO3/45/46
unused (good). Flash/PSRAM pins **26–37** are consumed by the N8R8 octal module — do not
route. Free & safe for future: GPIO1, 2, 38, 41, 42, 47, 48.

---

## Blocks to detail next (per-sheet net lists)

Foundation above is ready for review. I'll fill these in block by block on your go —
each becomes a KiCad hierarchical sheet:

1. **MCU + reset/boot** — WROOM-1 power/decoupling, EN reset RC (10 kΩ + 1 µF + button),
   IO0 boot button, antenna keep-out, test points (TX/RX/EN/IO0/3V3/5V/GND).
2. **USB-C + native USB + ESD** — connector, CC pull-downs, USBLC6-2, VBUS bulk.
3. **Audio out (MAX98357A)** — I2S, GAIN→Vin (6 dB), SD→GPIO7, decoupling, speaker JST-PH.
4. **Mic (INMP441)** — I2S, L/R→GND, placement/port-hole notes (far from speaker).
5. **LED ring (WS2812B + 74AHCT125)** — level shift, 330–470 Ω, 1000 µF, connector.
6. **Sensor (AHT20)** — I2C + pull-ups.
7. **Display (2.9" e-paper)** — SPI + connector matching Waveshare cable.

---

## BOM (draft — confirm LCSC stock before finalizing)

| Ref | Part | Notes / LCSC-class |
|---|---|---|
| U1 | ESP32-S3-WROOM-1-N8R8 | pre-certified module |
| U2 | 3V3 LDO ≥1 A low-noise | AP7361-33 / TLV75901 / RT9080-33 |
| U3 | MAX98357AETE+ | I2S Class-D amp |
| U4 | 74AHCT125 (SOIC/TSSOP) | LED level shifter |
| U5 | USBLC6-2SC6 | USB ESD array |
| MK1 | INMP441 | I2S MEMS mic (or footprint-compat upgrade path) |
| U6 | AHT20 | temp/humidity |
| J1 | USB-C receptacle (16-pin) | power + native USB |
| J2 | JST-PH 2-pin | speaker out |
| J3 | e-paper connector | match Waveshare 2.9" cable |
| — | caps | 470–1000 µF + 0.1 µF (amp), 1000 µF (LED), 22–47 µF (3V3 bulk), 10 µF+0.1 µF (VBUS), 0.1 µF per IC |
| — | resistors | 5.1 kΩ ×2 (CC), 4.7 kΩ ×2 (I2C), 330–470 Ω (DIN), 10 kΩ (EN) |

*(Speaker = Dayton CE32A-8 off-board via J2; ring = 27-px WS2812B off-board via connector.)*
