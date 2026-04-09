#!/usr/bin/env bash
if [[ -z $SPECTRUM_TAPES ]]; then
  echo "ERROR: SPECTRUM_TAPES is not set"
  exit 1
fi
if [[ ! -d $SPECTRUM_TAPES ]]; then
  echo "ERROR: $SPECTRUM_TAPES: directory not found"
  exit 1
fi

if ! command -v tapinfo.py &> /dev/null; then
  echo "ERROR: tapinfo.py: command not found"
  exit 1
fi

cd $SPECTRUM_TAPES
errors=gen-tapinfo-errors.txt
rm -f $errors

find spectrumcomputing.co.uk -type f -a \( -iname '*.tap' -o -iname '*.tzx' \) | while read t; do
  infofname="tapinfo/$t.txt"
  if [[ ! -f $infofname ]]; then
    infodirname=$(dirname "$infofname")
    mkdir -p "$infodirname"
    if ! tapinfo.py "$t" > "$infofname" 2> /dev/null; then
      rm -f "$infofname"
      echo "$t" >> $errors
    fi
  fi
done

find tapinfo -type f -iname '*.txt' | while read t; do
  infofile=${t#tapinfo/}
  tapefile=${infofile%.txt}
  [[ -f $tapefile ]] || rm "$t"
done

if [[ -f $errors ]]; then
  echo "Some errors occurred; see $(pwd)/$errors"
fi
