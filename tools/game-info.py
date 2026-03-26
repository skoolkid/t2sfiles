#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os
import sys

from libt2s import (T2S_ROOT_DIR, SPECTRUM_TAPES, GREEN, CYAN, RESET,
                    get_games, get_skipped_tapes, get_skipped_reason)

def run(iids, options):
    md5sums = defaultdict(list)
    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for t2sfile in files:
            with open(os.path.join(root, t2sfile)) as f:
                for line in f:
                    if line.startswith('--tape-sum'):
                        md5sum = line[11:].rstrip()
                        md5sums[md5sum].append(f'{GREEN}{t2sfile}{RESET}')
                        break

    games = get_games()
    skipped_tapes = get_skipped_tapes()

    for game_iid in iids:
        game_iid = game_iid.rjust(7, '0')
        game = games.get(game_iid)
        if game:
            name = game['name']
            print(f'{game_iid} {name}')
            tape_urls = []
            tzx_index = None
            if 'tapes' not in game:
                print(f'  Game within compilation(s):')
                for c in game['within']:
                    print(f'    {c}')
                continue
            for url, tapes in game['tapes']:
                tape_lines = []
                tape_urls.append((f'  {CYAN}{url}{RESET}', tape_lines))
                if not tapes:
                    tape_lines.append('    NO LOCAL TAPES FOUND')
                    continue
                path = url[:-4].split('/', 2)[-1]
                tape_dir = f'{SPECTRUM_TAPES}/{path}'
                for tape_spec in tapes:
                    md5sum, tape = tape_spec.split(' ', 1)
                    if md5sum in md5sums:
                        t2sfiles = ', '.join(md5sums[md5sum])
                        t2s = True
                    else:
                        t2sfiles = 'no t2s file'
                        reason = get_skipped_reason(skipped_tapes, game_iid, game['machines'])
                        if reason:
                            t2sfiles += f' - {reason}'
                        t2s = False
                    if options.t2s and not t2s:
                        continue
                    tape_lines.append((tape, [f'  - {md5sum} {tape} ({t2sfiles})']))
                    tape_path = f'{tape_dir}/{tape}'
                    if os.path.isfile(tape_path):
                        tape_lines[-1][1].append(f'    {tape_path}')
                    else:
                        tape_lines[-1][1].append('    TAPE NOT FOUND')
                    if tzx_index is None and tape.lower().endswith('.tzx'):
                        tzx_index = (len(tape_urls) - 1, len(tape_lines) - 1)
            if options.first_tape:
                if tzx_index is None:
                    tzx_index = (0, 0)
                tape_url = tape_urls[tzx_index[0]]
                if tape_url[1]:
                    tape_urls = [(tape_url[0], [tape_url[1][tzx_index[1]]])]
                else:
                    tape_urls = ()
            for url, tape_lines in tape_urls:
                if options.t2s and not tape_lines:
                    continue
                print(url)
                for tape, lines in tape_lines:
                    for line in lines:
                        try:
                            print(line)
                        except UnicodeEncodeError:
                            print('  - Tape unprintable')
            print()

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] INFOSEEKID [INFOSEEKID...]',
    description="List info and tapes for games.",
    add_help=False
)
parser.add_argument('iids', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('-1', dest='first_tape', action='store_true',
                   help="Limit output to the first TZX file, or the first TAP file if there is no TZX.")
group.add_argument('-t', dest='t2s', action='store_true',
                   help="Limit output to tapes already used in t2s files.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.iids:
    parser.exit(2, parser.format_help())
run(namespace.iids, namespace)
