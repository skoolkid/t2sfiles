#!/usr/bin/env python3
import os
import shutil
import sys

if len(sys.argv) < 3:
    print("""
Usage: {0} TAPE OPTION [OPTION...]

Move a tape into a subdirectory named 'other' along with a text file containing
the options specified. For example:

  $ {0} tapes/game.tap "--sim-load-config fast-load=0"

moves 'tapes/game.tap' to 'tapes/other/game.tap' and creates the text file
'tapes/other/game.txt' containing the line '--sim-load-config fast-load=0'.
""".strip().format(os.path.basename(sys.argv[0])))
    sys.exit(1)

tape = sys.argv[1]
tape_dir = os.path.dirname(tape)
subdir = f'{tape_dir}/other'
if not os.path.isdir(subdir):
    os.makedirs(subdir)
with open(f'{subdir}/{os.path.basename(tape)[:-4]}.txt', 'w') as f:
    for option in sys.argv[2:]:
        f.write(option + '\n')
shutil.move(tape, subdir)
print(f'Moved {tape} to {subdir}')
