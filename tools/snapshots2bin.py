#!/usr/bin/env python3
import argparse
import os
import sys

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.snapshot import Snapshot

def run(snapsdir, bindir, options):
    for b in os.listdir(bindir):
        if b.endswith('.bin') and not os.path.isfile(f'{snapsdir}/{b[:-4]}.z80'):
            binfile = f'{bindir}/{b}'
            print(f'Removing {binfile}')
            os.remove(binfile)
    for z in os.listdir(snapsdir):
        if z.endswith('.z80'):
            binfile = f'{bindir}/{z[:-4]}.bin'
            if not os.path.isfile(binfile) or options.force:
                print(f'Writing {binfile}')
                data = Snapshot.get(f'{snapsdir}/{z}').ram(-1)
                with open(binfile, 'wb') as f:
                    f.write(bytes(data))

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] SNAPSHOTS_DIR BIN_DIR',
    description="Create raw binary files in BIN_DIR from Z80 snapshots in SNAPSHOTS_DIR.",
    add_help=False
)
parser.add_argument('snapsdir', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('bindir', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-f', dest='force', action='store_true',
                   help="Overwrite existing raw binary files.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.bindir is None:
    parser.exit(2, parser.format_help())
run(namespace.snapsdir, namespace.bindir, namespace)
