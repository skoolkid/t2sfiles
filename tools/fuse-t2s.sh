#!/usr/bin/env bash
if [[ -z $SPECTRUM_TAPES ]]; then
  echo "ERROR: SPECTRUM_TAPES is not set"
  exit 1
fi
if [[ ! -d $SPECTRUM_TAPES ]]; then
  echo "ERROR: $SPECTRUM_TAPES: directory not found"
  exit 1
fi

MD5SUMS_TXT="$SPECTRUM_TAPES/md5sums.txt"
if [[ ! -f $MD5SUMS_TXT ]]; then
  echo "ERROR: $MD5SUMS_TXT: file not found; consider running gen-md5sums.sh"
  exit 1
fi

if ! command -v fuse &> /dev/null; then
  echo "ERROR: fuse: command not found"
  exit 1
fi

t2sfile=$1

if [[ -z $t2sfile ]]; then
  echo "$(basename $0) T2SFILE [options]"
  exit 1
fi

if [[ ! -f $t2sfile ]]; then
  echo "ERROR: $t2sfile not found"
  exit 1
fi

tape_sum=$(grep '^--tape-sum' $t2sfile | cut -c12-)
tape=$(grep -m 1 "^$tape_sum" "$MD5SUMS_TXT" | cut -c35-)
if [[ -z $tape ]]; then
  echo "ERROR: Could not find tape with sum $tape_sum"
  exit 1
fi

if [[ ! -f $tape ]]; then
  echo "ERROR: $tape not found"
  exit 1
fi

shift
fuse -g 2x --no-confirm-actions $* "$tape"
