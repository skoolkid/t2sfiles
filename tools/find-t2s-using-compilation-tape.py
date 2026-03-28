#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os
import sys

from libt2s import (COMPILATION_TYPES, T2S_ROOT_DIR, T2S, get_games, get_tapes,
                    get_zxdb_id, get_non_compilations)

def get_compilations(games, options):
    tapes = get_tapes()
    non_compilations = get_non_compilations()
    compilations = {}
    prefix_len = len(os.path.dirname(T2S_ROOT_DIR)) + 1
    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for t in sorted(files):
            t2s = os.path.join(root, t)
            with open(t2s) as f:
                for line in f:
                    if line.startswith('--tape-sum'):
                        tape_sum = line[11:].rstrip()
                        break
            if tape_sum not in tapes:
                print(f'WARNING: Tape used by {t} is not in ZXDB', file=sys.stderr)
                continue
            iid = tapes[tape_sum]['infoseek']
            if iid in non_compilations:
                if options.debug:
                    print(f'DEBUG: {t} ({iid} {games[iid]["name"]}) [excluded: marked as non-compilation]')
                continue
            game_info = games[iid]
            genre = game_info['genre']
            if options.is_compilation and genre not in COMPILATION_TYPES:
                if options.debug:
                    print(f'DEBUG: {t} ({iid} {game_info["name"]}) [excluded: genre={genre!r}]')
                continue
            if not (genre in COMPILATION_TYPES or 'contents' in game_info):
                if options.debug:
                    print(f'DEBUG: {t} ({iid} {game_info["name"]}) [excluded: not a compilation tape]')
                continue

            zxdb_id = get_zxdb_id(T2S(t[:-4], [tape_sum]), games, tapes)
            has_entry = zxdb_id != iid
            for item in game_info.get('contents', ()):
                if item.startswith(f'{iid} '):
                    # This compilation contains itself, so mark it as having
                    # an entry
                    has_entry = True
                    break
            has_tape = has_entry and 'tapes' in games[zxdb_id]
            if options.has_no_entry and has_entry:
                continue
            if options.hide_has_no_entry and not has_entry:
                continue
            if options.has_tape and not has_tape:
                continue
            if options.hide_has_tape and has_tape:
                continue
            c_info = compilations.setdefault(iid, game_info)
            c_t2s = c_info.setdefault('t2s', [])
            c_t2s.append((t2s[prefix_len:], zxdb_id))

    for iid, comp in compilations.items():
        # Some compilations contain themselves (e.g. 0002585 Jerico 2); for
        # each such compilation, remove it from its own contents list.
        contents = comp.get('contents', ())
        for item in contents[:]:
            if item.startswith(f'{iid} '):
                contents.remove(item)

    return compilations

def get_t2s_using_compilation_tapes(ids, options):
    # Identify t2s files for compilation items extracted from compilation tapes
    games = get_games()
    iids = [i.rjust(7, '0') for i in ids]
    compilations = []
    t2s_by_iid = defaultdict(list)
    for c_iid, comp in get_compilations(games, options).items():
        if iids and c_iid not in iids:
            continue
        c_name = comp['name']
        compilations.append((f'{c_iid} {c_name}', []))
        for t2s, t2s_iid in comp['t2s']:
            t2s_by_iid[t2s_iid].append(t2s)
            if t2s_iid == c_iid:
                suffix = ''
            else:
                i_name = games[t2s_iid]['name']
                suffix = f' [{t2s_iid} {i_name}]'
            compilations[-1][1].append(f'  {t2s}{suffix}')
    return t2s_by_iid, compilations

def run(ids, options):
    t2s_by_iid, compilations = get_t2s_using_compilation_tapes(ids, options)
    if options.by_id:
        for iid in sorted(t2s_by_iid):
            for t2s_file in t2s_by_iid[iid]:
                print(f'{iid} {t2s_file}')
    else:
        if options.by_num_items:
            key = lambda c: len(c[1])
        else:
            key = lambda c: c[0]
        for compilation, t2s_files in sorted(compilations, key=key):
            print(compilation)
            for t2s_file in t2s_files:
                print(f'  {t2s_file}')

parser = argparse.ArgumentParser(
    usage='%(prog)s [ID [ID...]]',
    description="List t2s files that use compilation tapes.",
    add_help=False
)
parser.add_argument('ids', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('-c', dest='is_compilation', action='store_true',
                   help="Only show t2s files that use tapes specifically marked as compilations.")
group.add_argument('-d', dest='debug', action='store_true',
                   help="Print debug info.")
group.add_argument('-e', dest='has_no_entry', action='store_true',
                   help="Only show t2s files for titles that have no ZXDB entry of their own.")
group.add_argument('-E', dest='hide_has_no_entry', action='store_true',
                   help="Hide t2s files for titles that have no ZXDB entry of their own.")
group.add_argument('-i', dest='by_id', action='store_true',
                   help="List t2s files by ID.")
group.add_argument('-n', dest='by_num_items', action='store_true',
                   help="Sort output by number of compilation items.")
group.add_argument('-t', dest='has_tape', action='store_true',
                   help="Only show t2s files for titles with their own tapes.")
group.add_argument('-T', dest='hide_has_tape', action='store_true',
                   help="Hide t2s files for titles with their own tapes.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace.ids, namespace)
