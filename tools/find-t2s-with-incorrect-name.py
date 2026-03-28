#!/usr/bin/env python3
import argparse
import os

from libt2s import (COMPILATION_TYPES, T2S_ROOT_DIR, CYAN, RESET, get_games,
                    get_tapes, get_exp_t2s_names, get_t2s_names,
                    get_t2s_suffix)

def t2s_path(name, show_subdir):
    path = name
    if show_subdir:
        subdir = name[0] if name[0].isalpha() else '0'
        path = f't2s/{subdir}/{name}'
    if not path.endswith('.t2s'):
        path += '.t2s'
    return path

def check_contents(t2s, games, names, iid, game_info, show_subdir, suffixes):
    game_names = names[iid]
    is_compilation = game_info['genre'] in COMPILATION_TYPES
    exp_names = []
    for spec in game_info['contents']:
        c_iid, c_name = spec.split(None, 1)
        if c_iid == '-------':
            for exp_name in get_exp_t2s_names(c_name, c_name):
                for comp_name in game_names:
                    exp_names.append(f'{comp_name}-{exp_name}')
        elif c_iid.isdigit():
            for exp_name in names[c_iid]:
                exp_names.append(exp_name)
                exp_names.append(f'{exp_name}-{c_iid}')
                if is_compilation:
                    for comp_name in game_names:
                        exp_names.append(f'{comp_name}-{exp_name}')
                        exp_names.append(f'{comp_name}-{exp_name}-{c_iid}')
    if t2s.startswith(tuple(exp_names)) and not (suffixes and get_t2s_suffix(t2s[:-4], exp_names)):
        return
    t2s_name = t2s_path(t2s, show_subdir)
    exp_t2s_names = ', '.join(t2s_path(n, show_subdir) for n in exp_names)
    game_name = games[iid]['name']
    return f'{CYAN}{t2s_name}{RESET}: {exp_t2s_names} [{CYAN}{iid} {game_name}{RESET}]'

def run(options):
    games = get_games()
    tapes = get_tapes()
    names = get_t2s_names(True)
    unknown = []
    compilations = []

    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for t2s in sorted(files):
            tape_sum = None
            with open(os.path.join(root, t2s)) as f:
                for line in f:
                    if line.startswith('--tape-sum'):
                        tape_sum = line[11:].rstrip()
                        break
            if tape_sum not in tapes:
                unknown.append(f'{t2s}: Unknown tape')
                continue
            iid = tapes[tape_sum]['infoseek']
            game_info = games[iid]
            game_name = game_info['name']
            is_compilation = game_info['genre'] in COMPILATION_TYPES
            if 'contents' in game_info:
                line = check_contents(t2s, games, names, iid, game_info, options.t2sdir, options.suffixes)
                if line:
                    if is_compilation:
                        compilations.append(line)
                    elif options.show:
                        print(line)
            elif options.show:
                exp_names = names[iid]
                t2s_name = t2s_path(t2s, options.t2sdir)
                exp_t2s_names = ', '.join(t2s_path(n, options.t2sdir) for n in exp_names)
                show = False
                if not t2s.startswith(tuple(exp_names)):
                    show = True
                elif options.suffixes:
                    if not is_compilation and get_t2s_suffix(t2s[:-4], exp_names, iid):
                        show = True
                if show:
                    print(f'{CYAN}{t2s_name}{RESET}: {exp_t2s_names} [{CYAN}{iid} {game_name}{RESET}]')

    if options.compilations and compilations:
        for line in compilations:
            print(line)

    if options.unknown and unknown:
        for line in unknown:
            print(line)

parser = argparse.ArgumentParser(
    usage='%(prog)s [options]',
    description="List t2s files that may have incorrect names.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-c', dest='compilations', action='store_true',
                   help="Show t2s files for compilations.")
group.add_argument('-t', dest='t2sdir', action='store_true',
                   help="Include t2s subdirectory in t2s filenames.")
group.add_argument('-s', dest='suffixes', action='store_true',
                   help="Include t2s files with unrecognised suffixes.")
group.add_argument('-u', dest='unknown', action='store_true',
                   help="Show t2s files with unknown tapes.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
namespace.show = not namespace.compilations and not namespace.unknown
run(namespace)
