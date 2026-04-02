#!/usr/bin/env python3
import argparse
import os
import sys

from libt2s import (COMPILATION_TYPES, get_games, get_tapes, get_exp_t2s_names,
                    get_t2s_names, get_skipped_tapes, get_skipped_reason,
                    get_non_compilations, get_duplicates, get_t2s_by_iid)

def run(options):
    games = all_games = get_games()
    tapes = get_tapes()
    t2s_names = get_t2s_names()
    skipped_tapes = get_skipped_tapes()
    non_compilations = get_non_compilations()
    duplicates = get_duplicates()
    t2s_by_iid = get_t2s_by_iid(games, tapes)

    if options.ids:
        games = {}
        for i in options.ids:
            iid = i.rjust(7, '0')
            games[iid] = all_games[iid]

    for iid, entry in games.items():
        if entry['genre'] in COMPILATION_TYPES or 'contents' in entry:
            if iid in non_compilations or iid in skipped_tapes:
                continue
            lines = []
            name = entry['name']
            e_t2s_files = t2s_by_iid[iid]
            if options.bbcode:
                lines.append(f'[url="https://spectrumcomputing.co.uk/entry/{iid}"]{name}[/url]')
            else:
                lines.append(f'{iid} {name}')
            contents = entry.get('contents')
            missing_t2s = 0
            prefixed = False
            if contents:
                contents_known = True
                has_all_t2s = True
                t2s_name = t2s_names[iid][0]
                for item in contents:
                    c_iid, c_name = item.split(' ', 1)
                    if c_iid in duplicates:
                        continue
                    if c_iid.startswith('*') and options.hide_nag:
                        continue
                    status = suffix = ''
                    item_t2s_files = t2s_by_iid[c_iid][:]
                    if c_iid in all_games:
                        machines = all_games[c_iid]['machines']
                    else:
                        machines = entry['machines']
                    if not machines:
                        machines = '48K'
                    skipped_reason = get_skipped_reason(skipped_tapes, c_iid, machines)
                    if item_t2s_files:
                        suffix = ' ({})'.format(', '.join(item_t2s_files))
                    elif skipped_reason:
                        if options.hide_skipped:
                            continue
                        status = f' ({skipped_reason})'
                    else:
                        if c_iid == '-------':
                            e_t2s_files = t2s_by_iid[iid]
                        elif c_iid.startswith('-'):
                            e_t2s_files = t2s_by_iid[c_iid.replace('-', '0')]
                        else:
                            e_t2s_files = t2s_by_iid[iid]
                        exp_c_t2s_names = tuple(f'-{n}' for n in get_exp_t2s_names(c_name, c_name))
                        for e_t2s_file in e_t2s_files:
                            if e_t2s_file[:-4].endswith(exp_c_t2s_names):
                                item_t2s_files.append(e_t2s_file)
                                suffix = f' ({e_t2s_file})'
                                break
                        else:
                            has_all_t2s = False
                            missing_t2s += 1
                    show_item = True
                    if suffix:
                        if options.hide:
                            show_item = False
                    elif options.hide_no_t2s:
                        show_item = False
                    if not c_iid.isdigit() and options.has_zxdb_id:
                        show_item = False
                    if not options.prefixed:
                        for item_t2s_file in item_t2s_files:
                            if item_t2s_file.startswith(t2s_name):
                                break
                        else:
                            show_item = False
                    item_has_tape = 'tapes' in games.get(c_iid, {})
                    if options.has_tape and item_has_tape:
                        show_item = False
                    if options.has_no_tape and not item_has_tape:
                        show_item = False
                    if show_item:
                        if options.bbcode:
                            zxdb_id = c_iid.lstrip('*')
                            if zxdb_id.isdigit():
                                zxdb_id = zxdb_id.rjust(7, '0')
                                lines.append(f'- [url="https://spectrumcomputing.co.uk/entry/{zxdb_id}"]{c_name}[/url]')
                            else:
                                lines.append(f'  {c_name}')
                        else:
                            lines.append(f'  {c_iid} {c_name}{suffix}{status}')
            else:
                contents_known = False
                has_all_t2s = False
                lines.append('  Contents unknown')
            if options.missing_t2s and has_all_t2s:
                continue
            if missing_t2s > options.max_missing > 0:
                continue
            if missing_t2s < options.min_missing:
                continue
            if not contents_known and options.known_contents:
                continue
            if contents_known and options.unknown_contents:
                continue
            if len(lines) > 1:
                for line in lines:
                    print(line)

parser = argparse.ArgumentParser(
    usage='{} [options] [ID [ID...]]'.format(os.path.basename(sys.argv[0])),
    description="List contents of compilations.",
    add_help=False
)
group = parser.add_argument_group('Options')
parser.add_argument('ids', help=argparse.SUPPRESS, nargs='*')
group.add_argument('-b', dest='bbcode', action='store_true',
                   help="Output in BBCode format.")
group.add_argument('-c', dest='prefixed', action='store_false',
                   help="Hide compilation items that don't have the compilation title in their t2s filename.")
group.add_argument('-G', dest='hide_nag', action='store_true',
                   help="Hide compilation items that are not games.")
group.add_argument('-h', dest='hide', action='store_true',
                   help="Hide compilation items that have t2s files.")
group.add_argument('-H', dest='hide_no_t2s', action='store_true',
                   help="Hide compilation items that do not have t2s files.")
group.add_argument('-i', dest='has_zxdb_id', action='store_true',
                   help="Hide compilation items with no ZXDB ID.")
group.add_argument('-k', dest='known_contents', action='store_true',
                   help="Limit output to entries with known contents.")
group.add_argument('-K', dest='unknown_contents', action='store_true',
                   help="Limit output to entries with unknown contents.")
group.add_argument('-m', dest='max_missing', metavar='MAX', type=int, default=0,
                   help="Limit output to entries with no more than MAX missing t2s files.")
group.add_argument('-M', dest='min_missing', metavar='MIN', type=int, default=0,
                   help="Limit output to entries with at least MIN missing t2s files.")
group.add_argument('-n', dest='missing_t2s', action='store_true',
                   help="Limit output to entries with missing t2s files.")
group.add_argument('-s', dest='hide_skipped', action='store_true',
                   help="Hide compilation items that have skipped tapes (RUI, DEM etc.).")
group.add_argument('-t', dest='has_tape', action='store_true',
                   help="Hide compilation items with their own tapes.")
group.add_argument('-T', dest='has_no_tape', action='store_true',
                   help="Hide compilation items without their own tapes.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())
run(namespace)
