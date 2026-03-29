#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os

def get_lines(fname, line_nos):
    if line_nos:
        with open(fname) as f:
            return set(f.readlines())
    lines = set()
    with open(fname) as f:
        for line in f:
            elements = line.split(None, 1)
            if len(elements) == 2:
                lines.add(elements[1])
    return lines

def run(basic, basicdir, options):
    b = get_lines(basic, options.line_nos)
    matching_lines = defaultdict(list)
    for f in os.listdir(basicdir):
        if f.endswith('.basic'):
            b2 = get_lines(os.path.join(basicdir, f), options.line_nos)
            matching_lines[len(b.intersection(b2))].append(f)
    for n in sorted(matching_lines):
        for m in matching_lines[n]:
            print(f'{n:>5} {m}')

parser = argparse.ArgumentParser(
    usage='%(prog)s game.basic BASICDIR',
    description="Compare game.basic with all the BASIC listings in BASICDIR.",
    add_help=False
)
parser.add_argument('basic', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('basicdir', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-n', dest='line_nos', action='store_false',
                   help="Compare without line numbers.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.basicdir is None:
    parser.exit(2, parser.format_help())
run(namespace.basic, namespace.basicdir, namespace)
