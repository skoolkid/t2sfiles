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

def run(t2sdirs):
    to_do = []
    acc_t2s = set()
    with open(ACCELERATORS, 'r') as f:
        for line in f:
            acc_t2s.add(line.split(':')[0])
    for t2sdir in t2sdirs:
        for root, subdirs, files in os.walk(t2sdir):
            for fname in files:
                if fname not in acc_t2s:
                    to_do.append((fname, os.path.join(root, fname)))
    for fname, fpath in sorted(to_do):
        print(fpath)

parser = argparse.ArgumentParser(
    usage='%(prog)s T2S_DIR [T2S_DIR...]',
    description="List t2s files that have no entry in {}.".format(os.path.basename(ACCELERATORS)),
    add_help=False
)
parser.add_argument('t2sdirs', help=argparse.SUPPRESS, nargs='*')
namespace, unknown_args = parser.parse_known_args()
if not namespace.t2sdirs or unknown_args:
    parser.exit(2, parser.format_help())
run(namespace.t2sdirs)
