#!/usr/bin/env python3
import argparse
import sys

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def get_word3(data, index):
    return get_word(data, index) + 65536 * data[index + 2]

def get_dword(data, index):
    return get_word3(data, index) + 16777216 * data[index + 3]

def _get_parity(data):
    parity = 0
    for b in data:
        parity ^= b
    return parity

def _print_block(index, data, info=(), block_id=None, header=None):
    if block_id is None:
        print(f"{index}:")
    else:
        print(f"{index}: {header} (0x{block_id:02X})")
    for line in info:
        print(line)
    if data and block_id in (None, 16):
        data_type = "Unknown"
        name_str = None
        line = 0xC000
        start = None
        if len(data) == 19 and data[0] == 0:
            block_type = data[1]
            if block_type == 0:
                name_str = 'Program'
                line = get_word(data, 14)
            elif block_type == 1:
                name_str = 'Number array'
            elif block_type == 2:
                name_str = 'Character array'
            elif block_type == 3:
                name_str = 'Bytes'
                size = get_word(data, 12)
                start = get_word(data, 14)
            if name_str:
                data_type = "Header block"
                name = ''.join(chr(b) for b in data[2:12])
        elif data[0] == 255:
            data_type = "Data block"
        print(f"Type: {data_type}")
        if name_str:
            print(f"{name_str}: {name}")
        if line < 0x8000:
            print(f'LINE: {line}')
        if start is not None:
            print(f"CODE: {start},{size}")
    if data:
        print(f"Length: {len(data)}")

def _get_block_info(data, i, block_num):
    # https://worldofspectrum.net/features/TZXformat.html
    block_id = data[i]
    info = []
    tape_data = []
    i += 1
    if block_id == 16:
        header = 'Standard speed data'
        info.append('Pause: {}ms'.format(get_word(data, i)))
        length = get_word(data, i + 2)
        tape_data = data[i + 4:i + 4 + length]
        i += 4 + length
    elif block_id == 17:
        header = 'Turbo speed data'
        info.append('Pilot pulse: {}'.format(get_word(data, i)))
        info.append('Sync pulse 1: {}'.format(get_word(data, i + 2)))
        info.append('Sync pulse 2: {}'.format(get_word(data, i + 4)))
        info.append('0-pulse: {}'.format(get_word(data, i + 6)))
        info.append('1-pulse: {}'.format(get_word(data, i + 8)))
        info.append('Pilot length: {} pulses'.format(get_word(data, i + 10)))
        info.append('Used bits in last byte: {}'.format(data[i + 12]))
        info.append('Pause: {}ms'.format(get_word(data, i + 13)))
        length = get_word3(data, i + 15)
        tape_data = data[i + 18:i + 18 + length]
        i += 18 + length
    elif block_id == 18:
        header = 'Pure tone'
        info.append('Pulse length: {} T-states'.format(get_word(data, i)))
        info.append('Pulses: {}'.format(get_word(data, i + 2)))
        i += 4
    elif block_id == 19:
        header = 'Pulse sequence'
        num_pulses = data[i]
        i += 1
        for pulse in range(num_pulses):
            info.append('Pulse {}/{}: {}'.format(pulse + 1, num_pulses, get_word(data, i)))
            i += 2
    elif block_id == 20:
        header = 'Pure data'
        info.append('0-pulse: {}'.format(get_word(data, i)))
        info.append('1-pulse: {}'.format(get_word(data, i + 2)))
        info.append('Used bits in last byte: {}'.format(data[i + 4]))
        info.append('Pause: {}ms'.format(get_word(data, i + 5)))
        length = get_word3(data, i + 7)
        tape_data = data[i + 10:i + 10 + length]
        i += length + 10
    elif block_id == 21:
        header = 'Direct recording'
        i += get_word3(data, i + 5) + 8
    elif block_id == 24:
        header = 'CSW recording'
        i += get_dword(data, i) + 4
    elif block_id == 25:
        header = 'Generalized data'
        i += get_dword(data, i) + 4
    elif block_id == 32:
        duration = get_word(data, i)
        if duration:
            header = "Pause (silence)"
            info.append('Duration: {}ms'.format(duration))
        else:
            header = "'Stop the tape' command"
        i += 2
    elif block_id == 33:
        header = 'Group start'
        length = data[i]
        i += length + 1
    elif block_id == 34:
        header = 'Group end'
    elif block_id == 35:
        header = 'Jump to block'
        offset = get_word(data, i)
        if offset > 32767:
            offset -= 65536
        info.append('Destination block: {}'.format(block_num + offset))
        i += 2
    elif block_id == 36:
        header = 'Loop start'
        info.append('Repetitions: {}'.format(get_word(data, i)))
        i += 2
    elif block_id == 37:
        header = 'Loop end'
    elif block_id == 38:
        header = 'Call sequence'
        i += get_word(data, i) * 2 + 2
    elif block_id == 39:
        header = 'Return from sequence'
    elif block_id == 40:
        header = 'Select block'
        index = i + 3
        for j in range(data[i + 2]):
            offset = get_word(data, index)
            length = data[index + 2]
            index += length + 3
        i += get_word(data, i) + 2
    elif block_id == 42:
        header = 'Stop the tape if in 48K mode'
        i += 4
    elif block_id == 43:
        header = 'Set signal level'
        i += 5
    elif block_id == 48:
        header = 'Text description'
        length = data[i]
        i += length + 1
    elif block_id == 49:
        header = 'Message'
        length = data[i + 1]
        i += length + 2
    elif block_id == 50:
        header = 'Archive info'
        num_strings = data[i + 2]
        j = i + 3
        for k in range(num_strings):
            try:
                str_len = data[j + 1]
            except IndexError:
                raise SkoolKitError('Unexpected end of file')
            j += 2 + str_len
        i += get_word(data, i) + 2
    elif block_id == 51:
        header = 'Hardware type'
        i += 1 + 3 * data[i]
    elif block_id == 53:
        header = 'Custom info'
        length = get_dword(data, i + 16)
        i += length + 20
    elif block_id == 90:
        header = '"Glue" block'
        i += 9
    else:
        print('Unknown block ID: 0x{:02X}'.format(block_id), file=sys.stderr)
        sys.exit(1)
    return i, block_id, header, info, tape_data

def _edit_tzx(tzx, block, options):
    if tzx[:8] != bytearray((90, 88, 84, 97, 112, 101, 33, 26)):
        print("Not a TZX file", file=sys.stderr)
        sys.exit(1)
    if len(tzx) < 10:
        print('TZX version number not found', file=sys.stderr)
        sys.exit(1)
    if block == 0:
        tzx[offset] = value
        return
    block_num = 1
    i = 10
    while i < len(tzx):
        if block == block_num:
            if options.set_value:
                tzx[i + 1 + options.set_value[0]] = options.set_value[1]
        i, block_id, header, info, tape_data = _get_block_info(tzx, i, block_num)
        if block == block_num:
            if block_id in (0x10, 0x11, 0x14):
                if options.flag is not None:
                    tzx[i - len(tape_data)] = tape_data[0] = options.flag
                if options.fix_parity:
                    tzx[i - 1] = tape_data[-1] = _get_parity(tape_data[:-1])
            _print_block(block_num, tape_data, info, block_id, header)
            break
        block_num += 1

def _edit_tap(tap, block, options):
    i = 0
    block_num = 1
    while i + 1 < len(tap):
        block_len = get_word(tap, i)
        if block == block_num:
            if options.set_value:
                tap[i + options.set_value[0]] = options.set_value[1]
            if options.flag is not None:
                tap[i + 2] = options.flag
            data = tap[i + 2:i + 2 + block_len]
            if options.fix_parity:
                tap[i + 1 + block_len] = data[-1] = _get_parity(data[:-1])
            _print_block(block_num, data)
            break
        i += block_len + 2
        block_num += 1

parser = argparse.ArgumentParser(
    usage="%(prog)s [options] TAPEFILE BLOCK OUTFILE",
    description="Change the value of a byte in a tape block. "
                "BLOCK 0 of a TZX file is the header block.",
    add_help=False
)
parser.add_argument('tapefile', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('block', help=argparse.SUPPRESS, nargs='?', type=int)
parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-f', dest='flag', type=int,
                   help="Set the flag byte.")
group.add_argument('-p', dest='fix_parity', action='store_true',
                   help="Fix the parity byte.")
group.add_argument('-s', dest='set_value', metavar='OFFSET,VALUE',
                   help="Set the value at the given 0-based offset. For TZX files the offset is relative to the byte that follows the block ID.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.outfile is None:
    parser.exit(2, parser.format_help())
if namespace.set_value is not None:
    namespace.set_value = [int(s) for s in namespace.set_value.split(',', 1)]
tape_type = namespace.tapefile[-4:].lower()
if tape_type not in ('.tap', '.tzx'):
    print('Unrecognised tape type', file=sys.stderr)
    sys.exit(1)
with open(namespace.tapefile, 'rb') as f:
    tape = bytearray(f.read())
if tape_type == '.tap':
    _edit_tap(tape, namespace.block, namespace)
else:
    _edit_tzx(tape, namespace.block, namespace)
with open(namespace.outfile, 'wb') as f:
    f.write(tape)
