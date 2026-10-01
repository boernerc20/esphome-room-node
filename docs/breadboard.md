# Breadboard wiring (as built, confirmed 2026-09-30)

Pins match [`../room-node.yaml`](../room-node.yaml). Power: 5 V USB into the dev board.

| Part | Wiring |
|---|---|
| ESP32-S3 dev board, N16R8 | 5 V USB in |
| Adafruit SPH0645 breakout (mic) | BCLK→GPIO4, LRCL→GPIO5, DOUT→GPIO6, SEL→GND, 3V→3V3 |
| MAX98357A breakout (amp) | BCLK→GPIO17, LRC→GPIO16, DIN→GPIO18, SD→GPIO7, GAIN→VIN (6 dB), VIN→5V. 470–1000 µF + 0.1 µF across VIN/GND at the amp |
| Dayton CE32A-8 speaker | amp + and −. Do not ground either wire |
| AHT20 breakout | SDA→GPIO8, SCL→GPIO9, VCC→3V3 (breakout has pull-ups) |
| Waveshare 2.9" e-paper v2 | CLK→GPIO12, DIN→GPIO11, CS→GPIO10, DC→GPIO13, RST→GPIO14, BUSY→GPIO15, VCC→3V3 |
| WS2812B strip, 27 px | GPIO21 → 330–470 Ω → DIN. 5V, GND. 1000 µF across 5V/GND at the strip |
| Voice button | GPIO0 to GND (the dev board BOOT button does the same) |

**Ground:** star. Amp GND and LED GND each go on their own wire to GND at the 5 V input.

**Audio:** keep GAIN→VIN (6 dB). 9 dB is louder but clips and cuts out on 5 V.
Firmware `volume_multiplier: 1.0` is the loudest clean setting. A sealed box behind
the speaker gives the biggest gain.

**Mic mute:** software switch "Mic muted" in Home Assistant.
