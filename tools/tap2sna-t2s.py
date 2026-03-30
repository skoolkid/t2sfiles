#!/usr/bin/env python3
import contextlib
import io
import os
import sys
import time

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import tap2sna

from libt2s import parse_t2sfile, find_tape, get_tapes

SNAPSHOTS = 'snapshots'

def error(msg):
    with open('tap2sna-errors.log', 'a') as f:
        f.write(msg + '\n')
    sys.stderr.write(msg + '\n')

def log(msg):
    with open('tap2sna.log', 'a') as f:
        f.write(msg + '\n')

def full_log(msg):
    with open('tap2sna-full.log', 'a') as f:
        f.write(msg + '\n')

def run_tap2sna(t2sfile, tapes_by_md5, extra_options):
    t2s = parse_t2sfile(t2sfile)
    if t2s.url is None:
        try:
            t2s.url = tapes_by_md5[t2s.tape_sum]['url']
        except Exception as e:
            error(f'ERROR: Could not determine URL for {t2sfile}: {e.args[0]}')
            return
    if t2s.snapshot is None:
        sna_fmt = 'szx' if 'DefaultSnapshotFormat=szx' in t2s.options else 'z80'
        t2s.snapshot = os.path.basename(t2sfile)[:-4] + f'.{sna_fmt}'
    tapes = [find_tape(t2s.url, t2s.tape_name)]
    if t2s.tape_name_2:
        tapes.append(find_tape(t2s.url, t2s.tape_name_2))
    start = time.time()
    try:
        with contextlib.redirect_stdout(io.StringIO()) as tap2sna_out:
            tap2sna.main((*t2s.options, *extra_options, *tapes, f'{SNAPSHOTS}/{t2s.snapshot}'))
    except (Exception, SystemExit) as e:
        tape_names = ' '.join(tapes)
        error(f'ERROR: Failed to LOAD {t2sfile} ({tape_names}): {e.args[0]}')
        return
    elapsed = time.time() - start
    msg = f'{elapsed:6.2f}s - {os.path.basename(t2sfile)}'
    log(msg)
    print(msg)
    full_log(tap2sna_out.getvalue())

def run(arg, extra_options):
    tapes_by_md5 = get_tapes()
    if not os.path.isdir(SNAPSHOTS):
        os.makedirs(SNAPSHOTS)
    if os.path.isfile(arg) and arg.endswith('.t2s'):
        run_tap2sna(arg, tapes_by_md5, extra_options)
    elif os.path.isdir(arg):
        for root, subdirs, files in sorted(os.walk(arg)):
            for fname in sorted(files):
                run_tap2sna(os.path.join(root, fname), tapes_by_md5, extra_options)
    elif os.path.isfile(arg):
        with open(arg, 'r') as f:
            for line in f:
                s_line = line.strip()
                if os.path.isfile(s_line) and s_line.endswith('.t2s'):
                    run_tap2sna(s_line, tapes_by_md5, extra_options)

if len(sys.argv) >= 2:
    run(sys.argv[1], sys.argv[2:])
else:
    sys.stderr.write("""
Usage: {0} game.t2s [options]
       {0} T2SDIR [options]
       {0} t2sfiles.txt [options]
""".lstrip().format(os.path.basename(sys.argv[0])))
