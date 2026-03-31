#!/usr/bin/env bash

usage() {
  cat <<EOF
Usage: $(basename $0) [options] TARGET_DIR MACHINE|FILE

  Create a directory for running gen-snapshots.py on a set of tapes.
  MACHINE must be one of: 16K 16K/48K 48K 48K/128K 128K.
  FILE may be a file either produced by list-games-status.py, or containing a
  list of tape files to use.

Options:
  -n NUM  Run this many gen-snapshot.py processes (default: 1)
  -q      Don't print 'cd' command when finished
  -t      Assume FILE contains a list of tape files
EOF
  exit 1
}

num=1
tapes=0
quiet=0
while getopts ":qtn:" opt; do
  case $opt in
    n) num=$OPTARG ;;
    q) quiet=1 ;;
    t) tapes=1 ;;
    *) usage ;;
  esac
done

shift $((OPTIND - 1))

TARGET_DIR=$1
MACHINE_OR_FILE=$2

[[ -z $MACHINE_OR_FILE ]] && usage

if [[ -e $TARGET_DIR ]]; then
  echo "ERROR: $TARGET_DIR already exists"
  exit 1
fi

listgames=$T2SFILES_HOME/tools/list-games-status.py
gameinfo=$T2SFILES_HOME/tools/game-info.py
splittapes=$T2SFILES_HOME/tools/t2s-gen/split-tapes.py

for v in listgames gameinfo splittapes; do
  util=${!v}
  if [[ ! -f $util ]]; then
    echo "ERROR: $util not found"
    exit 1
  fi
done

cwd=$(pwd)
mkdir -p $TARGET_DIR/{snapshots,tapes}
cd $TARGET_DIR

if [[ $tapes == 1 ]]; then
  while read t; do [[ -n $t ]] && cp -pv "$t" tapes; done < $cwd/$MACHINE_OR_FILE
else
  if [[ -f $cwd/$MACHINE_OR_FILE ]]; then
    iids=$(cut -c1-7 < "$cwd/$MACHINE_OR_FILE")
  else
    iids=$($listgames -s TBI $MACHINE_OR_FILE | cut -c1-7)
  fi
  $gameinfo -1 $iids | grep -o "${SPECTRUM_TAPES}/.*" | while read t; do
    cp -pv "$t" tapes
  done
fi

$splittapes tapes $num
[[ $num -gt 1 ]] && rmdir tapes

ln -s $T2SFILES_HOME/tools/add-tape.py
ln -s $T2SFILES_HOME/tools/game-info.py
ln -s $T2SFILES_HOME/tools/t2s-gen/divide-tape.py
ln -s $T2SFILES_HOME/tools/t2s-gen/other-options.py
ln -s $T2SFILES_HOME/tools/tape-info.py

if [[ $quiet == 0 ]]; then
  echo -e "\nNow: cd $(pwd)"
fi
