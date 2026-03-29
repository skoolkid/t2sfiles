#!/usr/bin/env python3
import argparse
import os
import sys

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

T2S_DIR = f'{T2SFILES_HOME}/t2s'

def run(root_dir):
    snapshots = []
    for root, subdirs, files in sorted(os.walk(root_dir)):
        for fname in sorted(files):
            letter = fname[0] if fname[0].isalpha() else '0'
            t2sfile = f'{T2S_DIR}/{letter}/{fname[:-4]}.t2s'
            if not os.path.isfile(t2sfile):
                snapshots.append(os.path.join(root, fname))

    if snapshots:
        print('Unused snapshots:')
        for s in snapshots:
            print(f'  {s}')
        print()

        remove = input('Remove these snapshots? [Y/n] ')
        if remove in 'Yy':
            for s in snapshots:
                try:
                    os.remove(s)
                    print(f'Removed {s}')
                except Exception as e:
                    print(f'Failed to remove {s}: {e.args[0]}')
    else:
        print('No unused snapshots')

parser = argparse.ArgumentParser(
    usage='%(prog)s [DIR]'.format(os.path.basename(sys.argv[0])),
    description="Remove unused snapshots or raw binary files from DIR. If not given, DIR defaults to 'snapshots'.",
    add_help=False
)
group = parser.add_argument_group('Options')
parser.add_argument('directory', help=argparse.SUPPRESS, nargs='?', default='snapshots')
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace.directory)
