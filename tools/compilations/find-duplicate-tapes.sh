#!/usr/bin/bash
if [[ $# -lt 1 ]] || [[ $# -gt 2 ]]; then
  echo -e "Usage: $(basename $0) TO_BE_UPLOADED_DIR [UPLOADED_DIR]\n"
  echo "  Find duplicate tapes in TO_BE_UPLOADED_DIR, or in TO_BE_UPLOADED_DIR"
  echo "  and UPLOADED_DIR."
  exit 1
fi

TAP='-[0-9][0-9][0-9][0-9][0-9][0-9][0-9].tap'
TZX='-[0-9][0-9][0-9][0-9][0-9][0-9][0-9].tzx'

if [[ $# -eq 1 ]]; then
  find $1 -type f -a \( -iname "*$TAP" -o -iname "*$TZX" \) | while read t; do
    echo $(basename "${t:0:-4}")
  done | sort | uniq -d | while read d; do
    find $1 -type f -name "$d.*"
    echo
  done
else
  find $1 -type f -a \( -iname "*$TAP" -o -iname "*$TZX" \) > uploaded.txt
  find $2 -type f -a \( -iname "*$TAP" -o -iname "*.TZX" \) | while read t; do
    b=$(basename "${t:0:-4}")
    grep -q "/$b" uploaded.txt && echo "$t": $(grep "/$b" uploaded.txt)
  done
  rm -f uploaded.txt
fi
