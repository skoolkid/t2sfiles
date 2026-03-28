#!/usr/bin/env bash
cd $T2SFILES_HOME
index=$(mktemp)
tools/list-games-status.py -h ALL > $index
t2sfiles=$(mktemp)
find t2s -name '*.t2s' | sort | cut -c7- > $t2sfiles
while read t; do
  grep -q $t $index || echo $t
done < $t2sfiles
rm -f $index $t2sfiles
