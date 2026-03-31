#!/usr/bin/env python3
import argparse
from collections import defaultdict
import json

from libt2s import RED, GREEN, RESET, get_games

def run(options):
    games = get_games(False)

    tapes = defaultdict(list)
    for iid, game_info in games.items():
        for url, game_tapes in game_info.get('tapes', ()):
            for tape in game_tapes:
                md5, tape_name = tape.split(' ', 1)
                tapes[md5].append({
                    'id': iid,
                    'game': game_info['name'],
                    'tape': tape_name,
                    'url': url
                })

    for md5, tapes in tapes.items():
        if len(tapes) > 1:
            num_titles = len(set(tape['id'] for tape in tapes))
            if options.different and num_titles == 1:
                continue
            if options.same and num_titles > 1:
                continue
            prev_iid = None
            for tape in tapes:
                iid = tape['id']
                game = tape['game']
                tape_name = tape['tape']
                path = tape['url'].split('/', 3)[-1]
                if prev_iid != iid:
                    if options.bbcode:
                        print(f'[url="https://spectrumcomputing.co.uk/entry/{iid}/"]{game}[/url]:')
                    else:
                        colour = GREEN if prev_iid is None else RED
                        print(f'{colour}{iid} {game}{RESET}')
                if options.bbcode:
                    print(f'- [b]{tape_name}[/b] (/{path})')
                else:
                    print(f'  /{path}')
                    print(f'    {md5} {tape_name}')
                prev_iid = iid
            print()

parser = argparse.ArgumentParser(
    usage='%(prog)s [options]',
    description="List ZXDB titles that have identical tapes.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-b', dest='bbcode', action='store_true',
                   help="Output as BBCode.")
group.add_argument('-d', dest='different', action='store_true',
                   help="Only show tapes shared between distinct titles.")
group.add_argument('-D', dest='same', action='store_true',
                   help="Don't show tapes shared between distinct titles.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
