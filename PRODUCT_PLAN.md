# Jarvis Room Node — Product Plan

**Goal:** take the working breadboard prototype to a manufacturable, sellable smart-speaker/sensor node ("room node") that anyone can flash, adopt into Home Assistant in minutes, and that works with any Assist-compatible pipeline — not just Chris's Hermes setup.

This is the execution roadmap for AI-assisted development sessions (Claude Opus / Sonnet / Fable). Read this file first in any session working on this project. Keep it updated: check items off, add discoveries, never let it drift from reality.

---

## Product definition

A per-room voice satellite + environment node for Home Assistant:

- **Voice:** on-device wake word (micro_wake_word), far-field mic, speaker for TTS replies. Works with any HA Assist pipeline (user's choice of STT/LLM/TTS — cloud, local, or an agent like Hermes).
- **Ambient info:** 2.9" e-ink (room name, temp/humidity, glanceable status) + LED ring for voice-state feedback (listening/thinking/speaking).
- **Sensors:** temp/humidity (v1); air quality (VOC/CO₂) reserved for v2.
- **Adoption story (the differentiator):** plug into USB-C → Improv Wi-Fi provisioning → auto-discovered by HA → one-click adopt. No YAML, no toolchain, no soldering.

**Positioning:** the open, hackable alternative to a Home Assistant Voice Preview Edition with a *display* and *sensors* built in. Open-source firmware, sold as assembled hardware. Revenue = hardware margin (open firmware is the marketing, not the product).

---

## Positioning & competition (researched 2026-07)

| Competitor | Price | Display | Sensors | Notes |
|---|---|---|---|---|
| HA Voice Preview Edition | ~$59 | ❌ | ❌ | Official; ESP32-S3 + XMOS AEC; the price anchor |
| FutureProofHomes Satellite1 | ~$65–90 | ❌ | some | S3 + XMOS, 4 mics, best-in-class audio; enthusiast favorite |
| ESP32-S3-BOX-3 | ~$50 | LCD | ❌ | Devkit aesthetics, dev audience |
| M5Stack ATOM Echo | ~$13 | ❌ | ❌ | Entry-level, poor audio |
| Echo / Nest / HomePod | $50–99 | some | ❌ | Cloud, closed — the narrative foil |

**Key insight:** "open source" is NOT the wedge vs Voice PE/Sat1 (they're open too) — it's only the wedge vs Big Tech. The defensible wedge: **no open competitor ships a persistent display or full room sensing.** We are a "room node"/ambient room instrument, useful 24/7, not a blind puck.

**Brand pillars:**
1. **Name the category** — never "smart speaker" (we lose on audio specs to XMOS rivals). It's a *room node*: the room at a glance, that you can also talk to.
2. **Calm tech** — e-ink/paper aesthetic, no glow at night (ring sleeps on schedule), no camera, no cloud account, works offline. Openness = verifiable trust.
3. **Sell the fleet** — one per room; e-ink shows the room's name; marketing photos show 3 units in 3 rooms. Justifies price: 3 of ours ≈ 1 HomePod.
4. **Honest about audio** — no XMOS AEC in v1: position for commands/answers, not music playback. Physical mic-mute switch reinforces the privacy pillar.
5. Working tagline: **"See the room. Speak to the house."**

**Named risk:** reviewers will benchmark audio/barge-in vs XMOS-equipped rivals. v1 answer = positioning + mechanical mic isolation; v2 answer = AEC-capable codec or XMOS option (Phase 2 should keep board space/JST for it if cheap to do).

---

## Current status (2026-07-28)

**Now:** Phase 0 **complete** (breadboard proven, audio verified clean, power measured — see Decisions log + Phase 0 checklist). **Phase 2 (KiCad) in progress** — schematic authored block-by-block in [`docs/schematic/`](docs/schematic/): `rev-a-architecture.md` (block diagram, power tree, strapping-checked pin map, BOM) + `block-1-mcu-power-usb.md` done, **pending review before drawing**. Workflow: net lists authored as visual docs in the repo → reviewed vs datasheets/breadboard → drawn in KiCad on the **workstation** (tailnet 100.88.81.67) → next block. **Next up: Block 2 (audio, MAX98357A)** — where the Phase 0 lessons (6 dB GAIN strap, decoupling, star ground, SD mute) get baked in. Repo pushed to GitHub (`git@github.com:boernerc20/esphome-room-node.git`) through `0be8b6b`.

**Working on breadboard:** ESP32-S3 devkit, INMP441 mic, MAX98357A + Dayton CE32A-8 8Ω speaker, AHT20, Waveshare 2.9" e-ink, 27-px WS2812B strip, hey_jarvis wake word, full HA Assist pipeline (node ↔ HA Pi5 ↔ conversation agent). Node pinned at 192.168.1.188 (manual_ip). Voice works end-to-end.

**Known issues / open items:**
- ~~Audio crackle + inconsistent volume~~ — **RESOLVED 2026-07-28**: volume_multiplier 1.0, GAIN→Vin (6 dB), 470–1000 µF + 0.1 µF at amp, star ground, SD→GPIO7 mute. Verified clean.
- No acoustic echo cancellation (mic self-trigger during TTS) — mitigate mechanically in enclosure; evaluate `micro_wake_word` VAD / AEC options later.
- ~~Repo hygiene~~ — **DONE**: committed + pushed to GitHub through `0be8b6b`; `ROOM_NODE.md` archived to `docs/archive/`; secrets verified untracked.
- ~~HARDWARE.md 8-px ring~~ — **DONE**: corrected to 27 px throughout.

**Source of truth ranking:** `room-node.yaml` (as-flashed) > `HARDWARE.md` > everything else. `ROOM_NODE.md` is historical — do not trust its pin map.

---

## How to run sessions (model routing)

| Model | Use for |
|---|---|
| **Opus / Fable** | Schematic architecture & review, PCB layout review, power-tree design, compliance research, anything where a wrong decision costs a board spin. Debugging weird hardware/firmware interactions. |
| **Sonnet** | YAML/firmware edits, doc writing & upkeep, BOM maintenance, CI setup, KiCad grunt work from an approved schematic (footprint assignment, BOM export), web flasher page, marketing copy drafts. |

**Rules for every session:**
1. Read this file + `HARDWARE.md` first. Update both before ending the session.
2. Never flash the node without validating (`esphome config room-node.yaml`) first. Flash target is `192.168.1.188` (static). Build env: `~/projects/homelab/esphome-venv/bin/esphome` on jarvis-node.
3. Commit at every working milestone. Small commits, real messages. The repo is the product's history.
4. Hardware changes (pins, parts) must land in `HARDWARE.md` + yaml in the same commit.
5. Decisions that constrain the PCB (pin choices, part swaps, power) get a short "Decision:" note appended to §Decisions log below.

---

## Phase 0 — Close out the breadboard prototype *(gating everything)*

Prove the design is worth laying out. Exit criteria: clean audio, reliable wake→reply loop, repo committed.

- [x] **Fix audio chain** — done 2026-07-28, verified clean on voice + repeated announcements (no clip/underrun in logs):
  - [x] `volume_multiplier: 2.0 → 1.0` (digital clipping was the crackle source).
  - [x] MAX98357A **GAIN → Vin directly (6 dB)** — killed float-noise, defined gain.
  - [x] **470–1000 µF electrolytic + 0.1 µF ceramic across amp Vin↔GND at the chip.**
  - [x] **Star ground:** amp GND and LED-strip GND return separately to board GND, never shared.
  - [x] Bonus: **SD wired to GPIO7** → idle mute now active (kills between-reply hiss/pop).
- [x] **End-to-end voice test** ("hey jarvis"): ring blue→amber→green, reply clean; fast-path + fall-through confirmed.
- [x] **Repo cleanup & commit:** committed `3b12319` (yaml + HARDWARE.md synced); ROOM_NODE.md already archived, no `.bak`s, secrets verified untracked. **Push still pending — jarvis-node SSH key not on GitHub (3 commits ahead).**
- [x] **Decide v1 LED count** — **27 px**, deliberate (wraps the e-ink display perimeter, sets enclosure size).
- [ ] Note real-world wake-word performance (range, false triggers) — *partial:* detected reliably in-room across many test triggers, no false fires observed; formal range/false-trigger characterization still TBD.

**Hardware to acquire for Phase 0–2 (bench + v1 design):**
- [ ] Cap kit: 470–1000 µF electrolytics + 0.1 µF ceramics (audio decoupling fix + PCB values)
- [ ] Resistor kit incl. 330–470 Ω (LED data) and 100 kΩ (GAIN straps)
- [ ] 74AHCT125 in DIP (validate LED level shifting on breadboard before it goes on the PCB)
- [ ] **Second complete breadboard set** (S3 devkit + INMP441 + MAX98357A + AHT20) — dev unit, so the working bedroom node stays in service while iterating
- [ ] USB power meter (~$15) — real current budget numbers for the power tree
- [ ] Cheap 8-ch logic analyzer (~$15, sigrok-compatible) — I2S/I2C debugging, essential for PCB bring-up
- [ ] **Physical mic-mute switch** (slide or latching) — v1 privacy feature, brand pillar
- [ ] Rotary encoder w/ push (optional) — volume/mute dial à la Voice PE; decide in v1 scope
- [ ] Final LED ring/strip at deliberate count & density for the enclosure (27 was incidental; 30/m wraps the display perimeter per HARDWARE.md)
- [ ] Good Display GDEY029T94 (or equiv raw 2.9" panel) — second-source/BOM-cost eval vs Waveshare module
- [ ] SHT40 breakout — accuracy + self-heating eval vs AHT20; informs sensor placement on PCB
- [ ] ReSpeaker Lite (~$25, XMOS XU316) — benchmark unit: measure what AEC/beamforming buys before deciding v2 audio front-end

## Phase 1 — Firmware productization

Make the firmware installable by strangers, not just us.

- [ ] Restructure yaml with ESPHome **`packages:`** (core/audio/display/ring/sensors) so users can override cleanly; put user-tweakables in `substitutions:`.
- [ ] Add **`project:`** block (`chris.room_node`, semver version) + **`dashboard_import:`** so ESPHome Dashboard offers the config by name.
- [ ] Add **Improv** provisioning (`improv_serial` + `esp32_improv` BLE) → Wi-Fi setup from phone/browser, no secrets.yaml.
- [ ] Add `captive_portal:`, `web_server:` (or at least captive portal on the fallback AP — currently a warning).
- [ ] **GitHub Actions CI:** compile firmware on every push; release job publishes `firmware.factory.bin` + manifest for **ESP Web Tools** (flash-from-browser page on GitHub Pages).
- [ ] User-facing docs: README rewrite (what it is, flash it, adopt it), FAQ, pipeline-agnostic setup (works with plain Assist, not just Hermes).
- [ ] Target **"Made for ESPHome"** compliance checklist (open config, Improv, project metadata) — apply once hardware is stable.

## Phase 2 — KiCad rev A (breadboard → PCB)

One board, devkit replaced by module. Get to "boards that work on the bench."

- [ ] **Schematic** (Opus-level review before layout):
  - ESP32-S3-**WROOM-1**-N8R8 module (pre-certified, castellated), proper RF keep-out.
  - USB-C power (+ native USB D±for flashing/logs): 5.1 kΩ CC pull-downs, ESD array (USBLC6-2), input bulk cap.
  - Power tree: 5 V rail → amp + LEDs; 3V3 via decent LDO (not AMS1117 — pick low-noise, e.g. ME6217/AP2112 class or small buck if LED budget grows); per-IC 0.1 µF + bulk per rail; **audio decoupling designed in from day 1** (this is what the breadboard taught us).
  - MAX98357A: GAIN strap footprint (choose 6 dB default), SD gate from GPIO7 as today; speaker JST-PH 2-pin.
  - WS2812B chain: **74AHCT125 level shifter**, 330 Ω series, 1000 µF bulk footprint.
  - INMP441 (or footprint-compatible upgrade path), placed **far from speaker**, port hole on board edge/underside per datasheet acoustic guidance.
  - AHT20 + I2C pull-ups; e-ink via FPC/JST matching Waveshare cable; boot/reset buttons; GPIO0 user button; test points (TX/RX/EN/IO0/3V3/5V/GND).
- [ ] Pin map review against strapping pins — current GPIO map in `HARDWARE.md` is the baseline; document any change in both files.
- [ ] **Layout:** 2-layer if routable (4-layer if audio noise demands ground plane discipline — likely worth it), antenna clearance per Espressif appnote, I2S short runs, LED power routed away from mic/amp analog area.
- [ ] DFM for **JLCPCB assembled** (parts from LCSC where possible; check stock/alternates before finalizing BOM).
- [ ] Order **5 boards assembled**, bring-up checklist (rails → USB enumerate → flash → each peripheral → audio noise floor vs breadboard).

## Phase 3 — Enclosure

- [ ] 3D-printed rev 1 (per HARDWARE.md acoustics): sealed 20–30 cc speaker chamber, mic mechanically isolated + front port, e-ink window at active area (66.9×29.1 mm), LED diffuser channel, USB-C cutout, wall/desk mount.
- [ ] Iterate for the PCB (rev A mounting bosses, board outline lock between KiCad and CAD — export DXF/STEP both ways).
- [ ] Print-farm-friendly design for early units; note draft angles/wall thickness if injection molding ever pencils out (only at >1k units).

## Phase 4 — Pilot run & test

- [ ] Rev B PCB with bring-up fixes → **25–50 unit pilot** (JLCPCB PCBA).
- [ ] **Factory flash + test jig:** pogo-pin or USB batch flash of factory firmware; scripted self-test (mic level, speaker tone, sensor read, LED walk, e-ink refresh) with pass/fail.
- [ ] QA checklist + serial/batch labeling.

## Phase 5 — Compliance (research early, spend late)

- [ ] FCC: WROOM-1 modular cert covers intentional radiator; product still needs **Part 15B unintentional-radiator** testing (~$1–3 k at a test lab). CE/RED if selling to EU (bigger lift — decide market scope first).
- [ ] RoHS-compliant BOM (JLCPCB default is fine — verify), WEEE labeling for EU, safety wording for the manual.
- [ ] Trademark/naming check before printing anything ("Jarvis" is not shippable — pick a product name; check USPTO + domains).

## Phase 6 — Launch

- [ ] **Channel:** start Tindie (built for exactly this) → CrowdSupply campaign if traction → own Shopify later. 
- [ ] **Pricing sanity:** BOM target ≤ $40 at qty 50 (incl. display, driver, PCB assy) → sell $89–119 assembled. Track actual BOM in `docs/bom.csv` from Phase 2 onward.
- [ ] Docs site (GitHub Pages: flash page + setup guide + API/yaml reference), demo video, HA community forum + r/homeassistant + ESPHome Discord launch posts.
- [ ] License decision: firmware/config **GPLv3 or MIT** (open), hardware **CERN-OHL or proprietary** — decide deliberately (Decision log).
- [ ] Support plan: GitHub issues, versioned OTA releases via web flasher page.

---

## Decisions log

- 2026-07-01: Whisper STT `small-int8` beam 2 on Pi5 CPU — big accuracy win.
- 2026-07-06: Speaker = Dayton CE32A-8 (8Ω, shallow 14.5 mm); BTL wiring, never ground a terminal.
- 2026-07-06: Addressable WS2812B over analog RGB strip (keeps comet effect, no MOSFETs).
- 2026-07-15: `led_count` 27 (actual strip); static IP 192.168.1.188 via `manual_ip`.
- 2026-07-23: GAIN strategy = tie to Vin (6 dB) not floating; product default gain 6 dB with strap options on PCB.
- 2026-07-28: **Power tree = USB-C 5 V** (5.1 kΩ CC pull-downs, no dedicated LED supply). Measured whole-node current on bench supply: **~0.31 A** blue-breathing state, **~1.0 A** at solid-white 100% — well within USB-C headroom. Keep a firmware LED-brightness cap as insurance for legacy 500 mA USB-A sources. WS2812B **1000 µF bulk cap + 330–470 Ω DIN series resistor = PCB footprints** (validated unnecessary on a stiff bench supply / short strip, but kept for real USB-C source impedance and full-white load; bulk cap at the strip/connector, DIN resistor source-side after the level shifter).

## Risks

1. **Audio quality on the PCB** — the breadboard crackle must be *understood* (not just patched) before layout, or we etch the noise in. Phase 0 is gating for a reason.
2. **Echo/self-trigger without AEC** — mechanical isolation may not be enough; may need `stop_after_detection`-style muting during TTS (already partially in yaml) or a v2 codec with AEC.
3. **E-ink cost** (~$15–20) dominates BOM — evaluate cheaper panels or a display-less SKU.
4. **HA Voice PE price anchor** (~$59) — our display+sensors must justify the delta; sharpen positioning early.
5. Single-source parts (Waveshare panel, CE32A-8) — identify seconds sources during Phase 2 BOM work.
