#!/usr/bin/env python3
import argparse
import os
import sys

from libt2s import get_games, get_tapes, parse_t2sfile

MSG = [
    '; This title is distribution denied.',
    '; A local copy of the zip archive is required to use this t2s file.',
    ''
]

def run(t2sfiles, options):
    games = get_games()
    tapes = get_tapes()
    for t2sfile in t2sfiles:
        t2s = parse_t2sfile(t2sfile)
        if t2s.tape_sum not in tapes:
            print(f'{t2sfile}: Unrecognised tape - skipping')
            continue
        if not games[tapes[t2s.tape_sum]['infoseek']]['denied'] and not options.force:
            print(f'{t2sfile}: Not a denied title - skipping')
            continue
        lines = []
        modify = False
        with open(t2sfile, 'r') as f:
            for line in f:
                s_line = line.rstrip()
                if s_line.startswith('http'):
                    modify = True
                    lines.append(os.path.basename(s_line))
                else:
                    lines.append(s_line)
        if not options.no_msg and lines[0:2] != MSG:
            lines = MSG + lines
        if options.print:
            for line in lines:
                print(line)
        elif modify:
            with open(t2sfile, 'w') as f:
                for line in lines:
                    f.write(line + '\n')
            print(f'{t2sfile}: Stripped URL')
        else:
            print(f'{t2sfile}: Already stripped')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] T2SFILE [T2SFILE...]',
    description="Strip the URL in a t2s file for a denied title of everything except the zip archive name.",
    add_help=False
)
parser.add_argument('t2sfiles', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('-f', dest='force', action='store_true',
                   help="Proceed even if the tape is not distribution denied.")
group.add_argument('-n', dest='no_msg', action='store_true',
                   help="Don't include a message about distribution being denied.")
group.add_argument('-p', dest='print', action='store_true',
                   help="Print the result to stdout instead of modifying the t2s file.")
namespace, unknown_args = parser.parse_known_args()
if not namespace.t2sfiles or unknown_args:
    parser.exit(2, parser.format_help())
run(namespace.t2sfiles, namespace)
