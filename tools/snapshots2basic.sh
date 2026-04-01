#!/usr/bin/env bash
if ! command -v snapinfo.py &> /dev/null; then
  echo "ERROR: snapinfo.py: command not found"
  exit 1
fi

usage() {
  cat <<EOF
Usage: $(basename $0) [options] SNAPSDIR BASICDIR

  Extract BASIC programs from Z80 snapshots in SNAPSDIR and dump them in
  BASICDIR.

Options:
  -f Overwrite existing BASIC program files
EOF
  exit 1
}

FORCE=0
while getopts ":f" opt; do
  case $opt in
    f) FORCE=1 ;;
    *) usage ;;
  esac
done

shift $((OPTIND - 1))

[[ -z $2 ]] && usage

if [[ ! -d $1 ]]; then
  echo "ERROR: $1: directory not found"
  exit 1
fi
if [[ ! -d $2 ]]; then
  echo "ERROR: $2: directory not found"
  exit 1
fi

SNAPSDIR=$(realpath "$1")
BASICDIR=$(realpath "$2")
errors=$(pwd)/snapshots2basic-errors.log

cd "$BASICDIR"
for b in *.basic; do
  [[ -f $SNAPSDIR/${b%.basic}.z80 ]] || rm -v "$b"
done

cd "$SNAPSDIR"
for z in *.z80; do
  basic=$BASICDIR/${z%.z80}.basic
  if [[ ! -f $basic ]] || [[ $FORCE -eq 1 ]]; then
    echo "Writing $basic"
    snapinfo.py -b "$z" > "$basic"
  fi
done 2>$errors

if [[ -s $errors ]]; then
  echo "There were errors: see $(basename $errors)"
else
  rm -f $errors
fi
