#!/usr/bin/env python3
import argparse
import contextlib
import hashlib
import io
import json
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

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)
sys.path.insert(1, f'{T2SFILES_HOME}/tools')

SPECTRUM_TAPES = os.environ.get('SPECTRUM_TAPES')
if not SPECTRUM_TAPES:
    sys.stderr.write('SPECTRUM_TAPES is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SPECTRUM_TAPES):
    sys.stderr.write(f'SPECTRUM_TAPES={SPECTRUM_TAPES}; directory not found\n')
    sys.exit(1)

from skoolkit import tap2sna
from skoolkit.snapshot import Snapshot
from libt2s import get_tapes

HEADER = r"""
#!/usr/bin/env python3
import gc
import hashlib
import os
import sys
import tempfile
import unittest

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import tap2sna
from skoolkit.snapshot import Snapshot

TMP = tempfile.gettempdir()

class SimLoadTest(unittest.TestCase):
    def _test_sim_load(self, tapes, fname, reg, options):
        outfile = f'{TMP}/{fname}'
        tap2sna.main((*options, *tapes, outfile))
        r = Snapshot.get(outfile)
        ram = r.ram(-1)
        md5sum = hashlib.md5(bytes(ram)).hexdigest()
        rvals = {
            "AF,BC,DE,HL": f'{r.a:02X}{r.f:02X},{r.bc:04X},{r.de:04X},{r.hl:04X}',
            "AF',BC',DE',HL'": f'{r.a2:02X}{r.f2:02X},{r.bc2:04X},{r.de2:04X},{r.hl2:04X}',
            "PC,SP,IX,IY": f'{r.pc:04X},{r.sp:04X},{r.ix:04X},{r.iy:04X}',
            "IR,iff,im,border": f'{r.i:02X}{r.r:02X},{r.iff2},{r.im},{r.border}',
            "ram": md5sum
        }
        self.assertEqual(reg, rvals)
""".lstrip()

TEST = """
    def test_{name}(self):
        self._test_sim_load(
            {tapes},
            {fname},
            {reg},
            {options}
        )
"""

FOOTER = r"""
if __name__ == '__main__':
    import nose2
    from skoolkit import CSimulator
    if {c} and CSimulator is None:
        print('CSimulator not found. Run the following command and try again:\n\n  make -C $SKOOLKIT_HOME cmods')
        sys.exit(1)
    sys.argv.extend(('--plugin=nose2.plugins.mp', '-N', '{processes}', '-B'))
    nose2.main()
"""

TEST_FNAME = 'test_t2sfiles.py'

TEST_C_FNAME = 'test_t2sfiles_c.py'

SNAPSHOTS_JSON = 'snapshots.json'

def error(msg):
    full_msg = f'ERROR: {msg}\n'
    with open('errors.log', 'a') as f:
        f.write(full_msg)
    sys.stderr.write(full_msg)

def find_tape(tapes_by_md5, tape_sum, t2sfile):
    tape = tapes_by_md5.get(tape_sum)
    if tape:
        url = tape['url']
        tape_name = tape['tape']
        tapefile = f'{SPECTRUM_TAPES}/{url[8:-4]}/{tape_name}'
        if os.path.isfile(tapefile):
            return tapefile
        error(f'{t2sfile}: {tapefile} not found')
    else:
        error(f'{t2sfile}: tape with sum {tape_sum} not found')

def write_snapshots_json(snapshots):
    with open(SNAPSHOTS_JSON, 'w') as f:
        f.write(json.dumps(snapshots, sort_keys=True, indent=4))

def run(root_dir, accelerators, gen_options):
    tapes_by_md5 = get_tapes()
    try:
        with open(SNAPSHOTS_JSON) as f:
            snapshots = json.load(f)
        snapshots_json_tstamp = os.stat(SNAPSHOTS_JSON).st_mtime
    except:
        snapshots = {}
        snapshots_json_tstamp = 0
    stale_count = 0
    for snapshot in list(snapshots.keys()):
        if not os.path.isfile(snapshot):
            stale_count += 1
            del snapshots[snapshot]
    if stale_count:
        write_snapshots_json(snapshots)
        print(f'Pruned {stale_count} snapshot(s) from {SNAPSHOTS_JSON}\n')

    new_count = 0
    tests = []
    t2s_r_time = 0
    snapshot_r_time = 0
    snapshot_w_time = 0
    total_time_start = time.time()
    gap = False

    for root, subdirs, files in sorted(os.walk(root_dir)):
        for fname in sorted(files):
            t2sfile = os.path.join(root, fname)
            t2s_options, t2s_accelerator, sna_fmt, tape_sums = [], None, 'z80', []
            t2s_r_time_start = time.time()
            with open(t2sfile) as f:
                for line in f:
                    s_line = line.strip()
                    if s_line.startswith('--tape-name'):
                        continue
                    if s_line.startswith('--tape-sum'):
                        tape_sums.append(s_line[10:].lstrip())
                    elif line.startswith('--'):
                        if 'accelerator=' in s_line:
                            t2s_accelerator = s_line.split()[1].split('=')[1]
                            continue
                        if s_line.startswith("--sim-load-config 'load="):
                            t2s_options.extend(('--sim-load-config', s_line[19:-1]))
                            continue
                        if s_line.startswith("--press '"):
                            t2s_options.extend(('--press', s_line[9:-1]))
                            continue
                        if s_line == '--ini DefaultSnapshotFormat=szx':
                            sna_fmt = 'szx'
                            continue
                        if ';' in s_line:
                            t2s_options.extend(s_line[:s_line.index(';')].rstrip().split())
                        else:
                            t2s_options.extend(s_line.split())
            tapes = [find_tape(tapes_by_md5, tape_sum, fname) for tape_sum in tape_sums]
            if not all(tapes):
                continue
            outfile = f'{fname[:-4]}.{sna_fmt}'
            t2s_r_time += time.time() - t2s_r_time_start
            for accelerator in accelerators:
                options = t2s_options[:]
                if accelerator:
                    options.extend(('--sim-load-config', f'accelerator={accelerator}'))
                elif t2s_accelerator:
                    options.extend(('--sim-load-config', f'accelerator={t2s_accelerator}'))
                if not gen_options.c:
                    options.extend(('--sim-load-config', 'python=1'))
                suffix = f'__{accelerator}' if accelerator else ''
                snapshot = os.path.join('snapshots', outfile)
                write_snapshot = False
                if not os.path.isfile(snapshot):
                    write_snapshot = True
                elif snapshot in snapshots:
                    if ' '.join(tape_sums) != snapshots[snapshot]['md5']:
                        write_snapshot = True
                    elif t2s_options != snapshots[snapshot]['options']:
                        write_snapshot = True
                if write_snapshot:
                    msg = f'LOADING - {fname} ({snapshot})'
                    msg += chr(8) * len(msg)
                    print(msg, end='', flush=True)
                    start = time.time()
                    try:
                        with contextlib.redirect_stdout(io.StringIO()) as tap2sna_out:
                            tap2sna.main((*options, *tapes, snapshot))
                    except Exception as e:
                        error(f'Failed to LOAD {fname}: {e.args[0]}')
                        continue
                    elapsed = time.time() - start
                    print(f'{elapsed:6.2f}s - {fname} ({snapshot})')
                    if '(timed out)' in tap2sna_out.getvalue():
                        error(f'{fname} timed out')
                        os.remove(snapshot)
                        continue
                    snapshot_w_time += elapsed
                    gap = True
                z80file_tstamp = os.stat(snapshot).st_mtime
                update = False
                if snapshot not in snapshots:
                    update = True
                elif z80file_tstamp > snapshots_json_tstamp:
                    update = True
                if update:
                    snapshot_r_time_start = time.time()
                    r = Snapshot.get(snapshot)
                    ram = r.ram(-1)
                    ramsum = hashlib.md5(bytes(ram)).hexdigest()
                    reg = {
                        "AF,BC,DE,HL": f'{r.a:02X}{r.f:02X},{r.bc:04X},{r.de:04X},{r.hl:04X}',
                        "AF',BC',DE',HL'": f'{r.a2:02X}{r.f2:02X},{r.bc2:04X},{r.de2:04X},{r.hl2:04X}',
                        "PC,SP,IX,IY": f'{r.pc:04X},{r.sp:04X},{r.ix:04X},{r.iy:04X}',
                        "IR,iff,im,border": f'{r.i:02X}{r.r:02X},{r.iff2},{r.im},{r.border}',
                        "ram": ramsum
                    }
                    snapshots[snapshot] = {
                        'md5': ' '.join(tape_sums),
                        'options': t2s_options,
                        'state': reg,
                    }
                    snapshot_r_time += time.time() - snapshot_r_time_start
                    new_count += 1
                    gap = True
                else:
                    reg = snapshots[snapshot]['state']
                name = ''.join(c.lower() if c.isalnum() else '_' for c in snapshot) + suffix
                if accelerator:
                    test_outfile = f'{outfile[:-4]}--{accelerator}.{sna_fmt}'
                else:
                    test_outfile = outfile
                tests.append({
                    'name': name,
                    'tapes': repr(tuple(tapes)),
                    'fname': repr(test_outfile),
                    'reg': repr(reg),
                    'options': repr(tuple(options))
                })

    if gap:
        print()
    if new_count:
        write_snapshots_json(snapshots)
        print(f'Added {new_count} snapshot(s) to {SNAPSHOTS_JSON}')
    else:
        print(f'{SNAPSHOTS_JSON} is up-to-date')
    print()

    if tests:
        test_fname = TEST_C_FNAME if gen_options.c else TEST_FNAME
        with open(test_fname, 'w') as f:
            f.write(HEADER)
            if gen_options.gc:
                f.write('        gc.collect()\n')
            for test in tests:
                f.write(TEST.format(**test))
            f.write(FOOTER.format(c=gen_options.c, processes=gen_options.processes))
        os.chmod(test_fname, 0o755)
        print(f'Wrote {test_fname} ({len(tests)} tests)')

    total_time = time.time() - total_time_start
    print(f'\nt2s read time: {t2s_r_time:.2f}s')
    print(f'Snapshot read time: {snapshot_r_time:.2f}s')
    print(f'Snapshot write time: {snapshot_w_time:.2f}s')
    print(f'Total time: {total_time:.2f}s')

    if tests:
        print(f'\nNow run ./{test_fname}')

DESCRIPTION = """
Generate tests for all the t2s files in T2S_DIR and its subdirectories, along
with a script to run them. If ACCELERATOR is given, it overrides any
accelerator specified in each t2s file.

Each reference snapshot required to generate the tests must exist in a
subdirectory named 'snapshots'. Any reference snapshot that doesn't already
exist will be generated. A reference snapshot is one expected from the
unmodified t2s file.

Snapshot metadata is cached in a file named 'snapshots.json'. Any out-of-date
metadata it contains is automatically updated by this script.
""".strip()

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] T2S_DIR [ACCELERATOR [ACCELERATOR...]]',
    description=DESCRIPTION,
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False
)
parser.add_argument('t2s_dir', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('accelerators', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('-c', action='store_true',
                   help="Generate tests for tap2sna.py using CSimulator.")
group.add_argument('-g', dest='gc', action='store_true',
                   help="Collect garbage after each test. This can help prevent OOM errors when running the tests on low-RAM systems.")
group.add_argument('-j', dest='processes', metavar='PROCS', type=int, default=0,
                   help="Run tests using this many processes.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.t2s_dir:
    parser.exit(2, parser.format_help())
accelerators = namespace.accelerators or ['']
run(namespace.t2s_dir, accelerators, namespace)
