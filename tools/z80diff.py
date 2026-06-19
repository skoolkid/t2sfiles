#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os
import sys

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}: directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.snapshot import Snapshot

T2S_SNAPSHOTS = os.environ.get('T2S_SNAPSHOTS')
if not T2S_SNAPSHOTS:
    sys.stderr.write('T2S_SNAPSHOTS is not set; aborting\n')
    sys.exit(1)
T2S_BIN_DIR = os.path.dirname(T2S_SNAPSHOTS) + '/bin'
if not os.path.isdir(T2S_BIN_DIR):
    sys.stderr.write(f'{T2S_BIN_DIR}: directory not found\n')
    sys.exit(1)

REGISTERS = {
    "A": "a",
    "F": "f",
    "BC": "bc",
    "DE": "de",
    "HL": "hl",
    "IX": "ix",
    "IY": "iy",
    "SP": "sp",
    "I": "i",
    "R": "r",
    "A'": "a2",
    "F'": "f2",
    "BC'": "bc2",
    "DE'": "de2",
    "HL'": "hl2",
    "PC": "pc",
}

STATE = {
    'Border': 'border',
    'Interrupts': 'iff2',
    'Interrupt mode': 'im',
    'T-states': 'tstates'
}

def _compare(s1, s2):
    count = 0
    for a in range(len(s1)):
        if s1[a] and s2[a] == s1[a]:
            count += 1
    return count

def _normalised_levenshtein(s1, s2):
    """
    Return the Normalised Levenshtein Distance (similarity): a number between
    0.0 (totally different) and 1.0 (identical).
    """
    slen = len(s1)
    prev_row = range(slen + 1)
    for i in range(1, slen + 1):
        curr_row = [i] * (slen + 1)
        for j in range(1, slen + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr_row[j] = min(
                curr_row[j - 1] + 1,   # Deletion
                prev_row[j] + 1,       # Insertion
                prev_row[j - 1] + cost # Substitution
            )
        prev_row = curr_row
    distance = prev_row[slen]
    return 1.0 - distance / slen

try:
    from libz80diff import compare, normalised_levenshtein
except ImportError:
    print('WARNING: libz80diff C extension not found; computing NLD will be VERY slow', file=sys.stderr)
    compare = _compare
    normalised_levenshtein = _normalised_levenshtein

def cmp2(z1, z2, nld):
    s1 = Snapshot.get(z1)
    s2 = Snapshot.get(z2)
    snapshot1 = s1.ram(-1)
    snapshot2 = s2.ram(-1)
    header1, reg1 = s1.header, s1
    header2, reg2 = s2.header, s2

    if nld:
        similarity = normalised_levenshtein(bytes(snapshot1), bytes(snapshot2))
    else:
        similarity = None

    reg_diffs = []
    for reg, attr in REGISTERS.items():
        r1 = getattr(reg1, attr)
        r2 = getattr(reg2, attr)
        if r1 != r2:
            reg_diffs.append(f'{reg:>3}: {r1:>5} {r2:>5}')

    state_diffs = []
    for s, attr in STATE.items():
        s1 = getattr(reg1, attr)
        s2 = getattr(reg2, attr)
        if s1 != s2:
            state_diffs.append(f'{s}: {s1} {s2}')

    ram_diffs = []
    if len(snapshot1) == 49152:
        for i in range(49152):
            b1, b2 = snapshot1[i], snapshot2[i]
            if b1 != b2:
                ram_diffs.append(f'{i + 16384}: {b1:>3} {b2:>3}')
    else:
        for bank in range(8):
            addr = 16384 * bank
            for i in range(16384):
                b1, b2 = snapshot1[addr + i], snapshot2[addr + i]
                if b1 != b2:
                    ram_diffs.append(f'Bank {bank}: {i:05}: {b1:>3} {b2:>3}')

    header_diffs = []
    for i in range(35, len(header1)):
        h1, h2 = header1[i], header2[i]
        if h1 != h2:
            header_diffs.append(f'Header {i}: {h1:>3} {h2:>3}')

    for name, diffs in (('Registers', reg_diffs), ('State', state_diffs), ('RAM', ram_diffs), ('Header', header_diffs)):
        print(name)
        if diffs:
            for d in diffs:
                print(f'  {d}')
            if name == 'RAM' and similarity is not None:
                print(f'  Similarity: {similarity:.02f}')
        else:
            print('  No differences')

def cpall(z80s, limit, nld):
    snapshots = [(z80, bytearray(Snapshot.get(z80).ram(-1))) for z80 in z80s]
    cps = defaultdict(list)
    for f in os.listdir(T2S_BIN_DIR):
        if not f.endswith('.bin'):
            continue
        with open(f'{T2S_BIN_DIR}/{f}', 'rb') as b:
            z = b.read()
        for z80, snapshot in snapshots:
            if len(snapshot) == len(z):
                cps[z80].append((compare(z, snapshot), snapshot, f))
    for z80, cp in cps.items():
        results = sorted(cp)
        if limit > 0:
            results = results[-limit:]
        print(z80)
        for n, s1, f in results:
            if nld:
                with open(f'{T2S_BIN_DIR}/{f}', 'rb') as b:
                    s2 = b.read()
                similarity = normalised_levenshtein(s1, s2)
                print(f'  {n:>6} {similarity:.02f} {f}')
            else:
                print(f'  {n:>6} {f}')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] snap1.z80 [snap2.z80 ...]',
    description="Compare Z80 snapshots.",
    add_help=False
)
parser.add_argument('snaps', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('-a', dest='cpall', action='store_true',
                   help="Compare with all t2s raw binary files, and sort by number of matching non-zero bytes.")
group.add_argument('-l', dest='limit', metavar='LIMIT', type=int, default=5,
                   help="Show not more than this many of the most similar snapshots (default: 5).")
group.add_argument('-n', dest='nld', action='store_true',
                   help="Compute and display normalised Levenshtein distance.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.snaps:
    parser.exit(2, parser.format_help())
if namespace.cpall:
    cpall(namespace.snaps, namespace.limit, namespace.nld)
elif len(namespace.snaps) == 2:
    cmp2(*namespace.snaps, namespace.nld)
else:
    parser.exit(2, parser.format_help())
