#!/usr/bin/env python3
import os
import shutil
import sys

if len(sys.argv) < 3:
    print("""
Usage: {0} TAPE BLOCK[-BLOCK]...

Copy a tape into subdirectories named tape-start-M/tape-stop-N based on the
block numbers supplied. For example:

  $ {0} tapes/game.tap 1-3 3-5 5-7 7

copies 'tapes/game.tap' to the following subdirectories:

  tapes/tape-stop-3
  tapes/tape-start-3/tape-stop-5
  tapes/tape-start-5/tape-stop-7
  tapes/tape-start-7
""".strip().format(os.path.basename(sys.argv[0])))
    sys.exit(1)

tape = sys.argv[1]
tape_dir = os.path.dirname(tape)
remove_tape = True
for spec in sys.argv[2:]:
    nums = [int(b) for b in spec.split('-')]
    if len(nums) == 2:
        start, stop = nums
    else:
        start, stop = nums[0], None
    if start > 1:
        subdir = f'tape-start-{start}'
    else:
        subdir = ''
    if stop:
        subdir = os.path.join(subdir, f'tape-stop-{stop}')
    if subdir:
        subdir_path = os.path.join(tape_dir, subdir)
        if not os.path.isdir(subdir_path):
            os.makedirs(subdir_path)
        shutil.copy(tape, subdir_path)
        print(f'Copied {tape} to {subdir_path}')
    else:
        remove_tape = False

if remove_tape:
    os.remove(tape)
    print(f'Removed {tape}')
