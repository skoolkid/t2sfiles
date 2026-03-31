#!/usr/bin/env python3
import argparse
import hashlib
import os
import sys

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

LIBT2S_DIR = f'{T2SFILES_HOME}/tools'
if not os.path.isdir(LIBT2S_DIR):
    sys.stderr.write(f'{LIBT2S_DIR}: directory not found\n')
    sys.exit(1)
sys.path.insert(0, LIBT2S_DIR)

from libt2s import SPECTRUM_TAPES, get_tape_sums, get_tapes

def run(options):
    tapes = get_tapes()
    md5sums = get_tape_sums()
    tapinfo = f'{SPECTRUM_TAPES}/tapinfo'
    results = {}
    for root, subdirs, files in sorted(os.walk(tapinfo)):
        for fname in sorted(files):
            if not fname.lower().endswith('.tzx.txt'):
                continue
            tapinfo_file = os.path.join(root, fname)
            tape_file = tapinfo_file.replace(tapinfo, SPECTRUM_TAPES)[:-4]
            if not os.path.isfile(tape_file):
                print(f'WARNING: {tape_file}: file not found', file=sys.stderr)
                continue
            md5 = md5sums.get(tape_file)
            if not md5:
                with open(tape_file, 'rb') as f:
                    md5 = hashlib.md5(f.read()).hexdigest()
            if md5 not in tapes:
                continue
            tape = tapes[md5]
            game = tape['game']
            iid = tape['infoseek']
            pause_no = 0
            with open(tapinfo_file) as f:
                for line in f:
                    if options.pause and line.startswith('  Pause:'):
                        pause_no += 1
                        if pause_no == options.pause[0]:
                            ms = int(line.rstrip()[9:-2])
                            if options.pause[1] <= ms <= options.pause[2]:
                                results[md5] = {
                                    'tape': tape_file,
                                    'iid': iid,
                                    'game': game,
                                    'info': [f'Pause: {ms}ms']
                                }
                            break
    for tape in results.values():
        print(tape['tape'])
        print('  {} {} [https://spectrumcomputing.co.uk/entry/{}]'.format(tape['iid'], tape['game'], tape['iid'].lstrip('0')))
        for s in tape['info']:
            print(f'  {s}')

parser = argparse.ArgumentParser(
    usage='%(prog)s option [arg]',
    description="Find TZX files with specified properties.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('--pause', metavar='N-A-B',
                   help='Find TZX files whose Nth pause is between A and B milliseconds (inclusive).')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or len(sys.argv) < 2:
    parser.exit(2, parser.format_help())
if namespace.pause:
    namespace.pause = tuple(int(i) for i in namespace.pause.split('-', 2))

run(namespace)
