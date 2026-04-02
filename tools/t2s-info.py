#!/usr/bin/env python3
import argparse

from libt2s import get_games, get_tapes, parse_t2sfile, get_zxdb_id

ALL_DETAILS_FMT = """
{f}
  {g}
  {i}
  {M} ({m})
  {s}
  {t}
  {T}
  {u}
""".strip()
DEFAULT_FMT = '{f}: {i} {g}'
LIST_ITEM_FMT = '[*][url=\"{s}\"]{g}[/url]'
GAMES_STATUS_FMT = '{i} T2S    {M:<8} {g} ({m})'

def run(t2sfiles, fmt):
    games = get_games()
    tapes = get_tapes()
    for t2sfile in t2sfiles:
        t2s = parse_t2sfile(t2sfile)
        zxdb_id = get_zxdb_id(t2s, games, tapes)
        if zxdb_id is None:
            continue
        game_info = games[zxdb_id]
        fields = {
            'f': t2sfile,
            'g': game_info['name'],
            'i': zxdb_id,
            'm': '128K' if 'machine=128' in t2s.options else '48K',
            'M': game_info['machines'],
            's': f'https://spectrumcomputing.co.uk/entry/{zxdb_id}',
            't': t2s.tape_name,
            'T': t2s.tape_sum,
            'u': t2s.url or 'No download URL'
        }
        print(fmt.format(**fields))

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] game.t2s [game.t2s...]',
    description="""
Print formatted details of t2s file(s). The format is specified by a Python
format string that recognises the following replacement fields:

  {f} - t2s filename (as provided on command line)
  {g} - game name
  {i} - ZXDB id (7 digits, 0-padded)
  {m} - machine simulated (48K or 128K)
  {M} - machines (16K, 16K/48K, 48K, 48K/128K, or 128K)
  {s} - spectrumcomputing.co.uk/entry URL
  {t} - tape filename
  {T} - tape MD5 sum
  {u} - tape download URL
""",
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False
)
parser.add_argument('t2sfiles', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('-a', dest='fmt', action='store_const', const=ALL_DETAILS_FMT,
                   help=f"Print all details.")
group.add_argument('-f', dest='fmt',
                   help=f"Use this format string (default: '{DEFAULT_FMT}').")
group.add_argument('-g', dest='fmt', action='store_const', const=GAMES_STATUS_FMT,
                   help=f"Print details in list-games-status.py format.")
group.add_argument('-l', dest='fmt', action='store_const', const=LIST_ITEM_FMT,
                   help=f"Print a BBCode list item: '{LIST_ITEM_FMT}'.")
namespace, unknown_args = parser.parse_known_args()
if not namespace.t2sfiles or unknown_args:
    parser.exit(2, parser.format_help())
run(namespace.t2sfiles, namespace.fmt or DEFAULT_FMT)
