#!/usr/bin/env python3
import argparse
from collections import defaultdict
import re
import os
import sys

from libt2s import (T2SFILES_HOME, T2S_ROOT_DIR, COMPILATION_TYPES, LANGUAGES,
                    get_games, get_tapes, get_t2s_names, get_t2s_suffix,
                    get_zxdb_id)

RE_LANG = '.*({}).t2s'.format('|'.join(LANGUAGES))

def run(options):
    games = get_games()
    tapes = get_tapes()
    infoseek_ids = defaultdict(list)
    game_names = {}
    if options.unknown_suffix:
        t2s_exp_names = get_t2s_names(True)
    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for fname in files:
            t2sfile = os.path.join(root, fname)
            zxdb_id, md5sum = get_zxdb_id(t2sfile, games, tapes, True)
            if zxdb_id:
                infoseek_ids[zxdb_id].append((t2sfile[len(T2SFILES_HOME) + 1:], md5sum, tapes[md5sum]['tape']))
                game_names[zxdb_id] = games[zxdb_id]['name']

    for iid, t2sfiles in infoseek_ids.items():
        if len(t2sfiles) > 1:
            t2s_names = [os.path.basename(i[0]) for i in t2sfiles]
            if options.language and all(re.match(RE_LANG, t2s) for t2s in t2s_names):
                continue
            if options.parts and all(re.match('.*-p[0-9].t2s', t2s) for t2s in t2s_names):
                continue
            if options.sides and all(re.match('.*-side-[1234abcd].t2s', t2s) for t2s in t2s_names):
                continue
            if options.machines:
                t2s_128k = [t for t in t2s_names if t.endswith('-128k.t2s')]
                if t2s_128k:
                    exp_t2s_48k = [f'{t[:-9]}.t2s' for t in t2s_128k]
                    exp_t2s_all = set(t2s_128k + exp_t2s_48k)
                    if exp_t2s_all == set(t2s_names):
                        continue
            if options.unknown_suffix:
                exp_t2s_names = t2s_exp_names[iid]
                for t in t2s_names:
                    if get_t2s_suffix(t[:-4], exp_t2s_names, iid):
                        break
                else:
                    continue
            game_info = games[iid]
            game = game_names[iid]
            suffix = ' [Compilation]' if 'contents' in game_info or game_info['genre'] in COMPILATION_TYPES else ''
            print(f'{iid} - {game}{suffix}')
            for t2sfile, md5sum, tape in sorted(t2sfiles):
                print(f'  {t2sfile:<50} ({md5sum} {tape})')

parser = argparse.ArgumentParser(
    usage='{} [options]'.format(os.path.basename(sys.argv[0])),
    description="List ZXDB entries that have two or more t2s files.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-l', dest='language', action='store_true',
                   help="Omit entries for which all t2s files are named '*-CC.t2s', where CC is a two-letter country code.")
group.add_argument('-m', dest='machines', action='store_true',
                   help="Omit entries for which all t2s files are named 'NAME.t2s' and 'NAME-128k.t2s'.")
group.add_argument('-p', dest='parts', action='store_true',
                   help="Omit entries for which all t2s files are named '*-p[0-9].t2s'.")
group.add_argument('-s', dest='sides', action='store_true',
                   help="Omit entries for which all t2s files are named '*-side-[1a2b3c4d].t2s'.")
group.add_argument('-u', dest='unknown_suffix', action='store_true',
                   help="Omit entries for which all t2s files have a recognised suffix.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
