#!/usr/bin/env python3
import argparse
from io import StringIO
import os
import sys
from urllib.request import Request, urlopen

def abort(msg=None):
    sys.stderr.write(msg or """
Either place t2s2sna.py alongside tap2sna.py in the SkoolKit root directory, or
set the SKOOLKIT_HOME environment variable to the full path to the SkoolKit
root directory.
""")
    sys.exit(1)

try:
    from skoolkit.tap2sna import SkoolKitArgumentParser, main
except ImportError:
    SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
    if not SKOOLKIT_HOME:
        sys.stderr.write('tap2sna.py not found and SKOOLKIT_HOME is not set.\n')
        abort()
    if not os.path.isdir(SKOOLKIT_HOME):
        sys.stderr.write(f'tap2sna.py not found and SKOOLKIT_HOME directory ({SKOOLKIT_HOME}) not found.\n')
        abort()
    sys.path.insert(0, SKOOLKIT_HOME)
    try:
        from skoolkit.tap2sna import SkoolKitArgumentParser, main
    except ImportError:
        sys.stderr.write(f'tap2sna.py not found in SKOOLKIT_HOME ({SKOOLKIT_HOME}).\n')
        abort()

def _parse_t2s(t2s):
    parser = SkoolKitArgumentParser()
    args = []
    for line in t2s.split('\n'):
        args.extend(parser.convert_arg_line_to_args(line))
    url, snapshot, options = args[0], args[1], args[2:]
    return (*options, url, snapshot)

def _get_t2s(t2s_name):
    if os.path.isfile(t2s_name):
        print(f'Reading local file {t2s_name}')
        with open(t2s_name) as f:
            return f.read()
    subdir = t2s_name[0] if t2s_name[0].isalpha() else '0'
    url = f'https://github.com/skoolkid/t2sfiles/raw/master/t2s/{subdir}/{t2s_name}'
    print(f'Downloading {url}')
    r = Request(url)
    try:
        u = urlopen(r, timeout=30)
        t2s = StringIO()
        while 1:
            data = u.read(4096)
            if not data:
                break
            t2s.write(data.decode('utf-8'))
        return t2s.getvalue()
    except Exception as e:
        error_msg = e.args[0] if e.args else e
        abort(f'Failed to download {t2s_name}: {error_msg}\n')

def run(t2s_name):
    t2s = _get_t2s(t2s_name)
    tap2sna_args = _parse_t2s(t2s)
    main(tap2sna_args)

parser = argparse.ArgumentParser(
    usage='%(prog)s file.t2s',
    description="Run tap2sna.py on file.t2s. If file.t2s doesn't exist locally, it is downloaded from the t2sfiles repository.",
    add_help=False
)
parser.add_argument('t2s', help=argparse.SUPPRESS, nargs='?')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.t2s:
    parser.exit(2, parser.format_help())
run(namespace.t2s)
