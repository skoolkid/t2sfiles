#!/usr/bin/env python3
from contextlib import redirect_stdout
import hashlib
import io
import os
import re
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

def log_msg(log_file, msg):
    with open(log_file, 'a') as f:
        f.write(msg + '\n')
    sys.stderr.write(msg + '\n')

def run(root_dir):
    while root_dir.endswith('/'):
        root_dir = root_dir[:-1]
    scount = 0
    default_options = ('-c', 'accelerator=list')
    if os.path.isfile('machine=128'):
        default_options += ('-c', 'machine=128')
    tdir = os.path.basename(root_dir)
    error_log = f'errors-{tdir}.log'
    warning_log = f'warnings-{tdir}.log'

    for root, subdirs, files in sorted(os.walk(root_dir)):
        for f in sorted(files):
            if not f.lower().endswith(('.tzx', '.tap')):
                continue
            options = list(default_options)
            if '/no-fast-load' in root:
                options.extend(('-c', 'fast-load=0'))
            if '/no-pause' in root:
                options.extend(('-c', 'pause=0'))
            if '/first-edge' in root:
                options.extend(('-c', 'first-edge=0'))
            m = re.search('/tape-start-([0-9]+)', root)
            if m:
                options.extend(('--tape-start', m.group(1)))
            m = re.search('/tape-stop-([0-9]+)', root)
            if m:
                options.extend(('--tape-stop', m.group(1)))
            if '/other' in root:
                options_file = os.path.join(root, f[:-4] + '.txt')
                if os.path.isfile(options_file):
                    with open(options_file) as options_f:
                        for line in options_f:
                            options.extend(line.strip().split(' ', 1))
                            if options[-1].startswith("'"):
                                options[-1] = options[-1][1:-1]
                else:
                    log_msg(error_log, f'ERROR: {options_file}: file not found')
                    continue
            tape = os.path.join(root, f)
            z80file = os.path.join('snapshots', root[len(root_dir) + 1:], f + '.z80')
            if os.path.isfile(z80file):
                print(f'*** Found {z80file}')
            else:
                print(f'*** Generating {z80file}')
                start = time.time()
                try:
                    with redirect_stdout(io.StringIO()) as output:
                        tap2sna.main((*options, tape, z80file))
                    log = output.getvalue()
                except Exception as e:
                    log_msg(error_log, f'ERROR: Failed to sim-load {tape}: {e.args[0]}')
                    continue

                elapsed = time.time() - start
                if elapsed > 60:
                    log_msg(warning_log, f'WARNING: {tape} took {elapsed:.03f}s to sim-load')

                if '(timed out)' in log:
                    log_msg(warning_log, f'WARNING: {tape} timed out')

                logfile = z80file[:-4] + '.log'
                with open(logfile, 'w') as logf:
                    logf.write(log)

            with open(z80file, 'rb') as zf:
                z80data = zf.read()
            checksum = hashlib.md5(z80data).hexdigest()
            name = ''
            for c in f:
                if c.isalnum():
                    name += c.lower()
                else:
                    name += '_'
            scount += 1

    print(f'\nGenerated {scount} snapshots')

if len(sys.argv) == 2:
    run(sys.argv[1])
else:
    sys.stderr.write('Usage: {} TAPES_DIR\n'.format(os.path.basename(sys.argv[0])))
