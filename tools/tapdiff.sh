#!/usr/bin/env bash
if ! command -v tapinfo.py &> /dev/null; then
  echo "ERROR: tapinfo.py: command not found"
  exit 1
fi

if ! command -v cdiff &> /dev/null; then
  echo "ERROR: cdiff: command not found"
  exit 1
fi

usage() {
  cat <<EOF
Usage: $(basename $0) TAPE1 TAPE2

  Show differences between TAPE1 and TAPE2.
EOF
  exit 1
}

TAPE1=$1
TAPE2=$2

[[ -z $TAPE2 ]] && usage

if [[ ! -f $TAPE1 ]]; then
  echo "ERROR: $TAPE1: file not found"
  exit 1
fi
if [[ ! -f $TAPE2 ]]; then
  echo "ERROR: $TAPE2: file not found"
  exit 1
fi

diff -u <(tapinfo.py -d "$TAPE1") <(tapinfo.py -d "$TAPE2") | cdiff
