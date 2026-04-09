from collections import defaultdict
import json
import os
import sqlite3
import sys

try:
    import unidecode
except ImportError:
    sys.stderr.write('Failed to import unidecode; have you installed python3-unidecode?\n')
    sys.exit(1)

SPECTRUM_TAPES = os.environ.get('SPECTRUM_TAPES')
if not SPECTRUM_TAPES:
    sys.stderr.write('SPECTRUM_TAPES is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SPECTRUM_TAPES):
    sys.stderr.write(f'SPECTRUM_TAPES={SPECTRUM_TAPES}; directory not found\n')
    sys.exit(1)

MD5SUMS_TXT = f'{SPECTRUM_TAPES}/md5sums.txt'

ACCELERATORS = f'{SPECTRUM_TAPES}/accelerators.txt'

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

ZXDB = os.environ.get('ZXDB')
if not ZXDB:
    sys.stderr.write('ZXDB is not set; aborting\n')
    sys.exit(1)
if not os.path.isfile(ZXDB):
    sys.stderr.write(f'ZXDB={ZXDB}; file not found\n')
    sys.exit(1)

ZXDB_DIR = os.path.dirname(ZXDB)

GAMES_JSON = f'{ZXDB_DIR}/games.json'
TAPES_JSON = f'{ZXDB_DIR}/tapes.json'

DATA_ROOT_DIR = f'{T2SFILES_HOME}/tools/data'
if not os.path.isdir(DATA_ROOT_DIR):
    sys.stderr.write(f'{DATA_ROOT_DIR}: directory not found\n')
    sys.exit(1)

COMPILATIONS_JSON = f'{DATA_ROOT_DIR}/compilations.json'
if not os.path.isfile(COMPILATIONS_JSON):
    sys.stderr.write(f'{COMPILATIONS_JSON}: file not found\n')
    sys.exit(1)

TAPES_TXT = f'{DATA_ROOT_DIR}/tapes.txt'
if not os.path.isfile(TAPES_TXT):
    sys.stderr.write(f'{TAPES_TXT}: file not found\n')
    sys.exit(1)

NON_COMPILATIONS_TXT = f'{DATA_ROOT_DIR}/non-compilations.txt'
if not os.path.isfile(NON_COMPILATIONS_TXT):
    sys.stderr.write(f'{NON_COMPILATIONS_TXT}: file not found\n')
    sys.exit(1)

DUPLICATES_TXT = f'{DATA_ROOT_DIR}/duplicates.txt'

EXCEPTIONS_TXT = f'{DATA_ROOT_DIR}/exceptions.txt'

T2S_ROOT_DIR = f'{T2SFILES_HOME}/t2s'
if not os.path.isdir(T2S_ROOT_DIR):
    sys.stderr.write(f'{T2S_ROOT_DIR}: directory not found\n')
    sys.exit(1)

COMPILATION_TYPES = ('Compilation', 'Covertape', 'Electronic Magazine', 'Compilation: Games')

LANGUAGES = ('-cs', '-cz', '-de', '-en', '-es', '-fr', '-hu', '-it', '-nl', '-pl', '-pt', '-ru', '-sk', '-sv')

T2S_SUFFIXES = (
    '-128k',
    '-side-1', '-side-2', '-side-3', '-side-4',
    '-side-a', '-side-b', '-side-c',
    '-tape-1',
    '-tape-a', '-tape-b', '-tape-c', '-tape-d',
    '-p0', '-p1', '-p1-2', '-p2', '-p3', '-p4',
    '-part-a', '-part-b', '-part-c',
    '-v1', '-v1.0', '-v1.1', '-v1.2', '-v1.3', '-v2', '-v2.0', '-v2.1', '-v3', '-v3.0', '-v3.5', '-v4', '-v4.0', '-v4.2',
    '-release-1', '-release-2', '-release-3',
    *LANGUAGES
)

REASONS = {
    'ADD': 'Add-on to existing game or game engine',
    'BMD': 'Tape is broken: incorrect or missing data',
    'DEM': 'Demo or pre-release',
    'NAG': 'Not a game',
    'NTA': 'No tape available',
    'RAH': 'Requires additional hardware',
    'RUI': 'Requires user input while LOADing',
    'UBT': 'Tape contains unsupported block type',
    'UMT': 'Game does not run on a 48K or 128K Spectrum',
}

ENTRY_SQL = """
SELECT e.title, elt.library_title, g.text, m.text
FROM entries e, entry_library_titles elt, genretypes g, machinetypes m
WHERE e.id = {}
AND e.id = elt.entry_id
AND e.genretype_id = g.id
AND e.machinetype_id = m.id
""".strip()

ENTRIES_SQL = """
SELECT {}
FROM entries e, entry_library_titles elt
WHERE (e.machinetype_id < 6 OR e.machinetype_id IS NULL)
AND (e.genretype_id < 34 OR e.genretype_id IN (80, 81, 82, 111) OR e.genretype_id IS NULL)
AND (e.availabletype_id IN ('A', 'R', '?', 'D', 'S') OR e.availabletype_id IS NULL)
AND e.id = elt.entry_id
""".strip()

RED = '\033[31m'
GREEN = '\033[32m'
CYAN = '\033[36m'
RESET = '\033[0m'

class T2S:
    def __init__(self, name, tape_sums, url=None, snapshot=None, tape_names=(), options=()):
        self.name = name
        self.tape_sum = tape_sums[0]
        self.tape_sum_2 = tape_sums[1] if len(tape_sums) > 1 else None
        self.url = url
        self.snapshot = snapshot
        self.tape_name = tape_names[0] if tape_names else None
        self.tape_name_2 = tape_names[1] if len(tape_names) > 1 else None
        self.options = options

def get_entries_sql(*columns):
    return ENTRIES_SQL.format(','.join(columns))

def get_tape_sums():
    tape_sums = {}
    if os.path.isfile(MD5SUMS_TXT):
        with open(MD5SUMS_TXT, 'rb') as f:
            for bline in f:
                try:
                    line = bline.decode('utf-8')
                except UnicodeDecodeError:
                    line = bline.decode('cp1252')
                md5 = line[:32]
                fname = line[34:].rstrip()
                tape_sums[fname] = md5
    else:
        print(f'WARNING: {MD5SUMS_TXT} not found; consider running gen-md5sums.sh')
    return tape_sums

def get_t2s_suffix(t2s_name, exp_names, iid='0000000'):
    suffix = t2s_name
    for exp_name in exp_names:
        if t2s_name.startswith(exp_name):
            s = t2s_name[len(exp_name):]
            if len(s) < len(suffix):
                suffix = s
    if suffix.startswith(f'-{iid}'):
        suffix = suffix[8:]
    while suffix:
        for s in T2S_SUFFIXES:
            if suffix == s or suffix.startswith(f'{s}-'):
                suffix = suffix[len(s):]
                break
        else:
            break
    return suffix

def get_t2s_name(name, index_name):
    if name and name.startswith(('A ', 'An ', '3D ')):
        index_name = name
    parts = ['']
    prev_c = ''
    for c in unidecode.unidecode(index_name):
        if c.isalnum():
            if c.isupper() and prev_c.islower():
                parts[-1] += '-'
            parts[-1] += c.lower()
        elif c == '&':
            parts.append('and-')
        elif c == '.':
            if prev_c == '.' and not parts[-1].endswith('-'):
                parts[-1] += '-'
            elif prev_c.isdigit():
                parts[-1] += '.'
        elif c == ':':
            parts.append('')
        elif c == "'":
            pass
        elif c == '+':
            parts.append('plus-')
        elif not parts[-1].endswith('-'):
            parts[-1] += '-'
        prev_c = c
    return '-'.join(p.strip('-') for p in parts)

def get_exp_t2s_names(name, index_name):
    names = set()
    names.add(get_t2s_name(name, index_name))
    names.add(get_t2s_name(name.lower(), index_name.lower()))
    for s in ("'", "."):
        names.add(get_t2s_name(name.replace(s, '-'), index_name.replace(s, '-')))
        names.add(get_t2s_name(name.lower().replace(s, '-'), index_name.lower().replace(s, '-')))
    return names

def get_t2s_names(include_alt=False):
    conn = sqlite3.connect(ZXDB)
    sql = get_entries_sql('e.id', 'e.title', 'elt.library_title')
    t2s_names = {}
    if include_alt:
        for iid, name, index_name in conn.execute(sql):
            t2s_names[f'{iid:07}'] = get_exp_t2s_names(name, index_name)
    else:
        for iid, name, index_name in conn.execute(sql):
            t2s_names[f'{iid:07}'] = (get_t2s_name(name, index_name), name)
    conn.close()
    return t2s_names

def get_t2s_name_iids(t2s_names):
    t2s_name_iids = defaultdict(list)
    for iid, (t2s_name, game_name) in t2s_names.items():
        t2s_name_iids[t2s_name].append(iid)
    return t2s_name_iids

def query_t2s_names(name, t2s_name_iids, games, t2s_names=None):
    qname = name.lower().replace(' ', '-')
    iids = t2s_name_iids.get(qname, ())
    if not iids:
        return ()
    lines = []
    for iid in iids:
        c_suffix = ' ***NOT IN games.json***'
        if iid in games:
            c_suffix = ''
            game = games[iid]
            name = game['name']
            publishers = game['publishers']
            authors = game['authors']
            if publishers == authors == '' and 'within' in game:
                c_iid = game['within'][0][:7]
                if c_iid in games:
                    comp = games[c_iid]
                    c_name = comp['name']
                    publishers = comp['publishers']
                    authors = comp['authors']
                    c_suffix = f' [{c_iid} {c_name}]'
        elif t2s_names and iid in t2s_names:
            name = t2s_names[iid][1]
            publishers = authors = '???'
        else:
            name = publishers = authors = '???'
        lines.append(f'{iid} {name} [{publishers}] [{authors}]{c_suffix}')
    return lines

def find_tape(url, tape_name, tape_md5):
    tape = get_tapes().get(tape_md5)
    if tape is None:
        sys.stderr.write(f'ERROR: Tape not found: url={url} md5={tape_md5}\n')
        sys.exit(1)
    tape_url = tape['url']
    tapefile = f'{SPECTRUM_TAPES}/{tape_url[8:-4]}/{tape_name}'
    if os.path.isfile(tapefile):
        return tapefile
    sys.stderr.write(f'ERROR: {tapefile} not found\n')
    sys.exit(1)

def parse_t2sfile(t2sfile):
    url, snapshot, tape_names, tape_sums, options = None, None, [], [], []
    with open(t2sfile) as f:
        for line in f:
            s_line = line.strip()
            if s_line.startswith(('"https://', 'https://')):
                url = s_line
                if url.startswith('"'):
                    url = url[1:-1]
            elif s_line.endswith(('.z80', '.szx')):
                snapshot = s_line
            elif line.startswith('--tape-name'):
                tape_name = line[11:].strip()
                if tape_name.startswith('"'):
                    tape_name = tape_name[1:-1]
                tape_names.append(tape_name)
            elif line.startswith('--tape-sum'):
                tape_sums.append(line[10:].strip())
            elif line.startswith("--sim-load-config '"):
                options.extend(('--sim-load-config', s_line[19:-1]))
            elif line.startswith('--'):
                if ';' in line:
                    elements = line[:line.index(';')].strip().split(' ', 1)
                else:
                    elements = s_line.split(' ', 1)
                for i, element in enumerate(elements):
                    if element.startswith("'"):
                        elements[i] = elements[i][1:-1]
                options.extend(elements)
    return T2S(os.path.basename(t2sfile)[:-4], tape_sums, url, snapshot, tape_names, options)

def get_zxdb_id(t2s, games, tapes, md5sum=False):
    if isinstance(t2s, T2S):
        t2s_name = t2s.name
        tape_sum = t2s.tape_sum
    else:
        t2s_name = os.path.basename(t2s)[:-4]
        tape_sum = None
        with open(t2s) as f:
            for line in f:
                if line.startswith('--tape-sum'):
                    tape_sum = line[10:].strip()
                    break
    tape = tapes.get(tape_sum)
    zxdb_id = None
    if tape:
        zxdb_id = tape['infoseek']
        game_info = games[zxdb_id]
        candidates = []
        for item in game_info.get('contents', ()):
            iid = item.split(' ', 1)[0]
            if iid.isdigit():
                item_name = games[iid]['name']
                item_t2s_name = get_t2s_name(item_name, games[iid].get('index_name', item_name))
                if t2s_name == item_t2s_name:
                    candidates.append((0, iid))
                    break
                if t2s_name.startswith(f'{item_t2s_name}-'):
                    candidates.append((1, iid))
                elif t2s_name.endswith(f'-{item_t2s_name}'):
                    candidates.append((2, iid))
                elif f'-{item_t2s_name}-' in t2s_name:
                    candidates.append((3, iid))
        if candidates:
            zxdb_id = sorted(candidates)[0][1]
    else:
        print(f'WARNING: Unknown tape in {t2s_name}.t2s', file=sys.stderr)
    if md5sum:
        return zxdb_id, tape_sum
    return zxdb_id

def get_skipped_tapes():
    tapes = {}
    with open(TAPES_TXT) as f:
        for line in f:
            zxdb_id, reason, machine = line.split(None, 3)[:3]
            if machine in ('48K', '128K'):
                tapes.setdefault(zxdb_id, {})[machine] = reason
            else:
                tapes[zxdb_id] = {'48K': reason, '128K': reason}
    return tapes

def get_skipped_reason(skipped_tapes, iid, machine):
    if iid in skipped_tapes:
        skipped_tape = skipped_tapes[iid]
        if machine == '48K/128K':
            reasons = [skipped_tape.get('48K'), skipped_tape.get('128K')]
            if reasons[0] == reasons[1]:
                return reasons[0]
            return ', '.join(f'{m}: {r}' for m, r in skipped_tape.items())
        if machine in ('16K', '16K/48K'):
            return skipped_tape.get('48K')
        return skipped_tape.get(machine)

def get_non_compilations():
    non_compilations = []
    with open(NON_COMPILATIONS_TXT) as f:
        for line in f:
            zxdb_id = line.split(None, 1)[0]
            non_compilations.append(zxdb_id)
    return non_compilations

def get_duplicates():
    duplicates = []
    if os.path.isfile(DUPLICATES_TXT):
        with open(DUPLICATES_TXT) as f:
            for line in f:
                if line.startswith('E '):
                    zxdb_id = line.split(None, 2)[1]
                    duplicates.append(zxdb_id)
    return duplicates

def get_exceptions():
    exceptions = defaultdict(list)
    if os.path.isfile(EXCEPTIONS_TXT):
        with open(EXCEPTIONS_TXT) as f:
            for line in f:
                if line[:7].isdigit():
                    zxdb_id, status = line.split(None, 2)[:2]
                    exceptions[status].append(zxdb_id)
    return exceptions

def _add_game(conn, games, iid):
    for name, index_name, genre, machines in conn.execute(ENTRY_SQL.format(iid)):
        games[iid] = {
            'authors': '',
            'genre': genre,
            'machines': machines.split(' ', 1)[1],
            'name': name,
            'publishers': ''
        }
        if name != index_name:
            games[iid]['index_name'] = index_name
    return games.get(iid)

def get_t2s_by_iid(games, tapes):
    t2s_by_iid = defaultdict(list)
    for root, subdirs, files in sorted(os.walk(T2S_ROOT_DIR)):
        for t in files:
            zxdb_id = get_zxdb_id(os.path.join(root, t), games, tapes)
            if zxdb_id:
                t2s_by_iid[zxdb_id].append(t)
    return t2s_by_iid

def get_games(include_other_contents=True):
    with open(GAMES_JSON) as f:
        games = json.load(f)

    if include_other_contents:
        # Add contents from compilations.json that aren't present in ZXDB
        conn = sqlite3.connect(ZXDB)
        with open(COMPILATIONS_JSON) as f:
            compilations = json.load(f)
        for c_iid, compilation in compilations.items():
            c_name = compilation['name']
            if c_iid not in games:
                print(f'WARNING: No entry for "{c_name}" ({c_iid}) in games.json', file=sys.stderr)
                continue
            for item in compilation['contents']:
                i_iid = item.split(' ')[0]
                if i_iid.isdigit():
                    if i_iid not in games:
                        game = _add_game(conn, games, i_iid)
                        if game:
                            games[i_iid] = game
                        else:
                            print(f'WARNING: No entry for {i_iid} in compilation "{c_name}" ({c_iid})', file=sys.stderr)
                    if i_iid in games:
                        games[i_iid].setdefault('within', []).append(f'{c_iid} {c_name}')
            contents = games[c_iid].setdefault('contents', [])
            contents.extend(compilation['contents'])
        conn.close()

    return games

def _get_duplicate_tapes():
    duplicates_by_iid = defaultdict(list)
    duplicates_by_tape = defaultdict(list)
    if os.path.isfile(DUPLICATES_TXT):
        with open(DUPLICATES_TXT) as f:
            for line in f:
                if line.startswith('T '):
                    md5, zxdb_id = line.split(None, 3)[1:3]
                    duplicates_by_iid[md5].append(zxdb_id)
                elif line.startswith('D '):
                    elements = line.split()[1:]
                    md5 = elements.pop(0)
                    fields = ['']
                    while elements:
                        v = elements.pop(0)
                        if v.startswith('"'):
                            fields[-1] = fields[-1] + v
                        else:
                            fields[-1] = fields[-1] + ' ' + v
                        if v.endswith('"'):
                            fields.append('')
                    url, tape = [s[1:-1] for s in fields[:2]]
                    duplicates_by_tape[md5].append((url, tape))
    return duplicates_by_iid, duplicates_by_tape

def get_tapes():
    if os.path.isfile(TAPES_JSON) and os.stat(TAPES_JSON).st_mtime > os.stat(GAMES_JSON).st_mtime:
        with open(TAPES_JSON) as f:
            return json.load(f)

    games = get_games()
    duplicates_by_iid, duplicates_by_tape = _get_duplicate_tapes()
    tapes = {}
    for iid, game in games.items():
        name = game['name']
        machines = game['machines']
        is_compilation = game['genre'] in COMPILATION_TYPES
        for url, tape_specs in game.get('tapes', ()):
            for tape_spec in tape_specs:
                md5, tape = tape_spec.split(' ', 1)
                if is_compilation and md5 in tapes:
                    # This tape already exists on its own, so don't replace its
                    # details with those of this compilation it belongs to
                    continue
                if iid in duplicates_by_iid.get(md5, ()):
                    # This tape appears in more than one entry, so don't add it
                    # unless it's for the "original" entry
                    continue
                if (url, tape) in duplicates_by_tape.get(md5, ()):
                    # This tape is identical to one that already exists within
                    # the same entry, so don't add it
                    continue
                tapes[md5] = {
                    'game': name,
                    'infoseek': iid,
                    'machines': machines,
                    'tape': tape,
                    'url': url
                }

    with open(TAPES_JSON, 'w') as f:
        json.dump(tapes, f, sort_keys=True, indent=4)
        f.write('\n')

    return tapes
