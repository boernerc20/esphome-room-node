# Enclosure notes (3D print)

- **Display window:** cut to the active area, 66.9 × 29.1 mm (module is 89.5 × 38 × 4.7 mm).
- **LED ring:** 27 px around the display. Cover with a translucent diffuser (PETG, 1.5–2 mm wall).
- **Speaker (Dayton CE32A-8):** cutout 31.5 mm, frame 32 mm, depth 14.5 mm.
  Sealed back chamber of 20–30 cc with some poly stuffing. Seal the cone to the front wall.
- **Mic (PCB):** bottom port. Bring a sealed path (gasket or foam ring) from a case
  opening to the hole under the mic on the **bottom** of the PCB.
- **Isolation:** keep the mic away from the speaker, with foam between them. There is no
  echo cancellation, so speaker sound in the mic can trigger the wake word.
- **Sensor:** put a vent above the AHT20, away from warm parts.
- **Cable exits (SQU-35, 2026-10-05).** Looking at the parts side with USB-C on the left:
  - **Left edge:** USB-C (J1) and, just below it, the LED strip connector (J4, cable
    exits upward off a vertical XH plug). Both need an opening or channel on that side.
  - **Right edge:** the display cable (J3, side entry, mouth flush with the edge). It
    runs straight out of the right edge into the gap behind the display.
  - **Bottom-right:** the speaker plug (J2, vertical, cable exits upward).
  - The mic opening stays at the **bottom-left** corner, unchanged, and is 9.3 mm clear
    of the LED connector.
  - The antenna still overhangs the **top** edge by about 6 mm: no metal in front of it.
