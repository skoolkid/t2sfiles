#!/usr/bin/env python3
import argparse
import hashlib
import os
import shutil
import sqlite3
import sys

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

sys.path.insert(0, f'{T2SFILES_HOME}/tools')
from libt2s import ZXDB

DOWNLOADS_SQL = """
SELECT file_link, file_md5
FROM downloads
WHERE file_link LIKE '/pub/sinclair/%.zip'
OR file_link LIKE '/zxdb/sinclair/entries/%.zip'
"""

def remove_zips(zips, desc, remove):
    print(f'Found {len(zips)} zip archive(s) {desc}:')
    for z in zips:
        print(f'  {z}')
    print()
    remove = remove or input('Remove these zip archives? [Y/n] ')
    if remove in 'Yy':
        for z in zips:
            try:
                os.remove(z)
                print(f'Removed {z}')
            except Exception as e:
                print(f'Failed to remove {z}: {e.args[0]}')
            zdir = z[:-4]
            if os.path.isdir(zdir):
                try:
                    shutil.rmtree(zdir)
                    print(f'Removed {zdir}')
                except Exception as e:
                    print(f'Failed to remove directory {zdir}: {e.args[0]}')

def run(options):
    downloads = {}
    conn = sqlite3.connect(ZXDB)
    for file_link, file_md5 in conn.execute(DOWNLOADS_SQL):
        downloads[file_link[1:]] = file_md5

    cwd = os.path.basename(os.getcwd())
    if cwd == 'worldofspectrum.net':
        root_dir = 'pub/sinclair'
    elif cwd == 'spectrumcomputing.co.uk':
        root_dir = 'zxdb/sinclair/entries'
    else:
        print('Not in worldofspectrum.net or spectrumcomputing.co.uk; aborting')
        sys.exit(1)

    zips_not_in_zxdb = []
    zips_with_mismatched_md5 = []
    for root, subdirs, files in sorted(os.walk(root_dir)):
        for fname in sorted(files):
            if not fname.lower().endswith('.zip'):
                continue
            zipfile = os.path.join(root, fname)
            if zipfile not in downloads:
                zips_not_in_zxdb.append(zipfile)
                continue
            exp_md5 = downloads.get(zipfile)
            if exp_md5:
                with open(zipfile, 'rb') as f:
                    md5 = hashlib.md5(f.read()).hexdigest()
                if md5 != exp_md5:
                    zips_with_mismatched_md5.append(zipfile)

    if zips_not_in_zxdb:
        remove_zips(zips_not_in_zxdb, 'not in ZXDB', options.yes)
    else:
        print('All zip archives in ZXDB')
    print()

    if zips_with_mismatched_md5:
        remove_zips(zips_with_mismatched_md5, 'with mismatched MD5 sums', options.yes)
    else:
        print('No zip archives with mismatched MD5 sums')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options]',
    description="Find tape zip archives that are not in ZXDB, and offer to remove them.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-y', dest='yes', action='store_const', const='y',
                   help="Remove zip archives without prompting.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
