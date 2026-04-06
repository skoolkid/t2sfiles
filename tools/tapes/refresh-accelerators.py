#!/usr/bin/env python3
import argparse
import os
import sys

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

LIBT2S_DIR = f'{T2SFILES_HOME}/tools'
if not os.path.isdir(LIBT2S_DIR):
    sys.stderr.write(f'{LIBT2S_DIR}: directory not found\n')
    sys.exit(1)
sys.path.insert(0, LIBT2S_DIR)

from libt2s import ACCELERATORS

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
