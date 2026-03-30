#!/usr/bin/env python3
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

from skoolkit import tapinfo

from libt2s import parse_t2sfile, find_tape

def run_tapinfo(t2sfile):
    t2s = parse_t2sfile(t2sfile)
    tape = find_tape(t2s.url, t2s.tape_name, t2s.tape_sum)
    print(f'\n---------- {t2sfile} ----------')
    tapinfo.main([tape])

def run(arg):
    if os.path.isfile(arg) and arg.endswith('.t2s'):
        run_tapinfo(arg)
    elif os.path.isdir(arg):
        for root, subdirs, files in sorted(os.walk(arg)):
            for fname in sorted(files):
                run_tapinfo(os.path.join(root, fname))
    elif os.path.isfile(arg):
        with open(arg, 'r') as f:
            for line in f:
                s_line = line.strip()
                if os.path.isfile(s_line) and s_line.endswith('.t2s'):
                    run_tapinfo(s_line)

if len(sys.argv) >= 2:
    run(sys.argv[1])
else:
    sys.stderr.write("""
Usage: {0} game.t2s
       {0} T2SDIR
       {0} t2sfiles.txt
""".lstrip().format(os.path.basename(sys.argv[0])))
