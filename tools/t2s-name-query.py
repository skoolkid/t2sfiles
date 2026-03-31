#!/usr/bin/env python3
import argparse
import re

from libt2s import get_games, get_t2s_names, get_t2s_name_iids, query_t2s_names

def run(qname, options):
    t2s_names = get_t2s_names()
    t2s_name_iids = get_t2s_name_iids(t2s_names)
    games = get_games()
    if options.regex:
        entries = []
        for name in t2s_name_iids:
            if re.match(qname, name):
                entries.extend(query_t2s_names(name, t2s_name_iids, games, t2s_names))
    else:
        entries = query_t2s_names(qname, t2s_name_iids, games, t2s_names)
    if entries:
        for line in entries:
            print(line)
    else:
        print('No titles found')

parser = argparse.ArgumentParser(
    usage='%(prog)s T2SNAME',
    description="List titles that would have a given t2s filename.",
    add_help=False
)
parser.add_argument('qname', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-r', dest='regex', action='store_true',
                   help="Treat T2SNAME as a regular expression.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.qname is None:
    parser.exit(2, parser.format_help())
run(namespace.qname.lower().replace(' ', '-'), namespace)
