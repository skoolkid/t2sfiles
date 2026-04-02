#!/usr/bin/env python3
import argparse
from collections import defaultdict

from libt2s import T2SFILES_HOME, get_games, get_tapes, get_t2s_by_iid, get_t2s_name_iids, get_t2s_names

def get_suffix(t2s_name):
    for s in ('-128k', '-p1', '-p2', '-p3', '-p4', '-en', '-es', '-pt', '-side-1', '-side-2', '-side-a', '-side-b', '-release-1', '-release-2', '-release-3', '-v1', '-v2'):
        if t2s_name.endswith(s):
            return s
    return ''

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
    root_dir = f'{T2SFILES_HOME}/t2s'
    names = defaultdict(list)
    for iid, t2s_files in t2s_by_iid.items():
        game = games[iid]['name']
        t2s_name = t2s_names[iid][0]
        for fname in t2s_files:
            names[(t2s_name, game)].append((iid, fname))

    for (t2s_name, game), t2s_files in sorted(names.items()):
        iids_for_t2s_name = set(t2s_name_iids[t2s_name])
        if options.hide_single_iid:
            show = len(set(iid for iid, fname in t2s_files)) > 1
        elif options.show_non_unique:
            show = len(iids_for_t2s_name) > 1
        else:
            show = len(t2s_files) > 1
        if show:
            entries = []
            for iid, t2s_file in sorted(t2s_files, key=lambda t: t[0]):
                iids_for_t2s_name.discard(iid)
                iid_in_t2s = f'-{iid}' in  t2s_file
                if options.show_t2s_with_iid:
                    alt_t2s_fname = get_alt_t2s_fname(t2s_file[:-4], t2s_name, iid)
                    t2s_ltr = t2s_file[0] if t2s_file[0].isalpha() else '0'
                    if iid_in_t2s:
                        if not options.hide_t2s_with_iid:
                            entries.append(f'  {iid} t2s/{t2s_ltr}/{t2s_file}')
                    elif alt_t2s_fname:
                        entries.append(f'  {iid} t2s/{t2s_ltr}/{t2s_file} -> t2s/{t2s_ltr}/{alt_t2s_fname}')
                    else:
                        entries.append(f'  {iid} t2s/{t2s_ltr}/{t2s_file} -> ???')
                elif not iid_in_t2s or not options.hide_t2s_with_iid:
                    entries.append(f'  {iid} {t2s_file}')
            if entries and options.show_non_unique and iids_for_t2s_name:
                entries.extend(f'  {iid} -' for iid in iids_for_t2s_name)
            if entries:
                print(f'{t2s_name} ({game}):')
                for line in sorted(entries):
                    print(line)

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
