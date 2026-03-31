#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os
import sqlite3

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')

from libt2s import (COMPILATION_TYPES, ZXDB, get_entries_sql,
                    get_skipped_tapes, get_non_compilations)

TAPE_SNIP = f'{T2SFILES_HOME}/tools/tape-snip.py'

# Note: '/pub/sinclair/utils/' is included for 'Expert for Bank' (0017097)
DOWNLOADS_SQL = """
SELECT entry_id, file_link, file_md5
FROM downloads
WHERE (file_link LIKE '%.tzx.zip'
OR file_link LIKE '%.tap.zip'
OR filetype_id IN (8, 20, 22))
AND (file_link LIKE '/pub/sinclair/compilations/%'
OR file_link LIKE '/pub/sinclair/games/%'
OR file_link LIKE '/pub/sinclair/magazines/%'
OR file_link LIKE '/pub/sinclair/utils/%'
OR file_link LIKE '/zxdb/sinclair/%')
""".strip()

GENRES_SQL = """
SELECT id, text
FROM genretypes
""".strip()

CONTENTS_SQL = """
SELECT c.container_id, c.entry_id, c.media_seq, c.media_side, c.prog_seq
FROM contents c, entries e
WHERE c.container_id = e.id
AND e.machinetype_id < 6
""".strip()

def snip(c_iid, magazines, games):
    snips = []
    mag = games[c_iid]
    print('{} {}'.format(c_iid, mag['name']))
    tapes = {}
    for mseq, mside, pseq, game in sorted(magazines[c_iid]):
        tape = tapes.get((mseq, mside))
        if tape is None:
            tape_files = sorted(f for f in os.listdir() if f.lower().endswith(('.tap', '.tzx')))
            for index, tf in enumerate(tape_files, 1):
                print(f'[{index}] {tf}')
            options = '/'.join(str(i) for i in range(1, len(tape_files) + 1))
            while True:
                index = input(f'Tape filename (tape {mseq} side {mside}) [{options}]: ')
                try:
                    index = int(index)
                except:
                    continue
                if 1 <= index <= len(tape_files):
                    tape = tapes[(mseq, mside)] = tape_files[index - 1]
                    break
                else:
                    print(f'ERROR: Invalid tape index ({index})')
        g_iid = game['iid']
        gname = game['name']
        while True:
            cut = input(f'Cut blocks for {mseq}-{mside}-{pseq} {g_iid} {gname}: ')
            try:
                block_nums = [int(b) for b in cut.split('-', 1)]
                break
            except:
                print('ERROR: Invalid cut spec; try again')
        snips.append((cut, tape, gname, g_iid))

    stfile = f'snip-tapes-{c_iid}.sh'
    with open(stfile, 'w') as f:
        f.write('#!/usr/bin/env bash\n')
        f.write(f'TAPE_SNIP={TAPE_SNIP}\n')
        f.write(f'mkdir -p tapes\n')
        for cut, tape, gname, g_iid in snips:
            tape_fname = tape.replace("'", r"'\''")
            fname = '{}-{}.{}'.format(gname.replace(' ', '-').replace("'", '-').replace('/', '-'), g_iid, tape.lower()[-3:])
            f.write(f"$TAPE_SNIP -c {cut} '{tape_fname}' 'tapes/{fname}'\n")
    os.chmod(stfile, 0o755)
    print(f'Wrote {stfile}')

def show(c_iid, magazines, games, options):
    c_name = games[c_iid]['name']
    print('{} {}'.format(c_iid, c_name))
    if not options.no_contents:
        for mseq, mside, pseq, game in magazines[c_iid]:
            print('  {}-{}-{} {} {}'.format(mseq, mside, pseq, game['iid'], game['name']))

def run(options):
    skip_ids = set(get_skipped_tapes())
    skip_ids.update(get_non_compilations())

    conn = sqlite3.connect(ZXDB)

    downloads = defaultdict(list)
    for iid, link, md5 in conn.execute(DOWNLOADS_SQL):
        link_l = link.lower()
        if link_l.endswith(('.tap.zip', '.tzx.zip')) or (link_l.endswith('.zip') and link.count('.') == 1):
            downloads[iid].append((link, md5))

    genres = {}
    for genre_id, name in conn.execute(GENRES_SQL):
        genres[genre_id] = name

    contents = defaultdict(list)
    for cid, iid, mseq, mside, pseq in conn.execute(CONTENTS_SQL):
        if iid:
            contents[f'{cid:07}'].append((mseq, mside, pseq, f'{iid:07}'))

    games = {}
    columns = ('e.id', 'e.title', 'e.machinetype_id', 'e.genretype_id', 'e.availabletype_id')
    for iid, name, machine, genre, availability in conn.execute(get_entries_sql(*columns)):
        zxdb_id = f'{iid:07}'
        if zxdb_id not in skip_ids:
            games[zxdb_id] = {
                'iid': zxdb_id,
                'genre': genres.get(genre, ''),
                'name': name,
                'denied': availability in ('D', 'S'),
                'tapes': [path for path, md5 in downloads[iid]]
            }

    conn.close()

    non_game_compilations = set()
    containers = defaultdict(list)
    for iid, game in games.items():
        if iid in contents:
            game_name = game['name']
            title_contents = set()
            for mseq, mside, pseq, c_iid in contents[iid]:
                if c_iid in games:
                    c_game = games[c_iid]
                    title_contents.add(f'{c_iid} {c_game["name"]}')
                    if not c_game.get('tapes'):
                        containers[c_iid].append((mseq, mside, pseq, iid, game_name))
            if title_contents:
                game['contents'] = sorted(title_contents)
            elif game['genre'] in COMPILATION_TYPES:
                non_game_compilations.add(iid)

    for iid, within in containers.items():
        games[iid]['within'] = within

    for iid in non_game_compilations:
        del games[iid]

    magazines = defaultdict(list)
    first_mag = options.snip_iid is None and options.c_iid is None
    for iid, game in games.items():
        if not game['tapes']:
            # This game has no tape of its own available; check whether it's on
            # a magazine/compilation tape
            for mseq, mside, pseq, container_iid, game_name in game.get('within', ()):
                if container_iid in games and games[container_iid]['tapes']:
                    container = games[container_iid]
                    tape = container['tapes'][0]
                    if options.compilations or tape.startswith('/pub/sinclair/magazines/'):
                        magazines[container_iid].append((mseq, mside, pseq, game))
                        if first_mag:
                            break

    if options.snip_iid:
        snip(options.snip_iid.rjust(7, '0'), magazines, games)
    elif options.c_iid:
        show(options.c_iid.rjust(7, '0'), magazines, games, options)
    else:
        for c_iid in sorted(magazines):
            show(c_iid, magazines, games, options)

parser = argparse.ArgumentParser(
    usage='%(prog)s [options]',
    description="Show games without their own tapes that are in /pub/sinclair/magazines tapes.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-c', dest='compilations', action='store_true',
                   help="Include compilations not in /pub/sinclair/magazines.")
group.add_argument('-i', dest='c_iid', metavar='ID',
                   help="Show tape with this ID.")
group.add_argument('-n', dest='no_contents', action='store_true',
                   help="Don't show tape contents.")
group.add_argument('-s', dest='snip_iid', metavar='ID',
                   help="Generate tape-snip.py commands for this tape.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
