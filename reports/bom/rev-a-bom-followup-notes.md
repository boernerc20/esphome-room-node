# SQU-19: Rev A BOM follow-up — sourcing notes

**Date:** 2026-09-30
**Agent:** Nora (Research & Docs)
**Branch:** `norasqu-19-bom-followup`

## Changes to `reports/bom/rev-a-bom-lcsc.csv`

### 1. PR #5 parts added

| Ref | Part | Value | Package | LCSC# | JLC Class | Stock | Notes |
|-----|------|-------|---------|-------|-----------|-------|-------|
| R6, R7 | 0603 100kΩ 1% | 100 kΩ | 0603 | C25803 | Basic | Very High | CC1/CC2 → CC_SENSE sum |
| C9 | 0603 0.1µF 50V X7R | 0.1 µF | 0603 | C30722 | Basic | Very High | CC_SENSE filter at GPIO1 |
| TP8 | Test pad D1.5mm | — | — | — | — | High | CC_SENSE test point |
| R8 | 0603 100kΩ 1% | 100 kΩ | 0603 | C25803 | Basic | Very High | Mic DATA pull-down to GND |
| R9, R10, R11 | 0603 33Ω | 33 Ω | 0603 | TBD | Basic | Very High | I2S mic damping |
| C10 | 0603 0.1µF X7R | 0.1 µF | 0603 | C30722 | Basic | Very High | Mic VDD decoupling |
| C11 | 0603 100pF C0G 50V | 100 pF | 0603 | TBD | Basic | High | Mic VDD RF filter (DNP) |

**LCSC# sources:**
- **C25803** — verified via `easyeda2kicad` API on 2026-09-30: symbol `0603WAF1003T5E` (UniOhm, 0603 package, 100×10³ = 100 kΩ)
- **C30722** — existing in BOM for C2/C5/C7/C_amp_cer (0603 0.1µF 50V X7R)
- **R9,R10,R11 (33Ω)** — LCSC# TBD. Candidate: C105881 (YAGEO RC0603FR-07330RL) per LCSC product listing, but `easyeda2kicad` API returned 403. Confirm 1% tolerance or if ±5% (JR series) is acceptable.
- **C11 (100pF C0G)** — LCSC# TBD. No candidate verified. Check availability of C0G 0603 100pF at LCSC.

### 2. CSV quoting fixes

The following multi-reference cells were unquoted, causing column shifts for CSV parsers:

| Row | Before | After |
|-----|--------|-------|
| SW1-SW3 | `SW1-SW3` | `"SW1-SW3"` |
| R1,R2 | `R1,R2` | `"R1,R2"` |
| R3-R5 | `R3-R5` | `"R3-R5"` (dash, technically safe but quoted for consistency) |
| C5,C7 | `C5,C7` | `"C5,C7"` |

### 3. MK1 lifecycle

**Previous BOM value:** Active
**Updated BOM value:** Transitioned (active via Syntiant; Knowles EOL)

**Research findings (2026-09-30):**

| Source | Finding | Date |
|--------|---------|------|
| DigiKey (part 5332440) | SPH0645LM4H-B listed under **Syntiant** (not Knowles). "Buy now, ships today" — active, in stock. | 2026-09-30 |
| Mouser | SPH0645LM4H-B listed under Syntiant. Available. | 2026-09-30 |
| DigiKey: SPH0645LM4H-B-8INACTIVE | The tape & reel variant `-B-8` has **"INACTIVE"** in DigiKey's part name (423-SPH0645LM4H-B-8INACTIVE-ND) | 2026-09-30 |
| Knowles | Product line moved to Syntiant. Knowles-branded datasheets still circulate; knowles.com PDF links return 404 (noted in rev-a-architecture.md, 2026-09-28) | 2026-09-28 |
| rev-a-architecture.md (PR #5) | Flagged SPH0645LM4H-B, -1, -1-8 as Obsolete at distributor listings. Suggested alternate: TDK ICS-43434. | 2026-09-28 |

**Conclusion:** The part is not fully obsolete — Syntiant still sells the -B variant as active. The Knowles-branded version is EOL, and the -B-8 tape & reel variant is inactive. For 5 hand-built rev A boards, the -B tray variant is orderable today from DigiKey/Mouser under Syntiant. For the Phase 4 pilot, evaluate TDK ICS-43434 (footprint/pinout compatibility unverified) or the Syntiant -1 variant.

### 4. U4 (74AHCT125)

Per D4, the 74AHCT125 level shifter is removed from rev A. Confirmed absent from `reports/bom/rev-a-bom-lcsc.csv` — no changes needed.

## Open questions

1. **33Ω 0603 resistor LCSC#:** C105881 (YAGEO RC0603FR-07330RL) is the top candidate from search results but not confirmed via the EasyEDA API (403). Verify tolerance requirement: 1% (FR series) or is ±5% (JR series) acceptable for I2S damping resistors?
2. **100pF C0G 0603 capacitor LCSC#:** Not found. Check LCSC for "0603 100pF C0G 50V" or equivalent. If C0G unavailable, evaluate X7R as fallback (different temp stability spec).