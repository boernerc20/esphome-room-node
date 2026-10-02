#!/usr/bin/env python3
"""Check the rev A schematic netlist against docs/pcb/pinout.md and docs/pcb/schematic.md.

Usage (from the repo root):
    python3 tools/check_pinout.py                # exports the netlist with kicad-cli
    python3 tools/check_pinout.py my.net         # use an existing KiCad (s-expr) netlist

Prints a Markdown report. Exit code 1 if any check fails.

Checks:
  1. Every module (U1) pin in pinout.md "Used pins" is on the net named there.
  2. Every pin in "Do not use" and "Free (spare)" is not connected.
  3. No other U1 pin is connected.
  4. Each net reaches the right pins on the other sheets (from schematic.md).
"""
import os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = os.path.join(ROOT, 'kicad/room-node/room-node.kicad_sch')
PINOUT = os.path.join(ROOT, 'docs/pcb/pinout.md')

# Net -> pins that must be on it ("REF.PIN"). From docs/pcb/schematic.md.
EXPECT = {
    'EN': ['U1.3', 'R3.2', 'C8.1', 'SW1.2', 'TP1.1'],
    'IO0': ['U1.27', 'R4.2', 'SW2.2', 'TP2.1'],
    'VA_BTN': ['U1.31', 'R5.2', 'SW3.2'],
    'TXD0': ['U1.37', 'TP3.1'],
    'RXD0': ['U1.36', 'TP4.1'],
    'CC1': ['J1.A5', 'R1.1', 'R6.1'],
    'CC2': ['J1.B5', 'R2.1', 'R7.1'],
    'CC_SENSE': ['U1.39', 'R6.2', 'R7.2', 'C9.1', 'TP8.1'],
    'USB_D+_CONN': ['J1.A6', 'J1.B6', 'U5.3'],
    'USB_D-_CONN': ['J1.A7', 'J1.B7', 'U5.1'],
    'USB_D+': ['U1.14', 'U5.4'],
    'USB_D-': ['U1.13', 'U5.6'],
    'I2S_MIC_BCLK': ['U1.4', 'R9.2'],
    'I2S_MIC_WS': ['U1.5', 'R10.2'],
    'I2S_MIC_DATA': ['U1.6', 'R11.2', 'R8.1'],
    'I2S_SPK_LRCLK': ['U1.9', 'U3.14'],
    'I2S_SPK_BCLK': ['U1.10', 'U3.16'],
    'I2S_SPK_DIN': ['U1.11', 'U3.1'],
    'AMP_SD': ['U1.7', 'U3.4', 'R20.1'],
    'I2C_SDA': ['U1.12', 'U6.4', 'R40.2'],
    'I2C_SCL': ['U1.17', 'U6.3', 'R41.2'],
    'EPD_CS': ['U1.18', 'J3.5'],
    'EPD_MOSI': ['U1.19', 'J3.3'],
    'EPD_CLK': ['U1.20', 'J3.4'],
    'EPD_DC': ['U1.21', 'J3.6'],
    'EPD_RST': ['U1.22', 'J3.7'],
    'EPD_BUSY': ['U1.8', 'J3.8'],
    'LED_DIN': ['U1.23', 'R30.1'],
    'STATUS_LED': ['U1.38', 'R12.1'],
    '+5V': ['J1.A4', 'J1.B4', 'J1.A9', 'J1.B9', 'C1.1', 'C2.1', 'U5.5', 'U2.3', 'C3.1', 'TP6.1',
            'U3.2', 'U3.7', 'U3.8', 'C20.1', 'C21.1', 'C22.1', 'J4.1', 'C30.1'],
    '+3V3': ['U2.2', 'C4.1', 'C5.1', 'U1.2', 'C6.1', 'C7.1', 'R3.1', 'R4.1', 'R5.1', 'TP5.1',
             'MK1.5', 'C10.1', 'C11.1', 'U6.2', 'C40.1', 'R40.1', 'R41.1', 'J3.1', 'C50.1'],
    'GND': ['U1.1', 'U1.40', 'U1.41', 'J1.A1', 'J1.B1', 'J1.A12', 'J1.B12', 'J1.SH', 'U5.2', 'U2.1',
            'R1.2', 'R2.2', 'C8.2', 'C9.2', 'SW1.1', 'SW2.1', 'SW3.1', 'TP7.1',
            'U3.3', 'U3.11', 'U3.15', 'U3.17', 'R20.2', 'MK1.2', 'MK1.3', 'R8.2', 'U6.5', 'J3.2', 'J4.3',
            'D1.1'],
}
# Pins that must share one (unnamed) net: series parts and the speaker.
SAME = [
    ('MK1.1', 'R10.1'), ('MK1.4', 'R9.1'), ('MK1.6', 'R11.1'),
    ('R30.2', 'J4.2'), ('R12.2', 'D1.2'), ('U3.9', 'J2.1'), ('U3.10', 'J2.2'),
]
NOT_CONNECTED = ['J1.A8', 'J1.B8', 'U6.1', 'U6.6', 'U3.5', 'U3.6', 'U3.12', 'U3.13']


def sexp(text):
    tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')
    stack, pos = [[]], 0
    while True:
        m = tok.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(m.group(3) if m.group(3) is not None else m.group(4))
    return stack[0][0]


def load_netlist(path):
    tree = sexp(open(path, encoding='utf-8').read())
    nets = next(e for e in tree if isinstance(e, list) and e[0] == 'nets')
    pin_net = {}
    for net in nets[1:]:
        name = next(e[1] for e in net if isinstance(e, list) and e[0] == 'name')
        for node in (e for e in net if isinstance(e, list) and e[0] == 'node'):
            d = {e[0]: e[1] for e in node[1:] if isinstance(e, list)}
            pin_net[f"{d['ref']}.{d['pin']}"] = name.lstrip('/')
    return pin_net


def nums(cell):
    out = []
    for part in cell.replace('–', '-').split(','):
        part = part.strip()
        if re.fullmatch(r'\d+-\d+', part):
            a, b = map(int, part.split('-'))
            out += list(range(a, b + 1))
        elif part.isdigit():
            out.append(int(part))
    return out


def load_pinout():
    used, unused, section = {}, {}, None
    for line in open(PINOUT, encoding='utf-8'):
        if line.startswith('## '):
            section = line[3:].strip()
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if not line.startswith('|') or len(cells) < 3 or not re.match(r'^[\d—]', cells[0]):
            continue
        pins = nums(cells[0])
        if section == 'Used pins':
            net = cells[2].strip('`')
            for p in pins:
                used[p] = (net, cells[1])
        elif section in ('Do not use', 'Free (spare)'):
            gpios = nums(cells[1])
            for i, p in enumerate(pins):
                unused[p] = (section, str(gpios[i]) if len(gpios) == len(pins) else cells[1])
    return used, unused


def connected(pin_net, key):
    n = pin_net.get(key)
    return n is not None and not n.startswith('unconnected-')


def main():
    if len(sys.argv) > 1:
        net_path = sys.argv[1]
    else:
        net_path = os.path.join(tempfile.mkdtemp(), 'room-node.net')
        subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', net_path, SCH],
                       check=True, stdout=subprocess.DEVNULL)
    pin_net = load_netlist(net_path)
    used, unused = load_pinout()
    fails = 0

    print('## 1. U1 used pins (pinout.md) vs netlist\n')
    print('| U1 pin | GPIO | pinout.md net | netlist net | Also on this net | OK |')
    print('|---|---|---|---|---|---|')
    for p in sorted(used):
        want, gpio = used[p]
        got = pin_net.get(f'U1.{p}', '(missing)')
        others = sorted(k for k, v in pin_net.items() if v == got and not k.startswith('U1.'))
        ok = got == want
        fails += not ok
        if want in ('GND', '+3V3'):
            others = [f'{len(others)} pins']
        print(f"| {p} | {gpio} | `{want}` | `{got}` | {', '.join(others)} | {'✅' if ok else '❌'} |")

    print('\n## 2. U1 pins that must stay not connected\n')
    print('| U1 pin | GPIO | Why | Netlist | OK |')
    print('|---|---|---|---|---|')
    for p in sorted(unused):
        why, gpio = unused[p]
        ok = not connected(pin_net, f'U1.{p}')
        fails += not ok
        print(f"| {p} | {gpio} | {why} | {'not connected' if ok else pin_net[f'U1.{p}']} | {'✅' if ok else '❌'} |")

    extra = sorted(int(k.split('.')[1]) for k in pin_net
                   if k.startswith('U1.') and connected(pin_net, k) and int(k.split('.')[1]) not in used)
    print(f"\n**U1 pins connected but not in pinout.md:** {', '.join(map(str, extra)) or 'none'}")
    fails += len(extra)

    print('\n## 3. Other end of each net (schematic.md)\n')
    print('| Net | Expected pins | Result |')
    print('|---|---|---|')
    for net, keys in EXPECT.items():
        bad = [k for k in keys if pin_net.get(k) != net]
        fails += len(bad)
        res = '✅' if not bad else '❌ ' + ', '.join(f'{k} on `{pin_net.get(k)}`' for k in bad)
        shown = ', '.join(keys) if len(keys) <= 6 else f'{len(keys)} pins'
        print(f'| `{net}` | {shown} | {res} |')
    for a, b in SAME:
        ok = pin_net.get(a) is not None and pin_net.get(a) == pin_net.get(b)
        fails += not ok
        print(f"| (series) | {a} = {b} | {'✅' if ok else '❌'} |")
    for k in NOT_CONNECTED:
        ok = not connected(pin_net, k)
        fails += not ok
        print(f"| (NC) | {k} | {'✅' if ok else '❌ on ' + pin_net[k]} |")

    print(f"\n**Result: {'PASS' if not fails else f'FAIL ({fails} problems)'}**")
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
