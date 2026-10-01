# Rev A pinout — ESP32-S3-WROOM-1-N16R8 (U1)

One row per module pin. **Pin** = module pin number on the KiCad symbol
`RF_Module:ESP32-S3-WROOM-1` (verified). **GPIO** = the ESP32 GPIO number. They are
two different numbers; always check which one you read.

The breadboard uses the same GPIOs (see [`../breadboard.md`](../breadboard.md)),
except the voice button (GPIO0 on the breadboard, GPIO38 on the PCB).

## Used pins

| Pin | GPIO | Net (global label) | Goes to | Sheet |
|---|---|---|---|---|
| 1, 40, 41 | — | `GND` | ground plane, via array under the pad | MCU |
| 2 | — | `+3V3` | LDO output | MCU |
| 3 | EN | `EN` | 10 kΩ pull-up, 1 µF to GND, RESET button | MCU |
| 4 | 4 | `I2S_MIC_BCLK` | mic BCLK (through 33 Ω) | Mic |
| 5 | 5 | `I2S_MIC_WS` | mic WS (through 33 Ω) | Mic |
| 6 | 6 | `I2S_MIC_DATA` | mic DATA (through 33 Ω), 100 kΩ to GND | Mic |
| 7 | 7 | `AMP_SD` | amp SD_MODE. HIGH = on, LOW = off | Audio |
| 8 | 15 | `EPD_BUSY` | e-paper BUSY (input) | Display |
| 9 | 16 | `I2S_SPK_LRCLK` | amp LRCLK | Audio |
| 10 | 17 | `I2S_SPK_BCLK` | amp BCLK | Audio |
| 11 | 18 | `I2S_SPK_DIN` | amp DIN | Audio |
| 12 | 8 | `I2C_SDA` | AHT20 SDA, 4.7 kΩ pull-up | Sensor |
| 13 | 19 | `USB_D-` | USB-C D− (through ESD U5) | MCU |
| 14 | 20 | `USB_D+` | USB-C D+ (through ESD U5) | MCU |
| 17 | 9 | `I2C_SCL` | AHT20 SCL, 4.7 kΩ pull-up | Sensor |
| 18 | 10 | `EPD_CS` | e-paper CS | Display |
| 19 | 11 | `EPD_MOSI` | e-paper DIN | Display |
| 20 | 12 | `EPD_CLK` | e-paper CLK | Display |
| 21 | 13 | `EPD_DC` | e-paper DC | Display |
| 22 | 14 | `EPD_RST` | e-paper RST | Display |
| 23 | 21 | `LED_DIN` | LED strip DIN (through 470 Ω) | LED |
| 27 | 0 | `IO0` | BOOT button, 10 kΩ pull-up. ⚠ strapping pin | MCU |
| 31 | 38 | `VA_BTN` | voice button, 10 kΩ pull-up | MCU |
| 36 | 44 (RXD0) | `RXD0` | test point | MCU |
| 37 | 43 (TXD0) | `TXD0` | test point | MCU |
| 39 | 1 | `CC_SENSE` | USB-C CC sense (analog, ADC1_CH0) | MCU |

## Do not use

| Pin | GPIO | Why |
|---|---|---|
| 15, 16, 26 | 3, 46, 45 | Strapping pins. Leave not connected. |
| 28, 29, 30 | 35, 36, 37 | Used inside the module by the octal PSRAM. |
| — | 26–32 | Flash. Not on the module pins. |

## Free (spare)

| Pin | GPIO | Note |
|---|---|---|
| 38 | 2 | Last free ADC1 pin. |
| 32–35 | 39–42 | JTAG. Keep free if you want hardware debug. |
| 24, 25 | 47, 48 | No ADC. |

Leave free pins not connected. A test pad on GPIO2 is optional.

## Why GPIO38 for the voice button

GPIO0 is the BOOT strap. If a user holds a GPIO0 button during power-on, the chip
enters flash mode and looks dead. Firmware cannot fix that after the board is made.
So GPIO0 is only the BOOT button, and the voice button is on GPIO38.
