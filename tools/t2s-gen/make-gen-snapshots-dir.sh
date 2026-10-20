#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

if [[ -z $SPECTRUM_TAPES ]]; then
  echo "ERROR: SPECTRUM_TAPES is not set"
  exit 1
fi
if [[ ! -d $SPECTRUM_TAPES ]]; then
  echo "ERROR: $SPECTRUM_TAPES: directory not found"
  exit 1
fi

RESET='\e[0m'
BOLD_RED='\e[1;31m'
GREEN='\e[0;32m'
YELLOW='\e[0;33m'
BOLD_YELLOW='\e[1;33m'

usage() {
  cat <<EOF
Usage: $(basename $0) [options] TARGET_DIR MACHINE|FILE

  Create a directory for running gen-snapshots.py on a set of tapes.
  MACHINE must be one of: 16K 16K/48K 48K 48K/128K 128K.
  FILE may be a file either produced by list-games-status.py, or containing a
  list of tape files to use.

Options:
  -a      Copy all tape files for each title
  -n NUM  Run this many gen-snapshot.py processes (default: 1)
  -q      Don't print 'cd' command when finished
  -t      Assume FILE contains a list of tape files
EOF
  exit 1
}

copy_tape() {
  src=$1
  destdir=$2

  echo -en "$GREEN"
  cp -pv "$src" "$destdir"
  echo -en "$RESET"
}

all=0
num=1
tapes=0
quiet=0
while getopts ":aqtn:" opt; do
  case $opt in
    a) all=1 ;;
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
  for iid in $iids; do
    readarray -t tfiles < <($gameinfo $iid 2>/dev/null | grep -o "${SPECTRUM_TAPES}/.*")
    if (( ${#tfiles[@]} > 1 )); then
      idx=1
      for tfile in "${tfiles[@]}"; do
        if [[ $all == 0 ]]; then
          echo -e "${BOLD_YELLOW}[$idx] ${tfile#"${SPECTRUM_TAPES}/"}${RESET}"
        else
          copy_tape "$tfile" tapes
        fi
        idx=$((idx + 1))
      done
      if [[ $all == 0 ]]; then
        copied=0
        while [[ $copied == 0 ]]; do
          read -p "Enter tape numbers separated by spaces: " -a tnums
          copied=1
          for tnum in "${tnums[@]}"; do
            if [[ $num =~ ^-?[0-9]+$ ]] && (( tnum >= 1 && tnum <= ${#tfiles[@]} )); then
              idx=$((tnum - 1))
              copy_tape "${tfiles[idx]}" tapes
            else
              copied=0
              echo -e "${BOLD_RED}ERROR: Invalid tape number: $tnum${RESET}"
              break
            fi
          done
        done
      fi
    elif (( ${#tfiles[@]} == 1 )); then
      copy_tape "${tfiles[0]}" tapes
    else
      echo -e "${YELLOW}WARNING: No tape found for game with ZXDB ID $iid${RESET}"
    fi
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
