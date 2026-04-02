#!/usr/bin/env python3
import argparse
import os

from libt2s import ACCELERATORS, T2SFILES_HOME

def run(options):
    req_accs = set(options.accs.split(',')) if options.accs else None
    with open(ACCELERATORS) as f:
        for line in f:
            t2s, info = [e.strip() for e in line.split(':', 1)]
            accelerators = []
            for e in info.split(';'):
                if not e.startswith('none'):
                    name, count = e.strip().split(':')
                    if name == 'misses':
                        misses = int(count)
                    elif name == 'dec-a':
                        dec_a_jr, dec_a_jp, dec_a_misses = [int(c) for c in count.split('/')]
                    else:
                        accelerators.append((name, int(count)))
            if accelerators:
                acc = '; '.join(f'{a}: {h}' for a, h in accelerators)
                acc_len = len(accelerators)
            else:
                acc = 'none'
                acc_len = 0
                accelerators.append((acc, 0))
            if misses < options.miss_threshold:
                continue
            if options.acc_num >= 0 and acc_len != options.acc_num:
                continue
            hits_min = min(h for a, h in accelerators)
            if options.hit_max > 0 and hits_min > options.hit_max:
                continue
            if options.acc_min > 0 and acc_len < options.acc_min:
                continue
            if dec_a_jr < options.dec_a_jr_min:
                continue
            if dec_a_jp < options.dec_a_jp_min:
                continue
            if dec_a_misses < options.dec_a_miss_min:
                continue
            if req_accs and not req_accs <= set(a[0] for a in accelerators):
                continue
            if t2s[0].isalpha():
                subdir = t2s[0]
            else:
                subdir = '0'
            accelerator = ''
            config = ''
            t2sfile = f'{T2SFILES_HOME}/t2s/{subdir}/{t2s}'
            if os.path.isfile(t2sfile):
                with open(t2sfile) as f:
                    for line in f:
                        if line.startswith('--sim-load-config accelerator='):
                            accelerator = line.split('=', 1)[1].rstrip()
                            config = f' [accelerator={accelerator}]'
                            break
                dec_a_counts = f'{dec_a_jr}/{dec_a_jp}/{dec_a_misses}'
                if options.path:
                    t2s = t2sfile
                print(f'{t2s} - {acc}; misses: {misses}; dec-a: {dec_a_counts}{config}')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options]',
    description="Display accelerator info.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-a', dest='accs', metavar='ACCS',
                   help="Limit output to tapes that use all of the accelerators in this comma-separated list.")
group.add_argument('-d', dest='dec_a_jr_min', metavar='D', type=int, default=0,
                   help="Limit output to tapes whose 'DEC A; JR NZ,$-1' hit count is at least equal to D.")
group.add_argument('-D', dest='dec_a_jp_min', metavar='D', type=int, default=0,
                   help="Limit output to tapes whose 'DEC A; JP NZ,$-1' hit count is at least equal to D.")
group.add_argument('-e', dest='dec_a_miss_min', metavar='E', type=int, default=0,
                   help="Limit output to tapes whose 'DEC A' miss count is at least equal to E.")
group.add_argument('-h', dest='hit_max', metavar='H', type=int, default=0,
                   help="Limit output to tapes with a hit count no greater than H for at least one accelerator.")
group.add_argument('-m', dest='miss_threshold', metavar='M', type=int, default=0,
                   help="Limit output to tapes whose miss count is at least equal to M.")
group.add_argument('-n', dest='acc_num', metavar='N', type=int, default=-1,
                   help="Limit output to tapes that use exactly N accelerators.")
group.add_argument('-N', dest='acc_min', metavar='N', type=int, default=-1,
                   help="Limit output to tapes that use at least N accelerators.")
group.add_argument('-p', dest='path', action='store_true',
                   help="Show the full path to each t2s file.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
