#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os

DEFAULT_MIN_THRESHOLD = 99
DEFAULT_MAX_THRESHOLD = 100

def run(z80diff, min_pc, max_pc):
    diffs = defaultdict(list)
    with open(z80diff) as f:
        for line in f:
            s_line = line.strip()
            if s_line.endswith('.z80'):
                snapshot = os.path.basename(s_line)[:-4]
            else:
                elements = s_line.split()
                diffs[snapshot].append((int(elements[0]), elements[1][:-4]))
    s_min = min_pc / 100
    s_max = max_pc / 100
    for snapshot, counts in diffs.items():
        ref_count = counts[-1][0]
        matches = []
        for count, b in counts:
            if b != snapshot:
                similarity = count / ref_count
                if s_min <= similarity <= s_max:
                    matches.append((b, similarity * 100))
        if matches:
            print(snapshot)
            for b, similarity in matches:
                print(f'  {b} ({similarity:0.1f}%)')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] z80diff.txt',
    description="Analyse the output of 'z80diff.py -a'.",
    add_help=False
)
parser.add_argument('z80diff', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-m', dest='min_pc', metavar='MIN', type=int, default=DEFAULT_MIN_THRESHOLD,
                   help=f"Find snapshots above this similarity percentage threshold (default: {DEFAULT_MIN_THRESHOLD}).")
group.add_argument('-M', dest='max_pc', metavar='MAX', type=int, default=DEFAULT_MAX_THRESHOLD,
                   help=f"Find snapshots below this similarity percentage threshold (default: {DEFAULT_MAX_THRESHOLD}).")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.z80diff:
    parser.exit(2, parser.format_help())
run(namespace.z80diff, namespace.min_pc, namespace.max_pc)
