# Jarvis Room Node

An ESP32-S3 voice assistant + room sensor node for [Home Assistant](https://www.home-assistant.io/). One small box per room: say the wake word, talk to your smart home, see the room's temperature and humidity at a glance.

Currently a working breadboard prototype, on its way to a custom PCB and enclosure — see the [product roadmap](PRODUCT_PLAN.md).

## What it does

- 🎙️ **Voice assistant** — on-device wake word ("hey jarvis"), far-field microphone, and a speaker for spoken replies. Plugs into Home Assistant's Assist pipeline, so *you* choose the speech-to-text, brain (rules, cloud LLM, or fully local), and text-to-speech.
- 🌡️ **Room sensing** — temperature + humidity reported to Home Assistant every 30 seconds.
- 🖥️ **Always-on e-ink display** — room name, temperature, humidity. Zero light, zero power draw between refreshes.
- 💡 **LED status ring** — breathing blue while listening, amber comet while thinking, green pulse while speaking.
- 🔘 **Push-to-talk button** — trigger the assistant without the wake word.

Everything runs on [ESPHome](https://esphome.io/) — no custom firmware to maintain, fully local, auto-discovered by Home Assistant.

## Hardware

| Part | Role |
|---|---|
| ESP32-S3 (devkit / WROOM-1) | MCU — wake word runs on-device |
| INMP441 | I2S MEMS microphone |
| MAX98357A + Dayton CE32A-8 (8Ω) | I2S amp + 1.25" full-range speaker |
| AHT20 | Temperature / humidity (I2C) |
| Waveshare 2.9" e-Paper v2 | Status display (SPI) |
| WS2812B strip | Status ring |

Full wiring, GPIO map, power budget, and enclosure notes: **[HARDWARE.md](HARDWARE.md)**.

## Firmware setup

1. Install [ESPHome](https://esphome.io/guides/getting_started_command_line/) (CLI or Dashboard).
2. Copy `secrets.yaml.example` → `secrets.yaml` and fill in your Wi-Fi and keys.
3. Validate and flash:

   ```bash
   esphome config room-node.yaml   # validate
   esphome run room-node.yaml      # compile + flash (USB first time, OTA after)
   ```

4. Home Assistant auto-discovers the node (ESPHome integration). Assign it an Assist pipeline under **Settings → Voice assistants**, and expose the entities you want it to control.

The wake word model (`models/hey_jarvis.tflite`) is the stock [micro_wake_word](https://esphome.io/components/micro_wake_word/) "hey jarvis" model.

## Repo layout

| File | What |
|---|---|
| [`room-node.yaml`](room-node.yaml) | The ESPHome config — source of truth |
| [`HARDWARE.md`](HARDWARE.md) | Build reference: BOM, wiring, enclosure, acoustics |
| [`PRODUCT_PLAN.md`](PRODUCT_PLAN.md) | Roadmap: breadboard → PCB → manufacturable product |
| `models/` | Wake word model |
| `docs/archive/` | Historical design docs (outdated — don't wire from these) |

## Status

- ✅ Voice pipeline working end-to-end (wake word → STT → agent → TTS)
- ✅ Sensors, e-ink display, LED ring all live in Home Assistant
- 🔧 Audio cleanup + breadboard → KiCad PCB next ([roadmap](PRODUCT_PLAN.md))

---

Built by [Chris Boerner](https://boernerc20.me).
