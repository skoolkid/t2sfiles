#!/usr/bin/env bash
t2sfile=$1

if [[ -z $t2sfile ]]; then
  echo "$(basename $0) T2SFILE [options]"
  exit 1
fi

if [[ ! -f $t2sfile ]]; then
  echo "ERROR: $t2sfile not found"
  exit 1
fi

shift

url=$(grep -o 'https://.*\.zip' $t2sfile)
tape_name=$(grep '^--tape-name' $t2sfile | cut -c13-)
if [[ ${tape_name:0:1} == '"' ]]; then
  tape_name=${tape_name:1}
  tape_name=${tape_name%\"}
fi
if [[ $tape_name == "Golfo Pérsico.tzx" ]]; then
  tape_name='Golfo P'$'\202''rsico.tzx'
fi

path=${url#https://}
path=${path%.zip}
tape="$SPECTRUM_TAPES/$path/$tape_name"

if [[ ! -f $tape ]]; then
  echo "ERROR: $tape not found"
  exit 1
fi

fuse -g 2x --no-confirm-actions $* "$tape"
