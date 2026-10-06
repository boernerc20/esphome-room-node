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
- **Cable exits (rev A board at dc89150, 2026-10-06).** Looking at the parts side with USB-C on the left:
  - **Left edge:** USB-C (J1) needs its own opening.
  - **Bottom edge:** the LED strip connector (J4, side-entry JST S3B-XH-A) faces
    outward. Provide a nominal 10 mm wide slot in the bottom wall, centred on
    PCB x = 126.5 mm (J4 pin 2). The housing spans x = 121.5–131.5 mm and its
    front face is at y = 137.7 mm, 0.3 mm inside the PCB edge (y = 138.0 mm).
    The mating plug and cable extend beyond that edge. **Open question:** final
    slot height, wall clearance and cable bend space need a physical fit check.
  - **Right edge:** the display cable (J3, side entry, mouth flush with the edge). It
    runs straight out of the right edge into the gap behind the display.
  - **Bottom-right:** the speaker plug (J2, vertical, cable exits upward).
  - The mic opening stays at the **bottom-left** corner; J4's courtyard is 12.5 mm
    to its right.
  - The antenna still overhangs the **top** edge by about 6 mm: no metal in front of it.
