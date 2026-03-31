#!/usr/bin/env python3
import argparse
import os

from libt2s import ACCELERATORS, T2SFILES_HOME

def run(acc_log):
    acc = {}
    with open(ACCELERATORS) as f:
        for line in f:
            t2s, info = line.rstrip().split(' ', 1)
            t2s = t2s[:-1]
            letter = t2s[0] if t2s[0].isalpha() else '0'
            if os.path.isfile(f'{T2SFILES_HOME}/t2s/{letter}/{t2s}'):
                acc[t2s] = info

    with open(acc_log, 'r') as f:
        for line in f:
            if line.startswith('Writing snapshots/'):
                t2s = line.split('/', 1)[-1].strip()[:-4] + '.t2s'
                acc[t2s] = accelerators
            elif line.startswith('Accelerators:'):
                accelerators = line.rstrip()[14:]

    with open(ACCELERATORS, 'w') as f:
        for t2s in sorted(acc):
            f.write(f'{t2s}: {acc[t2s]}\n')

parser = argparse.ArgumentParser(
    usage='%(prog)s tap2sna-full.log',
    description="Extract accelerator info from the full log file produced by tap2sna-t2s.py "
                "run on one or more tapes with '-c accelerator=list' and merge it with "
                "any existing info in {}.".format(os.path.basename(ACCELERATORS)),
    add_help=False
)
parser.add_argument('acc_log', help=argparse.SUPPRESS, nargs='?')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.acc_log is None:
    parser.exit(2, parser.format_help())
run(namespace.acc_log)
