#!/usr/bin/bash -x
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

if [[ -z $ZXDB ]]; then
  echo "ERROR: ZXDB environment variable not defined"
  exit 1
fi

if ! command -v sqlite3 &> /dev/null; then
  echo "ERROR: sqlite3: command not found"
  exit 1
fi

if ! command -v unzip &> /dev/null; then
  echo "ERROR: unzip: command not found"
  exit 1
fi

if ! command -v wget &> /dev/null; then
  echo "ERROR: wget: command not found"
  exit 1
fi

mkdir -p $(dirname $ZXDB)
rm -f ZXDB_mysql.sql.zip ZXDB_mysql.sql ZXDB_to_SQLite.py ZXDB_sqlite.sql
wget https://github.com/zxdb/ZXDB/raw/master/ZXDB_mysql.sql.zip &&
unzip ZXDB_mysql.sql.zip &&
wget https://github.com/zxdb/ZXDB/raw/master/scripts/ZXDB_to_SQLite.py &&
python3 ZXDB_to_SQLite.py ZXDB_mysql.sql &&
rm -f "$ZXDB"
sqlite3 "$ZXDB" < ZXDB_sqlite.sql &&
sqlite3 "$ZXDB" < "$T2SFILES_HOME/tools/library_titles.sql" &&
rm -f ZXDB_mysql.sql.zip ZXDB_mysql.sql ZXDB_to_SQLite.py ZXDB_sqlite.sql
ls -l "$ZXDB"
