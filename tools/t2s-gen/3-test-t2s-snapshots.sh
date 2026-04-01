#!/usr/bin/env bash
if ! command -v fuse &> /dev/null; then
  echo "ERROR: fuse: command not found"
  exit 1
fi

odir=t2s-snapshots-tested
mkdir -p $odir/{failed,ok} t2s-{failed/broken-snapshot,ok}
count=0

shopt -s nullglob # Expand glob to empty string when no filenames match
for z in t2s-snapshots/*.z80; do
  fuse --no-confirm-actions "$z" &> /dev/null
  read -p "$z: OK? [Y/n/lr/ft/:new-name] " ok
  name=$(basename "$z" .z80)
  t=${name}.t2s
  if [[ $ok == "n" ]]; then
    mv -v "$z" $odir/failed
    find t2s -name $t -exec mv -v {} t2s-failed/broken-snapshot \;
  elif [[ $ok == "lr" ]]; then
    t2s=$(find t2s -name $t)
    echo "--sim-load-config 'load=LOAD \"\": RUN'" >> "$t2s"
    rm -v "$z"
    count=$(( count + 1 ))
  elif [[ $ok == "ft" ]]; then
    t2s=$(find t2s -name $t)
    echo "--sim-load-config finish-tape=1" >> "$t2s"
    rm -v "$z"
    count=$(( count + 1 ))
  else
    mv -v "$z" $odir/ok
    if [[ ${ok:0:1} == ":" ]]; then
      new_name=${ok/:}
      old_z80=${name}.z80
      new_z80=${new_name}.z80
      new_t2s=${new_name}.t2s
      find t2s -name $t -exec mv -v {} t2s-ok/$new_t2s \;
      sed -i "s/^$old_z80/$new_z80/" t2s-ok/$new_t2s
    else
      find t2s -name $t -exec mv -v {} t2s-ok \;
    fi
  fi
  echo
done

if [[ $count -gt 0 ]]; then
  echo -e "\n$count t2s file(s) updated; re-run ./2-t2s-test.sh"
fi
