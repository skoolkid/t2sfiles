#!/usr/bin/env python3
import os
import shutil
import sys

if len(sys.argv) < 3:
    print("""
Usage: {} TAPES_DIR NUM

Split a tapes directory into NUM parts named tapes-1, tapes-2 etc. Also create
a script for running gen-snapshots.py on these tapes directories, and a script
to prepare a directory for generating t2s files from the snapshots.
""".strip().format(os.path.basename(sys.argv[0])))
    sys.exit(1)

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

gen_snapshots = os.path.join(T2SFILES_HOME, 'tools/t2s-gen/gen-snapshots.py')
if not os.path.isfile(gen_snapshots):
    print(f'ERROR: {gen_snapshots}: file not found')
    sys.exit(1)

tapes = sys.argv[1]
num = int(sys.argv[2])

if not os.path.isdir(tapes):
    print(f"ERROR: {tapes}: Directory not found")
    sys.exit(1)

parent_dir = os.path.dirname(tapes)
tape_names = os.listdir(tapes)
size = (len(tape_names) + num - 1) // num

if num > 1:
    tdirs = []
    for n in range(num):
        index = n * size
        tnames = tape_names[index:index + size]
        if tnames:
            tdirname = f'tapes-{n + 1}'
            tdir = os.path.join(parent_dir, tdirname)
            os.mkdir(tdir)
            tdirs.append(tdirname)
            for tname in tnames:
                shutil.move(os.path.join(tapes, tname), tdir)
        else:
            break
else:
    tdirs = [tapes]

fname = os.path.join(parent_dir, '1-gen-snapshots.sh')
with open(fname, 'w') as f:
    f.write('#!/usr/bin/env bash\n')
    for tdirname in tdirs:
        f.write(f'{gen_snapshots} {tdirname} &\n')
    f.write('wait\n')
    f.write('echo "Snapshot generation complete"\n')
os.chmod(fname, 0o755)

fname = os.path.join(parent_dir, '2-make-t2s-gen-dir.sh')
with open(fname, 'w') as f:
    f.write('#!/usr/bin/env bash\n')
    f.write('mkdir -p t2s-gen/{snapshots,tapes}\n')
    f.write('mv snapshots/* t2s-gen/snapshots\n')
    for tdirname in tdirs:
        f.write(f'rsync -a {tdirname}/ t2s-gen/tapes\n')
    f.write('[[ -f machine=128 ]] && touch t2s-gen/machine=128\n')
    f.write('[[ -f suffix-128k ]] && touch t2s-gen/suffix-128k\n')
    f.write(f't2sgenutils="{T2SFILES_HOME}/tools/t2s-gen"\n')
    f.write('ln -s ${t2sgenutils}/1-mkt2s.py t2s-gen\n')
    f.write('ln -s ${t2sgenutils}/2-t2s-test.sh t2s-gen\n')
    f.write('ln -s ${t2sgenutils}/3-test-t2s-snapshots.sh t2s-gen\n')
    f.write('ln -s ${t2sgenutils}/4-strip-urls.sh t2s-gen\n')
    f.write('ln -s ${t2sgenutils}/5-copy-t2s-files.sh t2s-gen\n')
    f.write('echo "Now: cd t2s-gen"\n')
os.chmod(fname, 0o755)
