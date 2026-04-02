#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

cd $T2SFILES_HOME
index=$(mktemp)
tools/list-games-status.py -h ALL | grep -Po '(?<=>)[^<]*\.t2s' | sort > $index
t2sfiles=$(mktemp)
find t2s -name '*.t2s' | sort | cut -c7- > $t2sfiles
comm -23 $t2sfiles $index
rm -f $index $t2sfiles
