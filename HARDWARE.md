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
| 1 | MCU | **ESP32-S3-WROOM-1** (N8R8: 8MB flash / 8MB PSRAM recommended) | — | esp-idf framework. PSRAM matters for audio buffers + micro_wake_word. |
| 2 | Microphone | **INMP441** I2S MEMS mic | I2S (mic bus) | Omnidirectional, digital. `L/R` pad → **GND** (selects left channel, matches `channel: left`). Far-field tuned in firmware (AGC 31 dBFS, noise-suppress 2). |
| 3 | Amp / DAC | **MAX98357A** I2S Class-D | I2S (spk bus) | 3.2 W @ 4Ω, ~1.4 W @ 8Ω. `SD` wired to GPIO7 — high on playback, low = shutdown (mutes idle hiss). **GAIN strapped to Vin = fixed 6 dB** (Phase 0 audio fix; floating would be 9 dB + noise). |
| 4 | Speaker | **Dayton Audio CE32A-8** — 1.25" (32mm) aluminum full-range, 8Ω / 2W RMS | wired to MAX98357A ± (BTL — do not ground either tab) | Response 240 Hz–20 kHz (clean voice, no deep bass). **31.5mm cutout, 32mm frame, 14.5mm depth** (shallow). Sealed back chamber ~20–30cc. Neo magnet, rubber surround. |
| 5 | Temp/Humidity | **AHT20** (AHT10 driver, `variant: AHT20`) | I2C | 3.3V. Reports °F (converted in firmware) + %RH every 30s. |
| 6 | Display | **Waveshare 2.9" e-Paper v2** (`model: 2.90inv2`, 296×128) | SPI (4-wire + BUSY) | ~89.5 × 38 × 4.7 mm module; active area 66.9 × 29.1 mm. Shows room name + temp + humidity, refresh 5 min. |
| 7 | Status ring | **WS2812B addressable, 27 px** | 1-wire (RMT) | Wraps the e-ink display perimeter (sets enclosure size). 5V; state effects <150 mA, but full-white ≈ **1.6 A — exceeds USB 500 mA**, so the PCB must cap brightness/count or spec a bigger 5V supply. |
| 8 | Button | Momentary tactile | GPIO (pull-up) | Manual voice-assistant trigger (bypasses wake word). |

---

## GPIO Map (ESP32-S3)

| Function | Signal | GPIO |
|----------|--------|------|
| **I2S mic** (INMP441) | BCLK (SCK) | GPIO4 |
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
| Voice-assistant button | (INPUT_PULLUP) | GPIO0 |

**Avoid** for future additions: strapping pins (0, 3, 45, 46), USB (19/20 — used
by USB-CDC logging), and PSRAM/flash pins (26–37 on the N8R8 module). Free & safe
if you need more: GPIO1, GPIO2, GPIO38, GPIO41, GPIO42, GPIO47 (GPIO48 is the
board's onboard LED on many devkits).

---

## Power

- Board + all peripherals run from a single **5V USB supply** into the S3.
- **AHT20** and **e-paper** are 3.3V — take them from the board's **3V3** rail.
- **INMP441** runs at 3.3V. **MAX98357A** and **WS2812B** run at **5V**.
- **WS2812B (27 px):** powered from the board's **5V** pin (USB VBUS, ~500 mA budget).
  State effects (breathing/comet) draw <150 mA and are fine on USB, but **full-white
  27 px ≈ 1.6 A far exceeds the USB budget** — the PCB power tree must cap LED
  brightness/count or provide a dedicated 5V supply. Never command the ring to 100%
  white on USB.
- **Grounds:** common ground overall (non-negotiable for I2S/WS2812B/I2C), but wire it
  as a **star** — the amp GND and the LED-strip GND each return on their own lead to
  board GND near the 5V input, **never daisy-chained together**. Phase 0 confirmed LED
  switching current sharing the amp's ground = audible noise. Amp + LEDs isolated; mic
  + sensors on the quiet side.

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
- **Mic placement:** put the INMP441 port near a small vent hole in the front/top
  face, and **mechanically isolate it from the speaker** (foam/standoff). No hardware
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
- Mechanically isolate from the INMP441 (see enclosure notes) — no HW echo
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
- INMP441 `L/R` → GND; MAX98357A `SD` → GPIO7; both amps/mic want a solid ground plane.
- Bring **GPIO0** (button) and **EN/RESET** to accessible pads/headers for flashing +
  recovery.
- WS2812B is 5V; ESP32 data is 3.3V — reliable on short runs, but leave a footprint for
  a **74AHCT125** level shifter on the DIN line in case the first pixel misbehaves.
