#!/usr/bin/env bash

usage() {
  cat <<EOF
Usage: $(basename $0) [options] TARGET_DIR FILE

  Create one or more subdirectories of TARGET_DIR for running gen-snapshots.py
  on a set of tapes.
  FILE must be a file produced by list-games-status.py.

Options:
  -n NUM  Run this many gen-snapshot.py processes (default: 1)
EOF
  exit 1
}

num=1
while getopts ":n:" opt; do
  case $opt in
    n) num=$OPTARG ;;
    *) usage ;;
  esac
done

shift $((OPTIND - 1))

TARGET_DIR=$1
FILE=$2

[[ -z $FILE ]] && usage

if [[ -e $TARGET_DIR ]]; then
  echo "ERROR: $TARGET_DIR already exists"
  exit 1
fi

if [[ ! -f $FILE ]]; then
  echo "ERROR: $FILE not found"
  exit 1
fi

listgames=$T2SFILES_HOME/tools/list-games-status.py
gameinfo=$T2SFILES_HOME/tools/game-info.py
splittapes=$T2SFILES_HOME/tools/t2s-gen/split-tapes.py
mkgensnapdir=$T2SFILES_HOME/tools/t2s-gen/make-gen-snapshots-dir.sh

for v in listgames gameinfo splittapes mkgensnapdir; do
  util=${!v}
  if [[ ! -f $util ]]; then
    echo "ERROR: $util not found"
    exit 1
  fi
done

t_48=titles-48k.txt
t_128=titles-128k.txt
t_48_128=titles-48k-128k.txt
rm -f $t_48 $t_128 $t_48_128
while read iid status machine name; do
  if [[ -z $name ]]; then
    # No machine specified; default to 48K
    echo "$iid 48K $machine" >> $t_48
  elif [[ $machine = 16K ]] || [[ $machine = 16K/48K ]] || [[ $machine = 48K ]]; then
    echo "$iid $machine $name" >> $t_48
  elif [[ $machine = 128K ]]; then
    echo "$iid $machine $name" >> $t_128
  elif [[ $machine = 48K/128K ]]; then
    if echo "$name" | grep -q '.* (48K)$'; then
      echo "$iid $machine $name" >> $t_48
    else
      echo "$iid $machine $name" >> $t_48_128
    fi
  fi
done < $FILE

if [[ -f $t_48 ]]; then
  $mkgensnapdir -n $num -q "$TARGET_DIR/48k" "$t_48" || exit 1
fi
if [[ -f $t_128 ]]; then
  $mkgensnapdir -n $num -q "$TARGET_DIR/128k" "$t_128" || exit 1
  touch "$TARGET_DIR/128k/machine=128"
fi
if [[ -f $t_48_128 ]]; then
  $mkgensnapdir -n $num -q "$TARGET_DIR/48k-128k" "$t_48_128" || exit 1
  touch "$TARGET_DIR/48k-128k/machine=128"
  touch "$TARGET_DIR/48k-128k/suffix-128k"
fi
rm -f $t_48 $t_128 $t_48_128
echo -e "\nNow: cd $TARGET_DIR"
