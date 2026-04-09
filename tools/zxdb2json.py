#!/usr/bin/env python3
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import os
import sqlite3

from libt2s import (COMPILATION_TYPES, GAMES_JSON, SPECTRUM_TAPES, ZXDB,
                    get_entries_sql, get_tape_sums)

# Note: '/pub/sinclair/utils/' is included for 'Expert for Bank' (0017097)
DOWNLOADS_SQL = """
SELECT entry_id, file_link, file_md5
FROM downloads
WHERE (file_link LIKE '%.tzx.zip'
OR file_link LIKE '%.tap.zip'
OR filetype_id IN (8, 20, 22))
AND (file_link LIKE '/pub/sinclair/compilations/%'
OR file_link LIKE '/pub/sinclair/games/%'
OR file_link LIKE '/pub/sinclair/utils/%'
OR file_link LIKE '/zxdb/sinclair/%'
OR file_link LIKE '/denied/%')
""".strip()

GENRES_SQL = """
SELECT id, text
FROM genretypes
""".strip()

MACHINES_SQL = """
SELECT id, text
FROM machinetypes
""".strip()

AUTHORS_SQL = """
SELECT a.entry_id, l.name
FROM authors a, labels l
WHERE a.label_id = l.id
ORDER BY a.entry_id, a.author_seq
""".strip()

PUBLISHERS_SQL = """
SELECT p.entry_id, l.name
FROM publishers p, labels l
WHERE p.label_id = l.id
ORDER BY p.entry_id, p.release_seq
""".strip()

CONTENTS_SQL = """
SELECT c.container_id, c.entry_id
FROM contents c, entries e
WHERE c.container_id = e.id
AND e.machinetype_id < 6
""".strip()

PATHS = (
    '/denied/entries/',
    '/pub/sinclair/compilations/',
    '/pub/sinclair/games/',
    '/pub/sinclair/utils/',
    '/zxdb/sinclair/entries/'
)

def run(options):
    debug = options.debug
    tape_sums = get_tape_sums()

    conn = sqlite3.connect(ZXDB)

    downloads = defaultdict(list)
    for iid, link, md5 in conn.execute(DOWNLOADS_SQL):
        link_l = link.lower()
        if link_l.endswith(('.tap.zip', '.tzx.zip')) or (link_l.endswith('.zip') and link.count('.') == 1):
            downloads[iid].append((link, md5))

    genres = {}
    for genre_id, name in conn.execute(GENRES_SQL):
        genres[genre_id] = name

    machines = {}
    for machine_id, name in conn.execute(MACHINES_SQL):
        machines[machine_id] = name[12:]

    authors = defaultdict(list)
    for iid, name in conn.execute(AUTHORS_SQL):
        authors[iid].append(name)

    publishers = defaultdict(list)
    for iid, name in conn.execute(PUBLISHERS_SQL):
        publishers[iid].append(name)

    contents = defaultdict(list)
    for cid, iid in conn.execute(CONTENTS_SQL):
        if iid:
            contents[f'{cid:07}'].append(f'{iid:07}')

    games = {}
    columns = ('e.id', 'e.title', 'elt.library_title', 'e.machinetype_id', 'e.genretype_id', 'e.availabletype_id')
    for iid, name, index_name, machine, genre, availability in conn.execute(get_entries_sql(*columns)):
        if debug:
            print(f'{iid:07} {name} [retrieved]')
        game_tapes = []
        if downloads[iid]:
            for path, md5 in downloads[iid]:
                if path.startswith(PATHS):
                    url = f'https://spectrumcomputing.co.uk{path}'
                    tsubdir = f'{SPECTRUM_TAPES}/spectrumcomputing.co.uk{path[:-4]}'
                else:
                    continue
                tape_files = []
                if os.path.isdir(tsubdir):
                    for r, s, tfiles in os.walk(tsubdir):
                        for t in sorted(tfiles):
                            if t.lower().endswith(('tap', 'tzx')):
                                tfname = os.path.join(r, t)
                                md5 = tape_sums.get(tfname)
                                if not md5:
                                    with open(tfname, 'rb') as tf:
                                        md5 = hashlib.md5(tf.read()).hexdigest()
                                member = tfname[len(tsubdir) + 1:]
                                tape_files.append(f'{md5} {member}')
                if tape_files or options.urls:
                    game_tapes.append((url, sorted(tape_files, key=lambda t: t.split(' ', 1)[1])))
        elif debug:
            print(f'{iid:07} {name} [warning: no downloads available]')
        game = games[f'{iid:07}'] = {
            'authors': ' / '.join(authors[iid]),
            'genre': genres.get(genre, ''),
            'machines': machines.get(machine, ''),
            'name': name,
            'publishers': ' / '.join(publishers[iid]),
            'denied': availability in ('D', 'S')
        }
        if game_tapes:
            game['tapes'] = game_tapes
        if index_name != name:
            game['index_name'] = index_name

    conn.close()

    non_game_compilations = set()
    containers = defaultdict(list)
    for iid, game in games.items():
        if iid in contents:
            game_name = game['name']
            title_contents = set()
            for c_iid in contents[iid]:
                if c_iid in games:
                    c_game = games[c_iid]
                    title_contents.add(f'{c_iid} {c_game["name"]}')
                    if not c_game.get('tapes'):
                        containers[c_iid].append(f'{iid} {game_name}')
            if title_contents:
                game['contents'] = sorted(title_contents)
            elif game['genre'] in COMPILATION_TYPES:
                non_game_compilations.add(iid)

    for iid, within in containers.items():
        games[iid]['within'] = within

    for iid in non_game_compilations:
        if debug:
            print(f'{iid:07} {games[iid]["name"]} [removed: not a game compilation]')
        del games[iid]

    for iid, game in tuple(games.items()):
        if 'tapes' not in game:
            # This game has no tape of its own available; consider removing it
            within = game.get('within')
            if within:
                for item in within:
                    container_iid = item[:7]
                    if container_iid in games and 'tapes' in games[container_iid]:
                        # This game is in a compilation that has a tape
                        # available, so don't remove it
                        break
                    elif downloads.get(int(container_iid)):
                        # This game is in a compilation for which one or more
                        # download links exist, so don't remove it
                        break
                else:
                    # This game is in one or more compilations, but none of
                    # them has any tape available
                    if debug:
                        print(f'{iid:07} {games[iid]["name"]} [removed: no compilation tapes available]')
                    del games[iid]
            else:
                # This game is not in any compilation
                if debug:
                    print(f'{iid:07} {games[iid]["name"]} [removed: not in any compilation]')
                del games[iid]

    if options.urls:
        prefix_len = len('https://spectrumcomputing.co.uk/')
        for iid, game in games.items():
            for url, tapes in game.get('tapes', ()):
                path = url[prefix_len:]
                if not path.startswith('denied/entries/') and not os.path.isfile(f'{SPECTRUM_TAPES}/spectrumcomputing.co.uk/{path}'):
                    print(url)
    elif not debug:
        if os.path.isfile(GAMES_JSON):
            mtime = datetime.fromtimestamp(os.stat(GAMES_JSON).st_mtime)
            fname = '{}/games-{}.json'.format(os.path.dirname(GAMES_JSON), mtime.strftime('%Y%m%d%H%M%S'))
            os.rename(GAMES_JSON, fname)

        with open(GAMES_JSON, 'w') as f:
            json.dump(games, f, sort_keys=True, indent=4)
            f.write('\n')
        print(f'Wrote {GAMES_JSON} ({len(games)} games)')

parser = argparse.ArgumentParser(
    usage='%(prog)s [options]',
    description="Convert the ZXDB SQLite database into a JSON file.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-d', dest='debug', action='store_true',
                   help="Print debug info only (without updating the JSON file).")
group.add_argument('-u', dest='urls', action='store_true',
                   help="Print download URLs (without updating the JSON file).")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
