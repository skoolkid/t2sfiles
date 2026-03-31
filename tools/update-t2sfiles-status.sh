#!/usr/bin/env bash
STATUSES="T2S TWM TBM TBI NTA ADD BMD DEM NAG RAH RUI UBT UMT"
LGS=$T2SFILES_HOME/tools/list-games-status.py

sdir=$(mktemp -d)

for s in $STATUSES; do
  mkdir $sdir/$s
done

rm -f status.json

for s in $STATUSES; do
  $LGS -c -h -s $s ALL > $sdir/$s/index.html
done
$LGS -c -h ALL > $sdir/index.html

rsync -rv $sdir/ $WEBHOST_USER@skoolkit.ca:skoolkit.ca/t2sfiles
rm -rf $sdir
rm -f status.json
