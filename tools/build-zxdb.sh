#!/usr/bin/bash -x
if [[ -z $ZXDB ]]; then
  echo "ERROR: ZXDB environment variable not defined"
  exit 1
fi

sdir=$(realpath $(dirname $0))
mkdir -p $(dirname $ZXDB)
rm -f ZXDB_mysql.sql.zip ZXDB_mysql.sql ZXDB_to_SQLite.py ZXDB_sqlite.sql
wget https://github.com/zxdb/ZXDB/raw/master/ZXDB_mysql.sql.zip &&
unzip ZXDB_mysql.sql.zip &&
wget https://github.com/zxdb/ZXDB/raw/master/scripts/ZXDB_to_SQLite.py &&
python3 ZXDB_to_SQLite.py ZXDB_mysql.sql &&
rm -f "$ZXDB"
sqlite3 "$ZXDB" < ZXDB_sqlite.sql &&
sqlite3 "$ZXDB" < "$sdir/library_titles.sql" &&
rm -f ZXDB_mysql.sql.zip ZXDB_mysql.sql ZXDB_to_SQLite.py ZXDB_sqlite.sql
ls -l "$ZXDB"
