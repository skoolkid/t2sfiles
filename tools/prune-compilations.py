#!/usr/bin/env python3
import argparse
import json

from libt2s import COMPILATIONS_JSON, get_games

def run(options):
    with open(COMPILATIONS_JSON) as f:
        compilations = json.load(f)
    games = get_games(False)

    count = 0
    for zxdb_id in list(compilations):
        if zxdb_id in games:
            compilation = games[zxdb_id]
            if 'contents' in compilation:
                name = compilation['name']
                print(f'- {zxdb_id} {name}')
                count += 1
                if not options.dry_run:
                    del compilations[zxdb_id]

    if count:
        if not options.dry_run:
            with open(COMPILATIONS_JSON, 'w') as f:
                json.dump(compilations, f, sort_keys=True, indent=4)
                f.write('\n')
            print(f'Wrote {COMPILATIONS_JSON} ({len(compilations)} compilations)')
    else:
        print('No compilations removed')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options]',
    description="Remove entries from compilations.json that already have contents in games.json.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-n', dest='dry_run', action='store_true',
                   help="Print entries that would be removed (without removing them).")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
