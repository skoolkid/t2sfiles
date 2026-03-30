#!/usr/bin/env python3
import argparse

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def get_parity(data):
    parity = 0
    for b in data:
        parity ^= b
    return parity

def fix_tap(tap):
    i = 0
    block_num = 1
    while i + 1 < len(tap):
        block_len = get_word(tap, i)
        data = tap[i + 2:i + 2 + block_len]
        parity = get_parity(data[:-1])
        if parity != data[-1]:
            print(f'Fixing parity byte in block {block_num}: {data[-1]} -> {parity}')
            tap[i + block_len + 1] = parity
        i += block_len + 2
        block_num += 1

parser = argparse.ArgumentParser(
    usage="%(prog)s TAPFILE OUTFILE",
    description="Fix parity bytes in a TAP file.",
    add_help=False
)
parser.add_argument('tapfile', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.outfile is None:
    parser.exit(2, parser.format_help())
with open(namespace.tapfile, 'rb') as f:
    tap = bytearray(f.read())
fix_tap(tap)
with open(namespace.outfile, 'wb') as f:
    f.write(tap)
