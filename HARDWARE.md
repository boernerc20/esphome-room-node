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
| 3 | Amp / DAC | **MAX98357A** I2S Class-D | I2S (spk bus) | 3.2 W @ 4Ω, ~1.4 W @ 8Ω. `SD` gated by GPIO7 (muted when idle). GAIN pin sets fixed gain (float = 9 dB default). |
| 4 | Speaker | **Dayton Audio CE32A-8** — 1.25" (32mm) aluminum full-range, 8Ω / 2W RMS | wired to MAX98357A ± (BTL — do not ground either tab) | Response 240 Hz–20 kHz (clean voice, no deep bass). **31.5mm cutout, 32mm frame, 14.5mm depth** (shallow). Sealed back chamber ~20–30cc. Neo magnet, rubber surround. |
| 5 | Temp/Humidity | **AHT20** (AHT10 driver, `variant: AHT20`) | I2C | 3.3V. Reports °F (converted in firmware) + %RH every 30s. |
| 6 | Display | **Waveshare 2.9" e-Paper v2** (`model: 2.90inv2`, 296×128) | SPI (4-wire + BUSY) | ~89.5 × 38 × 4.7 mm module; active area 66.9 × 29.1 mm. Shows room name + temp + humidity, refresh 5 min. |
| 7 | Status ring | **WS2812B addressable, 8 px** | 1-wire (RMT) | Surrounds the display. 5V, ~0.5 A worst case. See enclosure notes for pitch. |
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
- **WS2812B (8 px):** powered directly from the board's **5V** pin (USB VBUS,
  ~500 mA budget). 8 px worst case ~480 mA; status effects draw far less. Fine here.
  A full/long strip would need its own 5V supply with shared ground.
- **Grounds:** everything shares a common ground. Non-negotiable for I2S, WS2812B
  data, and I2C to work.

---

## Enclosure (3D-printed)

Target: display + PCB + LED ring in one small box.

- **Display window:** cut to the **active area 66.9 × 29.1 mm**, not the full 90 ×
  38 mm module — the module's border is bezel. Support the FPC/driver board behind.
- **LED ring layout:** 8 px around the display perimeter. Perimeter of a ~90 × 38 mm
  frame ≈ 256 mm, so:
  - **30 LEDs/m strip** (33.3 mm pitch) → 8 px ≈ 267 mm, wraps the whole perimeter
    evenly. **This is the right density for a full surround.**
  - 60 LEDs/m (16.7 mm pitch) → 8 px only reaches ~133 mm; use it for a top/side bar,
    or buy more px for a full wrap.
  - Print a **diffuser channel** (translucent PETG/white, ~1.5–2 mm wall) over the
    strip so 8 discrete pixels read as a smooth glow instead of dots.
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
- 8Ω: MAX98357A delivers ~1.4 W here, **safely under the 2 W RMS rating** — but don't
  crank the amp GAIN pin (default float = 9 dB). Sensitivity ~78 dB; ample for
  near-field voice. Trim loudness with firmware `volume_multiplier` if needed.

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
  a **1000 µF** cap across the strip's 5V/GND if you extend it. Short 8-px run usually
  fine without, but the footprint is cheap insurance on a PCB.
- Decouple each IC with a **0.1 µF** close to its VDD; bulk **10–100 µF** on the 5V and
  3V3 rails.
- INMP441 `L/R` → GND; MAX98357A `SD` → GPIO7; both amps/mic want a solid ground plane.
- Bring **GPIO0** (button) and **EN/RESET** to accessible pads/headers for flashing +
  recovery.
- WS2812B is 5V; ESP32 data is 3.3V — reliable on short runs, but leave a footprint for
  a **74AHCT125** level shifter on the DIN line in case the first pixel misbehaves.
