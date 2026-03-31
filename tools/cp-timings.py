#!/usr/bin/env python3
import os
import sys

def read_times(fname):
    entries = []
    with open(fname, 'r') as f:
        for line in f:
            elements = line.split('-', 1)
            t = float(elements[0].strip()[:-1])
            n = elements[1].strip()
            entries.append((t, n))
    return entries

if len(sys.argv) != 3:
    print("""
Usage: {} timings-before.log timings-after.log

Compare timings in log files produced by tap2sna-t2s.py.
""".strip().format(os.path.basename(sys.argv[0])))
    sys.exit(1)

before = read_times(sys.argv[1])
after = read_times(sys.argv[2])

total_t1 = total_t2 = 0
for i, (t1, n1) in enumerate(before):
    t2, n2 = after[i]
    total_t1 += t1
    total_t2 += t2
    if n1 != n2:
        sys.stderr.write(f'Broken: {n1} != {n2}\n')
    d = t2 - t1
    p = (d * 100) / t1
    print(f'{d:+6.2f}s : {p:+6.2f}% : {n1}')

print('-----------------')
total_d = total_t2 - total_t1
total_p = (total_d * 100) / total_t1
print(f'{total_d:+6.2f}s : {total_p:+6.2f}%')
