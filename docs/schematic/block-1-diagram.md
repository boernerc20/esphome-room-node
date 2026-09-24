# Block 1 — MCU + Power + USB — draw-from-this diagram

Companion to [`block-1-mcu-power-usb.md`](block-1-mcu-power-usb.md) (parts table, MPNs,
rationale). This file is the visual layout: draw each box as its KiCad symbol, wire
along the lines, use the net names as your global labels. Nothing here should
disagree with the parts doc — if it does, the parts doc is the tiebreaker and this
file has drifted and needs a fix.

---

## USB-C front end

```
                         +5V ────────────────────────┬──────────┬──────────┐
                          │                           │          │          │
                    ┌─────┴─────┐                    C1        C2         U2.VIN(3)
                    │  J1       │                   10µF      0.1µF        │
                    │ USB-C     │                     │          │        (LDO — see below)
                    │ receptacle│                     └────GND───┘
                    │           │
   VBUS (A4,B4,A9,B9)┤──────────┼──────────────────── +5V
   GND  (A1,B1,A12,B12)─────────┼──────────────────── GND
   CC1  (A5) ────────┤          ├──── R1 5.1k ──────── GND
   CC2  (B5) ────────┤          ├──── R2 5.1k ──────── GND
   D+   (A6,B6) ──────┤         ├──────────────────── USB_D+_CONN
   D−   (A7,B7) ──────┤         ├──────────────────── USB_D-_CONN
   SBU1 (A8) ─────────┤         │  no connect
   SBU2 (B8) ─────────┤         │  no connect
   Shield (SH) ───────┤         ├──────────────────── GND
                    └───────────┘

   USB_D+_CONN ──────────────────┐
   USB_D-_CONN ──────────────────┤
                            ┌─────┴─────┐
                            │    U5     │  USBLC6-2SC6 (SOT-23-6)
                            │ ESD array │  ✅ pinout verified vs ST DocID 11265
                            │           │
   I/O1 ── USB_D-_CONN ─────┤1        6├──── USB_D-  ──→ U1 pin13 (GPIO19)
   GND  ── GND ─────────────┤2        5├──── +5V
   I/O2 ── USB_D+_CONN ─────┤3        4├──── USB_D+  ──→ U1 pin14 (GPIO20)
                            └───────────┘
```

## LDO — 3V3 rail

```
   +5V ──┬──────────────┐
        C3             U2.VIN (pin 3)
       1µF          ┌───┴────┐
        │           │  U2    │   AP7361C-33ER-13, SOT-223
       GND          │ LDO    │
                     │        │
   GND ──────────────┤ pin1   │
                     │        │
   +3V3 ─────────────┤ pin2/tab (VOUT)
                     └────────┘
        │
        ├── C4 22µF ── GND
        └── C5 0.1µF ── GND
```

## ESP32-S3-WROOM-1-N16R8 (U1) — Block 1 pins only

```
                         ┌─────────────────────────┐
                  +3V3 ──┤2  3V3                    │
                  EN   ──┤3  EN                     │
                         │                          │
        USB_D− (from U5)─┤13 USB_D−                 │
        USB_D+ (from U5)─┤14 USB_D+                 │
                         │                          │
                  IO0  ──┤27 IO0/BOOT               │
             VA_BTN   ──┤31 IO38                    │
                         │                          │
   TXD0→TP3 ─────────────┤37 TXD0 / GPIO43          │
   RXD0→TP4 ─────────────┤36 RXD0 / GPIO44          │
                         │                          │
                  GND  ──┤1,40,41 (GND + thermal pad)│
                         └─────────────────────────┘
   All other GPIO → other block sheets, see rev-a-architecture.md master pin map.

   Unusable — in GPIO numbers, NOT module pin numbers: GPIO26-32 (flash),
   GPIO35/36/37 (PSRAM). Module pins 36/37 above are GPIO44/GPIO43 (UART0) —
   different numbering scheme, no actual conflict with the GPIO35-37 PSRAM pins.
```

> Module-pin-number and GPIO-number are two different schemes on this part and the
> docs mix both — always check which one a "pin 36/37"-style reference means before
> wiring, per the note above.

## Reset / Boot / VA button

```
   +3V3          +3V3          +3V3
    │             │             │
   R3 10k        R4 10k        R5 10k
    │             │             │
    ├── EN ───────┤             │         (EN = U1 pin 3)
    │             ├── IO0 ──────┤         (IO0 = U1 pin 27)
    │             │             ├── VA_BTN (= U1 pin 31 / IO38)
   C8 1µF        SW2            SW3
    │             │             │
   GND           GND           GND
    │
   SW1
    │
   GND
```

## Test points

```
   TP1 → EN net        TP5 → +3V3 rail
   TP2 → IO0 net        TP6 → +5V rail
   TP3 → TXD0 net       TP7 → GND
   TP4 → RXD0 net
```

---

## Net name checklist (tick off as you place global labels)

- [ ] `+5V`
- [ ] `+3V3`
- [ ] `GND`
- [ ] `CC1`, `CC2`
- [ ] `USB_D+_CONN`, `USB_D-_CONN` (connector side, before ESD array)
- [ ] `USB_D+`, `USB_D-` (module side, after ESD array)
- [ ] `EN`, `IO0`, `VA_BTN`
- [ ] `RXD0`, `TXD0`
