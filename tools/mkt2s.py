#!/usr/bin/env python3
import os
import sys
import unicodedata

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

from libt2s import RED, RESET, get_games, get_tapes, get_t2s_names, get_t2s_name_iids

T2S = """
{url}
--tape-name "{tape_names[0]}"
--tape-sum {md5sums[0]}
""".lstrip()

T2S_RS2 = """
{url}
--tape-name "{tape_names[0]}"
--tape-sum {md5sums[0]}
--tape-name "{tape_names[1]}"
--tape-sum {md5sums[1]}
""".lstrip()

def to_ascii(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.combining(c) == 0)

def run(iid):
    games = get_games()
    tapes = get_tapes()
    t2s_names = get_t2s_names()
    t2s_name_iids = get_t2s_name_iids(t2s_names)

    game_info = games[iid]
    game_name = game_info['name']
    t2s_name = t2s_names[iid][0]
    num_games = len(t2s_name_iids[t2s_name])
    if num_games == 1:
        count = '1 of 1'
    else:
        count = f'{RED}**********1 of {num_games}**********{RESET}'
    print(f'Game: {game_name} ({t2s_name}: {count})')
    authors = game_info['authors']
    publishers = game_info['publishers']
    genre = game_info['genre']
    machines = game_info['machines']
    print(f'  Authors: {authors}')
    print(f'  Publishers: {publishers}')
    print(f'  Genre: {genre}')
    print(f'  Machines: {machines}')
    print('  Tapes:')
    game_tapes = []
    if 'tapes' in game_info:
        game_tapes = game_info['tapes']
    elif 'within' in game_info:
        for ct in game_info['within']:
            c_iid, c_name = ct.split(' ', 1)
            if c_iid in games:
                game_tapes.extend(games[c_iid].get('tapes', ()))
    if not game_tapes:
        print(f'    NO TAPES AVAILABLE')
        sys.exit(1)
    tape_specs = {}
    index = 1
    for tape_url, tape_files in game_tapes:
        print(f'    {tape_url}')
        for tape_spec in tape_files:
            md5sum, fname = tape_spec.split(' ', 1)
            tape_specs[index] = (tape_url, fname, md5sum)
            try:
                print(f'      [{index}] {tape_spec}')
            except UnicodeEncodeError:
                print(f'      ???????')
            index += 1
    print()

    while True:
        numbers = input('Enter up to two tape numbers: ')
        chosen_tapes = [int(n) for n in numbers.split()]
        if len(chosen_tapes) > 2 or not set(chosen_tapes) <= set(tape_specs):
            continue
        break

    def_name = t2s_name
    name = input(f'Name ({def_name}) ([+suffix]): ')
    if name.startswith('+'):
        name = def_name + '-' + to_ascii(name[1:])
    elif not name:
        name = def_name
    name = name.replace(' ', '-').lower()
    t2sfile = f'{name}.t2s'
    url = tape_specs[chosen_tapes[0]][0]
    tape_names = [tape_specs[ct][1] for ct in chosen_tapes]
    md5sums = [tape_specs[ct][2] for ct in chosen_tapes]
    template = T2S if len(chosen_tapes) == 1 else T2S_RS2

    with open(t2sfile, 'w') as f:
        f.write(template.format(url=url, tape_names=tape_names, md5sums=md5sums))
        if machines == '128K':
            f.write('--sim-load-config machine=128\n')
    print(f'Wrote {t2sfile}')

    if machines == '48K/128K':
        t2sfile = t2sfile[:-4] + '-128k.t2s'
        with open(t2sfile, 'w') as f:
            f.write(template.format(url=url, tape_names=tape_names, md5sums=md5sums))
            f.write('--sim-load-config machine=128\n')
        print(f'Wrote {t2sfile}')

if len(sys.argv) < 2:
    print('Usage: {} ZXDB_ID'.format(os.path.basename(sys.argv[0])))
    sys.exit(1)
run(sys.argv[1].rjust(7, '0'))
