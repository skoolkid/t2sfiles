#!/usr/bin/env python3
import argparse
from collections import defaultdict
import hashlib
import os
import sys

from libt2s import TAPES_TXT, REASONS, get_tapes, get_games

def run(arg, reason, machine, force):
    games = get_games()
    tapes = get_tapes()
    if os.path.isfile(arg):
        with open(arg, 'rb') as f:
            tape_sum = hashlib.md5(f.read()).hexdigest()
        if tape_sum not in tapes:
            sys.stderr.write(f'ERROR: "{tape}" ({tape_sum}) not recognised\n')
            sys.exit(1)
        zxdb_id = tapes[tape_sum]['infoseek']
    elif len(arg) == 32:
        if arg not in tapes:
            sys.stderr.write(f'ERROR: {arg} not recognised\n')
            sys.exit(1)
        zxdb_id = tapes[arg]['infoseek']
    else:
        zxdb_id = arg.rjust(7, '0')

    name = games[zxdb_id]['name']
    existing_tapes = defaultdict(dict)
    with open(TAPES_TXT) as f:
        for line in f:
            iid, g_reason, g_machine, g_name = line.strip().split(None, 3)
            existing_tapes[iid][g_machine] = (g_reason, g_name)
    if zxdb_id in existing_tapes:
        if not force:
            sys.stderr.write(f'{zxdb_id} ({name}) already in {os.path.basename(TAPES_TXT)}; use -f to force\n')
            sys.exit(1)
        print(f'Removing existing entry for {zxdb_id} ({name}) from {os.path.basename(TAPES_TXT)}')
    existing_tapes[zxdb_id][machine] = (reason, name)
    if set(existing_tapes[zxdb_id]) == {'48K', '128K', '*'}:
        del existing_tapes[zxdb_id]['*']
    with open(TAPES_TXT, 'w') as f:
        for iid in sorted(existing_tapes):
            for g_machine, (g_reason, g_name) in existing_tapes[iid].items():
                f.write(f'{iid} {g_reason} {g_machine:<4} {g_name}\n')
    print(f'Added to {os.path.basename(TAPES_TXT)}: {zxdb_id} {reason} {machine:<4} {name}')

reasons = '|'.join(REASONS)
reason_descs = '\n'.join(f'    {k}: {v}' for k, v in REASONS.items())
parser = argparse.ArgumentParser(
    usage=f'%(prog)s [options] ZXDB_ID|TAPE_FILE|TAPE_SUM {reasons} [48K|128K]',
    description=f"Add an entry to tapes.txt for one of the following reasons:\n\n{reason_descs}",
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False
)
parser.add_argument('id', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('reason', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('machine', help=argparse.SUPPRESS, nargs='?', default='*')
group = parser.add_argument_group('Options')
group.add_argument('-f', dest='force', action='store_true',
                   help="Replace any existing entry for the same title/tape.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.reason not in REASONS or namespace.machine not in ('*', '48K', '128K'):
    parser.exit(2, parser.format_help())
run(namespace.id, namespace.reason, namespace.machine, namespace.force)
