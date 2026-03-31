#!/usr/bin/env python3
from collections import defaultdict
import hashlib
import os
import re
import sqlite3
import sys
import unicodedata

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import snapinfo, snapshot, trace

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

LIBT2S_DIR = f'{T2SFILES_HOME}/tools'
if not os.path.isdir(LIBT2S_DIR):
    sys.stderr.write(f'{LIBT2S_DIR}: directory not found\n')
    sys.exit(1)
sys.path.insert(0, LIBT2S_DIR)

from libt2s import (RED, GREEN, RESET, get_games, get_tapes, get_t2s_names,
                    get_t2s_name_iids, query_t2s_names)

T2S = """
{url}
--tape-name "{tape_name}"
--tape-sum {md5sum}
--start {pc}
""".lstrip()

ACC_NONE = '--sim-load-config accelerator=none'

def to_ascii(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.combining(c) == 0)

def run(root_dir):
    games = get_games()
    tapes = get_tapes()
    t2s_names = get_t2s_names()
    t2s_name_iids = get_t2s_name_iids(t2s_names)
    suffix_128k = os.path.isfile('suffix-128k')
    if os.path.isfile('machine=128'):
        default_options = ['--sim-load-config machine=128']
    else:
        default_options = []

    for root, subdirs, files in sorted(os.walk(root_dir)):
        for t in sorted(files):
            if not t.lower().endswith(('.tzx', '.tap')):
                continue
            options = default_options[:]
            if '/no-fast-load' in root:
                options.append('--sim-load-config fast-load=0')
            if '/no-pause' in root:
                options.append('--sim-load-config pause=0')
            if '/first-edge' in root:
                options.append('--sim-load-config first-edge=0')
            m = re.search('/tape-start-([0-9]+)', root)
            if m:
                options.append(f'--tape-start {m.group(1)}')
            m = re.search('/tape-stop-([0-9]+)', root)
            if m:
                options.append(f'--tape-stop {m.group(1)}')
            if '/other' in root:
                options_file = os.path.join(root, t[:-4] + '.txt')
                with open(options_file) as options_f:
                    for line in options_f:
                        options.append(line.strip())
            z80file = os.path.join('snapshots', root[len(root_dir) + 1:], t + '.z80')
            logfile = z80file[:-4] + '.log'
            acc_none, stop_condition = False, 'unknown'
            with open(logfile) as logf:
                for line in logf:
                    if line.startswith('Simulation stopped'):
                        stop_condition = line[20:line.index(')')]
                    elif line.startswith('Accelerators: none'):
                        misses = int(line.split()[3][:-1])
                        if misses and stop_condition == 'end of tape':
                            # Custom loader, but no accelerator identified
                            acc_none = True
            if acc_none:
                options.append(ACC_NONE)
            tape = os.path.join(root, t)
            with open(tape, 'rb') as f:
                tape_data = f.read()
            md5sum = hashlib.md5(tape_data).hexdigest()
            pc = snapshot.Snapshot.get(z80file).pc

            print('----------------------------------------------------------')
            try:
                snapinfo.main(('-b', z80file))
            except:
                print('ERROR: Failed to produce BASIC listing')
            print('----------------------------------------------------------')
            trace.main(('-v', '--max-operations', '500', z80file))

            if md5sum in tapes:
                tape_info = tapes[md5sum]
                url = tape_info['url']
                if "'" in url:
                    url = f'"{url}"'
                tape_name = tape_info['tape']
                iid = tape_info['infoseek']
                game_info = games[iid]
                game_name = game_info['name']
                t2s_name = t2s_names[iid][0]
                num_games = len(t2s_name_iids[t2s_name])
                if num_games == 1:
                    def_name = t2s_name
                    count = '1 of 1'
                else:
                    def_name = f'{t2s_name}-{iid}'
                    count = f'{RED}**********1 of {num_games}**********{RESET}'
                print(f'Game: {game_name} ({t2s_name}: {count})')
                authors = game_info['authors']
                publishers = game_info['publishers']
                genre = game_info['genre']
                print(f'  ZXDB ID: {iid}')
                print(f'  Authors: {authors}')
                print(f'  Publishers: {publishers}')
                print(f'  Genre: {genre}')
                print('  Tapes:')
                for tape_url, tape_files in game_info['tapes']:
                    print(f'    {tape_url}')
                    for tape_spec in tape_files:
                        m = tape_spec.split(' ', 1)[0]
                        prefix = GREEN if m == md5sum else ''
                        try:
                            print(f'      {prefix}{tape_spec}{RESET}')
                        except UnicodeEncodeError:
                            print(f'      ???????')
                print(f'{GREEN}{tape}{RESET}:')
                print(f'  PC={pc} ({stop_condition})')
                option_strs = []
                for option in options:
                    if option == ACC_NONE:
                        option = f'{RED}{ACC_NONE}{RESET}'
                    option_strs.append(option)
                print('  options: {}'.format(' '.join(option_strs)))
                print(f'  MD5={md5sum}')
                print(f'  URL={url}')
            else:
                print(f'Skipping unknown tape "{t}"')
                done_tape = tape.replace('tapes/', 'tapes-unknown/')
                done_tape_dir = os.path.dirname(done_tape)
                if not os.path.isdir(done_tape_dir):
                    os.makedirs(done_tape_dir)
                os.rename(tape, done_tape)
                print(f'Moved {tape} -> {done_tape}\n')
                continue

            new_pc = input('PC (decimal; hex prefixed by $; ! for SA/LD-RET; ? for 23316): ')
            if new_pc:
                if new_pc.startswith('!'):
                    pc = 0x053f # SA/LD-RET
                    options.append('--sim-load-config finish-tape=1')
                elif new_pc.startswith('?'):
                    pc = 23316
                    options.append('--sim-load-config finish-tape=1')
                elif new_pc[0] == '$':
                    pc = int(new_pc[1:], 16)
                else:
                    pc = int(new_pc)

            extra_options = input('Extra options (separate with ;): ')
            if extra_options:
                options.extend(extra_options.split(';'))

            while True:
                name = input(f'Name ({def_name}) ([?name/+suffix/skip/trace]): ')
                if name.startswith('?'):
                    print()
                    qname = name[1:]
                    entries = query_t2s_names(qname, t2s_name_iids, games)
                    contents_iids = [c[:7] for c in game_info.get('contents', ())]
                    print(f'{qname}: {len(entries)} title(s) found')
                    for line in entries:
                        n_iid = line[:7]
                        prefix = GREEN if n_iid in contents_iids else ''
                        print(f'  {prefix}{line}{RESET}')
                    print()
                    continue
                if not name:
                    name = def_name
                if name == 'skip':
                    dest_dir = 'tapes-skipped'
                elif name == 'trace':
                    dest_dir = 'tapes-to-trace'
                else:
                    if name.startswith('+'):
                        name = def_name + '-' + to_ascii(name[1:])
                    name = name.replace(' ', '-').lower()
                    if suffix_128k and '-128k' not in name:
                        name += '-128k'
                    letter = name[0]
                    if not letter.isalpha():
                        letter = '0'
                    t2sdir = f't2s/{letter}'
                    t2sfile = f'{t2sdir}/{name}.t2s'
                    if not os.path.isdir(t2sdir):
                        os.makedirs(t2sdir)
                    with open(t2sfile, 'w') as f:
                        f.write(T2S.format(url=url, tape_name=tape_name, md5sum=md5sum, pc=pc))
                        for option in options:
                            f.write(option + '\n')
                    dest_dir = 'tapes-done'
                break
            done_tape = tape.replace('tapes/', f'{dest_dir}/')
            done_tape_dir = os.path.dirname(done_tape)
            if not os.path.isdir(done_tape_dir):
                os.makedirs(done_tape_dir)
            os.rename(tape, done_tape)
            print(f'Moved {tape} -> {done_tape}\n')

run('tapes')
