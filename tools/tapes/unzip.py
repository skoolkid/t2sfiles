#!/usr/bin/env python3
import datetime
import os
import sys
import time
import zipfile

if len(sys.argv) != 3:
    print("""
Usage: {} file.zip DESTDIR

  Extract TAP/TZX files from file.zip in DESTDIR (which must exist). Unlike
  Info-ZIP's 'unzip', this writes files with names properly encoded in UTF-8.
""".strip().format(os.path.basename(sys.argv[0])))
    sys.exit(1)

z = zipfile.ZipFile(sys.argv[1])
for info in z.infolist():
    fname = info.filename
    if fname.lower().endswith(('.tap', '.tzx')):
        tfile = os.path.join(sys.argv[2], fname.lstrip('/'))
        tdir = os.path.dirname(tfile)
        if not os.path.isdir(tdir):
            os.makedirs(tdir)
        tape = z.open(fname)
        with open(tfile, 'wb') as f:
            f.write(tape.read())
        mtime = time.mktime(datetime.datetime(*info.date_time).timetuple())
        os.utime(tfile, (mtime, mtime))
        print(f'Wrote {tfile}')
z.close()
