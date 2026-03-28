#!/usr/bin/env python3
import argparse
import os

from libt2s import CYAN, RED, RESET, T2SFILES_HOME, T2S_ROOT_DIR, get_tapes, parse_t2sfile

def run():
    tapes = get_tapes()
    tapes_by_name = {}
    for md5sum, tape in tapes.items():
        tapes_by_name[(tape['url'], tape['tape'])] = md5sum

    unknowns = []
    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for fname in files:
            t2sfile = os.path.join(root, fname)
            t2s = parse_t2sfile(t2sfile)
            for md5sum, tape in ((t2s.tape_sum, t2s.tape_name), (t2s.tape_sum_2, t2s.tape_name_2)):
                if not md5sum:
                    break
                url = t2s.url
                if md5sum in tapes:
                    exp_url = tapes[md5sum]['url']
                    if url and url != exp_url and url.startswith('https://spectrumcomputing.co.uk/'):
                        unknowns.append((t2sfile, f'{md5sum} {tape} ({RED}{url}{RESET}): expected {exp_url}'))
                else:
                    exp_md5sum = tapes_by_name.get((url, tape))
                    if exp_md5sum:
                        unknowns.append((t2sfile, f'{RED}{md5sum}{RESET} {tape} ({url}): expected {exp_md5sum}'))
                    else:
                        unknowns.append((t2sfile, f'{RED}{md5sum}{RESET} {tape} ({url})'))

    plen = len(T2SFILES_HOME) + 1
    for t2sfile, line in unknowns:
        print(f'{CYAN}{t2sfile[plen:]}{RESET}')
        print(f'  {line}')

parser = argparse.ArgumentParser(
    usage='%(prog)s',
    description="List t2s files that use a tape with an incorrect URL or MD5 sum.",
    add_help=False
)
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run()
