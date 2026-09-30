# Room Node — Rev A Schematic Architecture

**Status:** in progress (Phase 2). This is the netlist-level design to draw in KiCad
(Eeschema) on the workstation. Opus authors/reviews here; CAD happens on the workstation.
Source-of-truth for connections = this doc + [`../../room-node.yaml`](../../room-node.yaml)
(as-built pin map) + [`../../HARDWARE.md`](../../HARDWARE.md).

**How to use:** each block below lists every net and pin. Draw one hierarchical sheet
per block in KiCad, wire per the tables, assign the footprints in the BOM section.
Review each block before layout — a wrong decision here costs a board spin.

**Design targets:** ESP32-S3-WROOM-1-**N16R8** module (matches the validated breadboard
part), USB-C 5 V input (native USB for
flash/logs), **4-layer with a solid ground plane** (decision 2026-09-25 — the plane
enforces the Phase 0 star-ground lesson with a Class-D amp, MEMS mic, WS2812B switching
and an RF module on one board; the earlier "2-layer if routable" fallback is dropped).
Everything the breadboard taught us in Phase 0 is designed in from day one.

---

## System block diagram

```
                 USB-C (5V, D+/D-, CC1/CC2)
                      │   └─ CC1/CC2 ─[2×100k sum]── CC_SENSE ── GPIO1 (ADC1_CH0)
              [USBLC6-2 ESD] ── D+/D- ─────────────┐
                      │ VBUS 5V                     │
        ┌─────────────┴───────────────┐            │
        │            5V RAIL          │            │
        │   (amp, LEDs, 3V3 LDO in)   │            │
        └──┬──────────┬───────────┬───┘            │
           │          │           │                │
     [3V3 LDO]   [MAX98357A]   WS2812B (27px)      │
     low-noise    +decoupl.     ring, DIN          │
           │          │           │                │
        3V3 RAIL   speaker        │                │
     ┌──┬──┬──┐    JST-PH        └──── 330–470 Ω ◄── GPIO21
     │  │  │  │                                    │
  ESP32 SPH  AHT  e-paper ◄── SPI ──┐               │
  -S3  0645  20   2.9"              │               │
   │     │    │    │                │               │
   └─────┴────┴────┴── I2S / I2C / SPI / GPIO ──────┘
                   ESP32-S3-WROOM-1-N16R8
```

DIN path (rev A): **GPIO21 → 330–470 Ω series → WS2812B DIN directly. No level shifter**
(D4, 2026-09-28 — proven on the breadboard). If the strip flickers at bring-up, rev B
adds the 74AHCT125 back.

Signal buses off the S3: **I2S-mic**, **I2S-speaker**, **I2C** (AHT20), **SPI** (e-paper),
**1-wire** (WS2812B, GPIO21 → DIN direct — no level shifter, D4 2026-09-28), **native USB**
(D+/D-), plus GPIO straps.

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
                │             └── 3V3 LDO Vin      (+ input cap per datasheet)
                │
                └── 3V3 LDO OUT ──┬── ESP32-S3 3V3 (+ bulk 22–47µF + per-pin 0.1µF)
                                  ├── SPH0645 VDD  (+0.1µF; via mic-mute switch, SQU-10)
                                  ├── AHT20 VDD    (+0.1µF)
                                  └── e-paper VCC  (+0.1µF)
```

**Rails & parts**
- **USB-C input:** 5.1 kΩ CC1/CC2 pull-downs to GND (sink advertisement). ESD:
  **USBLC6-2SC6** on D+/D-. Input bulk 10 µF + 0.1 µF on VBUS. Shield → GND (optionally
  via 1 MΩ ∥ small cap).
- **USB-C current sensing (decision 2026-09-28):** CC1 and CC2 are summed through two
  100 kΩ resistors onto `CC_SENSE` → GPIO1 (ADC1), so firmware can read the source's
  current advertisement and set the LED brightness cap. One ADC pin covers both plug
  orientations. Circuit, thresholds and ADC settings: see
  [USB-C CC sensing](#usb-c-cc-sensing-block-1-addition) below.
- **Inrush (accepted for rev A, decision 2026-09-28):** VBUS carries ~1.5–2 mF of bulk
  capacitance (amp 470–1000 µF + LED 1000 µF + 10 µF input + 3V3 bulk), well above the
  10 µF a USB device may present at attach (USB 2.0 §7.2.4.1). No soft-start switch in
  rev A; the bring-up hot-plug test below decides whether rev B needs one.
- **3V3 LDO — spec carefully (NOT AMS1117):** the S3 draws WiFi-TX bursts up to
  **~0.5 A** off 3V3, on top of mic + sensor + e-ink. Pick a **low-noise LDO rated ≥1 A**
  (e.g. AP7361-33, TLV75901, RT9080-33) with **22–47 µF bulk** on the output to ride out
  TX bursts. Low-noise matters — the amp and mic reference this rail's cleanliness.
- **Audio decoupling (Phase 0 lesson):** 470–1000 µF electrolytic + 0.1 µF ceramic
  across MAX98357A Vin↔GND, **at the chip**.
- **LED:** 1000 µF bulk at the strip connector; 330–470 Ω series on DIN at GPIO21
  (source-side, near the GPIO) — no level shifter (D4 2026-09-28).
- **Grounding:** **4-layer with a solid ground plane** (2026-09-25 decision). Route the
  amp and LED return currents so they do **not** share a path with the mic/sensor analog
  ground (Phase 0 star-ground lesson) — the plane makes that easy but doesn't draw the
  star routing for you; the returns still have to be routed deliberately.
- **Firmware LED cap:** keep a max-brightness clamp so a legacy 500 mA USB-A source can't
  be over-drawn by a full-white command.

---

## Master pin map (as-built, strapping-checked)

From `room-node.yaml`. **Strapping pins on ESP32-S3: GPIO0, 3, 45, 46.**

| Function | Signal | GPIO | Note |
|---|---|---|---|
| I2S mic (SPH0645LM4H) | BCLK | GPIO4 | module pin 4 → MK1 pin 4 |
| | WS/LRCLK | GPIO5 | module pin 5 → MK1 pin 1 |
| | DATA (data in) | GPIO6 | module pin 6 ← MK1 pin 6; 100 kΩ pull-down |
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
| WS2812B ring | DIN | GPIO21 | 3V3 → 330–470 Ω → strip; no level shifter (D4 2026-09-28) |
| VA button | INPUT_PULLUP | **GPIO38** (PCB) / GPIO0 (breadboard) | moved off GPIO0 for rev A — see below |
| Boot button | INPUT_PULLUP | GPIO0 | ⚠ strapping (BOOT). Recovery/flash only, not user-facing. |
| Native USB | D- / D+ | GPIO19 / GPIO20 | module pins **13 / 14**. USB-CDC logging + flashing — reserve |
| USB-C CC sensing | CC_SENSE (analog in) | **GPIO1** | module pin **39**, ADC1_CH0. Decision 2026-09-28 |
| Mic-mute state | MUTE_STATE (input) | GPIO2 *(reserved, pending SQU-10)* | module pin 38. Not final until the mute circuit lands |

**Strapping check:** GPIO0 is the only strapping pin in use and it is now **boot/recovery
only**. The VA button moved to **GPIO38** — on a shipped board, a user holding a
GPIO0 voice button through a power cycle enters download mode and the node looks
bricked, with no display feedback to explain it. Unfixable in firmware after fab.
GPIO3/45/46 unused (good).

**N16R8 pin availability:** GPIO26–32 are not broken out (flash), and **GPIO35/36/37 are
consumed by the octal PSRAM** — the KiCad symbol labels them `PSRAM`. Do not route any of
them. **GPIO1 is used** (CC sensing) and **GPIO2 is reserved** for the mic-mute state
(SQU-10). Free & safe for future: GPIO39–42 (JTAG — leave clear if you want debug), 47, 48.
None of these are ADC pins — GPIO1 and GPIO2 were the last free ADC1 channels (ADC1 =
GPIO1–10; ADC2 = GPIO11–20 is shared with Wi-Fi and cannot be read reliably while Wi-Fi
is on).

**Module pin numbers:** verified against the KiCad `RF_Module:ESP32-S3-WROOM-1` symbol.
Notably USB_D− = pin **13**, USB_D+ = pin **14** (pins 30/31 are IO37/IO38).

---

## Blocks (per-sheet net lists)

Each block becomes one KiCad hierarchical sheet. **MCU, power, and USB are one sheet**
(Block 1) — they were listed separately in an earlier draft; this numbering is canonical.

1. **MCU + power + USB** — ✅ [`block-1-mcu-power-usb.md`](block-1-mcu-power-usb.md).
   WROOM-1 decoupling, 3V3 LDO, USB-C + ESD, EN reset RC, IO0 boot, VA button on IO38,
   antenna keep-out, test points. **Addition 2026-09-28:** CC sensing network on GPIO1
   (R6, R7, C9, TP8) — see below.
2. **Audio out (MAX98357A)** — I2S, GAIN→Vin (6 dB), SD→GPIO7, decoupling, speaker JST-PH.
3. **Mic (SPH0645LM4H)** — I2S, SEL→GND, 100 kΩ DATA pull-down, VDD decoupling,
   bottom-port acoustic hole, placement far from speaker. Full net list below.
4. **LED ring (WS2812B)** — GPIO21 → DIN via 330–470 Ω (no level shifter, D4 2026-09-28), 1000 µF, connector.
5. **Sensor (AHT20)** — I2C + pull-ups, **thermal island** (see Block 1 LDO notes).
6. **Display (2.9" e-paper)** — SPI + connector matching Waveshare cable.
7. **Physical mic-mute switch + state GPIO** — hardware mic cut (approved 2026-09-25,
   decision A1). Circuit TBD by the architect; switch cuts the mic in hardware (mic
   power or mic data), and a free GPIO (e.g. GPIO1/2/47/48) lets firmware read the
   switch and show the state on the ring. See `PRODUCT_PLAN.md` Decisions log and
   rendered by Iris before it becomes a sheet.

---

## USB-C CC sensing (Block 1 addition)

Decided 2026-09-28 (Chris, `room-node-plan` v5 §5 D3). Firmware reads which current
the USB-C source advertises and sets the LED brightness cap from it.

**How the source advertises.** The source pulls its CC line up (Rp); our 5.1 kΩ Rd
pulls it down. The voltage on *our* CC pin tells the advertised current. Only one of
CC1/CC2 carries it — which one depends on plug orientation. The other CC pin sees only
its own Rd (≈ 0 V), or Ra ∥ Rd if an e-marked cable is attached.

**Circuit — one ADC pin, resistive sum:**

```
 J1 A5 CC1 ──┬── R1 5.1k ── GND          (existing)
             └── R6 100k 1% ──┐
                              ├── CC_SENSE ──┬── U1 pin 39 (GPIO1, ADC1_CH0)
             ┌── R7 100k 1% ──┘              ├── C9 100 nF ── GND   (at U1)
 J1 B5 CC2 ──┴── R2 5.1k ── GND          (existing)   └── TP8
```

With the active line at V_CC and the other at ≈ 0 V, the node sits at
`V_CC × (R7 + Rd) / (R6 + R7 + Rd) = V_CC × 105.1/205.1 ≈ 0.51 × V_CC`
(0.50 with an e-marked cable's Ra on the unused pin). Same result in either orientation.

**Why this works with the Type-C spec** (USB Type-C Cable and Connector Spec R2.0,
Aug 2019):
- The sum network loads the active CC with 205 kΩ in parallel with Rd → effective Rd
  4.98 kΩ (−2.4 %). Table 4-25 allows **Rd = 5.1 kΩ ±10 %** for a sink that detects
  the source's current advertisement. With 1 % R1/R2 the worst case is about −3.4 %,
  so it stays inside the limit.
- USB PD signalling on CC (if a PD source tries it) sees an extra ≥100 kΩ — negligible.

**Thresholds** (Table 4-36, "Voltage on Sink CC pins — Multiple Source Current
Advertisements"; Rp values from Table 4-24; values verified 2026-09-28):

| Source advertises | Typical Rp to 5 V | V_CC spec range | V_CC nominal* | CC_SENSE range (×0.50–0.51) | CC_SENSE nominal |
|---|---|---|---|---|---|
| Default USB (500/900 mA) | 56 kΩ (C-to-A cable) or 80 µA | 0.25–0.61 V | ~0.40 V | 0.13–0.31 V | ~0.20 V |
| 1.5 A @ 5 V | 22 kΩ or 180 µA | 0.70–1.16 V | ~0.91 V | 0.35–0.59 V | ~0.46 V |
| 3.0 A @ 5 V | 10 kΩ or 330 µA | 1.31–2.04 V | ~1.65 V | 0.66–1.04 V | ~0.84 V |

\* with the 4.98 kΩ effective Rd.

Firmware decision thresholds (the spec's sink thresholds, 0.2 / 0.66 / 1.23 V on CC,
scaled): **CC_SENSE < 0.10 V = no advertisement / fault**, **< 0.34 V = Default**,
**< 0.63 V = 1.5 A**, **≥ 0.63 V = 3.0 A**. Round down when ambiguous.

In practice only the **Default vs ≥ 1.5 A** boundary matters: the measured whole-node
worst case is ~1.0 A (solid white), which fits a 1.5 A source. Tightest margin at
that boundary is ~15–25 mV at the spec extremes (Default max 0.31 V vs 1.5 A min 0.35 V,
threshold 0.34 V). Nominal sources sit ~0.1 V away from it.

**ADC settings (interface for firmware, Phase 1):**
- GPIO1 = ADC1_CH0 — ADC1, so it works while Wi-Fi is on.
- Attenuation **2.5 dB** (≈ 0–1.25 V usable range on ESP32-S3) covers the full 3 A range
  (≤ 1.04 V). A reading at the top of the range means CC is out of spec → treat as fault,
  use the Default cap.
- Settling: τ ≈ 50 kΩ × 100 nF = 5 ms. Read ≥ 50 ms after boot, average 16+ samples,
  use eFuse calibration.
- Poll every few seconds, not only at boot. A source may lower its advertisement while
  attached; on a drop to Default, lower the LED cap promptly.
- LED cap policy (proposal, firmware to confirm): Default → hold total node draw under
  ~450 mA; 1.5 A or 3.0 A → no extra cap beyond the existing firmware clamp.

**Protection / ESD** (lens: ESD and user touch): the CC pins carry only passives. R6/R7
+ C9 form an RC filter that isolates GPIO1 from ESD on the connector, so no extra TVS
on CC. Fault case — CC shorted to VBUS (5 V) by a damaged cable: CC_SENSE ≈ 2.6 V, below
3.3 V, so no clamp current. No PD negotiation, so VBUS stays at 5 V.

**Placement:** R6/R7 close to J1 (keep the CC stubs short); C9 and TP8 at U1 pin 39.

**Second ADC pin needed? No.** Considered:

| Option | Pins | Verdict |
|---|---|---|
| **Resistive sum (chosen)** | GPIO1 only | Half the signal swing, but resolution is ample for Default vs ≥ 1.5 A. Keeps GPIO2 for the mute state (SQU-10). |
| One ADC per CC line | GPIO1 + GPIO2 | Full swing and simpler math. Takes GPIO2 (the last free ADC1 pin) from SQU-10, which would move the mute state to GPIO47/48. Good fallback if bring-up shows the margin is too tight. |
| Schottky diode-OR | GPIO1 only | Rejected: Vf at µA currents is 0.1–0.3 V and moves with temperature. That is as large as the 0.09 V gap between Default max and 1.5 A min. |

*Sources:* USB Type-C Spec R2.0 §4.11.3 Tables 4-24/4-25/4-36 (usb.org);
ESP32-S3 Technical Reference Manual — ADC chapter (ADC1 = GPIO1–10, ADC2 shared with
Wi-Fi). **Assumption:** ESP32-S3 calibrated ADC error at 2.5 dB is ≈ ±10 mV. Verify
against the ESP32-S3 datasheet ADC characteristics table at bring-up (measure TP8 with a
DMM against the firmware reading).

---

## Block 3 — Mic (SPH0645LM4H)

Decided 2026-09-28 (Chris, `room-node-plan` v5 §5 D1): **Knowles SPH0645LM4H replaces the
obsolete INMP441.** Same I2S bus and GPIOs as the breadboard. Source: Knowles
*SPH0645LM4H-B Datasheet Rev C* (knowles.com PDFs now return 404; read from the
Knowles-authored PDF mirrored by DigiKey).

> ⚠ **Lifecycle — decision for Chris.** Distributor listings (DigiKey, Mouser; checked
> 2026-09-28) show **SPH0645LM4H-B, -1 and -1-8 as Obsolete**. The Knowles consumer mic
> line now sells under **Syntiant**. DigiKey's suggested substitute, **SPH0655LM4H-1-8**,
> is a **PDM** mic — not an I2S drop-in. An active I2S part in the same 3.50 × 2.65 mm
> bottom-port package to evaluate: **TDK ICS-43434** (footprint/pinout compatibility
> **not yet verified**). Nora confirms status and stock (SQU-14). Rev A is 5 hand-built
> boards, so remaining stock or breakout boards may be enough. The pilot (Phase 4)
> needs an active part.

**Part:** MK1 = SPH0645LM4H (-B) — 3.50 × 2.65 × 0.98 mm LGA-6, bottom port, I2S slave,
24-bit frame / 18-bit data, VDD 1.62–3.6 V, ~600 µA (datasheet Table 2).

**KiCad (stock library):** symbol `Sensor_Audio:SPH0645LM4H`, footprint
`Sensor_Audio:Knowles_SPH0645LM4H-6_3.5x2.65mm`. The footprint includes the **0.5 mm
NPTH acoustic hole** and pad 3 (GND) as a **copper ring around it** — the ring solders
to the mic and seals the port. Symbol and footprint pin numbers match the datasheet.

| MK1 pin | Name | Net | Notes |
|---|---|---|---|
| 1 | WS | `I2S_MIC_WS` | ← R10 33 Ω ← U1 pin 5 (GPIO5) |
| 2 | SELECT | `GND` | **SEL → GND = left channel** (DATA driven while WS low), matches `channel: left`. Tie directly — SELECT low must be within GND + 0.2 V (Table 3). |
| 3 | GND (ring pad) | `GND` | vias straight into the plane beside the ring, never inside it |
| 4 | BCLK | `I2S_MIC_BCLK` | ← R9 33 Ω ← U1 pin 4 (GPIO4) |
| 5 | VDD | `MIC_VDD` | `+3V3` via the mic-mute switch (SQU-10); C10 0.1 µF + C11 100 pF DNP at the pin |
| 6 | DATA | `I2S_MIC_DATA` | → R11 33 Ω → U1 pin 6 (GPIO6); **R8 100 kΩ to GND** |

**Why each part:**
- **C10 0.1 µF X7R** — Knowles test and application circuit (Tables 2–3, Figure 8 note 1).
  Place as close as possible; GND pad via-to-plane, no trace (p.7).
- **C11 100 pF C0G, fitted as DNP** — the datasheet's optional RF filter (20–200 pF,
  Figure 8 note 2). The 2.4 GHz antenna shares the board, so keep the footprint. If
  fitted, it sits closest to the pin (note 3).
- **R8 100 kΩ DATA pull-down** — *"When operating a single microphone on an I2S bus, a
  pull down resistor (100K Ohms) should be placed from the Data pin to ground"* (p.6). It
  also makes GPIO6 read clean zeros when the mute switch removes VDD (the mic tri-states
  DATA when powered down, p.5).
- **R9/R10/R11 33 Ω series** — the datasheet's 27–51 Ω damping resistors (p.7), each at
  its **driving** end: R9/R10 at U1, R11 at MK1. They cut ringing and slow the 3 MHz BCLK
  edges (Part 15B hygiene). They can be 0 Ω if not needed.

**Constraint handed to SQU-10 (mute):** if the switch cuts **VDD**, BCLK/WS keep toggling
at 3.3 V into an unpowered mic. Check that the mic cannot be back-powered through its
input clamp diodes — otherwise the mute is not a hardware guarantee. Cutting DATA (with
R8 on the ESP side) or also gating BCLK are the alternatives.

**Acoustic hole and placement (respin risk if missed):**
- **Bottom port:** sound enters through the PCB hole under the mic. The acoustic path is
  on the **bottom side of the board** — the enclosure must port to the PCB underside
  (gasket or foam ring sealing the hole to an enclosure opening). Record this as a
  mechanical constraint for the enclosure role.
- Datasheet acoustic port (on the mic) = **0.325 ± 0.05 mm**; the stock footprint's PCB
  hole is **0.5 mm**. **Open question:** check the 0.5 mm hole against the land-pattern
  drawing on datasheet p.8. The drawing is an image the text extraction could not read.
- No traces, vias or pour inside the GND ring on any layer. Inner planes clear the
  NPTH with normal clearance. Keep the bottom side around the hole clear for the gasket.
- **Far from the speaker:** place MK1 at the opposite end of the board from J2 (speaker
  connector) and the driver. Also keep it away from the MAX98357A outputs, the LED 5 V
  current path and connector, and the antenna. Keep it on the quiet side of the ground
  return plan. The enclosure adds mechanical isolation (foam) — there is no hardware AEC.
- Keep the I2S traces short, over solid ground, away from the Class-D outputs.

**Hand-assembly notes** (datasheet p.10, MSL 1): stencil the ring pad fully — a gap in
the ring leaks sound. Reflow from the top with gentle airflow; never aim hot air or a
probe into the hole from below. **No board wash, IPA scrub or ultrasonic cleaning after
the mic is on.** No vacuum or >30 psi air on the port. Vacuum pickup only on the pick
area, ≤3 reflow cycles.

**Firmware interface (Felix, Phase 1):** I2S master on the S3, WS = BCLK/64,
BCLK 1.024–4.096 MHz (16 kHz → 1.024 MHz), so each channel slot is 32 BCLKs. Standard
I2S (MSB one BCLK after WS changes), 24-bit two's-complement word with 18 valid bits,
lower bits zero — read as 32-bit, as `room-node.yaml` does today. SPH0645 needs different ESP32 I2S settings from
INMP441 — check `room-node.yaml` on an SPH0645 breakout before the boards arrive.

---

## Assembly constraints — rev A is hand-built

Decided 2026-07-28 (see `PRODUCT_PLAN.md` Decisions log). Rev A is assembled by hand
on the bench, not by JLCPCB. These constraints bind layout and part selection:

| Constraint | Why |
|---|---|
| **4-layer, solid ground plane** | Enforces the Phase 0 star-ground lesson with a Class-D amp, MEMS mic, WS2812B switching and an RF module on one board. Cost delta at 5 boards is negligible. |
| **ENIG finish** | HASL leaves domed pads that fine-pitch parts rock on. Flat pads matter for the 0.5 mm-pitch QFN and USB-C. |
| **Stencil ordered with the boards** | The single highest-leverage item. Paste + stencil + hot air makes the MAX98357A QFN routine instead of the failure point. |
| **Single-sided placement** | All parts on top. Two-sided means a second reflow with the first side hanging upside down. |
| **≥0.5 mm passive spacing**, extra around module/QFN | Hot air blows neighbouring 0603s off a DFM-tight layout. |
| **0603 minimum**, no 0402 | Hand-placeable with tweezers. |
| **Through-hole audio bulk cap** | A 470–1000 µF radial is easier to place, mechanically solid, and heat-tolerant in a way SMD cans aren't. |
| **Tented thermal vias** (bottom side) | Untented vias in a pad wick solder through and starve the joint. Applies to the WROOM-1 ground pad and MAX98357A thermal pad. |
| **Windowpaned stencil apertures** on exposed pads | ~50–70% coverage in a grid. Full coverage floats the part on molten solder and lifts the perimeter pins. |
| **Human-readable silkscreen** | Pin-1 dots, polarity bars, legible refdes. Assembly houses ignore silkscreen; you won't. |

**Known risk:** the WROOM-1 ground pad and the MAX98357A thermal pad cannot be
inspected once placed. Marginal joints there mimic design bugs — resets under WiFi
load, an amp that works then thermally shuts down. During bring-up, suspect those two
joints before the schematic.

**Bring-up order:** continuity-check every rail to GND for shorts → power from a
current-limited bench supply at ~200 mA and watch the draw *before* plugging in USB →
5 V rail → 3V3 rail → USB enumerate → flash → each peripheral in turn → audio noise
floor vs breadboard. Use the Block 1 test points (EN, IO0, TXD0, RXD0, +3V3, +5V, GND,
CC_SENSE).

**Hot-plug inrush test (decision 2026-09-28):** after the board passes on the bench
supply, plug it into a **laptop USB port 10+ times** (unplug, wait ≥ 2 s, plug). Use a
USB-C port, and a USB-A port with a C-to-A cable if the laptop has one.
**Pass:** the port never shuts off or shows an over-current warning, and the board boots
every time (USB enumerates / ring shows the boot state). Record the laptop model and port.
**Fail → rev B adds a soft-start load switch on VBUS** (PRODUCT_PLAN Decisions log).

**CC sensing check:** at each plug-in, compare the TP8 DMM reading with the firmware
reading and the source's rating. Use a 3 A USB-C charger, a laptop port, and a C-to-A
cable (should read Default).

**Ordering:** 5 bare boards + stencil; 3–5× passives and 2–3× ICs/connectors as spares
(the USB-C receptacle especially). PCBA returns at the Phase 4 pilot. Fallback if
bring-up fights back: a later JLCPCB order placing *only* the module and the QFN,
passives by hand.

---

## BOM (draft — confirm LCSC stock before finalizing)

| Ref | Part | Notes / LCSC-class |
|---|---|---|
| U1 | ESP32-S3-WROOM-1-**N16R8** | pre-certified module; KiCad symbol is variant-agnostic |
| U2 | **AP7361C-33ER-13**, SOT-223 | 3V3 LDO 1 A. Package is load-bearing — see Block 1 |
| U3 | MAX98357AETE+ | I2S Class-D amp |
| U5 | USBLC6-2SC6 | USB ESD array |
| MK1 | **SPH0645LM4H** (Knowles/Syntiant), LGA-6 3.5×2.65 mm | I2S MEMS mic, bottom port (decision 2026-09-28; replaces obsolete INMP441). ⚠ lifecycle — see Block 3. Candidate alternate: TDK ICS-43434 (compat. unverified). Part number + stock: Nora, SQU-14 |
| U6 | AHT20 | temp/humidity |
| J1 | USB-C receptacle (16-pin) | power + native USB |
| J2 | JST-PH 2-pin | speaker out |
| J3 | e-paper connector | match Waveshare 2.9" cable |
| — | caps | 470–1000 µF + 0.1 µF (amp), 1000 µF (LED), 22–47 µF (3V3 bulk), 10 µF+0.1 µF (VBUS), 0.1 µF per IC |
| — | resistors | 5.1 kΩ ×2 (CC), 4.7 kΩ ×2 (I2C), 330–470 Ω (DIN), 10 kΩ (EN) |
| R6, R7 | 100 kΩ 1% 0603 | CC1/CC2 → CC_SENSE sum network (Block 1) |
| C9 | 100 nF X7R 0603 | CC_SENSE filter at GPIO1 (Block 1) |
| TP8 | test pad D1.5 mm | CC_SENSE (Block 1) |
| R8 | 100 kΩ 0603 | mic DATA pull-down (Block 3) |
| R9, R10, R11 | 33 Ω 0603 | I2S mic BCLK / WS / DATA damping (Block 3) |
| C10 | 0.1 µF X7R 0603 | mic VDD decoupling (Block 3) |
| C11 | 100 pF C0G 0603, **DNP** | mic VDD RF filter footprint (Block 3) |

*(Speaker = Dayton CE32A-8 off-board via J2; ring = 27-px WS2812B off-board via connector.)*
