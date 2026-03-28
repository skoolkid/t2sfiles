#!/usr/bin/env python3
import argparse
import os
import sys

from libt2s import T2S_ROOT_DIR

def run():
    t2sfiles = []
    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for t in files:
            t2sfiles.append(t)

    for t2s in sorted(t2sfiles):
        t = t2s[:-4]
        if t.endswith(('-p1', '-p2', '-p3', '-p4')):
            if t[-1] == '1':
                other = t[:-1] + '2'
            else:
                other = t[:-1] + '1'
            other_t2s = f'{other}.t2s'
            if other_t2s not in t2sfiles:
                print(f'{t2s}: no {other_t2s}')

parser = argparse.ArgumentParser(
    usage='%(prog)s',
    description="List t2s files that may have missing parts.",
    add_help=False
)
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run()
