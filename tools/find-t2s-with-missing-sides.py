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
        if t.endswith(('-side-1', '-side-a', '-side-2', '-side-b', '-side-3', '-side-c', '-side-4', '-side-d')):
            if t[-1] in '1a':
                other = t[:-1] + ('2' if t[-1] == '1' else 'b')
            else:
                other = t[:-1] + ('1' if t[-1] in '234' else 'a')
            other_t2s = f'{other}.t2s'
            if other_t2s not in t2sfiles:
                print(f'{t2s}: no {other_t2s}')

parser = argparse.ArgumentParser(
    usage='%(prog)s',
    description="List t2s files that may have missing sides.",
    add_help=False
)
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run()
