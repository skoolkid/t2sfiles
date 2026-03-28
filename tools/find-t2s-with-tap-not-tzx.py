#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os

from libt2s import T2SFILES_HOME, T2S_ROOT_DIR, get_tapes

def get_tzxs(tapes):
    tzxs = defaultdict(list)
    for md5sum, tape in tapes.items():
        tape_name = tape['tape']
        if tape_name.lower().endswith('.tzx'):
            tzxs[tape['infoseek']].append((md5sum, tape_name, tape['url']))
    return tzxs

def parse_t2sfile(t2sfile):
    tape_sum, tape_name, url = None, None, None
    with open(t2sfile) as f:
        for line in f:
            if line.startswith('http'):
                url = line.strip()
            elif line.startswith('--tape-name'):
                tape_name = line[11:].strip()
                if tape_name.startswith('"'):
                    tape_name = tape_name[1:-1]
                tape_name = os.path.basename(tape_name)
            elif line.startswith('--tape-sum'):
                tape_sum = line[10:].strip()
    return tape_sum, tape_name, url

def run():
    tapes = get_tapes()
    tzxs = get_tzxs(tapes)
    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for fname in files:
            t2sfile = os.path.join(root, fname)
            md5sum, tape_name, url = parse_t2sfile(t2sfile)
            if tape_name.lower().endswith('.tap') and md5sum in tapes:
                tape = tapes[md5sum]
                infoseek_id = tape['infoseek']
                if infoseek_id in tzxs:
                    t2s = t2sfile[len(T2SFILES_HOME) + 1:]
                    game = tape['game']
                    print(f'{t2s} ({game})')
                    print(f'  Actual: {md5sum} {tape_name} ({url})')
                    p = 'TZXs:'
                    for tzx_md5, tzx_name, tzx_url in tzxs[infoseek_id]:
                        print(f'    {p:>5} {tzx_md5} {tzx_name} ({tzx_url})')
                        p = ''

parser = argparse.ArgumentParser(
    usage='%(prog)s',
    description="List t2s files that use a TAP file where a TZX file is available.",
    add_help=False
)
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run()
