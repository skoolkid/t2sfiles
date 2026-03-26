#!/usr/bin/env python3
import argparse
import hashlib
import os
import sys

from libt2s import GREEN, RESET, SPECTRUM_TAPES, get_games, get_tapes, parse_t2sfile

def run(infile):
    if infile.endswith('.t2s'):
        md5sum = parse_t2sfile(infile).tape_sum
    else:
        with open(infile, 'rb') as f:
            md5sum = hashlib.md5(f.read()).hexdigest()
    games = get_games()
    tape = get_tapes().get(md5sum)
    if tape is None:
        print('Tape not recognised', file=sys.stderr)
        sys.exit(1)
    game_iid = tape['infoseek']
    game = games[game_iid]
    name = game['name']
    print(f'{game_iid} {name}')
    tape_urls = []
    for url, tapes in game['tapes']:
        tape_lines = []
        tape_urls.append((f'  {url}', tape_lines))
        if not tapes:
            tape_lines.append('    NO LOCAL TAPES FOUND')
            continue
        path = url[:-4].split('/', 2)[-1]
        tape_dir = f'{SPECTRUM_TAPES}/{path}'
        for tape_spec in tapes:
            tape_md5sum, tape_name = tape_spec.split(' ', 1)
            prefix = GREEN if tape_md5sum == md5sum else ''
            tape_lines.append((tape_name, [f'  {prefix}- {tape_name}{RESET}']))
            tape_path = f'{tape_dir}/{tape_name}'
            if os.path.isfile(tape_path):
                tape_lines[-1][1].append(f'    {prefix}{tape_path}{RESET}')
            else:
                tape_lines[-1][1].append('    TAPE NOT FOUND')
    for url, tape_lines in tape_urls:
        print(url)
        for tape, lines in tape_lines:
            for line in lines:
                try:
                    print(line)
                except UnicodeEncodeError:
                    print('  - Tape unprintable')

parser = argparse.ArgumentParser(
    usage='%(prog)s TAPEFILE|T2SFILE',
    description="Show info on a given tape/t2s file and other tape files for the same title.",
    add_help=False
)
parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.infile:
    parser.exit(2, parser.format_help())
run(namespace.infile)
