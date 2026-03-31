#!/usr/bin/env python3
import argparse
from collections import defaultdict
import os
import sqlite3
import sys

from libt2s import ZXDB

DOWNLOADS_SQL = """
SELECT entry_id, file_link, file_md5
FROM downloads
""".strip()

GENRES_SQL = """
SELECT id, text
FROM genretypes
""".strip()

MACHINES_SQL = """
SELECT id, text
FROM machinetypes
""".strip()

AVAILABILITY_SQL = """
SELECT id, text
FROM availabletypes
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

ENTRY_BY_ID_SQL = """
SELECT id, title, machinetype_id, genretype_id, availabletype_id
FROM entries
WHERE id = {}
""".strip()

ENTRY_BY_NAME_SQL = """
SELECT id, title, machinetype_id, genretype_id, availabletype_id
FROM entries
WHERE UPPER(title) LIKE '{}'
""".strip()

GAMES_ONLY = "AND (genretype_id < 33 OR genretype_id IN (80, 81) OR genretype_id IS NULL)"

def run(id_or_name, options):
    infoseek_id = game_name = None
    try:
        infoseek_id = int(id_or_name)
    except ValueError:
        game_name = id_or_name.upper()
        if not options.exact:
            game_name = f'%{game_name}%'

    conn = sqlite3.connect(ZXDB)

    downloads = defaultdict(list)
    for iid, link, md5 in conn.execute(DOWNLOADS_SQL):
        if link.lower().endswith(('.tap.zip', '.tzx.zip')):
            downloads[iid].append((link, md5))

    genres = {}
    for genre_id, name in conn.execute(GENRES_SQL):
        genres[genre_id] = name

    machines = {}
    for machine_id, name in conn.execute(MACHINES_SQL):
        machines[machine_id] = name[12:]

    availability = {}
    for availability_id, name in conn.execute(AVAILABILITY_SQL):
        availability[availability_id] = name

    authors = defaultdict(list)
    for iid, name in conn.execute(AUTHORS_SQL):
        authors[iid].append(name)

    publishers = defaultdict(list)
    for iid, name in conn.execute(PUBLISHERS_SQL):
        publishers[iid].append(name)

    if infoseek_id is not None:
        sql = ENTRY_BY_ID_SQL.format(infoseek_id)
    else:
        sql = ENTRY_BY_NAME_SQL.format(game_name)
    if options.games_only:
        sql += f' {GAMES_ONLY}'

    result = conn.execute(sql)

    if result:
        for iid, name, machine_id, genre_id, availability_id in result:
            author = ' / '.join(authors[iid])
            publisher = ' / '.join(publishers[iid])
            machine = machines.get(machine_id, '')
            genre = genres.get(genre_id, '')
            available = availability.get(availability_id, '')
            print(f'{iid:07} {name}')
            print(f'  Authors: {author}')
            print(f'  Publishers: {publisher}')
            print(f'  Machine: {machine}')
            print(f'  Genre: {genre}')
            print(f'  Availability: {available}')
            print(f'  Downloads:')
            for path, md5 in downloads[iid]:
                print(f'    {path}')
            print()

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] INFOSEEK_ID|GAME_NAME',
    description="Search ZXDB for game info.",
    add_help=False
)
parser.add_argument('id_or_name', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-e', dest='exact', action='store_true',
                   help="Search for titles with exactly this name.")
group.add_argument('-g', dest='games_only', action='store_true',
                   help="Restrict output to games.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.id_or_name:
    parser.exit(2, parser.format_help())
run(namespace.id_or_name, namespace)
