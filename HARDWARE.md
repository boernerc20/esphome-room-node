# Jarvis Room Node — Hardware

Per-room ESP32-S3 voice + sensor + display node. Wake word ("hey jarvis") and
capture run on-device; STT/intent/TTS run on the HA Pi 5 (Wyoming pipeline) with
Hermes as the conversation agent. This doc is the build reference for going from
**breadboard → PCB → 3D-printed enclosure**.

Firmware config: [`room-node.yaml`](room-node.yaml). Pin assignments below are the
source of truth as wired there — keep the two in sync.

---

## Bill of Materials

| # | Component | Part | Interface | Notes |
|---|-----------|------|-----------|-------|
| 1 | MCU | **ESP32-S3-WROOM-1-N16R8** (16MB flash / 8MB octal PSRAM) | — | esp-idf framework. PSRAM matters for audio buffers + micro_wake_word. Matches the breadboard part (Lonely Binary N16R8); PCB uses the bare WROOM-1 module. |
| 2 | Microphone | **PCB rev A: Knowles SPH0645LM4H** I2S MEMS mic (decision 2026-09-28). Breadboard (as-flashed): **INMP441** — obsolete. | I2S (mic bus) | Omnidirectional, digital, 3.3 V, ~0.6 mA. SPH0645: `SEL` → **GND** (left channel, matches `channel: left`), 0.1 µF at VDD, 100 kΩ DATA pull-down, **bottom port → acoustic hole through the PCB** (see `docs/schematic/rev-a-architecture.md` Block 3). INMP441: `L/R` → GND. Far-field tuned in firmware (AGC 31 dBFS, noise-suppress 2). ⚠ SPH0645LM4H distributor status reads Obsolete too — stock/alternate check in progress. |
| 3 | Amp / DAC | **MAX98357A** I2S Class-D | I2S (spk bus) | 3.2 W @ 4Ω, ~1.4 W @ 8Ω. `SD` wired to GPIO7 — high on playback, low = shutdown (mutes idle hiss). **GAIN strapped to Vin = fixed 6 dB** (Phase 0 audio fix; floating would be 9 dB + noise). |
| 4 | Speaker | **Dayton Audio CE32A-8** — 1.25" (32mm) aluminum full-range, 8Ω / 2W RMS | wired to MAX98357A ± (BTL — do not ground either tab) | Response 240 Hz–20 kHz (clean voice, no deep bass). **31.5mm cutout, 32mm frame, 14.5mm depth** (shallow). Sealed back chamber ~20–30cc. Neo magnet, rubber surround. |
| 5 | Temp/Humidity | **AHT20** (AHT10 driver, `variant: AHT20`) | I2C | 3.3V. Reports °F (converted in firmware) + %RH every 30s. |
| 6 | Display | **Waveshare 2.9" e-Paper v2** (`model: 2.90inv2`, 296×128) | SPI (4-wire + BUSY) | ~89.5 × 38 × 4.7 mm module; active area 66.9 × 29.1 mm. Shows room name + temp + humidity, refresh 5 min. |
| 7 | Status ring | **WS2812B addressable, 27 px** | 1-wire (RMT) | Wraps the e-ink display perimeter (sets enclosure size). 5V. Whole-node draw measured on the Phase 0 bench supply: **~0.31 A** blue-breathing, **~1.0 A** solid white — well within USB-C 5 V headroom (see Decisions log). Keep a firmware LED-brightness cap as insurance for legacy 500 mA USB-A sources. |
| 8 | Button | Momentary tactile | GPIO (pull-up) | Manual voice-assistant trigger (bypasses wake word). |
| 9 | Mic-mute switch | **PCB rev A only: C&K JS202011AQN** DPDT slide, right-angle THT | GPIO (pull-up) | Hardware privacy mute. One pole breaks the mic DATA line and holds GPIO6 at GND; the other reports the position on GPIO2 (LOW = muted). Firmware can read it but cannot override it. See `docs/schematic/rev-a-architecture.md` Block 7. |

---

## GPIO Map (ESP32-S3)

| Function | Signal | GPIO |
|----------|--------|------|
| **I2S mic** (INMP441 breadboard / SPH0645LM4H PCB) | BCLK (SCK) | GPIO4 |
| | LRCLK (WS) | GPIO5 |
| | DIN (SD) | GPIO6 |
| **I2S speaker** (MAX98357A) | BCLK | GPIO17 |
| | LRCLK | GPIO16 |
| | DOUT (DIN on amp) | GPIO18 |
| Amp shutdown/mute | SD | GPIO7 |
| **I2C** (AHT20) | SDA | GPIO8 |
| | SCL | GPIO9 |
| **SPI** (e-paper) | CLK (SCK) | GPIO12 |
| | MOSI (DIN) | GPIO11 |
| e-paper | CS | GPIO10 |
| | DC | GPIO13 |
| | RESET | GPIO14 |
| | BUSY | GPIO15 |
| **WS2812B ring** | DIN | GPIO21 |
| Voice-assistant button | (INPUT_PULLUP) | **GPIO0** (breadboard) → **GPIO38** (PCB rev A) |
| Boot/recovery button | (INPUT_PULLUP) | GPIO0 (PCB rev A — not user-facing) |
| USB-C CC sensing | CC_SENSE (ADC1_CH0, analog) | **GPIO1** (PCB rev A only — not on the breadboard) |
| Mic-mute state | `MIC_MUTE_N` (input, LOW = muted) | **GPIO2** (PCB rev A only — not on the breadboard) |

**VA button moves off GPIO0 on the PCB.** GPIO0 is the BOOT strap: a user holding a
GPIO0-wired voice button through a power cycle enters download mode and the node
appears bricked, with no display feedback to explain it — unfixable in firmware after
fab. Rev A puts the user button on **GPIO38** and keeps GPIO0 as a boot/recovery tact.
`room-node.yaml` still binds GPIO0 (correct for the breadboard) — move it to a
substitution when the PCB arrives.

**Avoid** for future additions: strapping pins (0, 3, 45, 46), USB (19/20 = module
pins 13/14, used by USB-CDC logging), flash pins (26–32, not broken out), and
**PSRAM pins 35/36/37** (consumed by the N16R8 octal PSRAM — the KiCad symbol labels
them `PSRAM`). **GPIO1 is used on the PCB** (USB-C CC sensing) and **GPIO2 is used on the
PCB** (mic-mute state). Free & safe if you need more: GPIO39–42 (JTAG — leave clear if
you want hardware debug), GPIO47, GPIO48 — none of these has an ADC.

---

## Power

- Board + all peripherals run from a single **5V USB supply** into the S3.
- **AHT20** and **e-paper** are 3.3V — take them from the board's **3V3** rail.
- **SPH0645LM4H** runs at 3.3V. **MAX98357A** and **WS2812B** run at **5V**.
- **WS2812B (27 px):** powered from the board's **5V** rail (USB-C VBUS). Whole-node draw measured on the Phase 0 bench supply: **~0.31 A** blue-breathing, **~1.0 A** solid-white 100% — comfortably within USB-C 5 V headroom, so no dedicated LED supply. Keep a firmware LED-brightness cap as insurance for legacy 500 mA USB-A sources; don't command the ring to full white off a plain 500 mA USB-A port.
- **Grounds:** common ground overall (non-negotiable for I2S/WS2812B/I2C), but wire it
  as a **star** — the amp GND and the LED-strip GND each return on their own lead to
  board GND near the 5V input, **never daisy-chained together**. Phase 0 confirmed LED
  switching current sharing the amp's ground = audible noise. Amp + LEDs isolated; mic
  + sensors on the quiet side.
- **PCB rev A mic:** SPH0645LM4H on the **3V3** rail (1.62–3.6 V, ~0.6 mA), always
  powered. The mic-mute switch breaks the mic DATA line, not its supply.
- **USB-C current sensing (PCB rev A):** CC1/CC2 are summed through 2 × 100 kΩ onto
  GPIO1 (ADC). Firmware reads the source's advertisement (Default / 1.5 A / 3 A) and
  sets the LED brightness cap from it. The ring stays capped on a Default (500/900 mA)
  source.
- **Inrush:** ~1.5–2 mF of VBUS bulk (amp + LED caps) is well above USB's 10 µF
  attach limit. Accepted for rev A. Bring-up hot-plugs the board 10+ times on a laptop
  port; if a port trips, rev B adds a soft-start switch.

---

## Enclosure (3D-printed)

Target: display + PCB + LED ring in one small box.

- **Display window:** cut to the **active area 66.9 × 29.1 mm**, not the full 90 ×
  38 mm module — the module's border is bezel. Support the FPC/driver board behind.
- **LED ring layout:** **27 px** — the length cut to wrap the e-ink display perimeter,
  which effectively sets the enclosure size. This is the deliberate v1 count (not
  incidental). Confirm the strip density/pitch against the physical strip when locking
  the board outline and diffuser channel.
  - Print a **diffuser channel** (translucent PETG/white, ~1.5–2 mm wall) over the
    strip so the 27 discrete pixels read as a smooth glow instead of dots.
- **Mic placement:** breadboard INMP441 — port near a small vent hole in the front/top
  face. **PCB rev A SPH0645LM4H is bottom-ported:** sound enters through a hole in the
  PCB under the mic, so the enclosure must bring a sealed (gasketed) acoustic path to
  the **underside** of the board at that spot. Either way, **mechanically isolate it
  from the speaker** (foam/standoff). No hardware
  echo-cancellation exists in the pipeline, so physical isolation is what keeps the
  speaker from self-triggering the mic during TTS.
- **Speaker:** give the driver a small **sealed back volume** (even 20–40 cc, a little
  poly stuffing) and seal the cone to the front baffle. Sealed + baffled sounds far
  cleaner than a driver rattling in an open box.

---

## Speaker — Dayton Audio CE32A-8 (chosen)

1.25" (32 mm) aluminum-cone full-range, **8Ω / 2 W RMS** (4 W max). Chosen as the
smallest quality full-range on Amazon — its shallow depth frees space for the PCB.
Bought at 8Ω because the small 4Ω CE32A isn't Amazon-stocked; 8Ω is fine here (see
electrical note). [amazon.com/dp/B00BYE9AKM](https://www.amazon.com/dp/B00BYE9AKM)

**Physical (drives the enclosure):**
- Overall frame **32 mm**, baffle **cutout 31.5 mm**, mounting **depth 14.5 mm**.
- Shallow — leaves depth for the PCB behind the baffle. Budget ~14.5 mm + gasket.

**Electrical / wiring:**
- Two solder tabs → MAX98357A **+** and **–** outputs. Output is bridged (BTL) —
  **do not ground either terminal**; both wires go straight to the amp.
- 8Ω: MAX98357A delivers ~1.4 W here, **safely under the 2 W RMS rating**. GAIN is
  strapped to **Vin = 6 dB** (Phase 0 fix; floating 9 dB added noise). Sensitivity
  ~78 dB. This driver is quiet by design — daily volume sits near `media_player` 1.0
  with `volume_multiplier` at **1.0** (2.0 digitally clipped TTS peaks → crackle).

**Acoustic / enclosure:**
- Response rolls off below **~240 Hz** (Fs 274 Hz) — no deep bass, fine for voice.
- Vas is tiny (~4 cc) and Qts ~0.87, so it's forgiving: a **sealed back chamber
  ~20–30 cc** with a pinch of poly stuffing is plenty. Sealed >> open-back.
- Gasket/foam-seal the cone to the front baffle so front/back waves don't cancel.
- Mechanically isolate from the mic (see enclosure notes) — no HW echo
  cancellation, so speaker vibration into the mic can self-trigger during TTS.

---

## Breadboard → PCB checklist

- Keep the **I2S mic** and **I2S speaker** buses as short/clean as possible; route
  their grounds back to a single point.
- Add a **330–470 Ω** series resistor on the **WS2812B DIN** line (tames ringing) and
  a **1000 µF** bulk cap across the 27-px strip's 5V/GND — at this count it's required,
  not optional.
- **Audio decoupling (Phase 0, design it in):** **470–1000 µF electrolytic + 0.1 µF
  ceramic across the MAX98357A Vin↔GND, right at the chip.** Together with the
  GAIN→Vin (6 dB) strap and the star ground, this is what killed the breadboard
  crackle — replicate all three in copper, don't rediscover them.
- Decouple every other IC with **0.1 µF** at its VDD; bulk **10–100 µF** per rail.
- Mic `SEL` (SPH0645, PCB) / `L/R` (INMP441, breadboard) → GND; MAX98357A `SD` → GPIO7;
  both amps/mic want a solid ground plane.
- SPH0645 is **bottom-port**: keep the stock footprint's acoustic hole and GND seal ring,
  place it far from the speaker, and never wash the board after it is fitted.
- USB-C CC1/CC2 → 2 × 100 kΩ → GPIO1 (+ 100 nF, test point) for source-current sensing.
- **Mic-mute switch** (SW4, DPDT slide) at the board edge next to the mic. Pole A in the
  mic DATA line (MUTE = GPIO6 held at GND via 1 kΩ), pole B → GPIO2. The enclosure needs a
  side slot for the actuator and a mark that shows in the MUTE position.
- Bring **GPIO0** (button) and **EN/RESET** to accessible pads/headers for flashing +
  recovery.
- WS2812B is 5V; ESP32 data is 3.3V. Rev A drives DIN **directly from GPIO21** through a **330–470 Ω series resistor** (source-side, near the GPIO) — **no level shifter** (decision D4, 2026-09-28). 3.3 V is just below the WS2812B "1" threshold (~3.5 V at 5 V), so if the strip flickers at bring-up, rev B adds the 74AHCT125 back. Keep the 1000 µF bulk cap at the strip.
