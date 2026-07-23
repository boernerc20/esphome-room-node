# Room Node — Project Doc

## Overview

ESP32-S3 based room sensor/voice node. Collects environmental data, handles voice input/output for Jarvis control, and displays status on a small e-ink screen with LED accent ring. 3D printed enclosure, one per room long-term.

## Feature Set

| Feature | Component | Status |
|---------|-----------|--------|
| Temperature + Humidity | AHT20 or SHT31 | Planned |
| Air quality (CO2/VOC) | SGP30 or ENS160 (future edition) | v2 |
| Microphone (voice input) | INMP441 (I2S MEMS mic) | Planned |
| Speaker (voice output) | MAX98357A (I2S amp) + small 4Ω speaker | Planned |
| Display | 2.9" e-ink (Waveshare, SPI) | Planned |
| LED ring | WS2812B ring (around display bezel) | Planned |
| MCU | ESP32-S3 | Planned |
| Enclosure | 3D printed | Planned |

## Architecture

```
Room Node (ESP32-S3)
    │
    ├── Sensors → ESPHome → Home Assistant (Pi 5, 192.168.1.138)
    │     └── temp, humidity, air quality
    │
    ├── Mic (INMP441) → Wyoming Satellite → Pi 5 Wyoming Server
    │     └── Whisper STT → intent → HA action → Piper TTS response
    │
    ├── Speaker (MAX98357A) ← audio response from Wyoming/Piper
    │
    └── e-ink display + LED ring ← driven by ESPHome
          └── shows: temp, humidity, time, active alerts, Jarvis status
```

## Software Stack

- **ESPHome** — firmware framework, handles sensors + display + LEDs + WiFi + HA integration natively
- **Wyoming Satellite** — ESPHome component (or separate process) for mic/speaker voice pipeline
- **Home Assistant** — receives all sensor data, sends display/LED updates, processes voice intents

## Key Components

| Part | Notes |
|------|-------|
| ESP32-S3 dev board | Has USB native, better I2S support than ESP32, needed for Wyoming satellite |
| INMP441 | I2S MEMS microphone, ~$3, standard for ESPHome voice satellite |
| MAX98357A | I2S class-D amp, ~$3, drives small 4Ω 3W speaker |
| AHT20 or SHT31 | I2C temp/humidity, AHT20 ~$2, SHT31 ~$4 (more accurate) |
| Waveshare 2.9" e-ink | SPI, 296×128px, ~$15–20, partial refresh capable |
| WS2812B LED ring | 12 or 16 LED ring to surround display bezel, ~$3–5 |
| SGP30 or ENS160 | I2C air quality (VOC + eCO2), save for v2 |

## Wiring (ESP32-S3)

| Peripheral | Interface | Pins |
|-----------|-----------|------|
| INMP441 mic | I2S | GPIO 4 (WS), 5 (SCK), 6 (SD) |
| MAX98357A amp | I2S | GPIO 7 (WS), 8 (BCK), 9 (DIN) |
| e-ink display | SPI | GPIO 10 (CS), 11 (CLK), 12 (MOSI), 13 (DC), 14 (RST), 15 (BUSY) |
| AHT20/SHT31 | I2C | GPIO 1 (SDA), 2 (SCL) |
| WS2812B ring | 1-wire | GPIO 3 |

*Pin assignments are flexible — finalize when breadboarding.*

## Display Layout (2.9" e-ink, 296×128px)

```
┌─────────────────────────────┐
│  72°F  •  45% RH            │
│  Living Room                │
│                             │
│  [Jarvis: Ready]            │
│  Mon Apr 28  •  8:42 PM     │
└─────────────────────────────┘
```

LED ring behavior:
- Idle: off or dim warm white
- Wake word detected: blue pulse
- Listening: rotating blue
- Processing: yellow
- Speaking: green pulse
- Alert: red

## ESPHome Voice Satellite

ESPHome 2024.x has built-in Wyoming satellite support:
```yaml
voice_assistant:
  microphone: i2s_mic
  speaker: i2s_speaker
  on_listening:
    - light.turn_on: led_ring  # blue
  on_tts_start:
    - light.turn_on: led_ring  # green
```

Requires Wyoming Whisper + Piper addons running on Pi 5 (not yet set up).

## Bill of Materials

### Phase 1 — Prototype BOM

| Part | Source | Cost | Status |
|------|--------|------|--------|
| Lonely Binary ESP32-S3 N16R8 Gold Edition | Amazon | $18.99 | Ordered |
| AHT20 I2C temp/humidity breakout | Amazon | ~$5 | Ordered |
| Waveshare 2.9" e-ink display (B/W/R, used B/W mode) | Amazon | ~$20 | Ordered |
| INMP441 I2S MEMS mic breakout | Amazon | ~$5 | Ordered |
| MAX98357A I2S amp breakout | On hand | — | Have |
| WS2812B LED ring (12 or 16 LED) | On hand | — | Have |
| Small 4Ω 3W speaker | On hand | — | Have |
| Breadboard + jumper wires | On hand | — | Have |
| USB-C cable | On hand | — | Have |
| **Prototype Total** | | **~$49** | |

### Phase 2 — Custom PCB BOM

| Part | Part # | Source | Qty | Cost ea. | Notes |
|------|--------|--------|-----|----------|-------|
| ESP32-S3-WROOM-1-N16R8 | ESP32-S3-WROOM-1-N16R8 | DigiKey | 1 | ~$4.50 | Official Espressif module, castellated edges |
| AHT20 | AHT20 | LCSC | 1 | ~$1.50 | LGA-8 package, I2C |
| INMP441 | INMP441ACTR | LCSC | 1 | ~$2.00 | LGA-6, I2S MEMS mic |
| MAX98357AETE+ | MAX98357AETE+ | DigiKey | 1 | ~$2.50 | TQFN-16, I2S class-D amp |
| WS2812B LEDs | WS2812B | LCSC | 12–16 | ~$0.15 | Individual SMD, 5050 package |
| AMS1117-3.3 LDO | AMS1117-3.3 | LCSC | 1 | ~$0.20 | 3.3V reg for sensors/display/mic |
| 10µF cap (×4) | — | LCSC | 4 | ~$0.05 | 0805, bulk/LDO decoupling |
| 100nF cap (×8) | — | LCSC | 8 | ~$0.02 | 0402, per-IC decoupling |
| 10nF cap (×4) | — | LCSC | 4 | ~$0.02 | 0402, RF bypass |
| 10kΩ resistor (×2) | — | LCSC | 2 | ~$0.02 | 0402, I2C pull-ups |
| 4.7µH inductor | — | LCSC | 1 | ~$0.20 | 0603, LDO output filter |
| USB-C connector | GT-USB-7010ASV | LCSC | 1 | ~$0.50 | Power + programming |
| JST 8-pin connector (display) | — | LCSC | 1 | ~$0.30 | Matches Waveshare e-ink cable |
| JST 2-pin connector (speaker) | — | LCSC | 1 | ~$0.20 | Speaker output |
| 10Ω resistor (×2) | — | LCSC | 2 | ~$0.02 | 0402, WS2812B data line |
| JLCPCB 2-layer PCB (5 boards) | — | JLCPCB | 5 | ~$1.00 | Standard 1.6mm FR4 |
| **PCB Total (per unit)** | | | | **~$15** | Excluding display/speaker (reuse from proto) |

---

## Wiring Schematic (Prototype)

### Power Rail

```
USB-C (5V)
    │
    ├──── ESP32-S3 dev board (onboard LDO handles 3.3V internally)
    │         └── 3V3 pin → sensors, display, mic
    │
    └──── WS2812B ring VCC (5V direct — LEDs need 5V)
```

### AHT20 — I2C (3.3V)

```
ESP32-S3          AHT20
─────────         ──────
3V3       ──────► VCC
GND       ──────► GND
GPIO8     ──────► SDA  (10kΩ pull-up to 3V3)
GPIO9     ──────► SCL  (10kΩ pull-up to 3V3)
```

*Note: Some AHT20 breakouts have pull-ups onboard — check your module.*

### Waveshare 2.9" e-ink — SPI (3.3V)

```
ESP32-S3          e-ink module
─────────         ────────────
3V3       ──────► VCC
GND       ──────► GND
GPIO11    ──────► DIN  (MOSI)
GPIO12    ──────► CLK  (SCLK)
GPIO10    ──────► CS
GPIO13    ──────► DC
GPIO14    ──────► RST
GPIO15    ──────► BUSY
```

### INMP441 — I2S Mic (3.3V)

```
ESP32-S3          INMP441
─────────         ───────
3V3       ──────► VDD
GND       ──────► GND
GND       ──────► L/R   (GND = left channel)
GPIO4     ──────► SCK   (bit clock)
GPIO5     ──────► WS    (word select / LRCLK)
GPIO6     ◄─────  SD    (data out from mic)
```

### MAX98357A — I2S Amp (3.3V or 5V)

```
ESP32-S3          MAX98357A         Speaker
─────────         ─────────         ───────
3V3       ──────► VIN
GND       ──────► GND
GPIO17    ──────► BCLK
GPIO16    ──────► LRC   (LRCLK)
GPIO18    ──────► DIN
                  SD    (leave floating = always on)
                  GAIN  (leave floating = 9dB gain)
                  OUT+  ──────────────────────────► +
                  OUT-  ──────────────────────────► -
```

### WS2812B LED Ring — Single Wire (5V)

```
ESP32-S3          WS2812B ring
─────────         ────────────
5V        ──────► VCC  (5V from USB rail)
GND       ──────► GND
GPIO3  ───10Ω──► DIN  (10Ω series resistor protects GPIO)
```

*Note: ESP32-S3 GPIO is 3.3V — WS2812B data threshold is ~0.7×VCC = 3.5V at 5V supply. Some rings work fine, some don't. If unreliable, add a level shifter (74HCT1G125) or power the ring from 3.3V instead.*

### Full Pin Summary

| GPIO | Function | Peripheral |
|------|----------|-----------|
| 3 | Data out | WS2812B ring |
| 4 | I2S SCK | INMP441 mic |
| 5 | I2S WS | INMP441 mic |
| 6 | I2S SD in | INMP441 mic |
| 8 | I2C SDA | AHT20 |
| 9 | I2C SCL | AHT20 |
| 10 | SPI CS | e-ink |
| 11 | SPI MOSI | e-ink |
| 12 | SPI CLK | e-ink |
| 13 | DC | e-ink |
| 14 | RST | e-ink |
| 15 | BUSY | e-ink |
| 16 | I2S LRC | MAX98357A amp |
| 17 | I2S BCLK | MAX98357A amp |
| 18 | I2S DIN | MAX98357A amp |
| 19–20 | **RESERVED** | USB (do not use) |
| 35–38 | **RESERVED** | PSRAM (do not use) |

---

## Build Phases

### Phase 1 — Breadboard (current)
- ESP32-S3 dev board
- INMP441 + MAX98357A wired up, test audio pipeline with ESPHome
- AHT20 sensor → verify data in HA
- WS2812B ring basic patterns

### Phase 2 — Add Display
- Wire 2.9" e-ink, write ESPHome display lambda
- Show temp/humidity/time
- LED ring animations tied to states

### Phase 3 — Voice Pipeline
- Wyoming satellite config in ESPHome
- Connect to Pi 5 Wyoming server (once Whisper + Piper addons installed)
- Test wake word → STT → HA action → TTS response

### Phase 4 — PCB
- Custom ESP32-S3 board with all peripherals integrated
- Clean power supply (LDO, filtering)
- Compact enough to fit in 3D printed enclosure

### Phase 5 — Enclosure
- 3D printed
- Display + LED ring visible on front face
- Mic opening (small hole or mesh grille)
- Speaker grille
- USB-C for power
- Wall mount or desk stand

## Parts to Order (Phase 1 Breadboard)

- [ ] ESP32-S3 dev board (S3-DevKitC-1 or similar)
- [ ] INMP441 breakout or bare IC
- [ ] MAX98357A breakout (Adafruit makes one, easy to start)
- [ ] AHT20 or SHT31 breakout
- [ ] Small 4Ω 3W speaker
- [ ] WS2812B ring (12 or 16 LED)
- [ ] Waveshare 2.9" e-ink display module

## Homelab Integration

- All sensor data → HA entities automatically via ESPHome
- Display + LED ring controllable from HA dashboard
- Voice pipeline feeds into existing Jarvis intent handling
- One node per room long-term — living room first
- Same visual design language as ADS-B tracker display if you want consistency
