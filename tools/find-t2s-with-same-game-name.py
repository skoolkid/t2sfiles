#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os

from libt2s import (T2SFILES_HOME, T2S_SUFFIXES, RED, GREEN, CYAN, RESET,
                    get_games, get_tapes, get_t2s_by_iid, get_t2s_name_iids,
                    get_t2s_names)

def get_suffix(t2s_name):
    for s in T2S_SUFFIXES:
        if t2s_name.endswith(s):
            return s

def get_suffixes(t2s_name):
    suffixes = []
    suffix = get_suffix(t2s_name)
    while suffix:
        suffixes.insert(0, suffix)
        t2s_name = t2s_name[:-len(suffix)]
        suffix = get_suffix(t2s_name)
    return ''.join(suffixes)

def get_alt_t2s_fname(t2s_name, prefix, iid):
    if t2s_name.startswith(prefix):
        suffixes = get_suffixes(t2s_name)
        return f'{prefix}-{iid}{suffixes}.t2s'
    return ''

def run(options):
    games = get_games()
    tapes = get_tapes()
    t2s_names = get_t2s_names()
    t2s_by_iid = get_t2s_by_iid(games, tapes)
    t2s_name_iids = get_t2s_name_iids(t2s_names)
    names = defaultdict(list)
    for iid, t2s_files in t2s_by_iid.items():
        game = games[iid]['name']
        t2s_name = t2s_names[iid][0]
        for fname in t2s_files:
            names[(t2s_name, game)].append((iid, os.path.basename(fname)))

    for (t2s_name, game), t2s_files in sorted(names.items()):
        iids_for_t2s_name = set(t2s_name_iids[t2s_name])
        if options.hide_single_iid:
            show = len(set(iid for iid, fname in t2s_files)) > 1
        elif options.show_non_unique:
            show = len(iids_for_t2s_name) > 1
        else:
            show = len(t2s_files) > 1
        if show:
            all_entries = []
            entries = []
            alt_t2s_names = []
            for iid, t2s_file in sorted(t2s_files, key=lambda t: t[0]):
                iids_for_t2s_name.discard(iid)
                iid_in_t2s = f'-{iid}' in t2s_file
                t2s_ltr = t2s_file[0] if t2s_file[0].isalpha() else '0'
                t2s_path = f't2s/{t2s_ltr}/{t2s_file}'
                if options.show_t2s_with_iid:
                    alt_t2s_fname = get_alt_t2s_fname(t2s_file[:-4], t2s_name, iid)
                    if iid_in_t2s:
                        all_entries.append((iid, t2s_path))
                        if not options.hide_t2s_with_iid:
                            entries.append(all_entries[-1])
                    elif alt_t2s_fname:
                        alt_t2s_names.append((iid, f'{CYAN}{t2s_path} -> t2s/{t2s_ltr}/{alt_t2s_fname}{RESET}'))
                    else:
                        all_entries.append((iid, f'{t2s_path} -> ???'))
                        entries.append(all_entries[-1])
                elif not iid_in_t2s or not options.hide_t2s_with_iid:
                    entries.append((iid, t2s_path))
            if alt_t2s_names:
                entries = alt_t2s_names + [(iid, f'{GREEN}{t}{RESET}') for iid, t in all_entries]
            if entries and options.show_non_unique and iids_for_t2s_name:
                for iid in iids_for_t2s_name:
                    if iid in games:
                        t2sf = t2s_by_iid.get(iid)
                        if t2sf:
                            colour = GREEN if alt_t2s_names else ''
                            info = ', '.join(f'{colour}{t}{RESET}' for t in t2sf)
                        else:
                            info = f'{RED}* no t2s file *{RESET}'
                    else:
                        info = f'{RED}* not in games.json *{RESET}'
                    entries.append((iid, info))
            if entries:
                print(f'{t2s_name} ({game}):')
                for iid, info in sorted(entries):
                    print(f'  {iid} {info}')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options]',
    description="List t2s files in groups of two or more by game name.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-h', dest='hide_t2s_with_iid', action='store_true',
                   help="Hide t2s file names that already include the ZXDB ID.")
group.add_argument('-i', dest='show_t2s_with_iid', action='store_true',
                   help="Suggest alternative t2s file names that include the ZXDB ID.")
group.add_argument('-n', dest='show_non_unique', action='store_true',
                   help="Show t2s file names for games with a non-unique name.")
group.add_argument('-s', dest='hide_single_iid', action='store_true',
                   help="Hide groups of t2s files with a single ZXDB ID.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
