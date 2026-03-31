#!/usr/bin/env python3
import argparse
import os
import sys

from libt2s import RED, GREEN, RESET, TAPES_TXT, get_games, get_tapes

def read_skipped_tapes():
    skipped_tapes = {}
    with open(TAPES_TXT) as f:
        for line in f:
            zxdb_id, reason, machine, name = line.strip().split(None, 3)
            skipped_tapes.setdefault(zxdb_id, {})[machine] = (reason, name)
    return skipped_tapes

def write_skipped_tapes(skipped_tapes):
    with open(TAPES_TXT, 'w') as f:
        for zxdb_id in sorted(skipped_tapes):
            if set(skipped_tapes[zxdb_id]) == {'48K', '128K', '*'}:
                del skipped_tapes[zxdb_id]['*']
            for machine, (reason, name) in skipped_tapes[zxdb_id].items():
                f.write(f'{zxdb_id} {reason} {machine:<4} {name}\n')
    print(f'Wrote {TAPES_TXT}')

def run(t2s_dir, options):
    games = get_games()
    tapes = get_tapes()
    skipped_tapes = read_skipped_tapes()

    for root, subdirs, files in sorted(os.walk(t2s_dir)):
        for t in sorted(files):
            t2s = os.path.join(root, t)
            tape_sum, machine = None, '48K'
            with open(t2s) as f:
                for line in f:
                    if line.startswith('--tape-sum'):
                        tape_sum = line[11:].rstrip()
                    elif line.startswith('--sim-load-config machine=128'):
                        machine = '128K'
            if tape_sum not in tapes:
                print(f'WARNING: {t2s}: Unrecognised tape', file=sys.stderr)
                continue
            zxdb_id = tapes[tape_sum]['infoseek']
            reasons = skipped_tapes.get(zxdb_id)
            if reasons:
                machines = games[zxdb_id]['machines']
                if options.machines and options.machines != machines:
                    continue
                if machines == '48K/128K':
                    key = machine
                    reason, name = reasons.get(key, (None, None))
                    if reason is None:
                        key = '*'
                        reason, name = reasons.get(key, (None, None))
                    if reason:
                        if key == machine:
                            if options.dry_run:
                                print(f'{t2s}:')
                                print(f'{RED}- {zxdb_id} {reason} {machine:<4} {name}{RESET}')
                            del reasons[machine]
                        else:
                            other = {'48K': '128K', '128K': '48K'}[machine]
                            if options.dry_run:
                                print(f'{t2s}:')
                                print(f'{RED}- {zxdb_id} {reason} *    {name}{RESET}')
                                print(f'{GREEN}+ {zxdb_id} {reason} {other:<4} {name}{RESET}')
                            del reasons['*']
                            reasons[other] = (reason, name)
                else:
                    if options.dry_run:
                        print(f'{t2s}:')
                        for machine, (reason, name) in reasons.items():
                            print(f'{RED}- {zxdb_id} {reason} {machine:<4} {name}{RESET}')
                    del skipped_tapes[zxdb_id]

    if not options.dry_run:
        write_skipped_tapes(skipped_tapes)

parser = argparse.ArgumentParser(
    usage='{} [options] T2S_DIR'.format(os.path.basename(sys.argv[0])),
    description="Remove entries from tapes.txt for which there are t2s files in T2S_DIR.",
    add_help=False
)
parser.add_argument('t2s_dir', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-m', dest='machines', metavar='MACHINES',
                   help="Only consider titles for MACHINES (48K, 128K, or 48K/128K).")
group.add_argument('-n', dest='dry_run', action='store_true',
                   help="Print entries that would be removed/added (without removing/adding them).")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.t2s_dir:
    parser.exit(2, parser.format_help())
run(namespace.t2s_dir, namespace)
