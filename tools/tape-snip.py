#!/usr/bin/env python3
import argparse
import os
import sys

class Tape:
    def __init__(self, blocks, version=None):
        self.blocks = blocks
        self.version = version

class TapeBlock:
    def __init__(self, number, contents):
        self.number = number
        self.contents = contents

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def get_word3(data, index):
    return get_word(data, index) + 65536 * data[index + 2]

def get_dword(data, index):
    return get_word3(data, index) + 16777216 * data[index + 3]

def error(msg):
    sys.stderr.write(f'ERROR: {msg}\n')
    sys.exit(1)

def get_tzx_block(data, start, block_num):
    # https://worldofspectrum.net/features/TZXformat.html
    i = start
    block_id = data[i]
    i += 1
    if block_id == 0x10:
        # Standard speed data block
        length = get_word(data, i + 2)
        i += 4 + length
    elif block_id == 0x11:
        # Turbo speed data block
        length = get_word3(data, i + 15)
        i += 18 + length
    elif block_id == 0x12:
        # Pure tone
        i += 4
    elif block_id == 0x13:
        # Sequence of pulses of various lengths
        num_pulses = data[i]
        i += 1 + 2 * num_pulses
    elif block_id == 0x14:
        # Pure data block
        length = get_word3(data, i + 7)
        i += length + 10
    elif block_id == 0x15:
        # Direct recording block
        num_bytes = get_word3(data, i + 5)
        i += 8 + num_bytes
    elif block_id in (0x16, 0x17, 0x18, 0x19):
        # C64 ROM type data / C64 turbo tape data / CSW / GDB
        i += get_dword(data, i) + 4
    elif block_id == 0x20:
        # Pause (silence) or 'Stop the tape' command
        i += 2
    elif block_id == 0x21:
        # Group start
        length = data[i]
        i += length + 1
    elif block_id == 0x22:
        # Group end
        pass
    elif block_id == 0x23:
        # Jump to block
        i += 2
    elif block_id == 0x24:
        # Loop start
        i += 2
    elif block_id == 0x25:
        # Loop end
        pass
    elif block_id == 0x26:
        # Call sequence
        i += get_word(data, i) * 2 + 2
    elif block_id == 0x27:
        # Return from sequence
        pass
    elif block_id == 0x28:
        # Select block
        i += get_word(data, i) + 2
    elif block_id == 0x2A:
        # Stop the tape if in 48K mode
        i += 4
    elif block_id == 0x2B:
        # Set signal level
        i += 5
    elif block_id == 0x30:
        # Text description
        length = data[i]
        i += length + 1
    elif block_id == 0x31:
        # Message block
        length = data[i + 1]
        i += length + 2
    elif block_id == 0x32:
        # Archive info
        i += get_word(data, i) + 2
    elif block_id == 0x33:
        # Hardware type
        i += data[i] * 3 + 1
    elif block_id == 0x34:
        # Emulation info
        i += 8
    elif block_id == 0x35:
        # Custom info block
        length = get_dword(data, i + 16)
        i += length + 20
    elif block_id == 0x40:
        # Snapshot block
        i += get_word3(data, i + 1) + 4
    elif block_id == 0x5A:
        # "Glue" block
        i += 9
    else:
        error(f'Unknown TZX block ID: 0x{block_id:02X}')
    return i, TapeBlock(block_num, data[start:i])

def parse_tap(tapfile):
    with open(tapfile, 'rb') as f:
        tap = f.read()
    blocks = []
    block_num = 1
    i = 0
    while i + 1 < len(tap):
        block_len = get_word(tap, i)
        blocks.append(TapeBlock(block_num, tap[i:i + 2 + block_len]))
        i += 2 + block_len
        block_num += 1
    return Tape(blocks)

def parse_tzx(tzxfile):
    with open(tzxfile, 'rb') as f:
        tzx = f.read()
    if tzx[:8] != b'ZXTape!\x1a':
        error('Not a TZX file')
    try:
        version = (tzx[8], tzx[9])
    except IndexError:
        error('TZX version number not found')
    blocks = []
    block_num = 1
    i = 10
    while i < len(tzx):
        i, block = get_tzx_block(tzx, i, block_num)
        blocks.append(block)
        block_num += 1
    return Tape(blocks, version)

def run(options, infile, outfile):
    if infile.lower().endswith('.tzx'):
        tape = parse_tzx(infile)
    else:
        tape = parse_tap(infile)
    if options.keep:
        block_nums = [int(i) for i in options.keep.split(',')]
    elif options.cut:
        if '-' in options.cut:
            start, end = [int(i) for i in options.cut.split('-', 1)]
            block_nums = list(range(start, end))
        else:
            block_nums = list(range(int(options.cut), tape.blocks[-1].number + 1))
    else:
        block_nums = [b.number for b in tape.blocks]
    with open(outfile, 'wb') as f:
        if outfile.lower().endswith('.tzx'):
            f.write(b'ZXTape!\x1a')
            f.write(bytes(tape.version))
        while block_nums:
            block_num = block_nums.pop(0)
            for block in tape.blocks:
                if block.number == block_num:
                    f.write(block.contents)
                    break

parser = argparse.ArgumentParser(
    usage='{} [options] INFILE OUTFILE'.format(os.path.basename(sys.argv[0])),
    description="Remove blocks from a TAP or TZX file. INFILE and OUTFILE must be of the same type.",
    add_help=False
)
parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-b', dest='keep', metavar='A[,B,C...]',
                   help="Keep only blocks A, B, C, etc.")
group.add_argument('-c', dest='cut', metavar='START[-END]',
                   help="Cut blocks before START and from END onwards.")
namespace, unknown_args = parser.parse_known_args()
if not namespace.infile or not namespace.outfile or unknown_args:
    parser.exit(2, parser.format_help())
run(namespace, namespace.infile, namespace.outfile)
