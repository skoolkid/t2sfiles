#!/usr/bin/env python3
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import os
import re
import sys
from textwrap import dedent

from libt2s import (COMPILATION_TYPES, DATA_ROOT_DIR, T2S_ROOT_DIR,
                    REASONS, T2S, get_games, get_tapes, get_skipped_tapes,
                    get_non_compilations, get_duplicates, get_exceptions,
                    get_zxdb_id)

CACHE_FILE = 'status.json'

MACHINE_NS = 'NS' # Machine type not specified in ZXDB

MACHINES = (MACHINE_NS, '16K', '16K/48K', '48K', '48K/128K', '128K')

NO_T2S = 'TBI'

T2S_WM = 'TWM' # t2s exists but possibly for wrong machine type

T2S_BM = 'TBM' # t2s exists for both 48K and 128K but game may be for only one of them

T2S_REASONS = {
    'T2S': 't2s files',
    T2S_WM: 't2s files possibly for the wrong machine type',
    T2S_BM: 't2s files for both 48K and 128K but game may be for only one of them',
    NO_T2S: 'To be investigated',
}

today = datetime.today().strftime('%Y/%m/%d')
t2s_reasons = '\n'.join(f'{k}: {v}' for k, v in T2S_REASONS.items())
reasons = '\n'.join(f'{k}: {v}' for k, v in REASONS.items())

HEADER = f"""
{today}

{t2s_reasons}
{reasons}

ID      Status Machines Game
--      ------ -------- ----
""".strip()

HEADER_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>t2sfiles</title>
<meta charset="utf-8" />
<style>
body {{ color: black; background-color: #a0a0a0; }}
table {{ margin-top: 10px; }}
th {{ text-align: left; }}
td {{ vertical-align: top; }}
</style>
</head>
<body>
<b>{today} ({status})</b>
<table>
{reasons}
</table>
<table>
<tr><th>ID</th><th>Status</th><th width="400">Game</th><th>Machines</th><th>Compilation</th><th>t2s files</th></tr>
""".strip()

FOOTER_HTML = """
</table>
</body>
</html>
""".strip()

def scan_skipped_tapes(games_by_iid, tapes):
    skipped_tapes = get_skipped_tapes()
    for iid, tape in skipped_tapes.items():
        if iid in games_by_iid:
            game_status = games_by_iid[iid]['status']
            for machine, reason in tape.items():
                game_status[machine == '128K'] = reason

def scan_t2s_files(games_by_iid, games, tapes):
    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for t in sorted(files):
            t2s = os.path.join(root, t)
            tape_sum, machine = None, '48K'
            with open(t2s) as f:
                for line in f:
                    if line.startswith('--tape-sum'):
                        tape_sum = line[11:].rstrip()
                    elif line.startswith('--sim-load-config machine=128'):
                        machine = '128K'
            iid = get_zxdb_id(T2S(t[:-4], [tape_sum]), games, tapes)
            if iid in games_by_iid:
                game = games_by_iid[iid]
                index = 0 if machine == '48K' else 1
                game['status'][index] = 'T2S'
                game['t2s'][index].append('t2s' + t2s[len(T2S_ROOT_DIR):])

def get_t2s_links(t2sfiles, suffix=''):
    if t2sfiles:
        return [f'<a href="https://github.com/skoolkid/t2sfiles/raw/master/{t}">{t[6:]}</a> {suffix}'.rstrip() for t in t2sfiles]
    return ['']

def get_games_by_iid(games, tapes):
    games_by_iid = {}

    # Add games from games.json
    for iid, game_info in games.items():
        games_by_iid[iid] = {
            'name': game_info['name'],
            'machines': game_info['machines'],
            'genre': game_info['genre'],
            'status': [NO_T2S, NO_T2S],
            't2s': [[], []]
        }

    # Add games from tapes.json that are not in games.json
    for md5sum, tape in tapes.items():
        iid = tape['infoseek']
        if iid not in games:
            games_by_iid[iid] = {
                'name': tape['game'],
                'machines': '48K',
                'genre': 'Game',
                'status': [NO_T2S, NO_T2S],
                't2s': [[], []]
            }

    # Scan skipped tapes first
    scan_skipped_tapes(games_by_iid, tapes)

    # Scan t2s files afterwards, to update status to T2S where appropriate
    scan_t2s_files(games_by_iid, games, tapes)

    # Determine which titles appear in compilations
    compilations = defaultdict(int)
    for iid, game_info in games.items():
        for c in game_info.get('contents', ()):
            c_iid = c.split()[0]
            if c_iid.isdigit():
                compilations[c_iid] += 1

    non_compilations = get_non_compilations()
    duplicates = get_duplicates()

    for iid, game_info in games.items():
        if iid in games_by_iid:
            if iid in duplicates:
                del games_by_iid[iid]
                continue
            game = games_by_iid[iid]
            if game_info['genre'] in COMPILATION_TYPES:
                if iid in non_compilations:
                    # This title is a non-compilation (i.e. contains multiple
                    # games in a single program), so keep it
                    continue
                if 'contents' in game_info and NO_T2S in game['status']:
                    for entry in game_info['contents']:
                        c_iid = entry.split(None, 1)[0]
                        if c_iid == '-------':
                            break
                    else:
                        # Every item in this compilation has an entry of its
                        # own, so remove the compilation
                        del games_by_iid[iid]
            elif 'tapes' not in game_info:
                if compilations[iid] == 0:
                    # This title has no tape of its own and doesn't appear in
                    # any compilations for which we have a tape, so remove it
                    del games_by_iid[iid]
                else:
                    for comp in game_info['within']:
                        comp_iid = comp.split(None, 1)[0]
                        if comp_iid not in non_compilations:
                            break
                    else:
                        # The only compilation(s) this title appears in are
                        # non-compilations, so remove the title
                        del games_by_iid[iid]

    return games_by_iid

def run(target_machines, options):
    if options.use_cache and os.path.isfile(CACHE_FILE):
        with open(CACHE_FILE) as f:
            games_by_iid = json.load(f)
    else:
        games = get_games()
        tapes = get_tapes()
        games_by_iid = get_games_by_iid(games, tapes)
        if options.use_cache:
            with open(CACHE_FILE, 'w') as f:
                json.dump(games_by_iid, f)

    exceptions = get_exceptions()

    if options.html:
        lines = []
        count = defaultdict(int)
    elif not options.status:
        print(HEADER)
    for iid in sorted(games_by_iid):
        game = games_by_iid[iid]
        machines = game['machines']
        if machines == '':
            if MACHINE_NS not in target_machines:
                continue
        elif machines not in target_machines:
            continue
        if game['genre'] in COMPILATION_TYPES:
            if not options.compilations:
                continue
            compilation = game['genre']
            suffix = f' [{compilation}]'
        else:
            suffix = ''
            compilation = ''
        name = game['name']
        name_link = f'<a href="https://spectrumcomputing.co.uk/entry/{iid}/">{name}</a>'
        entry_id = f' id="{iid}"'
        if machines == '48K/128K':
            status = game['status']
            if options.html:
                t2sfiles_48 = get_t2s_links(game['t2s'][0])
                t2sfiles_128 = get_t2s_links(game['t2s'][1])
                if options.status in (None, status[0]):
                    lines.append(f'<tr{entry_id}><td>{iid}</td><td>{status[0]}</td><td>{name_link} (48K)</td><td>{machines}</td><td>{compilation}</td><td>{t2sfiles_48[0]}</td></tr>')
                    entry_id = ''
                    count[status[0]] += len(t2sfiles_48)
                    if len(t2sfiles_48) > 1:
                        for t2s in t2sfiles_48[1:]:
                            lines.append(f'<tr><td colspan="5"></td><td>{t2s}</td></tr>')
                if options.status in (None, status[1]):
                    lines.append(f'<tr{entry_id}><td>{iid}</td><td>{status[1]}</td><td>{name_link} (128K)</td><td>{machines}</td><td>{compilation}</td><td>{t2sfiles_128[0]}</td></tr>')
                    count[status[1]] += len(t2sfiles_128)
                    if len(t2sfiles_128) > 1:
                        for t2s in t2sfiles_128[1:]:
                            lines.append(f'<tr><td colspan="5"></td><td>{t2s}</td></tr>')
            else:
                if options.status in (None, status[0]):
                    print(f'{iid} {status[0]}    {machines:<8} {name} (48K){suffix}')
                if options.status in (None, status[1]):
                    print(f'{iid} {status[1]}    {machines:<8} {name} (128K){suffix}')
        else:
            if machines == '128K':
                status = game['status'][1]
                if status != 'T2S' and game['status'][0] == 'T2S':
                    if iid in exceptions[T2S_WM]:
                        status = 'T2S'
                    else:
                        status = T2S_WM
                    t2sfiles = get_t2s_links(game['t2s'][0], '(48K)')
                else:
                    t2sfiles = get_t2s_links(game['t2s'][1])
                    if game['t2s'][0]:
                        if iid not in exceptions[T2S_BM]:
                            status = T2S_BM
                        t2sfiles += get_t2s_links(game['t2s'][0], '(48K)')
            elif machines == '48K':
                status = game['status'][0]
                if status != 'T2S' and game['status'][1] == 'T2S':
                    if iid in exceptions[T2S_WM]:
                        status = 'T2S'
                    else:
                        status = T2S_WM
                    t2sfiles = get_t2s_links(game['t2s'][1], '(128K)')
                else:
                    t2sfiles = get_t2s_links(game['t2s'][0])
                    if game['t2s'][1]:
                        if iid not in exceptions[T2S_BM]:
                            status = T2S_BM
                        t2sfiles += get_t2s_links(game['t2s'][1], '(128K)')
            else:
                status = 'T2S'
                if game['status'][0] == 'T2S':
                    suffix = '' if machines else '(48K)'
                    t2sfiles = get_t2s_links(game['t2s'][0], suffix)
                elif game['status'][1] == 'T2S':
                    suffix = '' if machines else '(128K)'
                    t2sfiles = get_t2s_links(game['t2s'][1], suffix)
                else:
                    t2sfiles = ['']
                    status = game['status'][0]
            if options.status in (None, status):
                if options.html:
                    lines.append(f'<tr{entry_id}><td>{iid}</td><td>{status}</td><td>{name_link}</td><td>{machines}</td><td>{compilation}</td><td>{t2sfiles[0]}</td></tr>')
                    count[status] += len(t2sfiles)
                    if len(t2sfiles) > 1:
                        for t2s in t2sfiles[1:]:
                            lines.append(f'<tr><td colspan="5"></td><td>{t2s}</td></tr>')
                else:
                    print(f'{iid} {status}    {machines:<8} {name}{suffix}')

    if options.html:
        reasons = []
        for reason_dict in (T2S_REASONS, REASONS):
            for status, desc in reason_dict.items():
                if options.status is None or status == options.status:
                    if options.status:
                        status_field = status
                    else:
                        status_field = f'<a href="{status}/">{status}</a>'
                    reasons.append(f'<tr><td>{status_field}</td><td align="right">{count[status]}</td><td>{desc}</td></tr>')
        if options.status:
            status = options.status
        else:
            status = 'ALL statuses'
        print(HEADER_HTML.format(today=today, status=status, reasons='\n'.join(reasons)))
        for line in lines:
            print(line)
        print(FOOTER_HTML)

parser = argparse.ArgumentParser(
    usage='{} [options] MACHINE [MACHINE...]'.format(os.path.basename(sys.argv[0])),
    description="List t2s status of games by machine type. MACHINE may be one of the following:\n\n"
                "  ALL  {}".format('  '.join(MACHINES)),
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False
)
parser.add_argument('machines', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('-c', dest='use_cache', action='store_true',
                   help=f"Read and/or write a cache file ({CACHE_FILE}). (Useful on multiple runs.)")
group.add_argument('-n', dest='compilations', action='store_false',
                   help="Do not show compilation titles.")
group.add_argument('-s', dest='status',
                   help="Limit output to games with this status.")
group.add_argument('-h', dest='html', action='store_true',
                   help="Output in HTML format.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.machines:
    parser.exit(2, parser.format_help())
machines = MACHINES if 'ALL' in namespace.machines else namespace.machines
run(machines, namespace)
