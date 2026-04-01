#!/usr/bin/bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

ZXDB_ID=$1
if [[ -z $ZXDB_ID ]]; then
  ZXDB_ID=$(basename "$(pwd)" | cut -c1-7)
  if [[ $ZXDB_ID != 00[0-9][0-9][0-9][0-9][0-9] ]]; then
    echo "Usage: $(basename $0) ZXDB_ID"
    exit 1
  fi
fi
$T2SFILES_HOME/tools/magazine-tapes.py -cs $ZXDB_ID
