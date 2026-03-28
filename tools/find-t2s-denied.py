#!/usr/bin/env python3
import argparse
import os
import sys

from libt2s import get_games, get_tapes, parse_t2sfile

def run(t2sdir, options):
    games = get_games()
    tapes = get_tapes()
    for root, subdirs, files in sorted(os.walk(t2sdir)):
        for fname in files:
            t2sfile = os.path.join(root, fname)
            t2s = parse_t2sfile(t2sfile)
            tape = tapes.get(t2s.tape_sum)
            if tape:
                iid = tape['infoseek']
                game = games[iid]
                if game.get('denied') and (not options.sc or (t2s.url and 'spectrumcomputing.co.uk' in t2s.url)):
                    name = game['name']
                    print(f'{t2sfile} ({iid} {name})')
            else:
                print(f'ERROR: {t2sfile}: unknown tape')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] T2S_DIR',
    description="Find t2s files for denied titles in T2S_DIR.",
    add_help=False
)
parser.add_argument('t2sdir', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-s', dest='sc', action='store_true',
                   help=f"Show only those t2s files with spectrumcomputing.co.uk URLs.")
namespace, unknown_args = parser.parse_known_args()
if not namespace.t2sdir or unknown_args:
    parser.exit(2, parser.format_help())
run(namespace.t2sdir, namespace)
