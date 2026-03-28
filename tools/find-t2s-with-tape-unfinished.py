#!/usr/bin/env python3
import os.path
import sys

if len(sys.argv) != 2:
    print("""
Usage: {} tap2sna.log

Find t2s files for which the simulation ends before the tape is finished (i.e.
before the last edge on the tape is detected). 'tap2sna.log' must be a log file
of the output of tap2sna.py loading one or more t2s files.
""".strip().format(os.path.basename(sys.argv[0])))
    sys.exit(1)

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

tape_finished = False
with open(sys.argv[1], 'r') as f:
    for line in f:
        if line.startswith('Writing '):
            if not tape_finished:
                game = os.path.basename(line.rstrip()[8:-4])
                if game[0].isalpha():
                    subdir = game[0]
                else:
                    subdir = '0'
                accelerator = ''
                with open(f'{T2SFILES_HOME}/t2s/{subdir}/{game}.t2s', 'r') as f:
                    for line in f:
                        if line.startswith('--sim-load-config accelerator='):
                            accelerator = line.split('=', 1)[1].rstrip()
                if accelerator:
                    print(f't2s/{subdir}/{game}.t2s accelerator={accelerator}')
                else:
                    print(f't2s/{subdir}/{game}.t2s')
            tape_finished = False
        elif line.startswith('Tape finished'):
            tape_finished = True
