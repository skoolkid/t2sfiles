#!/usr/bin/env bash
if ! command -v fuse &> /dev/null; then
  echo "ERROR: fuse: command not found"
  exit 1
fi

SNAPSHOTS_DIR=$1

if [[ -z $SNAPSHOTS_DIR ]]; then
  echo "Usage: $0 SNAPSHOTS_DIR"
  exit 1
fi

odir=snapshots-tested
mkdir -p $odir/{failed,ok}

for z in $SNAPSHOTS_DIR/*.z80; do
  fuse -g 2x --no-confirm-actions "$z" &> /dev/null
  read -p "$z: OK? [Y/n] " ok
  if [[ $ok == "n" ]]; then
    mv -v "$z" $odir/failed
  else
    mv -v "$z" $odir/ok
  fi
  echo
done
