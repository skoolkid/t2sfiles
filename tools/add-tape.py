#!/usr/bin/env python3
from collections import defaultdict
import hashlib
import json
import os
import sqlite3
import sys

from libt2s import TAPES_JSON, TAPES_TXT, REASONS, ZXDB, get_tapes, get_games

def print_usage():
    cmd = os.path.basename(sys.argv[0])
    reasons = '|'.join(REASONS)
    reason_descs = '\n'.join(f'    {k}: {v}' for k, v in REASONS.items())
    print(f"""
Usage:
  {cmd} T2S_FILE ZXDB_ID
  {cmd} [-f] ZXDB_ID|TAPE_FILE|TAPE_SUM {reasons} [48K|128K]

{reason_descs}

Add a tape to tapes.json or tapes.txt.
""".strip())
    sys.exit(1)

def add_new_tape(t2sfile, infoseek_id):
    tape = url = md5sum = None
    with open(t2sfile) as f:
        for line in f:
            s_line = line.strip()
            if 'https://' in s_line:
                url = s_line
                if url.startswith('"'):
                    url = url[1:-1]
            elif s_line.startswith('--tape-name'):
                tape = s_line[12:].lstrip()
                if tape.startswith('"'):
                    tape = tape[1:-1]
            elif s_line.startswith('--tape-sum'):
                md5sum = s_line[11:].lstrip()

    if not tape or not url or not md5sum:
        sys.stderr.write(f'ERROR: Could not read URL, tape name or tape sum from {t2sfile}\n')
        sys.exit(1)

    conn = sqlite3.connect(ZXDB)
    name = None
    for row in conn.execute(f'SELECT title FROM entries WHERE id = {infoseek_id}'):
        name = row[0]
    if not name:
        sys.stderr.write(f'ERROR: No game with id {infoseek_id} found in ZXDB\n')
        sys.exit(1)
    conn.close()

    with open(TAPES_JSON) as f:
        tapes = json.load(f)

    tapes[md5sum] = {
        "game": name,
        "infoseek": f'{infoseek_id:07}',
        "tape": tape,
        "url": url
    }

    with open(TAPES_JSON, 'w') as f:
        json.dump(tapes, f, indent=4, sort_keys=True)
        f.write('\n')

    print(f'Added tape {md5sum}:')
    print(json.dumps(tapes[md5sum], indent=4))

def add_tape(arg, reason, machine, force):
    games = get_games()
    tapes = get_tapes()
    if os.path.isfile(arg):
        with open(arg, 'rb') as f:
            tape_sum = hashlib.md5(f.read()).hexdigest()
        if tape_sum not in tapes:
            sys.stderr.write(f'ERROR: "{tape}" ({tape_sum}) not recognised\n')
            sys.exit(1)
        zxdb_id = tapes[tape_sum]['infoseek']
    elif len(arg) == 32:
        if arg not in tapes:
            sys.stderr.write(f'ERROR: {arg} not recognised\n')
            sys.exit(1)
        zxdb_id = tapes[arg]['infoseek']
    else:
        zxdb_id = arg.rjust(7, '0')

    name = games[zxdb_id]['name']
    existing_tapes = defaultdict(dict)
    with open(TAPES_TXT) as f:
        for line in f:
            iid, g_reason, g_machine, g_name = line.strip().split(None, 3)
            existing_tapes[iid][g_machine] = (g_reason, g_name)
    if zxdb_id in existing_tapes:
        if not force:
            sys.stderr.write(f'{zxdb_id} ({name}) already in {os.path.basename(TAPES_TXT)}; use -f to force\n')
            sys.exit(1)
        print(f'Removing existing entry for {zxdb_id} ({name}) from {os.path.basename(TAPES_TXT)}')
    existing_tapes[zxdb_id][machine] = (reason, name)
    if set(existing_tapes[zxdb_id]) == {'48K', '128K', '*'}:
        del existing_tapes[zxdb_id]['*']
    with open(TAPES_TXT, 'w') as f:
        for iid in sorted(existing_tapes):
            for g_machine, (g_reason, g_name) in existing_tapes[iid].items():
                f.write(f'{iid} {g_reason} {g_machine:<4} {g_name}\n')
    print(f'Added to {os.path.basename(TAPES_TXT)}: {zxdb_id} {reason} {machine:<4} {name}')

args = sys.argv[1:]

if len(args) < 2:
    print_usage()

if args[0] == '-f':
    force = True
    args = args[1:]
else:
    force = False

if len(args) < 2:
    print_usage()

if args[0].endswith('.t2s'):
    t2sfile = sys.argv[1]
    infoseek_id = int(sys.argv[2])
    add_new_tape(t2sfile, infoseek_id)
else:
    arg = args[0]
    reason = args[1]
    machine = args[2] if len(args) > 2 else '*'
    if reason not in REASONS:
        print_usage()
    if machine not in ('*', '48K', '128K'):
        print_usage()
    add_tape(arg, reason, machine, force)
