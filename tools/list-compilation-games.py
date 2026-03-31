#!/usr/bin/env python3
import argparse
import json
import os
import sys

from libt2s import get_games

def to_bbcode(iid, name):
    return f'[url="https://spectrumcomputing.co.uk/entry/{iid}"]{name}[/url]'

def run(iids, options):
    zxdb_games = get_games(False)
    compilations = {}
    for iid, game in zxdb_games.items():
        if options.genre and not game.get('genre'):
            continue
        tapes = game.get('tapes')
        within = game.get('within')
        if not tapes and within:
            comp_available = False
            for spec in within:
                within_iid = spec[:7]
                if within_iid in zxdb_games:
                    comp_available = True
                    break
            if comp_available:
                continue
            name = game['name']
            if options.by_comp:
                for spec in within:
                    comp = compilations.setdefault(spec[:7], {'name': spec[8:], 'contents': []})
                    comp['contents'].append(f'{iid} {name}')
            else:
                containers = [(w[:7], w[8:]) for w in within if iids is None or int(w[:7]) in iids]
                if containers:
                    if options.bbcode:
                        game = to_bbcode(iid, name)
                        containers = [to_bbcode(*c) for c in containers]
                    else:
                        game = f'{iid} {name}'
                        containers = [f'{i} {n}' for i, n in containers]
                    print('{} {}'.format(game, ' '.join(f'[{c}]' for c in containers)))
    for iid in sorted(compilations):
        comp = compilations[iid]
        name = comp['name']
        if iids is None or int(iid) in iids:
            if options.bbcode:
                print(to_bbcode(iid, name))
                print('[list]')
            else:
                print(f'{iid} {name}')
            for spec in comp['contents']:
                if options.bbcode:
                    print('[*]{}'.format(to_bbcode(spec[:7], spec[8:])))
                else:
                    print(f'  {spec}')
            if options.bbcode:
                print('[/list]')

parser = argparse.ArgumentParser(
    usage='{} [options] ALL|ID[-ID] [ID[-ID]...]'.format(os.path.basename(sys.argv[0])),
    description="List games that appear only on compilations/covertapes not present in games.json (e.g. because they're hosted on archive.org). "
                "Output is limited to the compilations with the given IDs (if any).",
    add_help=False
)
parser.add_argument('iids', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('-b', dest='bbcode', action='store_true',
                   help="Render output using BBCode.")
group.add_argument('-c', dest='by_comp', action='store_true',
                   help="Group games by compilation.")
group.add_argument('-g', dest='genre', action='store_true',
                   help="Omit titles with no genre defined.")
namespace, unknown_args = parser.parse_known_args()
if not namespace.iids or unknown_args:
    parser.exit(2, parser.format_help())
if 'ALL' in namespace.iids:
    iids = None
else:
    iids = []
    for i in namespace.iids:
        if '-' in i:
            j, k = [int(n) for n in i.split('-', 1)]
            iids.extend(list(range(j, k + 1)))
        else:
            iids.append(int(i))
run(iids, namespace)
