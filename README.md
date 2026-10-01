# Jarvis Room Node

An ESP32-S3 voice assistant and room sensor for [Home Assistant](https://www.home-assistant.io/),
built on [ESPHome](https://esphome.io/). Wake word ("hey jarvis") on the device, temperature
and humidity, e-ink display, LED status ring.

**Status:** breadboard works end to end. Next: rev A PCB in KiCad.

## Repo

| Path | What |
|---|---|
| [`room-node.yaml`](room-node.yaml) | ESPHome firmware (breadboard pins) |
| [`docs/breadboard.md`](docs/breadboard.md) | Breadboard wiring |
| [`docs/pcb/pinout.md`](docs/pcb/pinout.md) | Rev A PCB pinout |
| [`docs/pcb/schematic.md`](docs/pcb/schematic.md) | Rev A schematic, sheet by sheet — draw from this |
| [`docs/pcb/layout.md`](docs/pcb/layout.md) | Layout, assembly and bring-up (later) |
| [`docs/enclosure.md`](docs/enclosure.md) | Enclosure notes |
| `kicad/room-node/` | KiCad project |
| `reports/bom/rev-a-bom-lcsc.csv` | Rev A BOM with LCSC numbers |
| `models/` | Wake word model |

## Flash

1. Copy `secrets.yaml.example` to `secrets.yaml` and fill it in. Git ignores it.
2. `esphome run room-node.yaml` — USB the first time, then OTA (192.168.1.50).
3. Home Assistant finds the node. Assign an Assist pipeline under **Settings → Voice assistants**.

Built by [Chris Boerner](https://boernerc20.me).
